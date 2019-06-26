import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
import traceback
import asyncio
import asyncpg
import config
from datetime import datetime
import os
import sys
import logging
import aiohttp
import aioredis
import psutil
import lavalink
import discord
from utils import errorhandler
import logging.handlers
import utils

logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(
    filename=f"logs/bot.log",
    encoding="utf-8",
    when="D",
    interval=1,
    utc=True,
    backupCount=10,
)
handler.setFormatter(
    logging.Formatter("[%(asctime)s:%(levelname)s:%(name)s] %(message)s")
)
logger.addHandler(handler)

try:
    import uvloop
except ImportError:
    if (
        sys.platform == "linux"
    ):  # alert the user to install uvloop if they are on a linux system
        print("UVLoop not detected")
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

description = """uwu. A RPG bot made by mellowmarshe#0001"""


class uwu(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=self.get_pre,
            case_insensitive=True,
            description=description,
            reconnect=True,
            status=discord.Status.idle,
            activity=discord.Game("Booting up"),
        )
        self.launch_time = datetime.utcnow()
        self.config = config
        self.pool = None  # pool is unset till the bot is ready
        self.lavalink = None
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.process = psutil.Process(os.getpid())
        self.loop = asyncio.get_event_loop()
        self.logger = logging.getLogger("bot")
        self.blacklisted = []
        self.patrons = []
        self.prefixes = {}
        self.commands_ran = 0
        self.add_check(self.global_cooldown)

    map = commands.CooldownMapping.from_cooldown(1, 3, commands.BucketType.user)

    async def get_pre(self, bot, message):
        if not message.guild:
            return commands.when_mentioned_or(*self.config.prefixes)(bot, message)
        try:
            guild_prefix = bot.prefixes[message.guild.id]
            if guild_prefix:
                return commands.when_mentioned_or(guild_prefix)(bot, message)
        except KeyError:
            return commands.when_mentioned_or(*self.config.prefixes)(bot, message)

    async def global_cooldown(self, ctx: commands.Context):
        bucket = self.map.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()

        if retry_after:
            raise errorhandler.IsRatelimited(ctx, retry_after)
        else:
            return True

    async def start(self):
        for ext in self.config.startup_extensions:
            try:
                self.load_extension(ext)
            except BaseException as e:
                print(f"Failed to load {ext}\n{type(e).__name__}: {e}")
        await super().start(self.config.token)

    async def on_message_edit(self, before, after):
        if after.author.bot:
            return
        ctx = await self.get_context(after)

        if ctx.command:
            if after.author.id in self.blacklisted:
                return await after.channel.send(
                    f"You may not use uwu. You were blacklisted."
                )

        await self.process_commands(after)

    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message)

        if ctx.command:
            if message.author.id in self.blacklisted:
                return await message.channel.send(
                    f"You may not use uwu. You were blacklisted."
                )

            await self.process_commands(message)

    async def init_conns(self):
        await self.init_dbs()

    async def init_dbs(self):
        self.redis = await aioredis.create_redis_pool(
            "redis://localhost", password=self.config.redispassword, loop=self.loop
        )
        credentials = {
            "user": self.config.postgres["user"],
            "password": self.config.postgres["password"],
            "database": self.config.postgres["name"],
            "host": "127.0.0.1",
        }
        self.pool = await asyncpg.create_pool(**credentials, max_size=150)

    async def on_ready(self):
        await self.init_conns()
        with open("utils/schema.sql") as f:
            await self.pool.execute(f.read())

        bl_users = await self.pool.fetch("SELECT * FROM blacklists")
        patrons = await self.pool.fetch("SELECT * FROM p_users")
        prefixes = await self.pool.fetch("SELECT guild_id, prefix FROM guild_prefixes")

        for i in prefixes:
            self.prefixes[i[0]] = i[1]
        for i in range(len(bl_users)):
            self.blacklisted.append(int(bl_users[i]["user_id"]))
        self.logger.info(f"[Start] Added {len(bl_users)} blacklisted users.")
        for i in range(len(patrons)):
            self.patrons.append(int(patrons[i]["user_id"]))
        self.logger.info(f"[Start] Added {len(patrons)} patrons.")

        game = discord.Game(self.config.playing_status)
        await self.change_presence(status=discord.Status.dnd, activity=game)
        self.logger.info(
            f"[Start] Bot started with {len(self.guilds)} guilds and {len(self.users)} users."
        )

    async def on_command_completion(self, ctx):
        self.commands_ran += 1

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=utils.context.Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_message_delete(self, message):
        content = message.content
        msg_type_o = 0
        if message.attachments:
            content = message.attachments[0].proxy_url
            msg_type_o = 1
        if message.embeds:
            content = message.embeds[0].description
            msg_type_o = 2
        try:
            await self.pool.execute(
                """INSERT INTO del_snipe (guild_id, user_id, channel_id, message, msg_type) VALUES ($1, $2, $3, $4, $5) 
            ON CONFLICT (channel_id) DO UPDATE SET user_id = $2, message = $4, msg_type = $5""",
                message.guild.id,
                message.author.id,
                message.channel.id,
                content,
                msg_type_o,
            )
        except:
            pass

    async def on_guild_remove(self, guild):
        await self.redis.execute("DECR", "current_guilds")
        self.logger.info(
            f"[Guild] Left guild {guild.name}({guild.id}) with {len(guild.members)} members"
        )

    async def on_guild_join(self, guild):
        await self.redis.execute("INCR", "current_guilds")
        self.logger.info(
            f"[Guild] Joined guild {guild.name}({guild.id}) with {len(guild.members)} members"
        )


if __name__ == "__main__":
    uwu().run()
