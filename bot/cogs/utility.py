from __future__ import annotations

import platform
import time
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.process_start = time.perf_counter()

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Pong! Latency: {round(self.bot.latency * 1000)} ms")

    @app_commands.command(name="uptime", description="Show how long the bot has been running")
    async def uptime(self, interaction: discord.Interaction) -> None:
        delta = datetime.now(timezone.utc) - self.bot.start_time
        secs = int(delta.total_seconds())
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        await interaction.response.send_message(f"Uptime: {h}h {m}m {s}s")

    @app_commands.command(name="serverinfo", description="Information about this server")
    async def serverinfo(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        embed = discord.Embed(title=f"{guild.name}", color=discord.Color.blurple())
        embed.add_field(name="Members", value=str(guild.member_count))
        embed.add_field(name="Owner", value=f"<@{guild.owner_id}>" if guild.owner_id else "-")
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, style="R"))
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Information about a user")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member | None = None) -> None:
        member = member or interaction.user  # type: ignore[assignment]
        embed = discord.Embed(title=f"{member} ({member.id})", color=discord.Color.green())
        embed.add_field(name="Joined", value=discord.utils.format_dt(member.joined_at) if member.joined_at else "-")
        embed.add_field(name="Created", value=discord.utils.format_dt(member.created_at))
        embed.add_field(name="Top Role", value=member.top_role.mention if member.top_role else "-")
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Show a user's avatar")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member | None = None) -> None:
        member = member or interaction.user  # type: ignore[assignment]
        if member.display_avatar:
            await interaction.response.send_message(member.display_avatar.url)
        else:
            await interaction.response.send_message("No avatar")

    @app_commands.command(name="invite", description="Get the bot's invite link")
    async def invite(self, interaction: discord.Interaction) -> None:
        client_id = self.bot.application_id or self.bot.user.id  # type: ignore
        perms = discord.Permissions(administrator=True)
        url = discord.utils.oauth_url(client_id, permissions=perms)
        await interaction.response.send_message(f"Invite me: {url}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Utility(bot))