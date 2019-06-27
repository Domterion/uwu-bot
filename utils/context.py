import discord
from discord.ext import commands

caution_emote = "<:caution:521002590566219776>"


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def caution(self, error):
        new_error = f"{caution_emote} {error}"
        await self.send(new_error, delete_after=30)

    async def check(self):
        await self.message.add_reaction(self.bot.config.check_emoji)

    async def deny(self):
        await self.message.add_reaction(self.bot.config.deny_emoji)
