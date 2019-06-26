import dbl
import discord
from discord.ext import commands

import aiohttp
import asyncio
import logging


class DiscordBotsOrgAPI(commands.Cog):
    """Handles interactions with the discordbots.org API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = self.bot.config.dbl_token  # set this to your DBL token
        if self.token:  # ignore if the token isnt available
            self.dblpy = dbl.Client(self.bot, self.token)
        self.bot.loop.create_task(self.update_stats())

    async def update_stats(self):

        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.bot.logger.info("[DBL] Attempting to post server count")
            try:
                await self.dblpy.post_server_count()
                self.bot.logger.info(
                    f"[DBL] Posted guild count of {len(self.bot.guilds)} guilds"
                )
            except Exception as e:
                self.bot.logger.exception(
                    f"[DBL] Failed to post server count {type(e).__name__}: {e}"
                )
            await asyncio.sleep(1800)


def setup(bot):
    bot.add_cog(DiscordBotsOrgAPI(bot))
