from datetime import datetime
from os import environ
import traceback
import asyncio
from random import choice

import discord
from discord.ext import commands

import database as db
import custom_classes as cc

async def server_prefix(bots, message):
    """A callable Prefix for our bot.

    This allow for per server prefixes.

    Arguments:
        bots {discord.ext.commands.Bot} -- A variable that is passed automatically by commands.Bot.
        message {discord.Message} -- Also passed automatically, used to get Guild ID.

    Returns:
        string -- The prefix to be used by the bot for receiving commands.
    """
    if not message.guild:
        return bots.prefix

    if bots.server_prefixes.get(message.guild.id) is None:
        prefix = await bots.database.get_prefix(message)
        bots.server_prefixes[message.guild.id] = prefix
    else:
        prefix = bots.server_prefixes[message.guild.id]

    prefixes = [bots.prefix + " ", prefix + " ", bots.prefix, prefix]

    return commands.when_mentioned_or(*prefixes)(bots, message)

bot = cc.Bot(command_prefix=server_prefix,
             description='Multiple functions, including contests, definitions, and more.')

try:
    token = environ["AUTH_KEY"]
except KeyError:
    with open("client_secret.txt", encoding="utf-8") as file:
        lines = [l.strip() for l in file]
        token = lines[0]

async def load_extensions(bots):
    await asyncio.sleep(2)
    for extension in bots.extensions.copy().keys():
        try:
            bots.load_extension("cogs." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()

@bot.event
async def on_ready():
    bot.database = db.Database(bot)
    await bot.change_presence(status=discord.Status.online)
    bot.owner = (await bot.application_info()).owner
    await bot.user.edit(username="Kern")
    await bot.get_channel(bot.bot_logs_id).send("Bot Online at {}".format(datetime.utcnow().strftime(bot.time_format)))
    bot.loop.create_task(statusChanger())
    await load_extensions(bot)
    print('\nLogged in as:')
    print(bot.user.name, "(Bot)")
    print(bot.user.id)
    print('------')

async def statusChanger():
    status_messages = [discord.Game(name="for new contests.", type=3),
                       discord.Game(name="{} servers.".format(len(bot.guilds)), type=3)]
    while not bot.is_closed():
        message = choice(status_messages)
        await bot.change_presence(game=message)
        await asyncio.sleep(60)

@bot.event
async def on_message(message: discord.Message):
    async with bot.database.lock:
        if " && " in message.content:
            cmds_run_before = []
            failed_to_run = {}
            messages = message.content.split(" && ")
            for msg in messages:
                message.content = msg
                ctx = await bot.get_context(message, cls=cc.CustomContext)
                if ctx.valid:
                    if msg.strip(ctx.prefix) not in cmds_run_before:
                        await bot.invoke(ctx)
                        cmds_run_before.append(msg.strip(ctx.prefix))
                    else:
                        failed_to_run[msg.strip(ctx.prefix)] = "This command has been at least once before."
                else:
                    if ctx.prefix is not None:
                        failed_to_run[msg.strip(ctx.prefix)] = "Command not found."
                    else:
                        pass

            if failed_to_run:
                errors = ""
                for fail, reason in failed_to_run.items():
                    errors += f"{fail}: {reason}\n"
                await ctx.error(f"```{errors}```", "These failed to run:")

        else:
            ctx = await bot.get_context(message, cls=cc.CustomContext) #is a command returned
            await bot.invoke(ctx)

@commands.is_owner()
@bot.group(hidden=True)
async def cogs(ctx):
    pass

@cogs.command(name="reload")
async def reload_cog(ctx, cog_name: str):
    """Reload the cog `cog_name`"""
    bot.unload_extension("cogs." + cog_name)
    print("Cog unloaded.", end=' | ')
    bot.load_extension("cogs." + cog_name)
    print("Cog loaded.")
    await ctx.send("Cog `{}` sucessfully reloaded.".format(cog_name))

@cogs.command(name="list")
async def cogs_list(ctx):
    """List the loaded cogs"""
    des = ""
    for ext, enabled in bot.extensions.items():
        if enabled:
            des += ":white_small_square: {}\n".format(ext)
        else:
            des += ":black_small_square: {}\n".format(ext)
    await ctx.neutral(des, "Cogs:")

@cogs.command(name="unload", aliases=['disable', 'remove'])
async def cogs_unload(ctx, cog_name: str):
    """Unloads a cog"""
    if bot.extensions[cog_name.lower()]:
        bot.extensions[cog_name.lower()] = False
        bot.unload_extension("cogs." + cog_name)
        await ctx.success(f"`Cog {cog_name} unloaded.`")
    else:
        await ctx.neutral(f"`Cog {cog_name} already unloaded..`")

@cogs.command(name="load", aliases=['enable', 'add'])
async def cogs_load(ctx, cog_name: str):
    """Loads a cog"""
    if not bot.extensions[cog_name.lower()]:
        bot.extensions[cog_name.lower()] = True
        bot.unload_extension("cogs." + cog_name)
        await ctx.success(f"`Cog {cog_name} loaded.`")
    else:
        await ctx.neutral(f"`Cog {cog_name} already loaded..`")

@bot.event
async def on_command_error(ctx, error):
    # This prevents any commands with local handlers being handled here in on_command_error.
    do_send = True
    if hasattr(ctx.command, 'on_error'):
        return
    ignored = (commands.UserInputError, commands.NotOwner, commands.CheckFailure)

    error = getattr(error, 'original', error)
    if isinstance(error, ignored):
        return

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.error(ctx.error, "Missing Required Argument(s)")

    elif isinstance(error, commands.CommandNotFound):
        print("Command: {} not found.".format(ctx.invoked_with))
        return

    elif isinstance(error, TypeError) and ctx.command in ["set", "get"]:
        pass

    elif isinstance(error, asyncio.TimeoutError) and ctx.command in ['obama', 'meaning', 'synonym', 'antonym']:
        pass

    elif isinstance(error, ModuleNotFoundError):
        await ctx.error(str(error).split("'")[1].capitalize(), "Cog not found:")
        do_send = False
        print("Cog failed to unload.")

    elif isinstance(error, discord.errors.HTTPException):
        if "Invalid Form Body" in str(error):
            pass

    elif isinstance(error, bot.ResponseError):
        await ctx.error(error, "Response Code > 400:")

    elif isinstance(error, ValueError):
        if ctx.command in ['vote']:
            await ctx.error(error, "Error while voting: ")

    else:
        await ctx.error("```{}: {}```".format(type(error).__qualname__, error), title=f"Ignoring exception in command *{ctx.command}*:", channel=bot.get_channel(bot.bot_logs_id))
        print('Ignoring {} in command {}'.format(type(error).__qualname__, ctx.command))
        traceback.print_exception(type(error), error, error.__traceback__)
        do_send = False

    if do_send:
        print('Ignoring {} in command {}'.format(type(error).__qualname__, ctx.command))

@bot.command(name="help")
async def _help(self, ctx, command: str = None):
    """Shows this message. Does not display details for each command yet."""
    cogs = {}
    for cmd in self.bot.commands:
        if cmd.hidden:
            continue
        if not cmd.cog_name in cogs:
            cogs[cmd.cog_name] = []
        aliases = ", ".join(cmd.aliases)
        if not aliases:
            cogs[cmd.cog_name].append(cmd.qualified_name)
        else:
            cogs[cmd.cog_name].append("{} [{}]".format(cmd.qualified_name, ", ".join(cmd.aliases)))
    for cog in cogs.copy():
        cogs[cog] = sorted(cogs[cog])

    if command is None:
        command = "Help"
        embed = discord.Embed(description="{0}\nUse `{1}help command` or `{1}help cog` for further detail.".format(
            self.bot.description, ctx.clean_prefix()), color=0x00ff00)
        for cog in sorted(cogs):
            embed.add_field(name=cog, value=", ".join(cogs[cog]), inline=False)

    elif command.capitalize() in cogs:
        command = command.capitalize()
        embed = discord.Embed(description=inspect.cleandoc(self.bot.get_cog(command).__doc__), colour=0x00ff00)
        for cmd in self.bot.get_cog_commands(command):
            if not cmd.hidden:
                embed.add_field(name=cmd.qualified_name, value=cmd.help, inline=False)

    elif self.bot.get_command(command) in self.bot.commands and not self.bot.get_command(command).hidden:
        cmd_group = self.bot.get_command(command)
        embed = discord.Embed(description=cmd_group.help.format(ctx.prefix), color=0x00ff00)
        if isinstance(cmd_group, commands.Group):
            for cmd in cmd_group.commands:
                if not cmd.hidden:
                    embed.add_field(name=cmd.name, value=cmd.help, inline=False)

    else:
        embed = discord.Embed(description="The parsed cog or command `{}` does not exist.".format(command), color=0xff0000)
        command = "Error"

    embed.timestamp = datetime.utcnow()
    embed.set_author(name=command.capitalize(), url="https://discord.gg/bEYgRmc")
    embed.set_footer(text="Requested by: {}".format(ctx.message.author), icon_url=ctx.message.author.avatar_url)
    await ctx.send(embed=embed)

try:
    bot.run(token, reconnect=True)
except (KeyboardInterrupt, EOFError):
    pass
