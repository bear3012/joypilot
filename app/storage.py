from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from collections import deque


@dataclass
class ReplySessionState:
    session_id: str
    start_at: datetime
    expires_at: datetime
    context_snippets: list[str] = field(default_factory=list)
    last_message_bank: list[dict] = field(default_factory=list)


@dataclass
class EntitlementState:
    day: str
    reply_used: int = 0
    relationship_used: int = 0
    emergency_pack_credits: int = 0
    object_slots_active: int = 0


@dataclass
class EntitlementPendingDeduct:
    user_id: str
    day: str
    scope: str
    use_emergency_pack: bool


@dataclass
class InMemoryStore:
    reply_sessions: dict[str, ReplySessionState] = field(default_factory=dict)
    usage_counters: dict[str, dict[str, int]] = field(default_factory=dict)
    audit_entries: list[dict] = field(default_factory=list)
    segment_summaries: list[dict] = field(default_factory=list)
    audit_entries_by_user: dict[str, deque[dict]] = field(default_factory=dict)
    segment_summaries_by_target: dict[str, deque[dict]] = field(default_factory=dict)
    entitlement_state_by_user_day: dict[str, EntitlementState] = field(default_factory=dict)
    entitlement_user_locks: dict[str, asyncio.Lock] = field(default_factory=dict)
    entitlement_pending_deducts: dict[str, EntitlementPendingDeduct] = field(default_factory=dict)


STORE = InMemoryStore()
