"""SQLite-backed session helpers for the Agents SDK."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict
from uuid import uuid4

from agents import SQLiteSession


SESSION_DB_PATH = Path(__file__).resolve().parent.parent / "sessions.db"
SESSION_NAMES = ("scenario", "feedback", "reflection")


def _new_session_id(prefix: str) -> str:
    return f"{prefix}-{uuid4()}"


def _create_session(prefix: str) -> SQLiteSession:
    SESSION_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SQLiteSession(_new_session_id(prefix), str(SESSION_DB_PATH))


def create_session_store() -> Dict[str, SQLiteSession]:
    """Return a dict with dedicated sessions per agent."""

    return {name: _create_session(name) for name in SESSION_NAMES}


def clear_session(session: SQLiteSession) -> None:
    """Delete persisted history for a session."""

    asyncio.run(session.clear_session())


def replace_session(store: Dict[str, SQLiteSession], name: str) -> None:
    """Clear an existing session and create a new one."""

    if name in store:
        clear_session(store[name])
    store[name] = _create_session(name)


def reset_session_store(store: Dict[str, SQLiteSession] | None = None) -> Dict[str, SQLiteSession]:
    """Clear all known sessions and return a fresh store."""

    if store:
        for session in store.values():
            clear_session(session)
    return create_session_store()
