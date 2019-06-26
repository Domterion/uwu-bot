import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
import time
import asyncio
import asyncpg
from datetime import datetime, timedelta
from random import randint
from utils import errorhandler


class patron(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        uwulonian = await self.bot.redis.sismember("uwulonians", ctx.author.id)
        if uwulonian != 0:
            return True

        raise (errorhandler.hasUwU(ctx))

    @commands.group(
        invoke_without_command=True, description="Does nothing without a subcommand"
    )
    async def patron(self, ctx):
        await ctx.send(
            "No subcommand passed or invalid was passed. Valid subcommands timecheck, biweekly"
        )

    @patron.command(
        description="Check how long you have been a Patron",
        brief="Check how long you have been a patron",
    )
    async def timecheck(self, ctx):
        patron = await self.bot.pool.fetchrow(
            "SELECT patron_time FROM p_users WHERE user_id = $1", ctx.author.id
        )
        await ctx.send(
            f"""You have been a Patron since {patron['patron_time'].strftime("%x at %X")}. Thanks for supporting me!"""
        )

def setup(bot):
    bot.add_cog(patron(bot))
