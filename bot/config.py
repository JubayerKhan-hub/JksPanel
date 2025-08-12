import os
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv


def _parse_int_list(value: str | None) -> List[int]:
    if not value:
        return []
    result: List[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.append(int(part))
        except ValueError:
            continue
    return result


@dataclass
class Settings:
    discord_token: str
    owner_ids: List[int]
    guild_ids: List[int]
    openai_api_key: Optional[str]
    log_level: str


def load_settings() -> Settings:
    load_dotenv()

    discord_token = os.getenv("DISCORD_TOKEN", "").strip()
    if not discord_token:
        raise RuntimeError("DISCORD_TOKEN not set. Put it in a .env file or environment variables.")

    owner_ids = _parse_int_list(os.getenv("OWNER_IDS"))
    guild_ids = _parse_int_list(os.getenv("GUILD_IDS"))
    openai_api_key = os.getenv("OPENAI_API_KEY")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    return Settings(
        discord_token=discord_token,
        owner_ids=owner_ids,
        guild_ids=guild_ids,
        openai_api_key=openai_api_key,
        log_level=log_level,
    )