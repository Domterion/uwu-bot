import discord
from discord.ext import commands
from discord.ext.commands import cooldown
from discord.ext.commands.cooldowns import BucketType
import time
import asyncio
import asyncpg
from datetime import datetime
from utils import errorhandler
import secrets
from random import choice

heads = '<:uwuheads:517079577072238624>'
tails = '<:uwutails:517081802246979616>'
uwu_emote = '<:uwu:521394346688249856>'

class uwus:
    def __init__(self, bot):
        self.bot = bot
        self.active_games = []

    async def __local_check(self, ctx):
        if await self.bot.pool.fetchrow("SELECT user_id FROM user_settings WHERE user_id = $1", ctx.author.id):
           return True

        raise(errorhandler.hasUwU(ctx))

    @commands.command(aliases=['coinflip'], description="Flip a coin. Guess what the result will be if right you get the amount you bet.", brief="Flip a coin.")
    async def coin(self, ctx, choice, amount:int):
        async with self.bot.pool.acquire() as conn:
            user_amount = await conn.fetchrow("SELECT uwus FROM user_stats WHERE user_id = $1", ctx.author.id)
            choice = choice.lower()
            if amount < 50 or amount > 50000:
                return await ctx.send("You may not bet less then `50` uwus or more than `50000` on a coinflip", delete_after=30)
            if choice != "heads" and choice != "tails":
                return await ctx.send("Please only use heads or tails", delete_after=30)
            if amount > user_amount['uwus']:
                return await ctx.send("You don't have the funds to bet that much", delete_after=30)

            status = await ctx.send("Flipping the coin...")
            await asyncio.sleep(3)
            await status.delete()
            side = secrets.choice(["heads", "tails"])
            if side == "heads":
                emote = heads
            else:
                emote = tails

            if choice == side:
                booster = await conn.fetchrow("SELECT boost_type, boost_amount, active_boosters FROM user_boosters WHERE user_id = $1", ctx.author.id)
                if not booster or booster['boost_type'] == 'XP':
                    await conn.execute("UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2", amount, ctx.author.id)
                    return await ctx.send(f"{emote} You won `{amount}` uwus!")
                if booster['boost_type'] == 'uwus':
                    amount = amount * booster['boost_amount']
                    await conn.execute("UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2", amount, ctx.author.id)
                    return await ctx.send(f"{emote} You won `{amount}` uwus! You have an {booster['active_boosters']} activated! Enjoy the extra uwus")
            else:
                await conn.execute("UPDATE user_stats SET uwus = user_stats.uwus - $1 WHERE user_id = $2", amount, ctx.author.id)
                return await ctx.send(f"{emote} You lost.")

    @commands.command(description="Start a guessing game. Guess au users name from there discriminator and name", brief="Start a guessing game.")
    async def guess(self, ctx):
        members = [member for member in ctx.guild.members if member.id is not ctx.author.id and not member.bot]
        if len(members) < 15:
            return await ctx.send("You can only play guessing game if you are in a server with more then 15 members. Join uwus support server if you want to play but don't have 15 members.", delete_after=30)
        async with self.bot.pool.acquire() as conn:
            if ctx.channel.id in self.active_games:
                return await ctx.send("There is already a guessing game in this channel.", delete_after=30)
            self.active_games.append(ctx.channel.id)
            e = discord.Embed(description=
"""
Welcome to uwu's guessing game! To win guess the users name based off their avatar and discriminator(#0000)            
You have 30 seconds to guess! Good luck!
""")
            e.set_author(name="Guessing game")

            randmem = choice(members)

            e.add_field(name="Info", value=f"The users discriminator is {randmem.discriminator}. Hint: Their name starts with {randmem.name[:1]}")
            e.set_image(url=randmem.avatar_url_as(static_format="png"))
            embed = await ctx.send(embed=e)

            def check(amsg):
                return amsg.content == randmem.name
            try:
                name = await self.bot.wait_for('message', timeout=30, check=check)
            except asyncio.TimeoutError:
                await embed.delete()
                await conn.execute("DELETE FROM guessing WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, ctx.channel.id)
                self.active_games.remove(ctx.channel.id)
                return await ctx.send(f"Times up! The user was {randmem.name}.".replace('@','@\u200b'))

            amount = 50
            booster = await conn.fetchrow("SELECT boost_type, boost_amount, active_boosters FROM user_boosters WHERE user_id = $1", ctx.author.id)
            if not booster or booster['boost_type'] == 'XP':
                status = await conn.fetchrow("UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2 RETURNING True", amount, name.author.id)
                if status:
                    await embed.delete()
                    self.active_games.remove(ctx.channel.id)
                    return await ctx.send(f"{name.author} guessed correctly and got `50` uwus! It was {randmem.name}.")
            if booster['boost_type'] == 'uwus':
                amount = amount * booster['boost_amount']
                status = await conn.fetchrow("UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2 RETURNING True", amount, name.author.id)
                if status:
                    await embed.delete()
                    self.active_games.remove(ctx.channel.id)
                    return await ctx.send(f"{name.author} guessed correctly and got `{amount}` uwus! It was {randmem.name}. {name.author} has an {booster['active_boosters']} activated! Enjoy the extra uwus")

            self.active_games.remove(ctx.channel.id)
            await ctx.send(f"{name.author} got it right but does not have an uwulonian. It was {randmem.name}.")

    @commands.command(description="Give other people some of your uwus", brief="Give uwus")
    async def give(self, ctx, user: discord.Member, amount:int):
        async with self.bot.pool.acquire() as conn:
            user_amount = await conn.fetchrow("SELECT uwus FROM user_stats WHERE user_id = $1", ctx.author.id)
            if await conn.fetchrow("SELECT user_id FROM user_settings WHERE user_id = $1 OR user_id = $2", ctx.author.id, user.id) is None:
                return await ctx.send("You or the user don't have an uwulonian.")
            if ctx.author.id == user.id:
                return await ctx.send("You can't give yourself uwus.", delete_after=30)
            if amount < 50:
                return await ctx.send("You can't give less than `50` uwus.", delete_after=30)
            if amount > 50000:
                return await ctx.send("You can't give more then `50000` uwus", delete_after=30)
            if amount > user_amount['uwus']:
                return await ctx.send("You don't have the funds to give that much", delete_after=30)

            await conn.execute("UPDATE user_stats SET uwus = user_stats.uwus - $1 WHERE user_id = $2", amount, ctx.author.id)
            await conn.execute("UPDATE user_stats SET uwus = user_stats.uwus + $1 WHERE user_id = $2", amount, user.id)
            await ctx.send(f"{uwu_emote} You gave `{amount}` to `{user.name}`")

def setup(bot):
    bot.add_cog(uwus(bot))