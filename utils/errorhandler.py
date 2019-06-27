import sys
from discord.ext import commands
import discord

caution = "<:caution:521002590566219776>"


def on_cooldown(cooldown):
    async def predicate(ctx):
        user_cooldown = await ctx.bot.redis.pttl(
            f"{ctx.author.id}-{ctx.command.qualified_name}"
        )
        if user_cooldown == 0:
            ttl = await ctx.bot.redis.pttl(f"{ctx.author.id}-vote") / 1000
            await self.bot.redis.execute(
                "SET",
                f"{ctx.author.id}-{ctx.command.qualified_name}",
                "cooldown",
                "EX",
                int(ttl),
            )
        if user_cooldown == -2:
            await ctx.bot.redis.execute(
                "SET",
                f"{ctx.author.id}-{ctx.command.qualified_name}",
                "cooldown",
                "EX",
                cooldown,
            )
            return True

        raise commands.CommandOnCooldown(
            retry_after=user_cooldown / 1000, cooldown=None
        )

    return commands.check(predicate)


def has_uwulonian():
    async def predicate(ctx):
        uwulonian = await ctx.bot.redis.sismember("uwulonians", ctx.author.id)
        if uwulonian != 0:
            return True

        raise (hasUwU(ctx))

    return commands.check(predicate)


def has_voted():
    async def predicate(ctx):
        if await ctx.bot.redis.execute("GET", f"{ctx.author.id}-vote"):
            return True

        raise (hasVoted(ctx))

    return commands.check(predicate)


def is_patron():
    async def predicate(ctx):
        if await ctx.bot.pool.fetchrow(
            "SELECT user_id FROM p_users WHERE user_id = $1", ctx.author.id
        ):
            return True

        raise (NotPatron(ctx))

    return commands.check(predicate)


class NotPatron(commands.CommandError):
    def __init__(self, ctx):
        super().__init__(
            f"You are not a Patron. You can become one here <https://www.patreon.com/mellOwO>"
        )


class IsStaff(commands.CommandError):
    def __init__(self, ctx):
        super().__init__(f"This is a staff only command.")


class IsRatelimited(commands.CommandError):
    def __init__(self, ctx, retry_after):
        seconds = retry_after
        seconds = round(seconds, 2)
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        super().__init__(f"**Ratelimited**: {seconds} seconds.")


class isEvent(commands.CommandError):
    def __init__(self, ctx):
        super().__init__(f"This is an event staff only command.")


class hasUwU(commands.CommandError):
    def __init__(self, ctx):
        super().__init__(f"You need an uwulonian for this command.")


class hasVoted(commands.CommandError):
    def __init__(self, ctx):
        super().__init__(
            f"You haven't voted. You can vote here <https://discordbots.org/bot/508725128427995136/vote>. If you voted give me a few seconds to register it."
        )


class isBeta(commands.CommandError):
    def __init__(self, ctx):
        super().__init__(f"This is a beta-server only command.")


class errorhandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, "on_error"):
            return

        errors = (
            commands.NoPrivateMessage,
            commands.CommandInvokeError,
            commands.UserInputError,
        )
        c_errors = (
            NotPatron,
            IsStaff,
            hasUwU,
            isBeta,
            isEvent,
            hasVoted,
            IsRatelimited,
        )
        error = getattr(error, "original", error)

        if isinstance(error, errors):
            await ctx.caution(error)
        elif isinstance(error, commands.BadArgument):
            await ctx.caution(f"Invalid argument. Did you type it correct?")
        elif isinstance(error, commands.TooManyArguments):
            await ctx.caution(f"Too many arguments. Try less?")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.caution(
                f"Required argument {str(error.param).split(':')[0]} is missing. Ya sure you read the command description?"
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.caution(error)
        elif isinstance(error, commands.DisabledCommand):
            await ctx.caution(f"{ctx.command} is disabled.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.caution(
                f"I need the permission {', '.replace(error.missing_perms)}. You can check my role or channel overrides to find permissions."
            )
        elif isinstance(error, commands.CommandOnCooldown):
            seconds = error.retry_after
            seconds = round(seconds, 2)
            hours, remainder = divmod(int(seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            await ctx.caution(
                f"You are on cooldown for {hours}h {minutes}m {seconds}sec"
            )
        elif isinstance(error, c_errors):
            return await ctx.caution(error)
        else:
            print(error)


def setup(bot):
    bot.add_cog(errorhandler(bot))
