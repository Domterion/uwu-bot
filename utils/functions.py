import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
import time
import asyncio
import asyncpg
from datetime import datetime
from utils import errorhandler
import aioredis


class functions:
    def __init__(self, bot):
        self.bot = bot

    async def set_cooldown(self, ctx, user: discord.Member, time: int):
        await self.bot.redis.execute(
            "SET",
            f"{ctx.author.id}-{ctx.command.qualified_name}",
            "cooldown",
            "EX",
            time,
        )

    async def check4cooldown(self, ctx, user: discord.Member):
        cooldown = await self.bot.redis.execute(
            "TTL", f"{ctx.author.id}-{ctx.command.qualified_name}"
        )
        if cooldown == -2 or cooldown is None:
            return True

        return cooldown


def setup(bot):
    bot.add_cog(functions(bot))
