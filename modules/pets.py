import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
import time
import asyncio
import asyncpg
from datetime import datetime, timezone, timedelta
from utils import errorhandler, extras
from random import randint, choice
import secrets
import aioredis

heartt = "<:heartt:521071307769774080>"
broken_heartt = "<:brokenheartt:521074570707468308>"
beta_servers = [
    513_888_506_498_646_052,
    336_642_139_381_301_249,
    253_716_112_292_839_425,
    509_925_667_241_066_498,
]
caution = "<:caution:521002590566219776>"


class pets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.booster_left_task = self.bot.loop.create_task(self.booster_left())

    async def cog_check(self, ctx):
        uwulonian = await self.bot.redis.sismember("uwulonians", ctx.author.id)
        if uwulonian != 0:
            return True

        raise (errorhandler.hasUwU(ctx))

    async def cog_unload(self):
        try:
            await self.booster_left_task.cancel()
        except:
            pass

    async def booster_left(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(2)
            rows = await self.bot.pool.fetchrow(
                "SELECT user_id, pet_id, active_boosters, expire_time FROM user_boosters ORDER BY expire_time ASC LIMIT 1;"
            )
            if not rows:
                continue
            await extras.sleep_time(rows["expire_time"])
            user = self.bot.get_user(rows["user_id"])
            await user.send(f"Your {rows['active_boosters']} is over!")
            await self.bot.pool.execute(
                "DELETE FROM user_boosters WHERE user_id = $1 AND pet_id = $2",
                rows["user_id"],
                rows["pet_id"],
            )

    @commands.group(
        invoke_without_command=True, description="Does nothing without a subcommand"
    )
    async def pet(self, ctx):
        await ctx.send("No subcommand passed. Valid subcommands adopt, special")

    # TODO Shorten queries in adopt and activate.

    @pet.command(description="Adopt a pet")
    async def adopt(self, ctx):
        async with self.bot.pool.acquire() as conn:
            all_pets = await conn.fetchval(
                "SELECT COUNT(*) FROM user_pets WHERE user_id = $1", ctx.author.id
            )
            user_amount = await conn.fetchrow(
                "SELECT uwus FROM user_stats WHERE user_id = $1", ctx.author.id
            )
            if all_pets >= 3:
                return await ctx.caution("You can only have 3 pets")
            if user_amount["uwus"] < 500:
                return await ctx.caution(
                    "You don't have enough uwus to adopt a pet. *Hint the amount of dailies gained is enough to adopt*"
                )

            animal = None
            cost = None
            gender = choice(["male", "female"])
            e = discord.Embed(
                colour=0x7289DA,
                description="""If you are interested in adopting a pet say which number. If you aren't say "Cancel" """,
            )
            e.set_author(name="Adopt a pet!")
            e.add_field(
                name="[1] Wolf",
                value="uwus 500 This cuddly friend will bring hours of joy",
                inline=False,
            )
            e.add_field(name="[2] Gold Fish", value="uwus 500 The OG pet", inline=False)
            e.add_field(
                name="[3] Birb", value="uwus 1000 *insert birb sounds*", inline=False
            )
            e.add_field(
                name="[4] Cat",
                value="uwus 1500 The purrfect pet for cat lovers",
                inline=False,
            )
            e.add_field(
                name="[5] Doggo",
                value="uwus 1500 You won't have a rufftime with this great pet",
                inline=False,
            )
            e.add_field(
                name="[6] Dragon",
                value="uwus 100,000 Takes all your uwus and burns em!",
                inline=False,
            )
            e.add_field(
                name="[7] uwu",
                value="uwus 999,999,999 If you manage to get uwu you are a legend",
                inline=False,
            )
            e.set_footer(text=f"You have {user_amount['uwus']} uwus")
            pet_embed = await ctx.send(embed=e)
            pet_nums = ["1", "2", "3", "4", "5", "6", "7"]

            def check(amsg):
                return amsg.author == ctx.author

            try:
                pet_adopt = await self.bot.wait_for("message", timeout=30, check=check)
            except asyncio.TimeoutError:
                await pet_embed.delete()
                return await ctx.caution("Adoption timed out")

            if pet_adopt.content.lower() == "cancel":
                return await ctx.send("Cancelled.")
            if pet_adopt.content not in pet_nums:
                return await ctx.caution("Invalid choice.")

            if pet_adopt.content == "1":
                animal = "Wolf"
                cost = 500
            elif pet_adopt.content == "2":
                animal = "Gold Fish"
                cost = 500
            elif pet_adopt.content == "3":
                animal = "Birb"
                cost = 1000
            elif pet_adopt.content == "4":
                animal = "Cat"
                cost = 1500
            elif pet_adopt.content == "5":
                animal = "Doggo"
                cost = 1500
            elif pet_adopt.content == "6":
                animal = "Dragon"
                cost = 100_000
            elif pet_adopt.content == "7":
                animal = "uwu"
                cost = 999_999_999

            if user_amount["uwus"] < cost:
                await pet_embed.delete()
                return await ctx.caution("You can't afford this pet.")

            await conn.execute(
                "INSERT INTO user_pets (user_id, pet_name, pet_type, gender) VALUES ($1, $2, $3, $4)",
                ctx.author.id,
                animal,
                animal,
                gender,
            )
            await conn.execute(
                "UPDATE user_stats SET uwus = user_stats.uwus - $1 WHERE user_id = $2",
                cost,
                ctx.author.id,
            )
            await pet_embed.delete()
            await ctx.send(f"Congratulations on your new pet {animal}!")

    @pet.command(description="Adopt a pet")
    async def special(self, ctx):
        async with self.bot.pool.acquire() as conn:
            all_pets = await conn.fetchval(
                "SELECT COUNT(*) FROM spc_user_pets WHERE user_id = $1", ctx.author.id
            )
            user_amount = await conn.fetchrow(
                "SELECT uwus, level FROM user_stats WHERE user_id = $1", ctx.author.id
            )
            if all_pets >= 2:
                return await ctx.caution("You can't have more then 2 special pets")
            if user_amount["level"] < 10:
                return await ctx.caution(
                    "You must be higher then level 10 to adopt a special pet"
                )
            if user_amount["uwus"] < 500:
                return await ctx.caution(
                    "You don't have enough uwus to adopt a pet. *Hint the amount of dailies gained is enough to adopt*"
                )

            animal = None
            cost = None
            level = None
            gender = choice(["male", "female"])
            e = discord.Embed(
                colour=0x7289DA,
                description="""If you are interested in adopting a special pet say which number. If you aren't say "Cancel" """,
            )
            e.set_author(name="Adopt a special pet!")
            e.add_field(
                name="[1] Tiger",
                value="Level 15 uwus 200,000 Very pawsome animal",
                inline=True,
            )
            e.add_field(
                name="[2] Lion",
                value="Level 20 uwus 250,000 Not the cutest animal...",
                inline=True,
            )
            e.add_field(
                name="[3] Peacock",
                value="Level 30 uwus 250,000 Don't let the beauty get you off track",
                inline=True,
            )
            e.add_field(
                name="[4] Kitten",
                value="Level 50 uwus 1,000,000 My favorite animal :shrug:",
                inline=True,
            )
            e.set_footer(text=f"You have {user_amount['uwus']} uwus")
            pet_embed = await ctx.send(embed=e)
            pet_nums = ["1", "2", "3", "4"]

            def check(amsg):
                return amsg.author == ctx.author

            try:
                pet_adopt = await self.bot.wait_for("message", timeout=30, check=check)
            except asyncio.TimeoutError:
                await pet_embed.delete()
                return await ctx.caution("Adoption timed out")

            if pet_adopt.content.lower() == "cancel":
                await pet_embed.delete()
                return await ctx.caution("Cancelled.")
            if pet_adopt.content not in pet_nums:
                await pet_embed.delete()
                return await ctx.caution("Invalid choice.")

            if pet_adopt.content == "1":
                animal = "Tiger"
                cost = 200_000
                level = 15
            elif pet_adopt.content == "2":
                animal = "Lion"
                cost = 250_000
                level = 20
            elif pet_adopt.content == "3":
                animal = "Peacock"
                cost = 250_000
                level = 30
            elif pet_adopt.content == "4":
                animal = "Kitten"
                cost = 1_000_000
                level = 50

            if user_amount["uwus"] < cost or user_amount["level"] < level:
                await pet_embed.delete()
                return await ctx.send(
                    "You can't afford this pet or you aren't the required level.",
                    delete_after=30,
                )

            await conn.execute(
                """INSERT INTO spc_user_pets (user_id, pet_name, pet_type, gender) VALUES ($1, $2, $3, $4)""",
                ctx.author.id,
                animal,
                animal,
                gender,
            )
            await pet_embed.delete()
            await ctx.send(f"Congratulations on your new special pet {animal}!")

    @commands.command(description="Check your family")
    async def pets(self, ctx, special=None):
        async with self.bot.pool.acquire() as conn:
            pets = await conn.fetch(
                "SELECT * FROM spc_user_pets WHERE user_id = $1", ctx.author.id
            )
            if special is None:
                pets = await conn.fetch(
                    "SELECT * FROM user_pets WHERE user_id = $1", ctx.author.id
                )

            if pets is None:
                return await ctx.caution("You have no pets")
            e = discord.Embed(colour=0x7289DA)
            if special is not None:
                e.set_author(name=f"{ctx.author.name}'s special pets")
                num = 0
                for i in pets:
                    e.add_field(
                        name=pets[num]["pet_name"],
                        value=f"[{pets[num]['pet_id']}] Love {pets[num]['love']}; Gender {pets[num]['gender']}; Born {pets[num]['birthdate'].strftime('%x on %X')}",
                    )
                    num += 1
                if num == 0:
                    e.add_field(
                        name="No pets", value=f"{ctx.author.name} has no special pets"
                    )
            else:
                e.set_author(name=f"{ctx.author.name}'s pets")
                num = 0
                for i in pets:
                    e.add_field(
                        name=pets[num]["pet_name"],
                        value=f"[{pets[num]['pet_id']}] Love {pets[num]['love']}; Gender {pets[num]['gender']}; Born {pets[num]['birthdate'].strftime('%x on %X')}",
                    )
                    num += 1
                if num == 0:
                    e.add_field(name="No pets", value=f"{ctx.author.name} has no pets")
            await ctx.send(embed=e)

    @commands.command(description="Cuddles with your pet", aliases=["cuddle"])
    async def cuddles(self, ctx, *, pet: int = None):
        async with self.bot.pool.acquire() as conn:
            if pet is None:
                return await ctx.caution(
                    "Do uwu pets to find your pets to cuddles with. You need to do uwu cuddle ID replace ID with the pets ID."
                )
            pets = await conn.fetch(
                "SELECT user_id, pet_id FROM user_pets WHERE user_id = $1 AND pet_id = $2",
                ctx.author.id,
                pet,
            )
            if not pets:
                return await ctx.caution("You don't have that pet or it's special.")
            user_cooldown = await self.bot.redis.pttl(
                f"{ctx.author.id}-{ctx.command.qualified_name}-{pet}"
            )
            if user_cooldown == -2:
                await self.bot.redis.execute(
                    "SET",
                    f"{ctx.author.id}-{ctx.command.qualified_name}-{pet}",
                    "cooldown",
                    "EX",
                    3600,
                )

                love = randint(0, 2)
                msg = "Your pet loved the cuddles!"
                cud_msg = "Cuddling!"
                bloop_or_cud = "cuddles"
                cuddle = await ctx.send(cud_msg)
                await asyncio.sleep(5)
                if love == 0:
                    msg = f"Your pet didn't like the {bloop_or_cud}."
                if love == 1 or love == 2:
                    msg = f"Your pet enjoyed the {bloop_or_cud}!"
                await conn.execute(
                    "UPDATE user_pets SET love = user_pets.love + $1 WHERE user_id = $2 AND pet_id = $3",
                    love,
                    ctx.author.id,
                    pet,
                )
                await cuddle.delete()
                await ctx.send(f"{msg} You gained {love} loves!")
            else:
                base_time = user_cooldown / 1000
                seconds = round(base_time, 2)
                hours, remainder = divmod(int(seconds), 3600)
                minutes, seconds = divmod(remainder, 60)
                await ctx.send(
                    f"You can't cuddle that pet for {hours}h {minutes}m {seconds}sec",
                    delete_after=30,
                )

    @commands.command()
    async def entertain(self, ctx, pet: int = None):
        async with self.bot.pool.acquire() as conn:
            if pet is None:
                return await ctx.send(
                    "Do uwu pets special to find your pets to entertain. You need to do uwu entertain ID replace ID with the pets ID."
                )
            pets = await conn.fetch(
                "SELECT user_id, pet_id FROM spc_user_pets WHERE user_id = $1 AND pet_id = $2",
                ctx.author.id,
                pet,
            )
            if not pets:
                return await ctx.caution("You don't have that pet or it isn't special.")
            user_cooldown = await self.bot.redis.pttl(
                f"{ctx.author.id}-{ctx.command.qualified_name}"
            )
            if user_cooldown == -2:
                await self.bot.redis.execute(
                    "SET",
                    f"{ctx.author.id}-{ctx.command.qualified_name}",
                    "cooldown",
                    "EX",
                    7200,
                )
                love = randint(1, 2)
                chance_of_item = randint(1, 100)
                entertain_msges = [
                    "You and your pet are watching a movie together!",
                    "You are buying your pet a new toy.",
                    "You and your pet are playing dress up together!",
                ]
                msg = "Your pet loves the entertainment"
                enter_msg = await ctx.send(choice(entertain_msges))
                await asyncio.sleep(2)
                if love == 0:
                    msg = f"Your pet didn't like the entertainment."
                if chance_of_item < 5 and love != 0:
                    items = [
                        "2x XP",
                        "2x XP",
                        "2x uwus",
                        "2x uwus",
                        "3x XP",
                        "3x uwus",
                        "4x XP",
                        "5x XP",
                    ]
                    item = choice(items)
                    msg = f"Your pet enjoyed the entertainment and found a {item} booster (Note: All boosters only last 24 hours)!"
                    did_insert = await self.bot.pool.fetchval(
                        """INSERT INTO pet_boosters (pet_id, booster_name)
SELECT $1, $2
WHERE (SELECT COUNT(*) FROM pet_boosters WHERE pet_id = $1) < 5
RETURNING True;""",
                        pet,
                        item,
                    )
                    if not did_insert:
                        msg = "You earned a booster but already have 5."
                await conn.execute(
                    "UPDATE spc_user_pets SET love = spc_user_pets.love + $1 WHERE user_id = $2 AND pet_id = $3",
                    love,
                    ctx.author.id,
                    pet,
                )
                await enter_msg.delete()
                await ctx.send(f"{msg} You gained {love} loves!")
            else:
                base_time = user_cooldown / 1000
                seconds = round(base_time, 2)
                hours, remainder = divmod(int(seconds), 3600)
                minutes, seconds = divmod(remainder, 60)
                await ctx.caution(
                    f"You can't entertain again for {hours}h {minutes}m {seconds}sec"
                )

    @commands.group(
        invoke_without_command=True, description="Does nothing without a subcommand"
    )
    async def booster(self, ctx):
        await ctx.send(
            "No subcommand passed. Valid subcommands `activate, sell, and list`",
            delete_after=30,
        )

    @booster.command(description="List all the boosters you have")
    async def list(self, ctx, pet: int = None):
        boosters = await self.bot.pool.fetch(
            "SELECT booster_name FROM pet_boosters WHERE pet_id = $1", pet
        )
        if pet is None:
            return await ctx.caution(
                "Do uwu pets special to find your special pets. You need to do uwu booster list ID replace ID with the pets ID."
            )
        if not boosters:
            return await ctx.caution(
                "You don't have any boosters or you don't have any special pets."
            )
        list_boosters = []
        for i in range(len(boosters)):
            list_boosters.append(boosters[i]["booster_name"])
        await ctx.send(
            f"""Boosters for your pet with ID {pet} are {", ".join(list_boosters)}."""
        )

    @booster.command(description="Sell boosters")
    async def sell(self, ctx, pet: int = None):
        async with self.bot.pool.acquire() as conn:
            user_cooldown = await self.bot.redis.pttl(
                f"{ctx.author.id}-{ctx.command.qualified_name}"
            )
            if user_cooldown == -2:
                await self.bot.redis.execute(
                    "SET",
                    f"{ctx.author.id}-{ctx.command.qualified_name}",
                    "cooldown",
                    "EX",
                    7,
                )
                boosters = await conn.fetchrow(
                    "SELECT booster_name FROM pet_boosters WHERE pet_id = $1", pet
                )
                if pet is None:
                    return await ctx.caution(
                        "Do uwu pets special to find your sepcial pets. You need to do uwu booster sell ID replace ID with the pets ID."
                    )
                if boosters is None:
                    return await ctx.caution(
                        "You don't have any boosters or you don't have any special pets."
                    )

                e = discord.Embed(
                    color=0x7289DA,
                    description=f"Welcome to uwus shop! Here you can sell your boosters. The uwus/xp earned for selling each booster is listed below! Reply with the number of the booster you would like to sell.",
                )
                e.set_author(name="Sell your boosters!")
                e.add_field(name="[1] 2x XP", value="100 uwus", inline=False)
                e.add_field(name="[2] 2x uwus", value="100 uwus", inline=False)
                e.add_field(name="[3] 3x XP", value="300 uwus", inline=False)
                e.add_field(name="[4] 3x uwus", value="300 uwus", inline=False)
                e.add_field(name="[5] 4x XP", value="700 uwus 200 XP", inline=False)
                e.add_field(name="[6] 5x XP", value="1000 uwus 500 XP", inline=False)
                xp_from = None
                uwus = None
                option = None
                list_embed = await ctx.send(embed=e)

                def check(amsg):
                    return amsg.author == ctx.author

                try:
                    sell_booster = await self.bot.wait_for(
                        "message", timeout=30, check=check
                    )
                except asyncio.TimeoutError:
                    await list_embed.delete()
                    return await ctx.caution("Sell timed out")

                booster_nums = ["1", "2", "3", "4", "5", "6"]
                if sell_booster.content not in booster_nums:
                    await list_embed.delete()
                    return await ctx.caution("Invalid number.")

                if sell_booster.content == "1":
                    uwus = 100
                    option = "2x XP"
                elif sell_booster.content == "2":
                    uwus = 100
                    option = "2x uwus"
                elif sell_booster.content == "3":
                    uwus = 300
                    option = "3x XP"
                elif sell_booster.content == "4":
                    uwus = 300
                    option = "3x uwus"
                elif sell_booster.content == "5":
                    uwus = 700
                    xp_from = 200
                    option = "4x XP"
                elif sell_booster.content == "6":
                    uwus = 1000
                    xp_from = 500
                    option = "5x XP"
                del_conf = await conn.fetchval(
                    "DELETE FROM pet_boosters WHERE booster_id = (SELECT booster_id FROM pet_boosters WHERE pet_id = $1 AND booster_name = $2 LIMIT 1) AND pet_id = $1 RETURNING True",
                    pet,
                    option,
                )
                if not del_conf:
                    return await ctx.caution(f"You don't have a {option} booster.")
                if xp_from:
                    await conn.execute(
                        "UPDATE user_stats SET uwus = user_stats.uwus + $1, xp = user_stats.xp + $2 WHERE user_id = $3",
                        uwus,
                        xp_from,
                        ctx.author.id,
                    )
                    await list_embed.delete()
                    return await ctx.send(
                        f"Sold your {option} for {uwus} uwus and {xp_from} xp."
                    )

                await conn.execute(
                    "UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2",
                    uwus,
                    ctx.author.id,
                )
                await list_embed.delete()
                return await ctx.send(f"Sold your {option} for {uwus} uwus.")

            else:
                base_time = user_cooldown / 1000
                seconds = round(base_time, 2)
                hours, remainder = divmod(int(seconds), 3600)
                minutes, seconds = divmod(remainder, 60)

                await ctx.caution(
                    f"You can't sell a booster again for {hours}h {minutes}m {seconds}sec"
                )

    @booster.command()
    async def activate(self, ctx, pet: int = None, *, booster_type=None):
        async with self.bot.pool.acquire() as conn:
            boosters_1 = await conn.fetchrow(
                "SELECT pet_name, pet_id FROM spc_user_pets WHERE user_id = $1 AND pet_id = $2",
                ctx.author.id,
                pet,
            )
            if pet is None:
                return await ctx.caution(
                    "Do uwu pets special to see the special pets you have."
                )
            if boosters_1 is None:
                return await ctx.caution(
                    "You don't have any boosters or you don't have any special pets."
                )
            boosters = ["2x XP", "2x uwus", "3x XP", "3x uwus", "4x XP", "5x XP"]
            boosters_lower = ["2x xp", "2x uwus", "3x xp", "3x uwus", "4x xp", "5x xp"]
            if booster_type is None or booster_type.lower() not in boosters_lower:
                return await ctx.send(
                    f"""Invalid booster type. Valid `{", ".join(boosters)}`"""
                )
            booster_left = await conn.fetchrow(
                f"SELECT expire_time, active_boosters FROM user_boosters WHERE user_id = $1",
                ctx.author.id,
            )
            if booster_left is None or not booster_left:
                boost_amount = None
                boost_type = None
                if booster_type.lower() == "2x xp":
                    boost_amount = 2
                    boost_type = "XP"
                elif booster_type.lower() == "2x uwus":
                    boost_amount = 2
                    boost_type = "uwus"
                elif booster_type.lower() == "3x xp":
                    boost_amount = 3
                    boost_type = "XP"
                elif booster_type.lower() == "3x uwus":
                    boost_amount = 3
                    boost_type = "uwus"
                elif booster_type.lower() == "4x xp":
                    boost_amount = 4
                    boost_type = "XP"
                elif booster_type.lower() == "5x xp":
                    boost_amount = 5
                    boost_type = "XP"
                del_conf = await conn.fetchval(
                    "DELETE FROM pet_boosters WHERE booster_id = (SELECT booster_id FROM pet_boosters WHERE pet_id = $1 AND booster_name = $2 LIMIT 1) AND pet_id = $1 RETURNING True",
                    pet,
                    booster_type,
                )
                if not del_conf:
                    return await ctx.caution(
                        f"You don't have a {booster_type} booster."
                    )
                end_time = datetime.utcnow() + timedelta(days=1)
                await conn.execute(
                    """INSERT INTO user_boosters (pet_id, active_boosters, boost_amount, boost_type, user_id, expire_time) 
VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (pet_id) DO UPDATE SET pet_id = $1, active_boosters = $2, boost_amount = $3, boost_type = $4, user_id = $5, expire_time = $6""",
                    pet,
                    booster_type,
                    boost_amount,
                    boost_type,
                    ctx.author.id,
                    end_time,
                )
                return await ctx.send(f"Activated {booster_type} booster for 24 hours.")

            time_left = booster_left["expire_time"] - datetime.utcnow()
            hu_time_left = time_left.total_seconds()
            seconds = round(hu_time_left, 2)
            hours, remainder = divmod(hu_time_left, 3600)
            minutes, seconds = divmod(remainder, 60)
            return await ctx.caution(
                f"You already have a {booster_left['active_boosters']}. It ends in {int(hours)}h {int(minutes)}m {int(seconds)}sec"
            )

    @commands.command()
    async def release(self, ctx, special: bool, pet: int = None):
        async with self.bot.pool.acquire() as conn:
            if pet is None:
                return await ctx.caution("Do uwu pets to find your pets to release.")
            pets = None
            if special is False:
                pets = await conn.fetchrow(
                    "SELECT user_id, pet_id FROM user_pets WHERE user_id = $1 AND pet_id = $2",
                    ctx.author.id,
                    pet,
                )
            if special is True:
                pets = await conn.fetchrow(
                    "SELECT user_id, pet_id FROM spc_user_pets WHERE user_id = $1 AND pet_id = $2",
                    ctx.author.id,
                    pet,
                )
            if not pets:
                return await ctx.caution("You don't have that pet or it's special.")
            else:
                if special is True:
                    await conn.execute(
                        "DELETE FROM spc_user_pets WHERE pet_id = $1 AND user_id = $2",
                        pet,
                        ctx.author.id,
                    )
                if special is False:
                    await conn.execute(
                        "DELETE FROM user_pets WHERE pet_id = $1 AND user_id = $2",
                        pet,
                        ctx.author.id,
                    )
                await ctx.send(
                    f"""Released your {pets["pet_id"]}. Special pet: {special}"""
                )


def setup(bot):
    bot.add_cog(pets(bot))
