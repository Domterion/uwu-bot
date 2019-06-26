import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType


class help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        await ctx.send(
            "You can find the commands list here <https://uwu-bot.xyz/commands/>. If you need command help join the support server https://discord.gg/733URZq"
        )


def setup(bot):
    bot.remove_command("help")
    bot.add_cog(help(bot))
