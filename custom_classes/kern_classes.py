import discord
from discord.ext import commands

from datetime import datetime

from .paginator import Paginator


class KernGroup(commands.Group):
    async def can_run(self, ctx):
        if not self.enabled:
            return False
        return await super().can_run(ctx)

    def command(self, *args, **kwargs):
        def decorator(func):
            result = command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator


class KernCommand(commands.Command):
    async def can_run(self, ctx):
        if not self.enabled:
            return False
        return await super().can_run(ctx)


def command(name=None, cls=KernCommand, **attrs):
    return commands.command(name=name, cls=cls, **attrs)


def group(name=None, **attrs):
    return command(name=name, cls=KernGroup, **attrs)


class KernContext(commands.Context):
    async def paginator(self, num_entries, max_fields=5, base_embed=discord.Embed()):
        return await Paginator.init(self, num_entries, max_fields, base_embed)

    def clean_prefix(self):
        user = self.bot.user
        prefix = self.prefix.replace(user.mention, '@' + user.name)
        return prefix

    async def add_reaction(self, reaction):
        try:
            await self.message.add_reaction(reaction)
        except discord.Forbidden:
            pass

    async def del_reaction(self, reaction):
        try:
            await self.message.remove_reaction(reaction, self.guild.me)
        except discord.Forbidden:
            pass

    async def __embed(self, title, description, colour, rqst_by, timestamp, channel, footer, **kwargs):
        e = discord.Embed(colour=colour)
        if title is not None:
            e.title = str(title)
        if description is not None:
            e.description = str(description)
        if rqst_by:
            e.set_footer(icon_url=self.message.author.avatar_url)
        if footer:
            e.set_footer(text=footer)
        if timestamp:
            e.timestamp = datetime.utcnow()
        if channel is None:
            return await self.send(embed=e, **kwargs)
        return await channel.send(embed=e, **kwargs)

    async def error(self, error, title="Error:", channel: discord.TextChannel = None, footer=None, **kwargs):
        if isinstance(error, Exception):
            if title == "Error:":
                title = error.__class__.__name__
            error = str(error)
        return await self.__embed(title, error, discord.Colour.red(), False, False, channel, footer, **kwargs)

    async def success(self, success, title="Success:", channel: discord.TextChannel = None, rqst_by=True, timestamp=True, footer=None, **kwargs):
        return await self.__embed(title, success, discord.Colour.green(), rqst_by, timestamp, channel, footer, **kwargs)

    async def neutral(self, text, title=None, channel: discord.TextChannel = None, rqst_by=True, timestamp=True, footer=None, **kwargs):
        return await self.__embed(title, text, 0x36393E, rqst_by, timestamp, channel, footer, **kwargs)

    async def warning(self, warning, title=None, channel: discord.TextChannel = None, rqst_by=True, timestamp=True, footer=None, **kwargs):
        return await self.__embed(title, warning, discord.Colour.orange(), rqst_by, timestamp, channel, footer, **kwargs)

    async def upload(self, content):
        async with self.bot.session.post("http://mystb.in/documents", data=content) as r:
            link = "http://mystb.in/" + (await r.json())["key"] + ".py"
        return link

    async def send(self, content: str = None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None):
        if content and len(content) > 1990:
            content = "**Output too long**:" + await self.upload(content)

        return await super().send(content=content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, nonce=nonce)
