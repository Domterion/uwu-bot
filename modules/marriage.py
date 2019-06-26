import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
import time
import asyncio
import asyncpg
from datetime import datetime, timezone, timedelta
from utils import errorhandler
from random import randint, choice

heartt = "<:heartt:521071307769774080>"
broken_heartt = "<:brokenheartt:521074570707468308>"
caution = "<:caution:521002590566219776>"


class marriage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        uwulonian = await self.bot.redis.sismember("uwulonians", ctx.author.id)
        if uwulonian != 0:
            return True

        raise (errorhandler.hasUwU(ctx))

    @commands.command(descritpion="Marry your lover.", brief="Marry someone")
    async def marry(self, ctx, lover: discord.Member = None):
        async with self.bot.pool.acquire() as conn:
            if lover is None or lover.id == ctx.author.id or lover.bot:
                return await ctx.caution("Invalid lover...")

            if await conn.fetchrow(
                "SELECT user1_id, user2_id FROM marriages WHERE user1_id = $1 OR user2_id = $1 OR user1_id = $2 OR user2_id = $2",
                ctx.author.id,
                lover.id,
            ):
                return await ctx.caution("One of you are married already.")

            proposal = await ctx.send(
                f"{lover} would you like to marry {ctx.author}? You have 15 seconds to react..."
            )
            await proposal.add_reaction("\U00002764")

            def check(reaction, user):
                return (
                    user.id == lover.id
                    and str(reaction.emoji) == "\U00002764"
                    and reaction.message.id == proposal.id
                )

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=15, check=check
                )
            except asyncio.TimeoutError:
                await proposal.delete()
                return await ctx.send(f"{lover} does not want to marry...")

            await conn.execute(
                "UPDATE user_stats SET married_to = $1 WHERE user_id = $2",
                lover.id,
                ctx.author.id,
            )
            await conn.execute(
                "UPDATE user_stats SET married_to = $1 WHERE user_id = $2",
                ctx.author.id,
                lover.id,
            )
            await conn.execute(
                "INSERT INTO marriages (user1_id, user2_id) VALUES ($1, $2)",
                ctx.author.id,
                lover.id,
            )

            await proposal.delete()
            await ctx.send(f"{ctx.author.mention} is now married to {lover.mention}!")

    @commands.command()
    async def divorce(self, ctx):
        async with self.bot.pool.acquire() as conn:
            uwulonian = await conn.fetchrow(
                "SELECT married_to FROM user_stats WHERE user_id = $1", ctx.author.id
            )
            if not uwulonian["married_to"]:
                return await ctx.caution("You aren't married...")

            await conn.execute(
                "UPDATE user_stats SET married_to = null WHERE user_id = $1",
                ctx.author.id,
            )
            await conn.execute(
                "UPDATE user_stats SET married_to = null WHERE user_id = $1",
                uwulonian["married_to"],
            )
            await conn.execute(
                "DELETE FROM marriages WHERE user1_id = $1 OR user2_id = $1",
                ctx.author.id,
            )
            await conn.execute(
                "DELETE FROM marriages WHERE user1_id = $1 OR user2_id = $1",
                uwulonian["married_to"],
            )
            await ctx.send("Divorced...")


def setup(bot):
    bot.add_cog(marriage(bot))
