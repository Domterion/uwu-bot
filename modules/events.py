import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
from utils import errorhandler
import asyncpg
import asyncio
from random import choice, randint


class events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.author.id in self.bot.config.event_staff:
            return True

        raise (errorhandler.isEvent(ctx))


def setup(bot):
    bot.add_cog(events(bot))
