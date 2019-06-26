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
import inspect
import textwrap
from contextlib import redirect_stdout
import io
import copy
from typing import Union


class staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.staff_ids = [
            300_088_143_422_685_185,
            422_181_415_598_161_921,
            428_888_500_964_687_873,
            311_553_339_261_321_216,
            440_113_725_970_710_528,
        ]

    async def cog_check(self, ctx):
        if ctx.author.id in self.staff_ids:
            return True

        raise (errorhandler.IsStaff(ctx))

    @commands.command(description="Blacklist a user via ID", brief="Blacklist")
    async def blacklist(self, ctx, user_id: int, *, reason=None):
        user = self.bot.get_user(user_id)
        if reason is None:
            reason = "No reason"
        if len(reason) > 512:
            return await ctx.send("Reason can't be more then 512 characters.")

        try:
            await self.bot.pool.execute(
                "INSERT INTO blacklists (user_id, reason, mod_id) VALUES ($1, $2, $3)",
                user_id,
                reason,
                ctx.author.id,
            )
            self.bot.blacklisted.append(user_id)
            return await ctx.send(f"Done. Blacklisted {user.name} for {reason}")
        except asyncpg.UniqueViolationError:
            return await ctx.send("Error. User already blacklisted.", delete_after=30)

    @commands.command(
        description="Unblacklist a user from their ID", brief="Unblacklist"
    )
    async def unblacklist(self, ctx, user_id: int):
        try:
            await self.bot.pool.execute(
                "DELETE FROM blacklists WHERE user_id = $1", user_id
            )
            self.bot.blacklisted.remove(user_id)
            return await ctx.send("Done")
        except:
            await ctx.send("User not blacklisted.", delete_after=30)

    @commands.group(invoke_without_command=True)
    async def patreon(self, ctx):
        await ctx.send(
            "No subcommand passed. Valid subcommands add, remove", delete_after=30
        )

    @patreon.command()
    async def add(self, ctx, user_id: int, tier):
        if tier not in ["Supporter", "Awesome", "Wow"]:
            return await ctx.send("Invalid tier. Valid are Supporter, Awesome, Wow")

        try:
            user = self.bot.get_user(user_id)
            await self.bot.pool.execute(
                "INSERT INTO p_users (user_id, tier) VALUES ($1, $2)", user_id, tier
            )
            self.bot.patrons.append(user_id)
            await user.send(
                f"""
Thanks for your **{tier}** patronage! Enjoy your patron only commands!
```
"uwu color random" Set your profile color to a random color
"uwu patron timecheck" Check how long you have been a patron for
"uwu patron biweekly" Extra 5000 uwus per 2 weeks
```
*Have recommendations? DM mellowmarshe#0001 or join the support server (https://uwu-bot.xyz/discord)*
"""
            )
            return await ctx.send("Done")
        except asyncpg.UniqueViolationError:
            return await ctx.send("User already a patron.", delete_after=30)

    @patreon.command()
    async def remove(self, ctx, user_id: int):
        try:
            self.bot.patrons.remove(user_id)
        except:
            user = self.bot.get_user(user_id)
            return await ctx.send(f"{user} is not a Patron.")

        await self.bot.pool.execute("DELETE FROM p_users WHERE user_id = $1", user_id)
        await ctx.send("Done")

    @commands.group(invoke_without_command=True)
    async def uwulonian(self, ctx):
        await ctx.send(
            "No subcommand passed. Valid subcommands givexp, giveuwus, removexp, removeuwu",
            delete_after=30,
        )

    @uwulonian.command()
    async def givexp(self, ctx, user_id: int, amount: int):
        user = self.bot.get_user(user_id)
        await self.bot.pool.execute(
            "UPDATE user_stats SET xp = user_stats.xp + $1 WHERE user_id = $2",
            amount,
            user_id,
        )
        await ctx.send(f"Gave {user.name} {amount} xp.")

    @uwulonian.command()
    async def giveuwus(self, ctx, user_id: int, amount: int):
        user = self.bot.get_user(user_id)
        await self.bot.pool.execute(
            "UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2",
            amount,
            user_id,
        )
        await ctx.send(f"Gave {user.name} {amount} uwus.")

    @uwulonian.command()
    async def removexp(self, ctx, user_id: int, amount: int):
        user = self.bot.get_user(user_id)
        await self.bot.pool.execute(
            "UPDATE user_stats SET xp = user_stats.xp - $1 WHERE user_id = $2",
            amount,
            user_id,
        )
        await ctx.send(f"Removed {amount} xp from {user.name}.")

    @uwulonian.command()
    async def removeuwus(self, ctx, user_id: int, amount: int):
        user = self.bot.get_user(user_id)
        await self.bot.pool.execute(
            "UPDATE user_stats SET uwus = user_stats.uwus - $1 WHERE user_id = $2",
            amount,
            user_id,
        )
        await ctx.send(f"Removed {amount} uwws from {user.name}.")

    @uwulonian.command()
    async def status(self, ctx):
        adv = self.bot.get_cog("exploring").adventure_task
        expl = self.bot.get_cog("exploring").exploring_task
        await ctx.send(f"Exploring status: \n```{expl}```")
        await ctx.send(f"Adventure status: \n```{adv}```")


def setup(bot):
    bot.add_cog(staff(bot))
