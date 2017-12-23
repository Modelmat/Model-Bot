import discord
from discord.ext import commands
import database_old as db

async def settings_perm_check(ctx):
    if commands.is_owner():
        return True
    elif commands.has_permissions(manage_server=True):
        return True
    else:
        await ctx.send("You do not have valid permissions to do this. (Manage Server Permission).")
        return False

class Settings:
    """Sets and gets the settings for the bot"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def get(self, ctx):
        """Commands related to determining the value of settings."""
        pass

    @commands.check(settings_perm_check)
    @commands.group(name="set")
    async def _set(self, ctx):
        """Commands related to the changing of settings."""
        pass

    @get.command(name="channels")
    async def get_channels(self, ctx):
        channels = db.get_server_channels(ctx.guild.id)
        if len(channels) == 3:
            await ctx.send("​Channels for {}: <#{}>, <#{}>, and <#{}>.".format(ctx.guild.name, *channels))
        else:
            await ctx.send("​This server does not have channels set up yet, use {}settings channels set <receiveChannel> <allowChannel> <outputChannel>.".format(ctx.prefix))

    # @_set.command(name="channels")
    # async def set_channels(self, ctx):
    #     ch_mentions = ctx.message.channel_mentions
    #     raw_ch_mentions = ctx.message.raw_channel_mentions
    #     if len(ch_mentions) == 1:
    #         receiveChannelID, allowChannelID, outputChannelID = raw_ch_mentions * 3
    #         ch_mentions = ch_mentions * 3
    #     elif len(ch_mentions) < 3:
    #         raise TypeError("Too few channels supplied, you need three. Type {}help settings set channels for more inforamtion".format(ctx.prefix))
    #     else:
    #         receiveChannelID, allowChannelID, outputChannelID = raw_ch_mentions 
    #     db.set_server_channels(ctx.guild.id, receiveChannelID, allowChannelID, outputChannelID)
    #     await ctx.send("​Set channels to {} {} {}".format(*ch_mentions))

    @_set.command(name="channels")
    async def set_channels(self, ctx, *channels: discord.TextChannel):
        print(channels)
        if len(channels) == 1:
            channels *= 3
            receiveChannelID, allowChannelID, outputChannelID = channels
        elif len(channels) < 3:
            raise commands.MissingRequiredArgument("Too few channels supplied, you need three. Type {}help settings set channels for more information".format(ctx.prefix))
        else:
            receiveChannelID, allowChannelID, outputChannelID = [channel.id for channel in channels]
        db.set_server_channels(ctx.guild.id, receiveChannelID, allowChannelID, outputChannelID)
        await ctx.send("​Set channels to {} {} {}".format(*[channel.mention for channel in channels]))

    @_set.command(name="prefix")
    async def set_prefix(self, ctx, *, prefix: str):
        prefix = prefix.strip("'").strip('"')
        if db.set_prefix(ctx.guild.id, prefix): 
            await ctx.send("Channels are not set. Currently a limitation.")
        await ctx.send("Set prefix to `{}`".format(db.get_prefix(ctx.guild.id)))

    @get.command(name="prefix")
    async def get_prefix(self, ctx):
        await ctx.send("Prefix for {}: `{}`".format(ctx.guild.name, ctx.prefix))

    @commands.is_owner()
    @get.command(hidden=True)
    async def permissions(self, ctx):
        await ctx.send()

def setup(bot):
    bot.add_cog(Settings(bot))
