import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
from utils import errorhandler
import asyncpg
import asyncio
from random import choice, randint

event_ids = [
    246938839720001536,
    300088143422685185,
    422181415598161921,
    311553339261321216,
    428888500964687873,
]


class events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.author.id in event_ids:
            return True

        raise (errorhandler.isEvent(ctx))


def setup(bot):
    bot.add_cog(events(bot))
