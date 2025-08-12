# Pro Discord Bot (Python)

A modern, professional Discord bot featuring administration, moderation, fun, minigames, music (with queue), utilities, and optional AI chat.

## Features
- Administration: kick, ban, unban, purge, timeout, slowmode, say, announce
- Music: join, play, pause, resume, skip, stop, queue (yt-dlp + FFmpeg)
- Fun: 8ball, dice, choose, meme, cat/dog
- Games: Rock-Paper-Scissors, TicTacToe (buttons)
- Utility: ping, uptime, userinfo, serverinfo, avatar, invite
- Owner: load/unload/reload cogs
- Chat: optional AI chat command if `OPENAI_API_KEY` is set

## Requirements
- Python 3.10+
- FFmpeg installed and on PATH (for music)
  - Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y ffmpeg`

## Setup
1. Clone repo and open terminal in project root
2. Create and fill `.env` from `.env.example`
3. Create venv and install deps:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## Run
```bash
# Activate the venv first
source .venv/bin/activate
# Run the bot
python -m bot.main
```

To speed up slash-command registration during development, set `GUILD_IDS` in `.env` to your test server ID(s).

## Deploy tips
- Keep your `DISCORD_TOKEN` private
- Use `LOG_LEVEL=INFO` in production
- Ensure FFmpeg is installed on your host

## License
MIT