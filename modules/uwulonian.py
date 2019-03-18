import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
import time
import asyncio
from random import choice
from utils import errorhandler, extras
from PIL import Image, ImageSequence, ImageFont, ImageDraw, ImageColor
from io import BytesIO


class uwulonian(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if await self.bot.pool.fetchrow(
            "SELECT user_id FROM user_settings WHERE user_id = $1", ctx.author.id
        ):
            return True

        raise (errorhandler.hasUwU(ctx))

    def do_profile(self, author, avy, color):
        with Image.open("assets/profbg.png") as prof:
            font = ImageFont.truetype("assets/Comfortaa-Regular.ttf", 29)
            font1 = ImageFont.truetype("assets/Comfortaa-Regular.ttf", 45)
            font2 = ImageFont.truetype("assets/Comfortaa-Regular.ttf", 34)
            draw = ImageDraw.Draw(prof)
            resize_avy = avy.resize((200, 200), Image.ANTIALIAS)
            fill = ImageColor.getrgb(color["profile_color"])
            draw.text((25, 215), f"{color['username']}", fill=(0, 0, 0), font=font1)
            draw.text((640, 35), f"{color['current_level']}", fill=fill, font=font)
            draw.text((640, 93), f"{color['uwus']:6}", fill=fill, font=font)
            draw.text((640, 147), f"{color['current_xp']:6}", fill=fill, font=font)
            draw.text(
                (606, 219),
                f"""{color['time_created'].strftime("%x")}""",
                fill=(0, 0, 0),
                font=font2,
            )
            resize_avy = resize_avy.convert("RGBA")
            prof.paste(resize_avy)
            output = BytesIO()
            prof.save(output, "png")
            output.seek(0)
            return output

    @commands.bot_has_permissions(attach_files=True)
    @commands.command()
    async def profile(self, ctx, user: discord.Member = None):
        async with self.bot.pool.acquire() as conn:
            if user is None:
                user = ctx.author
            uwulonian_name = await conn.fetchrow(
                "SELECT * FROM user_settings INNER JOIN user_stats ON user_settings.user_id = user_stats.user_id WHERE user_settings.user_id = $1 AND user_stats.user_id = $1",
                user.id,
            )
            if uwulonian_name is None:
                return await ctx.caution(
                    "You or the user doesn't have an uwulonian created."
                )

            start = time.perf_counter()
            async with self.bot.session.get(
                user.avatar_url_as(format="png"), raise_for_status=True
            ) as r:
                author_avy = Image.open(BytesIO(await r.read()))
            async with ctx.typing():
                await ctx.send(
                    file=discord.File(
                        await self.bot.loop.run_in_executor(
                            None, self.do_profile, user, author_avy, uwulonian_name
                        ),
                        filename=f"{user.id}_prof.png",
                    )
                )

            end = time.perf_counter()
            await ctx.send(f"That took {end - start:.3f}sec to complete")

    @commands.group(invoke_without_command=True, aliases=["colour"])
    async def color(self, ctx):
        await ctx.send(
            "No subcommand passed. Valid subcommands set, default, current, random, and list",
            delete_after=30,
        )

    @color.command()
    async def set(self, ctx, color):
        try:
            rgb = ImageColor.getrgb(color)
        except ValueError as e:
            return await ctx.caution(
                "Not a valid color for all valid colors do uwu color list."
            )
        await self.bot.pool.execute(
            "UPDATE user_settings SET profile_color = $1 WHERE user_id = $2",
            color,
            ctx.author.id,
        )
        await ctx.send(f"Set your profile color to {color}")

    @color.command()
    async def list(self, ctx):
        await ctx.send(
            f"""Some valid colors are {", ".join(extras.pil_colors)}. A full list of colors can be found here <https://www.uwu-bot.xyz/color/>"""
        )

    @errorhandler.is_patron()
    @color.command()
    async def random(self, ctx):
        rand_color = choice(extras.all_pil_colors)
        await self.bot.pool.execute(
            "UPDATE user_settings SET profile_color = $1 WHERE user_id = $2",
            rand_color,
            ctx.author.id,
        )
        await ctx.send(f"Your profile is now {rand_color}")

    @color.command()
    async def current(self, ctx):
        current_color = await self.bot.pool.fetchrow(
            "SELECT profile_color FROM user_settings WHERE user_id = $1", ctx.author.id
        )
        await ctx.send(
            f"Your profiles current color is {current_color['profile_color']}"
        )

    @color.command()
    async def default(self, ctx):
        await self.bot.pool.execute(
            "UPDATE user_settings SET profile_color = $1 WHERE user_id = $2",
            "white",
            ctx.author.id,
        )
        await ctx.send("Set your profiles color to white")

    @commands.command(
        description="Get an uwulonians or your stats",
        aliases=["bal", "wallet"],
        brief="Check a users stats.",
    )
    async def stats(self, ctx, user: discord.Member = None):
        async with self.bot.pool.acquire() as conn:
            user = user or ctx.author
            uwulonian_name = await conn.fetchrow(
                "SELECT * FROM user_settings INNER JOIN user_stats ON user_settings.user_id = user_stats.user_id WHERE user_settings.user_id = $1 AND user_stats.user_id = $1",
                user.id,
            )
            if uwulonian_name is None:
                return await ctx.caution(
                    "You or the user doesn't have an uwulonian created."
                )
            roles = "Yes"
            is_patron = await conn.fetchrow(
                "SELECT * FROM p_users WHERE user_id = $1", user.id
            )
            if is_patron is None:
                roles = "No"

            e = discord.Embed(colour=0x7289DA)

            e.add_field(
                name=f"Stats for {uwulonian_name['username']}",
                value=f"""Foes killed - {uwulonian_name['foes_killed']}\nDeaths - {uwulonian_name['total_deaths']}\nuwus - {uwulonian_name['uwus']}""",
            )
            e.add_field(
                name="Levels",
                value=f"XP - {uwulonian_name['current_xp']}\n Level - {uwulonian_name['current_level']}",
            )
            e.add_field(
                name="Time created",
                value=f"""{uwulonian_name['time_created'].strftime("%x at %X")}""",
            )
            e.add_field(name="Is Patron?", value=roles)
            await ctx.send(embed=e)

    @commands.command(
        aliases=["lb", "wowcheaterhenumber1onlb"],
        description="Check the leaderboard for total_deaths, foes_killed, uwus, and current_xp, or current_level.",
        brief="Check leaderboards",
    )
    async def leaderboard(self, ctx, sort=None):
        sorts = ["deaths", "foes", "uwus", "xp", "level"]
        new_sort = None
        if sort is None or sort.lower() not in sorts:
            return await ctx.caution(
                f"Invalid type. Valid `deaths, foes, uwus, xp, and level`"
            )
        if sort.lower() == "deaths":
            new_sort = "total_deaths"
        elif sort.lower() == "foes":
            new_sort = "foes_killed"
        elif sort.lower() == "level":
            new_sort = "current_level"
        elif sort.lower() == "xp":
            new_sort = "current_xp"
        elif sort.lower() == "uwus":
            new_sort = "uwus"
        lb = await self.bot.pool.fetch(
            f"SELECT username, {new_sort} FROM user_stats ORDER BY {new_sort} DESC LIMIT 5;"
        )
        e = discord.Embed(colour=0x7289DA)
        num = 0
        e.set_author(name=f"Leaderboard - {sort.lower()}")
        for i in lb:
            e.add_field(
                name=f"#{num + 1}. {lb[num]['username']}",
                value=f"{sort.lower()} - {lb[num][new_sort]}",
                inline=False,
            )
            num += 1
        await ctx.send(embed=e)

    @errorhandler.has_uwulonian()
    @commands.command(description="Level up your uwulonian")
    async def levelup(self, ctx):
        async with self.bot.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM user_stats WHERE user_id = $1", ctx.author.id
            )
            new_level = user["current_level"] + 1
            uwus_needed = new_level * 500
            xp_needed = new_level * 1500
            if new_level * 1500 > user["current_xp"]:
                return await ctx.caution(
                    f"You don't have enough xp to level up to level {new_level}. (Hint: you need {xp_needed} xp to level up)"
                )
            if new_level * 500 > user["uwus"]:
                return await ctx.caution(
                    f"You don't have enough uwus to level up to level {new_level}. (Hint: you need {uwus_needed} uwus to level up)"
                )

            await conn.execute(
                """UPDATE user_stats SET uwus = user_stats.uwus - $1, current_xp = user_stats.current_xp - $2, current_level = $3 
            WHERE user_id = $4""",
                uwus_needed,
                xp_needed,
                new_level,
                ctx.author.id,
            )
            await ctx.send(f"{user['username']} is now level {new_level}!")


def setup(bot):
    bot.add_cog(uwulonian(bot))
