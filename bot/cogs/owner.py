from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        bot: commands.Bot = interaction.client  # type: ignore[assignment]
        settings = getattr(bot, "settings", None)
        owners = set(getattr(settings, "owner_ids", []))
        if not owners:
            return await bot.is_owner(interaction.user)  # type: ignore[arg-type]
        return interaction.user.id in owners

    return app_commands.check(predicate)


class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @is_owner()
    @app_commands.command(name="reload", description="Reload a cog by dotted path")
    async def reload(self, interaction: discord.Interaction, extension: str) -> None:
        try:
            await self.bot.reload_extension(extension)
            await interaction.response.send_message(f"Reloaded {extension}.")
        except Exception as exc:
            await interaction.response.send_message(f"Failed to reload: {exc}")

    @is_owner()
    @app_commands.command(name="load", description="Load a cog by dotted path")
    async def load(self, interaction: discord.Interaction, extension: str) -> None:
        try:
            await self.bot.load_extension(extension)
            await interaction.response.send_message(f"Loaded {extension}.")
        except Exception as exc:
            await interaction.response.send_message(f"Failed to load: {exc}")

    @is_owner()
    @app_commands.command(name="unload", description="Unload a cog by dotted path")
    async def unload(self, interaction: discord.Interaction, extension: str) -> None:
        try:
            await self.bot.unload_extension(extension)
            await interaction.response.send_message(f"Unloaded {extension}.")
        except Exception as exc:
            await interaction.response.send_message(f"Failed to unload: {exc}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Owner(bot))