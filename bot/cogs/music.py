from __future__ import annotations

import asyncio
import functools
import itertools
from dataclasses import dataclass
from typing import Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands

import yt_dlp


YTDL_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": "%(_id)s.%(ext)s",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
}

FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


audioloader = yt_dlp.YoutubeDL(YTDL_OPTS)


@dataclass
class Track:
    title: str
    url: str
    webpage_url: str
    requester_id: int


class GuildMusic:
    def __init__(self, voice_client: discord.VoiceClient | None = None) -> None:
        self.voice_client = voice_client
        self.queue: List[Track] = []
        self.now_playing: Optional[Track] = None
        self.play_next = asyncio.Event()

    def add(self, track: Track) -> None:
        self.queue.append(track)

    def skip(self) -> None:
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()

    def clear(self) -> None:
        self.queue.clear()


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.music: Dict[int, GuildMusic] = {}

    def get_guild_music(self, guild_id: int) -> GuildMusic:
        if guild_id not in self.music:
            self.music[guild_id] = GuildMusic()
        return self.music[guild_id]

    async def ensure_voice(self, interaction: discord.Interaction) -> discord.VoiceClient:
        if not interaction.user or not isinstance(interaction.user, discord.Member):
            raise commands.CommandError("Only members can use voice commands")
        if not interaction.user.voice or not interaction.user.voice.channel:
            raise commands.CommandError("You are not in a voice channel")
        guild = interaction.guild
        assert guild is not None
        voice = guild.voice_client
        if voice is None:
            voice = await interaction.user.voice.channel.connect()
        return voice

    @app_commands.command(name="join", description="Join your voice channel")
    async def join(self, interaction: discord.Interaction) -> None:
        await self.ensure_voice(interaction)
        await interaction.response.send_message("Joined your voice channel.")

    @app_commands.command(name="leave", description="Disconnect from voice channel")
    async def leave(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        voice = interaction.guild.voice_client
        if voice:
            await voice.disconnect(force=True)
            await interaction.response.send_message("Disconnected.")
        else:
            await interaction.response.send_message("Not connected.")

    @app_commands.command(name="play", description="Play a song from YouTube or URL")
    @app_commands.describe(query="YouTube URL or search query")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer()
        voice = await self.ensure_voice(interaction)
        guild_music = self.get_guild_music(interaction.guild_id)  # type: ignore[arg-type]

        loop = asyncio.get_running_loop()

        def extract() -> Track:
            info = audioloader.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            return Track(
                title=info.get("title", "Unknown"),
                url=info["url"],
                webpage_url=info.get("webpage_url", query),
                requester_id=interaction.user.id,
            )

        track: Track = await loop.run_in_executor(None, extract)
        guild_music.add(track)

        await interaction.followup.send(f"Queued: [{track.title}]({track.webpage_url})")

        if not voice.is_playing() and not voice.is_paused():
            await self._play_loop(interaction.guild, voice)

    async def _play_loop(self, guild: discord.Guild | None, voice: discord.VoiceClient) -> None:
        if guild is None:
            return
        gm = self.get_guild_music(guild.id)
        while gm.queue:
            track = gm.queue.pop(0)
            gm.now_playing = track

            def after_play(err: Optional[Exception]) -> None:
                if err:
                    self.bot.dispatch("command_error", err)
                self.bot.loop.call_soon_threadsafe(gm.play_next.set)

            source = await discord.FFmpegOpusAudio.from_probe(track.url, **FFMPEG_OPTS)
            voice.play(source, after=after_play)
            channel = discord.utils.get(guild.text_channels, name="music") or guild.system_channel
            if channel:
                try:
                    await channel.send(f"Now playing: {track.title}")
                except Exception:
                    pass
            await gm.play_next.wait()
            gm.play_next.clear()
        gm.now_playing = None

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not interaction.guild.voice_client:
            await interaction.response.send_message("Not playing anything.")
            return
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipped.")

    @app_commands.command(name="stop", description="Stop playback and clear the queue")
    async def stop(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        gm = self.get_guild_music(interaction.guild.id)
        gm.clear()
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
        await interaction.response.send_message("Stopped and cleared queue.")

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction) -> None:
        vc = interaction.guild.voice_client if interaction.guild else None
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("Paused.")
        else:
            await interaction.response.send_message("Nothing is playing.")

    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction) -> None:
        vc = interaction.guild.voice_client if interaction.guild else None
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("Resumed.")
        else:
            await interaction.response.send_message("Nothing to resume.")

    @app_commands.command(name="queue", description="Show the music queue")
    async def queue(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        gm = self.get_guild_music(interaction.guild.id)
        if gm.now_playing is None and not gm.queue:
            await interaction.response.send_message("Queue is empty.")
            return
        lines: List[str] = []
        if gm.now_playing:
            lines.append(f"Now: {gm.now_playing.title}")
        for i, t in enumerate(gm.queue[:10], start=1):
            lines.append(f"{i}. {t.title}")
        await interaction.response.send_message("\n".join(lines))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))