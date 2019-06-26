import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
from discord import Color
import asyncpg
import asyncio
from random import choice, randint
from datetime import datetime, timedelta
from utils import extras, errorhandler
import lavalink
import time
import re
import logging
import math
import aiodns
import cchardet
import aioredis

time_rx = re.compile("[0-9]+")
url_rx = re.compile("https?:\/\/(?:www\.)?.+")

beta_servers = [
    513_888_506_498_646_052,
    336_642_139_381_301_249,
    253_716_112_292_839_425,
]
uwu_emote = "<:uwu:521394346688249856>"
caution = "<:caution:521002590566219776>"


class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, "lavalink"):
            bot.lavalink = lavalink.Client(508725128427995136)
            bot.lavalink.add_node(
                bot.config.lavalink["ip"],
                8080,
                bot.config.lavalink["password"],
                "us",
                "us-east",
            )
            bot.add_listener(
                self.bot.lavalink.voice_update_handler, "on_socket_response"
            )
        bot.lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()

    def cog_load(self):
        if self.bot.is_ready:
            if self.bot.lavalink is None:
                self.bot.lavalink = lavalink.Client(self.bot.user.id)
                self.bot.lavalink.add_node(
                    bot.config.lavalink["ip"],
                    8080,
                    bot.config.lavalink["password"],
                    "us",
                    "us-east",
                )
                self.bot.add_listener(
                    self.bot.lavalink.voice_update_handler, "on_socket_response"
                )
                self.bot.lavalink.add_event_hook(self.track_hook)

    async def track_hook(self, event):
        if isinstance(event, lavalink.TrackStartEvent):
            chnnl = event.player.fetch("channel")
            if chnnl:
                chnnl = self.bot.get_channel(chnnl)
                if chnnl:
                    durtion = lavalink.utils.format_time(event.track.duration)
                    await chnnl.send(
                        f"Started song `{event.track.title}` with duration `{durtion}`.",
                        delete_after=30,
                    )
        elif isinstance(event, lavalink.TrackEndEvent):
            chnnl = event.player.fetch("channel")
            if chnnl:
                chnnl = self.bot.get_channel(chnnl)
                if len(event.player.queue) == 0:
                    await event.player.stop()
                    await self.connect_to(chnnl.guild.id, None)
                    return await chnnl.send(
                        f"Disconnecting because queue is over...", delete_after=30
                    )
                await chnnl.send(f"Song ended...", delete_after=30)

    async def connect_to(self, guild_id: int, channel_id: str):
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)

    async def cog_check(self, ctx):
        if not await self.bot.redis.execute("GET", f"{ctx.author.id}-vote"):
            raise (errorhandler.hasVoted(ctx))
        player = self.bot.lavalink.players.create(
            ctx.guild.id, endpoint=ctx.guild.region.value
        )

        should_connect = ctx.command.name in (
            "play",
            "now",
            "seek",
            "skip",
            "stop",
            "pause",
            "volume",
            "disconnect",
            "queue",
            "remove",
            "music_player",
        )

        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.caution("You must be in a voice channel.")

        if not player.is_connected:
            if not should_connect:
                return await ctx.caution("Not connected...")

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect:
                return await ctx.caution(
                    f"I need the permission connect to use voice channels. You can check my role or channel overrides to find permissions."
                )

            if not permissions.speak:
                return await ctx.caution(
                    f"I need the permission speak to use voice channels. You can check my role or channel overrides to find permissions."
                )

            player.store("channel", ctx.channel.id)
            await self.connect_to(ctx.guild.id, str(ctx.author.voice.channel.id))
        if (
            player.is_connected
            and int(player.channel_id) != ctx.author.voice.channel.id
        ):
            return await ctx.caution("You need to be in my current voice channel.")

        return True

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, query: str):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        query = query.strip("<>")

        if not url_rx.match(query):
            query = f"ytsearch:{query}"

        results = await player.node.get_tracks(query)

        if not results or not results["tracks"]:
            return await ctx.send("No song found...", delete_after=30)

        e = discord.Embed(color=0x7289DA)

        if results["loadType"] == "PLAYLIST_LOADED":
            tracks = results["tracks"]

            for track in tracks:
                player.add(requester=ctx.author.id, track=track)

            e.set_author(name=f"Playlist queued by {ctx.author}")
            e.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} songs'
            await ctx.send(embed=e)
        else:
            track = results["tracks"][0]
            e.set_author(name=f"Song queued by {ctx.author}")
            e.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
            await ctx.send(embed=e)
            player.add(requester=ctx.author.id, track=track)

        if not player.is_playing:
            await player.play()

    @commands.command(aliases=["np", "n", "playing"])
    async def now(self, ctx):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        position = lavalink.utils.format_time(player.position)
        if player.current.stream:
            duration = "Live"
        else:
            duration = lavalink.utils.format_time(player.current.duration)

        e = discord.Embed(
            color=0x7289DA,
            description=f"[{player.current.title}]({player.current.uri})",
        )
        e.add_field(name="Duration", value=f"[{position}/{duration}]")
        await ctx.send(embed=e)

    @commands.command()
    async def seek(self, ctx, *, time: str):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        seconds = time_rx.search(time)
        if not seconds:
            return await ctx.send(
                "Please specify a time in seconds to skip.", delete_after=30
            )

        seconds = int(seconds.group()) * 1000
        if time.startswith("-"):
            seconds *= -1

        track_time = player.position + seconds
        await player.seek(track_time)

        await ctx.send(f"Moved song to `{lavalink.utils.format_time(track_time)}`")

    @commands.command()
    async def skip(self, ctx):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        await player.skip()
        await ctx.send("Skipped.", delete_after=30)

    @commands.command()
    async def stop(self, ctx):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        player.queue.clear()
        await player.stop()
        await ctx.send("Stopped.", delete_after=30)

    @commands.command(aliases=["resume"])
    async def pause(self, ctx):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if player.paused:
            await player.set_pause(False)
            await ctx.send("Resumed.", delete_after=30)
        else:
            await player.set_pause(True)
            await ctx.send("Paused.", delete_after=30)

    @commands.command(aliases=["vol"])
    async def volume(self, ctx, volume: int = None):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not volume:
            return await ctx.send(
                f"My current player volume is `{player.volume}`%", delete_after=30
            )

        await player.set_volume(volume)
        await ctx.send(f"Set player volume to `{player.volume}`%", delete_after=30)

    @commands.command(aliases=["dc"])
    async def disconnect(self, ctx):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        player.queue.clear()
        await player.stop()
        await self.connect_to(ctx.guild.id, None)
        await ctx.send("Disconnected.", delete_after=30)

    @commands.command(aliases=["q"])
    async def queue(self, ctx, page: int = 1):
        """ Shows the player's queue. """
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.queue:
            return await ctx.send("Nothing queued.", delete_after=30)

        items_per_page = 10
        pages = math.ceil(len(player.queue) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = ""
        for index, track in enumerate(player.queue[start:end], start=start):
            queue_list += f"{index + 1} - [{track.title}]({track.uri})\n"

        e = discord.Embed(colour=0x7289DA, description=queue_list)
        e.set_author(name=f"{len(player.queue)} songs in the queue ({page}/{pages})")
        e.set_footer(
            text=f'To change pages do "uwu queue PAGE" replacing page with the desired page'
        )
        await ctx.send(embed=e)

    @commands.command()
    async def remove(self, ctx, index: int):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if index > len(player.queue) or index < 1:
            return await ctx.send(
                f"Invalid index please use an index of `1`-`{len(player.queue)}`"
            )

        index -= 1
        removed = player.queue.pop(index)

        await ctx.send(f"Removed `{removed.title}` from the queue.")

    @commands.command()
    async def music_player(self, ctx):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        is_paused = "No"
        if player.paused:
            is_paused = "Yes"
        e = discord.Embed(colour=0x7289DA)
        e.set_author(name=f"Player info for {ctx.guild}")
        e.add_field(name="Volume", value=f"{player.volume}/1000", inline=False)
        e.add_field(
            name=f"Current song",
            value=f"[{player.current.title}]({player.current.uri})",
            inline=False,
        )
        e.add_field(name="Is paused", value=is_paused, inline=False)
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(music(bot))
