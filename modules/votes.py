import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
import time
import asyncio
import asyncpg
import aioredis
from utils import errorhandler
from datetime import datetime, timedelta
from random import randint


class votes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if await self.bot.redis.execute("GET", f"{ctx.author.id}-vote"):
            return True

        raise (errorhandler.hasVoted(ctx))

    @commands.group(invoke_without_command=True)
    async def vote(self, ctx):
        await ctx.send(
            "No subcommand passed or invalid was passed. Valid subcommands reward, cat"
        )

    @errorhandler.on_cooldown(5)
    @errorhandler.has_uwulonian()
    @vote.command(description="Cat pictures")
    async def cat(self, ctx):
        headers = {"x-api-key": self.bot.config.cat_api_token}
        e = discord.Embed(color=0x7289DA)
        e.set_footer(text="Powered by https://thecatapi.com/")
        async with self.bot.session.get(
            "https://api.thecatapi.com/v1/images/search", headers=headers
        ) as r:
            res = await r.json()
            e.set_image(url=res[0]["url"])
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(votes(bot))
