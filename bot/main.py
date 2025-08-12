from __future__ import annotations

import argparse
import asyncio
import logging

from .bot import ProBot
from .config import load_settings
from .utils.logging import setup_logging


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Run the Pro Discord Bot")
    parser.add_argument("--check", action="store_true", help="Validate config and exit")
    args = parser.parse_args()

    settings = load_settings()
    setup_logging(settings.log_level)

    if args.check:
        logging.getLogger("startup").info("Configuration OK. Owners: %s | Guilds: %s", settings.owner_ids, settings.guild_ids)
        return

    bot = ProBot(settings)
    await bot.start(settings.discord_token)


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass