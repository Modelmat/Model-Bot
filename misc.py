from datetime import datetime, timedelta
from os import execl
from sys import executable, argv

import discord
from discord.ext import commands

time_format = '%H:%M:%S UTC on the %d of %B, %Y'

class Misc:
    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(382780308610744331)

    async def on_guild_join(self, guild):
        self.bot_logs.send("Joined {} at {}".format(guild.name, datetime.utcnow().strftime(time_format)))

    @commands.is_owner()
    @commands.command(hidden=True)
    async def restart(self, ctx):
        """Owner of this bot only command; Restart the bot"""
        if ctx.channel != self.bot_logs:
            await ctx.send("Restarting bot.")
        await self.bot_logs.send("Restarting bot.")
        await self.bot.change_presence(status=discord.Status.offline)
        print("\nRestarting...\n")
        await self.bot.close()
        execl(executable, 'python "' + "".join(argv) + '"')

        #MAKE THIS CHANGE STATUS

    @commands.is_owner()
    @commands.command(hidden=True)
    async def shutdown(self, ctx):
        """Owner of this bot only command; Shutdown the bot"""
        if ctx.channel == self.bot_logs:
            await ctx.send("Shutting Down.")
        await self.bot_logs.send("Shutting down bot.")
        await self.bot.change_presence(status=discord.Status.offline)
        print("\nShutting Down...\n")
        await self.bot.close()

    @commands.command()
    async def ping(self, ctx):
        time_difference = datetime.utcnow() - ctx.message.created_at
        await ctx.send("Pong. Time taken: `{}ms`".format(round(time_difference.total_seconds() * 1000)))

def setup(bot):
    bot.add_cog(Misc(bot))
