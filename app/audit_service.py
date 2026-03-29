from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
import json
from typing import Any

from app.config import (
    MAX_AUDIT_LOGS_PER_USER,
    MAX_SEGMENT_SUMMARIES_PER_TARGET,
    MAX_SEGMENT_SUMMARY_BYTES,
)
from app.storage import STORE

_AUDIT_BLOCK_KEYS = (
    "ocr_preview",
    "dialogue_turns",
    "text_input",
    "left_text",
    "right_text",
)
_AUDIT_ALLOWLIST_KEYS = {
    "event",
    "code",
    "status",
    "safety_status",
    "gate_decision",
    "scope",
    "mode",
    "issue_codes",
    "risk_level",
    "asymmetric_risk",
    "strategy",
    "send_recommendation",
    "triggered_rules",
    "degrade_type",
    "decision",
    "latency_ms",
    "elapsed_ms",
    "duration_ms",
    "check_id",
    "reason",
    "message",
    "count",
    "limit",
    "bytes",
    "action",
}
_MAX_AUDIT_VALUE_LEN = 512
_MAX_AUDIT_ITEMS = 20
_SUMMARY_MAX_TEXT = 2000
_SUMMARY_MAX_BULLETS = 8
_SUMMARY_MAX_BULLET_LEN = 200


def write_audit_event(
    *,
    event: str,
    user_id: str | None = None,
    target_id: str | None = None,
    mode: str | None = None,
    payload: dict[str, Any] | None = None,
    created_at: datetime | None = None,
) -> bool:
    try:
        timestamp = created_at or datetime.now(UTC)
        entry: dict[str, Any] = {
            "event": event,
            "created_at": timestamp.isoformat(),
        }
        if user_id:
            entry["user_id"] = user_id
        if target_id:
            entry["target_id"] = target_id
        if mode:
            entry["mode"] = mode
        if payload:
            safe_payload = sanitize_audit_payload(payload)
            if safe_payload:
                entry["payload"] = safe_payload

        _append_audit_entry(entry=entry, user_id=user_id or "__anonymous__")
        return True
    except Exception:
        # Fail-safe: side-channel logging errors must never break business flows.
        return False


def write_segment_summary(
    *,
    target_id: str,
    source_type: str,
    stage: str,
    summary: str,
    asymmetric_risk: str,
    summary_version: str = "v1",
    created_at: datetime | None = None,
    payload: dict[str, Any] | None = None,
) -> bool:
    try:
        entry: dict[str, Any] = {
            "target_id": target_id,
            "summary_version": summary_version,
            "created_at": (created_at or datetime.now(UTC)).isoformat(),
            "source_type": source_type,
            "stage": stage,
            "summary": summary,
            "asymmetric_risk": asymmetric_risk,
        }
        if payload:
            entry["payload"] = _sanitize_summary_payload(payload)

        if _summary_size_bytes(entry) > MAX_SEGMENT_SUMMARY_BYTES:
            entry = _trim_segment_entry(entry)

        if _summary_size_bytes(entry) > MAX_SEGMENT_SUMMARY_BYTES:
            write_audit_event(
                event="SEGMENT_SUMMARY_TOO_LARGE",
                target_id=target_id,
                mode="RELATIONSHIP",
                payload={
                    "bytes": _summary_size_bytes(entry),
                    "limit": MAX_SEGMENT_SUMMARY_BYTES,
                    "action": "reject",
                },
            )
            return False

        _append_segment_summary(entry=entry, target_id=target_id)
        return True
    except Exception:
        # Fail-safe: side-channel summary write errors must never break business flows.
        return False


def sanitize_audit_payload(payload: dict[str, Any]) -> dict[str, Any]:
    safe_payload: dict[str, Any] = {}
    for key, value in payload.items():
        key_text = str(key)
        lower_key = key_text.lower()
        if _is_blocked_audit_key(lower_key):
            continue
        if key_text not in _AUDIT_ALLOWLIST_KEYS:
            continue
        safe_payload[key_text] = _sanitize_audit_value(value)
    return safe_payload


def _sanitize_audit_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, str):
        return value[:_MAX_AUDIT_VALUE_LEN]
    if isinstance(value, list):
        return [_sanitize_audit_value(item) for item in value[:_MAX_AUDIT_ITEMS]]
    if isinstance(value, dict):
        nested: dict[str, Any] = {}
        for key, nested_value in list(value.items())[:_MAX_AUDIT_ITEMS]:
            key_text = str(key)
            if _is_blocked_audit_key(key_text.lower()):
                continue
            if key_text not in _AUDIT_ALLOWLIST_KEYS:
                continue
            nested[key_text] = _sanitize_audit_value(nested_value)
        return nested
    return str(value)[:_MAX_AUDIT_VALUE_LEN]


def _sanitize_summary_payload(payload: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        key_text = str(key)
        if key_text == "evidence_bullets" and isinstance(value, list):
            safe[key_text] = [str(item)[:_SUMMARY_MAX_BULLET_LEN] for item in value[:_SUMMARY_MAX_BULLETS]]
            continue
        if isinstance(value, (int, float, bool, type(None))):
            safe[key_text] = value
            continue
        safe[key_text] = str(value)[:_MAX_AUDIT_VALUE_LEN]
    return safe


def _is_blocked_audit_key(lower_key: str) -> bool:
    if "prepared_upload" in lower_key and "text" in lower_key:
        return True
    if "dialogue" in lower_key and "text" in lower_key:
        return True
    return any(blocked in lower_key for blocked in _AUDIT_BLOCK_KEYS)


def _summary_size_bytes(entry: dict[str, Any]) -> int:
    dumped = json.dumps(entry, ensure_ascii=False, default=str)
    return len(dumped.encode("utf-8"))


def _trim_segment_entry(entry: dict[str, Any]) -> dict[str, Any]:
    trimmed = dict(entry)
    summary_text = str(trimmed.get("summary", ""))
    if len(summary_text) > _SUMMARY_MAX_TEXT:
        trimmed["summary"] = summary_text[:_SUMMARY_MAX_TEXT]

    payload = trimmed.get("payload")
    if isinstance(payload, dict):
        limited_payload: dict[str, Any] = {}
        for key, value in list(payload.items())[:_MAX_AUDIT_ITEMS]:
            if key == "evidence_bullets" and isinstance(value, list):
                limited_payload[key] = [str(item)[:_SUMMARY_MAX_BULLET_LEN] for item in value[:_SUMMARY_MAX_BULLETS]]
            elif isinstance(value, str):
                limited_payload[key] = value[:_MAX_AUDIT_VALUE_LEN]
            elif isinstance(value, list):
                limited_payload[key] = [str(item)[:_SUMMARY_MAX_BULLET_LEN] for item in value[:_SUMMARY_MAX_BULLETS]]
            else:
                limited_payload[key] = value
        trimmed["payload"] = limited_payload
    return trimmed


def _append_audit_entry(*, entry: dict[str, Any], user_id: str) -> None:
    bucket = STORE.audit_entries_by_user.get(user_id)
    if bucket is None:
        bucket = deque(maxlen=MAX_AUDIT_LOGS_PER_USER)
        STORE.audit_entries_by_user[user_id] = bucket
    bucket.append(entry)

    STORE.audit_entries.append(entry)
    _trim_legacy_audit_list(user_id=user_id)


def _append_segment_summary(*, entry: dict[str, Any], target_id: str) -> None:
    bucket = STORE.segment_summaries_by_target.get(target_id)
    if bucket is None:
        bucket = deque(maxlen=MAX_SEGMENT_SUMMARIES_PER_TARGET)
        STORE.segment_summaries_by_target[target_id] = bucket
    bucket.append(entry)

    STORE.segment_summaries.append(entry)
    _trim_legacy_segment_list(target_id=target_id)


def _trim_legacy_audit_list(*, user_id: str) -> None:
    matching = [idx for idx, item in enumerate(STORE.audit_entries) if item.get("user_id", "__anonymous__") == user_id]
    overflow = len(matching) - MAX_AUDIT_LOGS_PER_USER
    for idx in matching[:max(0, overflow)]:
        STORE.audit_entries[idx] = {}
    if overflow > 0:
        STORE.audit_entries[:] = [item for item in STORE.audit_entries if item]


def _trim_legacy_segment_list(*, target_id: str) -> None:
    matching = [idx for idx, item in enumerate(STORE.segment_summaries) if item.get("target_id") == target_id]
    overflow = len(matching) - MAX_SEGMENT_SUMMARIES_PER_TARGET
    for idx in matching[:max(0, overflow)]:
        STORE.segment_summaries[idx] = {}
    if overflow > 0:
        STORE.segment_summaries[:] = [item for item in STORE.segment_summaries if item]
