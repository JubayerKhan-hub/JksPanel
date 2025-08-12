from __future__ import annotations

import asyncio
import logging
from typing import Iterable, Sequence

import discord
from discord.ext import commands

from .config import Settings


COGS: Sequence[str] = (
    "bot.cogs.utility",
    "bot.cogs.admin",
    "bot.cogs.fun",
    "bot.cogs.games",
    "bot.cogs.music",
    "bot.cogs.chat",
    "bot.cogs.owner",
)


class ProBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.reactions = True
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=None,
        )
        self.settings = settings
        self.log = logging.getLogger("ProBot")
        self.start_time = discord.utils.utcnow()

    async def setup_hook(self) -> None:
        for ext in COGS:
            try:
                await self.load_extension(ext)
                self.log.info("Loaded extension %s", ext)
            except Exception as exc:
                self.log.exception("Failed to load extension %s: %s", ext, exc)

        await self._sync_commands()

    async def _sync_commands(self) -> None:
        try:
            if self.settings.guild_ids:
                for guild_id in self.settings.guild_ids:
                    guild = discord.Object(id=guild_id)
                    await self.tree.sync(guild=guild)
                self.log.info("Slash commands synced to %d guild(s)", len(self.settings.guild_ids))
            else:
                await self.tree.sync()
                self.log.info("Slash commands globally synced (may take up to 1 hour)")
        except Exception:
            self.log.exception("Failed to sync application commands")

    async def on_ready(self) -> None:
        self.log.info("Logged in as %s (ID: %s)", self.user, getattr(self.user, "id", "?"))
        await self.change_presence(activity=discord.Game(name="/help | !help"))

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("You don't have permission to use this command.")
            return
        if isinstance(error, commands.CommandNotFound):
            return
        self.log.exception("Command error: %s", error)
        await ctx.reply("An error occurred. Please try again.")