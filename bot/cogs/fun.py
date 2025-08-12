from __future__ import annotations

import random

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands


EIGHTBALL_ANSWERS = [
    "It is certain.",
    "Without a doubt.",
    "You may rely on it.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "My reply is no.",
    "Outlook not so good.",
    "Very doubtful.",
]


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    async def eightball(self, interaction: discord.Interaction, question: str) -> None:
        await interaction.response.send_message(f"🎱 {random.choice(EIGHTBALL_ANSWERS)}")

    @app_commands.command(name="dice", description="Roll a dice N d M")
    async def dice(self, interaction: discord.Interaction, n: int = 1, m: int = 6) -> None:
        n = max(1, min(20, n))
        m = max(2, min(1000, m))
        rolls = [random.randint(1, m) for _ in range(n)]
        await interaction.response.send_message(f"Rolls: {', '.join(map(str, rolls))} | Total: {sum(rolls)}")

    @app_commands.command(name="choose", description="Let the bot choose from options")
    async def choose(self, interaction: discord.Interaction, options: str) -> None:
        parts = [p.strip() for p in options.split(",") if p.strip()]
        if len(parts) < 2:
            await interaction.response.send_message("Provide at least two options separated by commas.", ephemeral=True)
            return
        await interaction.response.send_message(f"I choose: {random.choice(parts)}")

    @app_commands.command(name="meme", description="Fetch a random meme")
    async def meme(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        url = "https://meme-api.com/gimme"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    await interaction.followup.send("Failed to fetch a meme.")
                    return
                data = await resp.json()
        embed = discord.Embed(title=data.get("title", "Meme"), url=data.get("postLink"))
        embed.set_image(url=data.get("url"))
        embed.set_footer(text=f"r/{data.get('subreddit', '')}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cat", description="Random cat image")
    async def cat(self, interaction: discord.Interaction) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search", timeout=15) as resp:
                data = await resp.json()
                url = data[0]["url"] if data else None
        await interaction.response.send_message(url or "Could not fetch cat :(")

    @app_commands.command(name="dog", description="Random dog image")
    async def dog(self, interaction: discord.Interaction) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random", timeout=15) as resp:
                data = await resp.json()
                url = data.get("message")
        await interaction.response.send_message(url or "Could not fetch dog :(")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))