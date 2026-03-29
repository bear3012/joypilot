from __future__ import annotations

import json
from datetime import datetime
from threading import Lock
from uuid import uuid4

from app.config import MAX_SESSION_TOTAL_CHARS, MAX_SESSION_TURNS, SESSION_DURATION
from app.storage import ReplySessionState, STORE

_LOCK_GUARD = Lock()
_SESSION_LOCKS: dict[str, Lock] = {}


def build_session_key(user_id: str, target_id: str) -> str:
    # Use canonical JSON tuple to avoid delimiter collision attacks.
    return json.dumps([user_id, target_id], ensure_ascii=False, separators=(",", ":"))


def get_or_create_session(
    *, user_id: str, target_id: str, now: datetime, force_new: bool
) -> tuple[ReplySessionState, bool]:
    """Atomically get or create one active session per user-target key."""
    key = build_session_key(user_id, target_id)
    with _get_lock(key):
        existing = STORE.reply_sessions.get(key)
        if existing and existing.expires_at > now and not force_new:
            return existing, False

        session = ReplySessionState(
            session_id=f"reply_{uuid4().hex[:12]}",
            start_at=now,
            expires_at=now + SESSION_DURATION,
        )
        STORE.reply_sessions[key] = session
        return session, True


def update_session_after_reply(
    *,
    user_id: str,
    target_id: str,
    snippet: str,
    message_bank: list[dict],
) -> None:
    key = build_session_key(user_id, target_id)
    with _get_lock(key):
        session = STORE.reply_sessions.get(key)
        if session is None:
            return
        _append_context(session, snippet)
        session.last_message_bank = message_bank


def _append_context(session: ReplySessionState, snippet: str) -> None:
    text = snippet.strip()
    if not text:
        return
    if len(text) > MAX_SESSION_TOTAL_CHARS:
        text = text[:MAX_SESSION_TOTAL_CHARS]

    session.context_snippets.append(text)

    # Space lock: enforce FIFO by turns first, then by total characters.
    while len(session.context_snippets) > MAX_SESSION_TURNS:
        session.context_snippets.pop(0)
    while _total_chars(session.context_snippets) > MAX_SESSION_TOTAL_CHARS and session.context_snippets:
        session.context_snippets.pop(0)


def _get_lock(key: str) -> Lock:
    with _LOCK_GUARD:
        lock = _SESSION_LOCKS.get(key)
        if lock is None:
            lock = Lock()
            _SESSION_LOCKS[key] = lock
        return lock


def _total_chars(snippets: list[str]) -> int:
    return sum(len(snippet) for snippet in snippets)
