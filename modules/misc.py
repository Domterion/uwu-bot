import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
import time
import asyncio
import asyncpg
from datetime import datetime, timedelta, timezone
from random import choice, randint, seed
from utils import errorhandler
import psutil
import os
import re
import logging
import math
import sys

colors = [0xE56B6B, 0xDD5151, 0xBA3434, 0xAB1F1F, 0x940808]
online = "<:online_status:506963324391653387>"
offline = "<:offline_status:506963324521414661>"
dnd = "<:dnd_status:506963324634791936>"
idle = "<:idle_status:506963324529803264>"

# git fix again again again


class misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @errorhandler.on_cooldown(86400)
    @commands.command(description="Claim your daily uwus.", aliases=["daily"])
    async def dailies(self, ctx):
        streak = await self.bot.redis.execute(
            "INCR", f"{ctx.author.id}-{ctx.command.qualified_name}-streak"
        )
        await self.bot.redis.execute(
            "EXPIRE", f"{ctx.author.id}-{ctx.command.qualified_name}-streak", 108000
        )
        daily = min(30 * streak, 210)
        xp_bonus = 0
        if streak >= 8:
            xp_bonus = streak * 1

        await self.bot.pool.execute(
            "UPDATE user_stats SET uwus = user_stats.uwus + $1, xp = user_stats.xp + $2 WHERE user_id = $3",
            daily,
            xp_bonus,
            ctx.author.id,
        )
        await ctx.send(
            f"You get {daily} uwus for a streak of {streak}, 8+ day streak xp bonus: {xp_bonus}."
        )

    @commands.command(
        description="Give someone a slap", brief="Slap", usage="slap [user]"
    )
    async def slap(self, ctx, *, user: discord.Member):
        embed = discord.Embed(colour=choice(colors))
        embed.set_author(name=f"{ctx.author.name} slapped {user.name}! Ouchy!")
        embed.set_image(url="https://media.giphy.com/media/RXGNsyRb1hDJm/giphy.gif")
        await ctx.send(embed=embed)

    @commands.command(
        description="Give someone a hug! Awwww", brief="Hug", usage="hug [user]"
    )
    async def hug(self, ctx, *, user: discord.Member):
        embed = discord.Embed(colour=choice(colors))
        embed.set_author(name=f"{ctx.author.name} gave {user.name} hug! How cute!")
        embed.set_image(url="https://media.giphy.com/media/lXiRKBj0SAA0EWvbG/giphy.gif")
        await ctx.send(embed=embed)

    @commands.command(
        aliases=["pong"],
        description="Check the bots latency to Discord Websockets",
        brief="Check the bots ping",
        usage="ping",
    )
    async def ping(self, ctx):
        t_1 = time.perf_counter()
        await ctx.trigger_typing()
        t_2 = time.perf_counter()
        time_delta = round((t_2 - t_1) * 1000)
        await ctx.send(
            f":ping_pong: Websocket: {round(self.bot.latency*1000)}ms. Typing: {time_delta}ms"
        )

    @commands.command(
        aliases=["avy"],
        description="Get a users or your avatar",
        usage="avatar [user]",
        brief="Get a users or your avatar",
    )
    async def avatar(self, ctx, *, user: discord.Member = None):
        user = user or ctx.author
        embed = discord.Embed(
            colour=0x7289DA, description=f"[Link]({str(user.avatar_url)})"
        )
        embed.set_author(name=f"{user.name}'s avatar", url=str(user.avatar_url))
        embed.set_image(url=str(user.avatar_url_as(static_format="png")))
        await ctx.send(embed=embed)

    @commands.command(
        aliases=["about"],
        description="Get stats about the bot",
        brief="Check bot stats",
        usage="info",
    )
    async def info(self, ctx):
        cmds_used = await self.bot.pool.fetchval("""SELECT * FROM commands_used;""")
        uwulonian = await self.bot.pool.fetchval(
            "SELECT count(user_id) FROM user_settings;"
        )
        delta_uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        cpu_usage = self.bot.process.cpu_percent()
        cpu_count = psutil.cpu_count()
        memory_usage = self.bot.process.memory_full_info().uss / (1024 ** 2)
        version = sys.version_info
        user_count = len(self.bot.users)
        embed = discord.Embed(color=0x7289DA)
        embed.set_author(name="Bot Stats")
        embed.add_field(
            name="Info",
            value=f"""
<@300088143422685185> (mellowmarshe#0001)
[discord.py](https://github.com/Rapptz/discord.py)
Python {version.major}.{version.minor}.{version.micro}
Uptime: {days}d {hours}h {minutes}m, Servers: {len(self.bot.guilds)}
""",
        )
        embed.add_field(
            name="Host and Usage",
            value=f"""
Memory {round(memory_usage, 2)}MiB, CPU {cpu_usage/cpu_count}%
{self.bot.commands_ran} commands used since boot, {cmds_used + self.bot.commands_ran} commands used, Users {user_count}
{uwulonian} uwulonians
""",
        )
        embed.add_field(name="Members", value=f"{user_count}")
        embed.add_field(
            name="Links",
            value="""
[Invite](https://discordapp.com/oauth2/authorize?client_id=508725128427995136&scope=bot&permissions=67501248)
[Support](https://discord.gg/733URZq)
[Donate](https://www.patreon.com/mellOwO)
[Vote](https://discordbots.org/bot/508725128427995136/vote)
[Website](https://uwu-bot.xyz/)
[DigitalOcean Referral](https://m.do.co/c/e9f223fd5a5c)
""",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(
        description="Get the link to the support server",
        brief="Get a link to support server.",
    )
    async def support(self, ctx):
        await ctx.send("The link to the support server is https://discord.gg/733URZq")

    @commands.command()
    async def uptime(self, ctx):
        delta_uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        await ctx.send(f"I have been up for {days}d {hours}h {minutes}m")

    @commands.command(
        description="Check our lovely Patrons!", brief="Check out our lovely patrons."
    )
    async def patrons(self, ctx):
        patrons = await self.bot.pool.fetch("SELECT * FROM p_users")
        e = discord.Embed(
            color=0x7289DA, description="Patreon https://www.patreon.com/mellOwO"
        )
        for i in range(len(patrons)):
            user = self.bot.get_user(patrons[i]["user_id"])
            time_p = datetime.now(timezone.utc) - patrons[i]["patron_time"]
            e.add_field(
                name=user.name,
                value=f"{patrons[i]['tier']} | Has been a patron for `{int(time_p.days)}` days!",
            )
        e.set_author(name="Our awesome Patrons")
        await ctx.send(embed=e)

    @commands.command(description="Send voting link", brief="Send a link to vote")
    async def upvote(self, ctx):
        await ctx.send(
            "You can vote for me here! https://discordbots.org/bot/508725128427995136/vote or <https://botsfordiscord.com/bot/508725128427995136/vote> I greatly appreciate voting as it helps the bot a lot"
        )

    @commands.command(description="Bot rules", aliases=["tos"], brief="Our bot rules")
    async def rules(self, ctx):
        await ctx.send(
            """
uwu rules. You must follow these or we will take action
`-` Don't spam or abuse commands with the intent to harm or slow the bot down. We want the best experience for our users anything to harm this is a problem.
`-` Don't rename or create an uwulonian with a harmful, racist, or any name that can offend someone. We will most likely delete your uwulonian if you do this.
`-` The use of scripts or anything to gain an advantage is forbidden.
`-` DM staff if you are having problems with the bot don't DM regular members unless they say you can.
"""
        )

    @commands.command(description="Get bot invite link", brief="Get invite for bot")
    async def invite(self, ctx):
        permissions = discord.Permissions()

        permissions.update(
            add_reactions=True,
            attach_files=True,
            change_nickname=True,
            embed_links=True,
            external_emojis=True,
            manage_messages=True,
            read_messages=True,
            read_message_history=True,
            send_messages=True,
            send_tts_messages=True,
            view_audit_log=True,
        )

        await ctx.send(
            f"<{discord.utils.oauth_url(self.bot.user.id, permissions=permissions)}>"
        )

    @commands.command(description="Snipe a deleted message", aliases=["snipsnop"])
    async def snipe(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel
        snop = await self.bot.pool.fetchrow(
            "SELECT * FROM del_snipe WHERE channel_id = $1 AND guild_id = $2",
            channel.id,
            ctx.guild.id,
        )
        if snop is None:
            return await ctx.send("Nothing to snipe", delete_after=30)
        if channel.is_nsfw() is True and ctx.channel.is_nsfw() is False:
            return await ctx.send(
                "No sniping NSFW outside of NSFW channel.", delete_after=30
            )
        user = self.bot.get_user(snop["user_id"])
        guild = self.bot.get_guild(snop["guild_id"])
        chnl = discord.utils.get(guild.text_channels, id=snop["channel_id"])
        del_time = datetime.now(timezone.utc) - snop["msg_time"]
        if snop["msg_type"] == 1:
            e = discord.Embed(
                colour=0x7289DA, description="The image may not be visible"
            )
            e.set_author(name=f"{user.name} sent in {chnl.name}")
            e.set_image(url=snop["message"])
            e.set_footer(text=f"sniped!")
            await ctx.send(embed=e)
        else:
            user = self.bot.get_user(snop["user_id"])
            guild = self.bot.get_guild(snop["guild_id"])
            chnl = discord.utils.get(guild.text_channels, id=snop["channel_id"])
            e = discord.Embed(colour=0x7289DA, description=snop["message"])
            e.set_author(name=f"{user.name} said in {chnl.name}")
            e.set_footer(text=f"sniped!")
            await ctx.send(embed=e)

    @commands.command(description="Report a bug or user")
    async def report(
        self,
        ctx,
        *,
        report: commands.clean_content(
            fix_channel_mentions=False, use_nicknames=False, escape_markdown=True
        ),
    ):
        if len(report) > 512:
            return await ctx.send("Your report was too long")

        supp = self.bot.get_channel(529_722_574_301_560_842)
        e = discord.Embed(
            color=0xFF0000, description=f"```{report}```", timestamp=datetime.utcnow()
        )
        e.set_author(
            name=f"Report by {ctx.author}({ctx.author.id}) in {ctx.guild.name}({ctx.guild.id})"
        )
        e.set_footer(text="Report at")
        await ctx.send(
            "Your report was sent. Join the support server for news on your report!"
        )
        await supp.send(embed=e)

    # Sourced mainly from NekoBot https://github.com/hibikidesu/NekoBot/blob/master/modules/fun.py
    @commands.command()
    async def minesweeper(self, ctx, size: int = 5):
        m_offsets = [
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
        ]
        m_numbers = [":one:", ":two:", ":three:", ":four:", ":five:", ":six:"]
        size = max(min(size, 8), 2)
        bombs = [
            [randint(0, size - 1), randint(0, size - 1)] for x in range(int(size - 1))
        ]
        is_on_board = lambda x, y: 0 <= x < size and 0 <= y < size
        has_bomb = lambda x, y: [i for i in bombs if i[0] == x and i[1] == y]
        embed = discord.Embed(color=0x7289DA, description="")
        embed.set_author(name="Press to play")
        for y in range(size):
            for x in range(size):
                tile = f"||{chr(11036)}||"
                if has_bomb(x, y):
                    tile = f"||{chr(128163)}||"
                else:
                    count = 0
                    for xmod, ymod in m_offsets:
                        if is_on_board(x + xmod, y + ymod) and has_bomb(
                            x + xmod, y + ymod
                        ):
                            count += 1
                    if count != 0:
                        tile = f"||{m_numbers[count - 1]}||"
                embed.description += tile
            embed.description += "\n"
        await ctx.send(embed=embed)

    @commands.command(aliases=["8ball"])
    async def eightball(self, ctx, *, question):
        responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes - definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]
        msg = await ctx.send(f"Q: {question}...")
        await asyncio.sleep(3)
        await msg.edit(content=f"A: {choice(responses)}")

    @commands.command(aliases=["lovedar"])
    async def love(self, ctx, lover: discord.Member, lovee: discord.Member):
        msg = await ctx.send("**Calculating...**")
        await asyncio.sleep(3)
        if lover.id in (
            300_088_143_422_685_185,
            422_181_415_598_161_921,
        ) and lovee.id in (300_088_143_422_685_185, 422_181_415_598_161_921):
            love = 100.00
        else:
            seed(int(str(lover.id) + str(lovee.id)))
            if lover == lovee:
                love = 0
            else:
                love = randint(1, 10000) / 100
        await msg.edit(
            content=f"The love calculator says {lover.name} loves {lovee.name} {love}%"
        )


def setup(bot):
    bot.add_cog(misc(bot))
