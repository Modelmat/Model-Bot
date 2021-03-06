import asyncio
import json
import random
from collections import OrderedDict
from datetime import datetime
from random import sample

import aiogoogletrans
import aiohttp
import async_timeout
import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from fuzzywuzzy import process
from tabulate import tabulate

import custom_classes as cc

PROTOCOLS = ['ssh', 'smb', 'smtp', 'ftp', 'imap', 'http', 'https', 'pop', 'htcpcp', 'telnet', 'tcp', 'ipoac']
TABLE_HEADERS = ["PORT", "PROTOCOL", "SECURE"]


def gen_data():
    fake_ports = sorted([random.randint(0, 65535) for i in range(random.randint(0, 10))])
    protocols = random.sample(PROTOCOLS, len(fake_ports))
    secured = [random.choice(["'false'", 'true']) for i in fake_ports]
    table_data = list(zip(fake_ports, protocols, secured))
    table = str(tabulate(table_data, TABLE_HEADERS, tablefmt="rst"))
    open_data = [data[0:3] for data in table_data if data[2]]
    open_ports = ", ".join([str(data[0]) for data in open_data if data[2] == "true"])
    return table_data, table, open_ports, open_data


class Internet(cc.KernCog):
    """Web functions (that make requests)"""

    def __init__(self, bot: cc.KernBot):
        self.bot = bot
        self.translator = aiogoogletrans.Translator()

    async def get_youtube_videos(self, page_url, cutoff_length=80, result_length=5):
        results = OrderedDict()
        vids = []

        with async_timeout.timeout(10):
            async with self.bot.session.get(page_url) as resp:
                soup = BeautifulSoup((await resp.read()).decode('utf-8'), "lxml")

        for link in soup.find_all('a', href=True):
            url = link.get('href', "")
            title = link.get('title', "")
            if "/watch" in url and title and not title.startswith('https') and "googleads" not in url:
                if not url.startswith('https://www.youtube.com'):
                    url = 'https://www.youtube.com' + url
                results[title] = url

        for vid, url in results.items():
            vid = vid.replace("[", "⦋").replace("]", "⦌")
            if vid.isupper():
                vid = vid[:int(cutoff_length * 3 / 4)] + "..."
            if len(vid) > cutoff_length:
                vid = vid[:cutoff_length] + "..."
            vids.append(f"[{vid}]({url})")

        return vids[:result_length]

    @commands.group(invoke_without_command=True)
    async def youtube(self, ctx, *, keyword: str):
        """Searches YouTube for a video"""
        url = f"https://www.youtube.com/results?search_query={keyword}&sp=EgIQAQ%253D%253D"
        vids = await self.get_youtube_videos(url)

        if len(keyword) > 40:
            keyword = keyword[:40] + "..."

        results = "\n".join(vids)
        await ctx.neutral(results, f"YouTube Search Results for: {keyword}")

    @youtube.command()
    async def trending(self, ctx, num_results=5):
        """Gets current trending videos"""
        url = "https://www.youtube.com/feed/trending"
        vids = await self.get_youtube_videos(url, 77, num_results)
        results = "\n".join([f"{index}) {title}" for index, title in enumerate(vids, start=1)])
        await ctx.neutral(results, "YouTube Trending")

    @youtube.command()
    async def channel(self, ctx, channel, num_videos=5):
        """Get a channel's latest 5 videos"""
        pass

    @youtube.command()
    async def playlist(self, ctx, playlist, num_videos=5):
        """Get a playlist's 1st 5 videos"""
        pass

    @commands.command()
    async def demotivate(self, ctx, *, search_term=""):
        """Provides an embed with a demotivating quote & poster.
        Without a search_term specified a random result is returned."""
        async with ctx.typing():
            search_term = search_term.lower()
            demotivators = self.bot.demotivators
            if search_term:
                dem = demotivators.get(search_term)
            else:
                dem = sample(list(demotivators.values()), 1)[0]
            if dem is None:
                fuzzy = process.extractOne(search_term, demotivators.keys()) or (0, 0)
                if fuzzy[1] < 75:
                    return await ctx.error("No demotivator found.")
                dem = demotivators.get(fuzzy[0])
            e = discord.Embed(colour=discord.Colour.green(), description=dem['quote'])
            e.set_author(
                name=dem['title'],
                url=dem['product_url'],
                icon_url="https://i.imgur.com/SAQRxIc.png",
            )
            e.set_footer(
                text="Data from Despair, Inc",
                icon_url=ctx.message.author.avatar_url)
            e.timestamp = datetime.utcnow()
            e.set_image(url=dem['img_url'])
            await ctx.send(embed=e)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(hidden=True)
    async def hack(self, ctx, *, url: cc.url):
        """Starts a fake hacking instance on a specified URL."""
        loading, th, hu, te, on = self.bot.get_emojis(395834326450831370, 396890900783038499, 396890900158218242,
                                                      396890900753547266, 396890900426653697)
        table_data, table, open_ports, open_data = gen_data()

        msg = await ctx.send(f"Looking for open ports in <{url}>")
        content = msg.content
        await msg.edit(content=f"{content}\nPort: {th}{hu}{te}{on}{loading}")
        await asyncio.sleep(10)

        if not open_ports:
            return await msg.edit(content=f":x: Port scan complete. No insecure ports found.")

        await msg.edit(
            content=
            f"Port scan complete. Scan report: ```ml\n{table}```\n{loading}Attempting to bruteforce insecure ports: ({open_ports})"
        )

        # Now do fake atatck on unsecure port (note, add a RFC 1149 reference)

    async def create_video(self, text):
        with async_timeout.timeout(10):
            async with self.bot.session.post(
                    url="http://talkobamato.me/synthesize.py", data={"input_text": text}) as resp:
                if resp.status >= 400:
                    raise discord.HTTPException(resp, f"{resp.url} returned error code {resp.status}")
                url = resp.url

        key = url.query['speech_key']
        link = f"http://talkobamato.me/synth/output/{key}/obama.mp4"
        await asyncio.sleep(len(text) // 5)
        with async_timeout.timeout(10):
            async with self.bot.session.get(link) as resp:
                if resp.status >= 400:
                    raise discord.HTTPException(resp, f"{resp.url} returned error code {resp.status}")
        return link

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def obama(self, ctx, *, text: str):
        """Makes obama speak."""
        if len(text) - len(ctx.prefix + "obama") > 280:
            return await ctx.send("A maximum character total of 280 is enforced. You sent: `{}` characters".format(
                len(text)))
        async with ctx.typing():
            link = await self.create_video(text)
            await ctx.send(link)

    @obama.error
    async def obama_error_handler(self, ctx, error):
        error = getattr(error, "original", error)
        if isinstance(error, asyncio.TimeoutError):
            await ctx.error("http://talkobamato.me/ is not responding.", "Request Timed Out")
        elif isinstance(error, discord.HTTPException):
            await ctx.error(error.text,
                            error.response.reason,
                            footer="Most likely you passed an emoji or special char. It doesn't like them.")
        elif isinstance(error, aiohttp.ServerDisconnectedError):
            await ctx.error("A connection error occurred. Please try again later.")

    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.command(aliases=["translate_mixup", "googletrans"])
    async def translate(self, ctx, *, text):
        """Translates text to 10 random languages then back to English."""
        async with ctx.typing():
            languages = sample(list(aiogoogletrans.LANGUAGES), 10)
            source_language = (await self.translator.translate(text)).src
            if source_language in languages:
                languages.remove(source_language)
            languages = languages[:9] + ["en"]

            for language in languages:
                translation = await self.translator.translate(text, dest=language)
                text = translation.text

            if len(text) > 1900:
                text = await ctx.upload(text)
            else:
                text = f"```{text}```"

            await ctx.send(f"""**User:** {ctx.author.display_name}
**Languages:** ```{" > ".join(aiogoogletrans.LANGUAGES[l] for l in languages)}```
**Result:** {text}""")

    @translate.error
    async def translate_error_handler(self, ctx, error):
        error = getattr(error, "original", error)
        if isinstance(error, json.JSONDecodeError):
            await ctx.error("There was an error translating your input. "
                            "Please try again.\n"
                            f"Remove any emojis and try again")
        elif isinstance(error, ValueError):
            await ctx.error("There was an error translating your input. "
                            "Please try again.")


def setup(bot):
    bot.add_cog(Internet(bot))
