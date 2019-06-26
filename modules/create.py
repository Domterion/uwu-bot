import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
import time
import asyncio
import asyncpg
from datetime import datetime
from utils import errorhandler


class create(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Create a new uwulonian.", brief="Create a uwulonian")
    async def create(self, ctx):
        if await self.bot.pool.fetchrow(
            "SELECT user_id FROM user_settings WHERE user_id = $1", ctx.author.id
        ):
            return await ctx.send(
                "You already have an uwulonian created.", delete_after=30
            )

        def check(amsg):
            return amsg.author == ctx.author

        name_set = await ctx.send(
            "Please enter your uwulonians name. This will timeout after 30 seconds."
        )
        try:
            name = await self.bot.wait_for("message", timeout=30, check=check)
        except asyncio.TimeoutError:
            return await name_set.edit(content="Create timed out", delete_after=30)

        if len(name.content) > 60 or len(name.content) < 3:
            await name_set.delete()
            return await ctx.send(
                "Invalid name. Names can't be longer then 60 chars or less than 3 chars.",
                delete_after=30,
            )
        try:
            await self.bot.pool.execute(
                "INSERT INTO user_settings (user_id, username) VALUES ($1, $2);",
                ctx.author.id,
                name.content,
            )
        except asyncpg.UniqueViolationError:
            return await ctx.send(
                f"{name.content} is already used. Please try again with a different name.",
                delete_after=30,
            )

        await self.bot.pool.execute(
            "INSERT INTO user_stats (user_id, uwus, foes, deaths, xp, level, username) VALUES ($1, $2, $3, $4, $5, $6, $7);",
            ctx.author.id,
            1000,
            0,
            0,
            0,
            0,
            name.content,
        )
        await self.bot.redis.sadd("uwulonians", ctx.author.id)
        await name_set.delete()
        await ctx.send(
            f"Success! Made uwulonian with name {name.content}. Please read uwu rules for uwus rules regarding usage.".replace(
                "@", "@\u200b"
            )
        )

    @errorhandler.has_uwulonian()
    @commands.command(
        description="Rename your uwulonian.", brief="Rename your uwulonian"
    )
    async def rename(self, ctx, *, name):
        if len(name) > 60 or len(name) < 3:
            return await ctx.send(
                "Invalid name. Names can't be longer then 60 chars or less than 3 chars.",
                delete_after=30,
            )
        try:
            await self.bot.pool.execute(
                "UPDATE user_settings SET username = $1 WHERE user_id = $2",
                name.replace("@", "@\u200b"),
                ctx.author.id,
            )
            await self.bot.pool.execute(
                "UPDATE user_stats SET username = $1 WHERE user_id = $2",
                name.replace("@", "@\u200b"),
                ctx.author.id,
            )
        except asyncpg.UniqueViolationError:
            return await ctx.send(
                f"That name is already used. Please try again with a different name."
            )
        await ctx.send(
            "Name changed. Note: Abuse of this system will end with a character deletion or blacklist."
        )

    @errorhandler.has_uwulonian()
    @commands.command(description="Delete your uwulonian.", brief="Delete uwulonian.")
    async def delete(self, ctx):
        async with self.bot.pool.acquire() as conn:

            def check(amsg):
                return amsg.author == ctx.author

            delete_con = await ctx.send(
                "Are you sure you would like to delete your uwulonian?"
            )
            try:
                delete_cons = await self.bot.wait_for(
                    "message", timeout=30, check=check
                )
            except asyncio.TimeoutError:
                return await delete_con.edit(content="Not deleting uwulonian")

            if delete_cons.content.lower() == "yes":
                del_msg = await ctx.send("Deleting uwulonian. Give me a few seconds.")
                await conn.execute(
                    "DELETE FROM user_settings WHERE user_id = $1", ctx.author.id
                )
                await asyncio.sleep(2)
                await conn.execute(
                    "DELETE FROM marriages WHERE user1_id = $1 OR user2_id = $1",
                    ctx.author.id,
                )
                await asyncio.sleep(2)
                await conn.execute(
                    "DELETE FROM children WHERE lover1_id = $1 OR lover2_id = $1",
                    ctx.author.id,
                )
                await asyncio.sleep(2)
                await conn.execute(
                    "DELETE FROM user_pets WHERE user_id = $1", ctx.author.id
                )
                await asyncio.sleep(2)
                await conn.execute(
                    "DELETE FROM spc_user_pets WHERE user_id = $1", ctx.author.id
                )
                await asyncio.sleep(2)
                await self.bot.redis.srem("uwulonians", ctx.author.id)
                await delete_con.delete()
                await del_msg.delete()
                return await ctx.send("Deleted uwulonian :(")
            if delete_cons.content.lower() == "no":
                await delete_con.delete()
                return await ctx.send("Not deleting uwulonian.")
            else:
                await delete_con.delete()
                return await ctx.send("Invalid choice.")


def setup(bot):
    bot.add_cog(create(bot))
