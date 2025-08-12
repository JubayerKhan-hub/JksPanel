from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DATA_DIR / "bot.db"


def _ensure_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS game_stats (
                user_id INTEGER,
                game TEXT,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, game)
            )
            """
        )
        conn.commit()


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def get_value(key: str) -> Optional[str]:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM kv_store WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else None


def set_value(key: str, value: str) -> None:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO kv_store(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()


def bump_game_stat(user_id: int, game: str, result: str) -> None:
    if result not in ("win", "loss", "draw"):
        raise ValueError("result must be one of: win, loss, draw")
    col = {"win": "wins", "loss": "losses", "draw": "draws"}[result]
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO game_stats(user_id, game, wins, losses, draws) VALUES (?, ?, 0, 0, 0) ON CONFLICT(user_id, game) DO NOTHING",
            (user_id, game),
        )
        cur.execute(f"UPDATE game_stats SET {col} = {col} + 1 WHERE user_id = ? AND game = ?", (user_id, game))
        conn.commit()


def get_game_stats(user_id: int, game: str) -> tuple[int, int, int]:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT wins, losses, draws FROM game_stats WHERE user_id = ? AND game = ?",
            (user_id, game),
        )
        row = cur.fetchone()
        if row:
            return int(row[0]), int(row[1]), int(row[2])
        return 0, 0, 0