from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta


def _mod_perms():
    return app_commands.default_permissions(manage_guild=True)


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @_mod_perms()
    @app_commands.command(name="purge", description="Delete a number of messages from this channel")
    @app_commands.describe(amount="How many messages to delete (max 100)")
    async def purge(self, interaction: discord.Interaction, amount: int) -> None:
        if not interaction.channel or not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("This command can only be used in text channels.", ephemeral=True)
            return
        amount = max(1, min(100, amount))
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)

    @_mod_perms()
    @app_commands.command(name="kick", description="Kick a member")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None) -> None:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"Kicked {member.mention}. Reason: {reason or 'No reason provided'}")

    @_mod_perms()
    @app_commands.command(name="ban", description="Ban a member")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None) -> None:
        await member.ban(reason=reason, delete_message_days=0)
        await interaction.response.send_message(f"Banned {member.mention}. Reason: {reason or 'No reason provided'}")

    @_mod_perms()
    @app_commands.command(name="unban", description="Unban a user by ID")
    async def unban(self, interaction: discord.Interaction, user_id: int) -> None:
        user = await self.bot.fetch_user(user_id)
        await interaction.guild.unban(user)  # type: ignore[arg-type]
        await interaction.response.send_message(f"Unbanned {user.mention}")

    @_mod_perms()
    @app_commands.command(name="timeout", description="Timeout a member for N minutes")
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str | None = None) -> None:
        minutes = max(1, min(10080, minutes))
        await member.timeout(discord.utils.utcnow() + timedelta(minutes=minutes), reason=reason)
        await interaction.response.send_message(f"Timed out {member.mention} for {minutes} minutes.")

    @_mod_perms()
    @app_commands.command(name="slowmode", description="Set channel slowmode in seconds")
    async def slowmode(self, interaction: discord.Interaction, seconds: int) -> None:
        if not interaction.channel or not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("This command can only be used in text channels.", ephemeral=True)
            return
        seconds = max(0, min(21600, seconds))
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"Slowmode set to {seconds}s")

    @_mod_perms()
    @app_commands.command(name="say", description="Make the bot say something")
    async def say(self, interaction: discord.Interaction, message: str) -> None:
        await interaction.response.send_message("Sent.", ephemeral=True)
        if interaction.channel and isinstance(interaction.channel, discord.TextChannel):
            await interaction.channel.send(message)

    @_mod_perms()
    @app_commands.command(name="announce", description="Send an embed announcement")
    async def announce(self, interaction: discord.Interaction, title: str, message: str) -> None:
        embed = discord.Embed(title=title, description=message, color=discord.Color.gold())
        await interaction.response.send_message("Announcement sent.", ephemeral=True)
        if interaction.channel and isinstance(interaction.channel, discord.TextChannel):
            await interaction.channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))