from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore


class ChatAI(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.client: Optional[AsyncOpenAI] = None
        settings = getattr(bot, "settings", None)
        api_key = getattr(settings, "openai_api_key", None) if settings else None
        if api_key and AsyncOpenAI is not None:
            self.client = AsyncOpenAI(api_key=api_key)

    @app_commands.command(name="chat", description="Ask the AI a question (requires OPENAI_API_KEY)")
    async def chat(self, interaction: discord.Interaction, prompt: str) -> None:
        if not self.client:
            await interaction.response.send_message("AI chat is not configured.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            resp = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful, concise assistant for a Discord bot."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=256,
            )
            content = resp.choices[0].message.content if resp.choices else "No response."
            await interaction.followup.send(content)
        except Exception as exc:
            await interaction.followup.send(f"Error: {exc}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ChatAI(bot))