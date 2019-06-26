import aiohttp
import discord
import discord.ext.commands
from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter


class logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = True
        self.can_be_disabled = False

    async def commandtask(self, ctx):
        passed = (
            "<:uwuyes:519291795541065768>"
            if not ctx.command_failed
            else "<:uwuno:519291795285344265>"
        )
        embed = discord.Embed(
            color=0x7289DA,
            title=f"Command {passed}",
            description=f"```{ctx.message.clean_content}```",
        )
        embed.set_author(
            name=ctx.author, icon_url=ctx.author.avatar_url_as(format="jpg")
        )
        embed.add_field(
            name="Author", value=f"{ctx.author}({ctx.author.id})", inline=False
        )
        if ctx.guild:
            embed.add_field(
                name="Guild", value=f"{ctx.guild}({ctx.guild.id})", inline=False
            )
        else:
            embed.add_field(name="Guild", value=f"Private message", inline=False)
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(
                self.bot.config.webhook_url, adapter=AsyncWebhookAdapter(session)
            )
            await webhook.send(
                embed=embed,
                username=self.bot.user.name,
                avatar_url=self.bot.user.avatar_url,
            )

    async def dmtask(self, ctx):
        embed = discord.Embed(
            color=0x7289DA,
            title="Private message",
            description=f"```{ctx.message.clean_content}```",
        )
        embed.set_author(
            name=ctx.author, icon_url=ctx.author.avatar_url_as(format="jpg")
        )
        embed.add_field(
            name="Author", value=f"{ctx.author}({ctx.author.id})", inline=False
        )
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(
                self.bot.config.webhook_url, adapter=AsyncWebhookAdapter(session)
            )
            await webhook.send(
                embed=embed,
                username=self.bot.user.name,
                avatar_url=self.bot.user.avatar_url,
            )

    async def guildtask(self, guild, _type):
        embed = discord.Embed(color=0x7289DA, title=f"Guild {_type}")
        embed.add_field(name="Guild", value=f"{guild}({guild.id})", inline=False)
        embed.set_thumbnail(url=guild.icon_url)
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(
                self.bot.config.webhook_url, adapter=AsyncWebhookAdapter(session)
            )
            await webhook.send(
                embed=embed,
                username=self.bot.user.name,
                avatar_url=self.bot.user.avatar_url,
            )

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.bot.loop.create_task(self.commandtask(ctx))

    @commands.Cog.listener()
    async def on_message(self, message):
        ctx = await self.bot.get_context(message)
        if (
            not ctx.command
            and not ctx.prefix
            and not ctx.guild
            and ctx.author != ctx.me
        ):
            self.bot.loop.create_task(self.dmtask(ctx))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.loop.create_task(self.guildtask(guild, "Join"))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.bot.loop.create_task(self.guildtask(guild, "Leave"))


def setup(bot):
    bot.add_cog(logging(bot))
