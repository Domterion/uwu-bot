from discord.ext import commands
import discord
from utils import errorhandler
import asyncpg
from datetime import datetime
import copy
from typing import Union
import inspect
import textwrap
from contextlib import redirect_stdout
import io
import traceback
import textwrap
import utils


class owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def die(self, ctx):
        await self.bot.pool.execute(
            "UPDATE commands_used SET commands_used = commands_used + $1",
            self.bot.commands_ran,
        )
        self.bot.logger.info("[Logout] Logging out...")
        await ctx.check()
        await self.bot.logout()


def setup(bot):
    bot.add_cog(owner(bot))
