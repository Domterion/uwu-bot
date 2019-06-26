import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
import time
import asyncio
import asyncpg
from datetime import datetime, timedelta
from random import randint, choice
from utils import errorhandler
from utils import extras


class exploring(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.exploring_task = self.bot.loop.create_task(self.explore_waiter())
        self.adventure_task = self.bot.loop.create_task(self.adventure_waiter())
        self.task_check_task = self.bot.loop.create_task(self.task_check())

    async def cog_check(self, ctx):
        uwulonian = await self.bot.redis.sismember("uwulonians", ctx.author.id)
        if uwulonian != 0:
            return True

        raise (errorhandler.hasUwU(ctx))

    def cog_unload(self):
        try:
            self.exploring_task.cancel()
            self.adventure_task.cancel()
            self.task_check_task.cancel()
        except:
            pass

    async def task_check(self):
        if self.exploring_task.done():
            self.exploring_task.cancel()
            self.exploring_task = self.bot.loop.create_task(self.exploring_task())
        if self.adventure_task.done():
            self.adventure_task.cancel()
            self.adventure_task = self.bot.loop.create_task(self.adventure_task())

    async def explore_waiter(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(2)
            rows = await self.bot.pool.fetchrow(
                "SELECT user_explores.user_id, finish_time, user_stats.uwus, user_stats.level, user_stats.xp FROM user_explores INNER JOIN user_stats ON user_explores.user_id = user_stats.user_id ORDER BY finish_time ASC LIMIT 1;"
            )
            if not rows:
                continue
            await extras.sleep_time(rows["finish_time"])
            try:
                user = self.bot.get_user(rows["user_id"])
            except:
                return await self.bot.pool.execute(
                    "DELETE FROM user_explores WHERE user_id = $1", rows["user_id"]
                )
            foes = randint(20, 1000)
            deaths = randint(0, 2)
            uwus = (foes * 6) - (deaths * 40)
            random_tip = choice(extras.quick_tips)
            xp = round(uwus / 2, 0)
            try:
                e = discord.Embed(
                    color=0x7289DA,
                    description=f"""
{foes} killed (6 uwus per)
{deaths} deaths (-40 uwus per)       

{xp} xp earned
{uwus} uwus earned!

Total uwus {rows['uwus'] + uwus}
xp {rows['xp'] + xp} (Hint: You need {(rows['level'] + 1) * 1500} xp and {(rows['level'] + 1) * 500} uwus to level up)
""",
                )
                e.set_author(name="Exploring")
                e.set_footer(text=f"Quick fact {random_tip}")
                await user.send(embed=e)
            except (discord.Forbidden, TypeError, AttributeError):
                pass
            await self.bot.pool.execute(
                "UPDATE user_stats SET uwus = user_stats.uwus + $1, xp = user_stats.xp + $2, foes = user_stats.foes + $3, deaths = user_stats.deaths + $4 WHERE user_id = $5",
                uwus,
                xp,
                foes,
                deaths,
                user.id,
            )
            await self.bot.pool.execute(
                "DELETE FROM user_explores WHERE user_id = $1", rows["user_id"]
            )

    async def adventure_waiter(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(2)
            rows = await self.bot.pool.fetchrow(
                "SELECT user_adventures.user_id, finish_time, user_stats.uwus, user_stats.level, user_stats.xp FROM user_adventures INNER JOIN user_stats ON user_adventures.user_id = user_stats.user_id ORDER BY finish_time ASC LIMIT 1;"
            )
            if not rows:
                continue
            await extras.sleep_time(rows["finish_time"])
            try:
                user = self.bot.get_user(rows["user_id"])
            except:
                return await self.bot.pool.execute(
                    "DELETE FROM user_adventures WHERE user_id = $1", rows["user_id"]
                )
            foes = randint(80, 1000)
            deaths = randint(0, 4)
            uwus = (foes * 8) - (deaths * 45)
            random_tip = choice(extras.quick_tips)
            xp = round(uwus / 2, 0)
            try:
                e = discord.Embed(
                    color=0x7289DA,
                    description=f"""
{foes} killed (8 uwus per)
{deaths} deaths (-45 uwus per)       

{xp} xp earned
{uwus} uwus earned!

Total uwus {rows['uwus'] + uwus}
xp {rows['xp'] + xp} (Hint: You need {(rows['level'] + 1) * 1500} xp and {(rows['level'] + 1) * 500} uwus to level up)
""",
                )
                e.set_author(name="Adventure")
                e.set_footer(text=f"Quick fact {random_tip}")
                await user.send(embed=e)
            except (discord.Forbidden, TypeError, AttributeError):
                pass
            await self.bot.pool.execute(
                "UPDATE user_stats SET uwus = user_stats.uwus + $1, xp = user_stats.xp + $2, foes = user_stats.foes + $3, deaths = user_stats.deaths + $4 WHERE user_id = $5",
                uwus,
                xp,
                foes,
                deaths,
                user.id,
            )
            await self.bot.pool.execute(
                "DELETE FROM user_adventures WHERE user_id = $1", rows["user_id"]
            )

    @commands.command(description="Make your uwulonian explore", aliases=["exp"])
    async def explore(self, ctx):
        async with self.bot.pool.acquire() as conn:
            explore = await conn.fetchrow(
                "SELECT * FROM user_explores WHERE user_id = $1", ctx.author.id
            )
            adventure = await conn.fetchrow(
                "SELECT * FROM user_adventures WHERE user_id = $1", ctx.author.id
            )
            if explore:
                time_left = explore["finish_time"] - datetime.utcnow()
                hu_time_left = time_left.total_seconds()
                seconds = round(hu_time_left, 2)
                minutes, seconds = divmod(hu_time_left, 60)
                return await ctx.caution(
                    f"Your uwulonian is already exploring. It will return in `{minutes}`m `{int(seconds)}`sec."
                )
            if adventure:
                time_left = adventure["finish_time"] - datetime.utcnow()
                hu_time_left = time_left.total_seconds()
                seconds = round(hu_time_left, 2)
                minutes, seconds = divmod(hu_time_left, 60)
                return await ctx.caution(
                    f"Your uwulonian is already adventuring. It will return in `{minutes}`m `{int(seconds)}`sec."
                )
            end_time = datetime.utcnow() + timedelta(minutes=30)
            await conn.execute(
                "INSERT INTO user_explores (user_id, finish_time) VALUES ($1, $2)",
                ctx.author.id,
                end_time,
            )
            await ctx.send(
                f"Your uwulonian is now exploring! It will return in 30 minutes"
            )

    @commands.command(description="Set your uwulonian on an adventure", aliases=["adv"])
    async def adventure(self, ctx):
        async with self.bot.pool.acquire() as conn:
            explore = await conn.fetchrow(
                "SELECT * FROM user_explores WHERE user_id = $1", ctx.author.id
            )
            adventure = await conn.fetchrow(
                "SELECT * FROM user_adventures WHERE user_id = $1", ctx.author.id
            )
            if explore:
                time_left = explore["finish_time"] - datetime.utcnow()
                hu_time_left = time_left.total_seconds()
                seconds = round(hu_time_left, 2)
                minutes, seconds = divmod(hu_time_left, 60)
                return await ctx.caution(
                    f"Your uwulonian is already exploring. It will return in {int(minutes)}m {int(seconds)}sec."
                )
            if adventure:
                time_left = adventure["finish_time"] - datetime.utcnow()
                hu_time_left = time_left.total_seconds()
                seconds = round(hu_time_left, 2)
                minutes, seconds = divmod(hu_time_left, 60)
                return await ctx.caution(
                    f"Your uwulonian is already adventuring. It will return in {int(minutes)}m {int(seconds)}sec."
                )
            end_time = datetime.utcnow() + timedelta(hours=1)
            await conn.execute(
                "INSERT INTO user_adventures (user_id, finish_time) VALUES ($1, $2)",
                ctx.author.id,
                end_time,
            )
            await ctx.send(
                f"Your uwulonian is now adventuring! It will return in 1 hour"
            )

def setup(bot):
    bot.add_cog(exploring(bot))
