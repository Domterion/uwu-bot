import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
import time
import asyncio
import asyncpg
from datetime import datetime
from utils import errorhandler
import secrets
from random import choice, randint

heads = "<:uwuheads:517079577072238624>"
tails = "<:uwutails:517081802246979616>"
uwu_emote = "<:uwu:521394346688249856>"


class uwus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = []

    async def cog_check(self, ctx):
        uwulonian = await self.bot.redis.sismember("uwulonians", ctx.author.id)
        if uwulonian != 0:
            return True

        raise (errorhandler.hasUwU(ctx))

    @commands.command(
        aliases=["coinflip"],
        description="Flip a coin. Guess what the result will be if right you get the amount you bet.",
        brief="Flip a coin.",
    )
    async def coin(self, ctx, choice, amount: int):
        async with self.bot.pool.acquire() as conn:
            user_amount = await conn.fetchrow(
                "SELECT uwus FROM user_stats WHERE user_id = $1", ctx.author.id
            )
            choice = choice.lower()
            if amount < 50 or amount > 50000:
                return await ctx.send(
                    "You may not bet less then 50 uwus or more than 50000 on a coinflip",
                    delete_after=30,
                )
            if choice != "heads" and choice != "tails":
                return await ctx.send("Please only use heads or tails", delete_after=30)
            if amount > user_amount["uwus"]:
                return await ctx.send(
                    "You don't have the funds to bet that much", delete_after=30
                )

            status = await ctx.send("Flipping the coin...")
            await asyncio.sleep(2)
            await status.delete()
            side = secrets.choice(["heads", "tails"])
            if side == "heads":
                emote = heads
            else:
                emote = tails

            if choice == side:
                booster = await conn.fetchrow(
                    "SELECT boost_type, boost_amount, active_boosters FROM user_boosters WHERE user_id = $1",
                    ctx.author.id,
                )
                if not booster or booster["boost_type"] == "XP":
                    await conn.execute(
                        "UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2",
                        amount,
                        ctx.author.id,
                    )
                    return await ctx.send(f"{emote} You won {amount} uwus!")
                if booster["boost_type"] == "uwus":
                    amount = amount * booster["boost_amount"]
                    await conn.execute(
                        "UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2",
                        amount,
                        ctx.author.id,
                    )
                    return await ctx.send(
                        f"{emote} You won {amount} uwus! You have an {booster['active_boosters']} activated! Enjoy the extra uwus"
                    )
            else:
                await conn.execute(
                    "UPDATE user_stats SET uwus = user_stats.uwus - $1 WHERE user_id = $2",
                    amount,
                    ctx.author.id,
                )
                return await ctx.send(f"{emote} You lost.")

    @commands.command(
        description="Start a guessing game. Guess au users name from there discriminator and name",
        brief="Start a guessing game.",
    )
    async def guess(self, ctx):
        members = [
            member
            for member in ctx.guild.members
            if member.id is not ctx.author.id and not member.bot
        ]
        if len(members) < 15:
            return await ctx.send(
                "You can only play guessing game if you are in a server with more then 15 members. Join uwus support server if you want to play but don't have 15 members.",
                delete_after=30,
            )
        async with self.bot.pool.acquire() as conn:
            if ctx.channel.id in self.active_games:
                return await ctx.caution(
                    "There is already a guessing game in this channel."
                )
            self.active_games.append(ctx.channel.id)
            e = discord.Embed(
                description="""
Welcome to uwu's guessing game! To win guess the users name based off their avatar and discriminator(#0000)            
You have 30 seconds to guess! Good luck!
"""
            )
            e.set_author(name="Guessing game")

            randmem = choice(members)

            e.add_field(
                name="Info",
                value=f"The users discriminator is {randmem.discriminator}. Hint: Their name starts with {randmem.name[:1]}",
            )
            e.set_image(url=randmem.avatar_url_as(static_format="png"))
            embed = await ctx.send(embed=e)

            def check(amsg):
                return amsg.content == randmem.name

            try:
                name = await self.bot.wait_for("message", timeout=30, check=check)
            except asyncio.TimeoutError:
                await embed.delete()
                self.active_games.remove(ctx.channel.id)
                return await ctx.send(
                    f"Times up! The user was {randmem.name}.".replace("@", "@\u200b")
                )
            try:
                amount = 50
                booster = await conn.fetchrow(
                    "SELECT boost_type, boost_amount, active_boosters FROM user_boosters WHERE user_id = $1",
                    name.author.id,
                )
                if not booster or booster["boost_type"] == "XP":
                    status = await conn.fetchrow(
                        "UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2 RETURNING True",
                        amount,
                        name.author.id,
                    )
                    if status:
                        await embed.delete()
                        self.active_games.remove(ctx.channel.id)
                        return await ctx.send(
                            f"{name.author} guessed correctly and got 50 uwus! It was {randmem.name}."
                        )
                if booster["boost_type"] == "uwus":
                    amount = amount * booster["boost_amount"]
                    status = await conn.fetchrow(
                        "UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2 RETURNING True",
                        amount,
                        name.author.id,
                    )
                    if status:
                        await embed.delete()
                        self.active_games.remove(ctx.channel.id)
                        return await ctx.send(
                            f"{name.author} guessed correctly and got {amount} uwus! It was {randmem.name}. {name.author} has an {booster['active_boosters']} activated! Enjoy the extra uwus"
                        )
            except:
                self.active_games.remove(ctx.channel.id)
                await ctx.send(
                    f"{name.author} got it right but does not have an uwulonian. It was {randmem.name}."
                )

    @commands.command(
        description="Give other people some of your uwus", brief="Give uwus"
    )
    async def give(self, ctx, user: discord.Member, amount: int):
        async with self.bot.pool.acquire() as conn:
            user_amount = await conn.fetchrow(
                "SELECT uwus FROM user_stats WHERE user_id = $1", ctx.author.id
            )
            if (
                await conn.fetchrow(
                    "SELECT user_id FROM user_settings WHERE user_id = $1 OR user_id = $2",
                    ctx.author.id,
                    user.id,
                )
                is None
            ):
                return await ctx.caution("You or the user don't have an uwulonian.")
            if ctx.author.id == user.id:
                return await ctx.caution("You can't give yourself uwus.")
            if amount < 50:
                return await ctx.caution("You can't give less than 50 uwus.")
            if amount > 50000:
                return await ctx.caution("You can't give more then 50000 uwus")
            if amount > user_amount["uwus"]:
                return await ctx.caution("You don't have the funds to give that much")

            await conn.execute(
                "UPDATE user_stats SET uwus = user_stats.uwus - $1 WHERE user_id = $2",
                amount,
                ctx.author.id,
            )
            await conn.execute(
                "UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2",
                amount,
                user.id,
            )
            await ctx.send(f"{uwu_emote} You gave {amount} to {user.name}")

    @commands.command()
    async def scavenge(self, ctx):
        async with self.bot.pool.acquire() as conn:
            uwulonian = await conn.fetchrow(
                "SELECT * FROM user_stats WHERE user_id = $1", ctx.author.id
            )
            if uwulonian["xp"] < 500:
                return await ctx.caution("You must have atleast 500xp to scavenge.")
            if choice(["false", "true"]) == "false":
                xp_lost = randint(100, 300)
                await conn.execute(
                    "UPDATE user_stats SET xp = user_stats.xp - $1, deaths = user_stats.deaths + 1 WHERE user_id = $2",
                    xp_lost,
                    ctx.author.id,
                )
                return await ctx.send(
                    f"You died while scavenging and lost {xp_lost}xp..."
                )
            else:
                xp_won = randint(50, 175)
                booster = await conn.fetchrow(
                    "SELECT boost_type, boost_amount, active_boosters FROM user_boosters WHERE user_id = $1",
                    ctx.author.id,
                )
                if not booster or booster["boost_type"] == "uwus":
                    await conn.execute(
                        "UPDATE user_stats SET xp = user_stats.xp + $1 WHERE user_id = $2",
                        xp_won,
                        ctx.author.id,
                    )
                    return await ctx.send(
                        f"""{uwulonian["username"]} is back from scavenging and gained {xp_won}xp"""
                    )
                if booster["boost_type"] == "XP":
                    xp_won = 50 * booster["boost_amount"]
                    await ctx.send(
                        f"""You have a {booster["boost_amount"]} XP booster active."""
                    )
                    await conn.execute(
                        "UPDATE user_stats SET xp = user_stats.xp + $1 WHERE user_id = $2",
                        xp_won,
                        ctx.author.id,
                    )
                    return await ctx.send(
                        f"""{uwulonian["username"]} is back from scavenging and gained {xp_won}xp"""
                    )
                await conn.execute(
                    "UPDATE user_stats SET xp = user_stats.xp + $1 WHERE user_id = $2",
                    xp_won,
                    ctx.author.id,
                )
                return await ctx.send(
                    f"""{uwulonian["username"]} is back from scavenging and gained {xp_won}xp"""
                )

    @commands.command()
    async def convert(self, ctx, exchange, amount: int):
        async with self.bot.pool.acquire() as conn:
            uwulonian = await conn.fetchrow(
                "SELECT * FROM user_stats WHERE user_id = $1", ctx.author.id
            )
            if exchange.lower() not in ["uwus", "xp"]:
                return await ctx.caution("Please only use uwus or xp.")
            amount_with_e = amount * 1.7
            if exchange.lower() == "xp":
                if uwulonian["xp"] < amount_with_e:
                    return await ctx.caution(
                        "You don't have enough XP to exchange that. (Note: There is a fee)"
                    )
                await conn.execute(
                    "UPDATE user_stats SET xp = user_stats.xp - $1, uwus = user_stats.uwus + $2 WHERE user_id = $3",
                    amount_with_e,
                    amount,
                    ctx.author.id,
                )
                await ctx.send(f"Converted {amount}xp to {amount} uwus")
            if exchange.lower() == "uwus":
                if uwulonian["uwus"] < amount_with_e:
                    return await ctx.caution(
                        "You don't have enough uwus to exchange that. (Note: There is a fee)"
                    )
                await conn.execute(
                    "UPDATE user_stats SET xp = user_stats.xp + $1, uwus = user_stats.uwus - $2 WHERE user_id = $3",
                    amount,
                    amount_with_e,
                    ctx.author.id,
                )
                await ctx.send(f"Converted {amount} uwus to {amount}xp")


def setup(bot):
    bot.add_cog(uwus(bot))
