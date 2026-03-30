"""复盘库（Review Library）。

存储用户对话术的选择/拒绝历史，用于 Few-Shot 个性化。

存储格式：data/review_library/{user_id}.json（每用户一个 JSON 文件）
指纹算法：SHA-256(last_3_turns_text | J28:{j28} | J29:{j29} | J30:{j30})[:16]
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import REVIEW_LIBRARY_PATH
from app.contracts import LLMContext, ReviewEntry

logger = logging.getLogger(__name__)

_LIBRARY_ROOT = Path(REVIEW_LIBRARY_PATH)

# 只允许字母、数字、连字符、下划线；最长 128 字符，拒绝路径穿越字符
_SAFE_USER_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,128}$")


def _safe_user_path(user_id: str) -> Path | None:
    """返回 user_id 对应的安全文件路径；id 不合规时返回 None。"""
    if not _SAFE_USER_ID_RE.match(user_id):
        logger.warning("复盘库：user_id 含非法字符，已拒绝 I/O: %r", user_id)
        return None
    return _LIBRARY_ROOT / f"{user_id}.json"


# ──────────────────────────────────────────────────────────────────────────────
# 指纹计算
# ──────────────────────────────────────────────────────────────────────────────


def compute_context_fingerprint(
    last_3_turns: list[dict],
    llm_context: LLMContext,
) -> str:
    """
    生成对话场景的唯一指纹，防止跨用户/跨上下文碰撞。

    组成：(最后 3 轮文本拼接) | J28:{trend} | J29:{naked} | J30:{interrupted}
    取 SHA-256 前 16 位（64bit）。
    """
    turns_text = " / ".join(
        f"{t.get('speaker', '')}:{t.get('text', '')}" for t in last_3_turns[-3:]
    )
    raw = (
        f"{turns_text}"
        f"|J28:{llm_context.j28_trend or 'NONE'}"
        f"|J29:{llm_context.j29_naked_punct}"
        f"|J30:{llm_context.j30_triggered}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# ──────────────────────────────────────────────────────────────────────────────
# I/O 辅助
# ──────────────────────────────────────────────────────────────────────────────


def _load_user_entries(user_id: str) -> list[dict]:
    path = _safe_user_path(user_id)
    if path is None or not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("复盘库读取失败 user=%s: %s", user_id, e)
        return []


def _save_user_entries(user_id: str, entries: list[dict]) -> None:
    path = _safe_user_path(user_id)
    if path is None:
        return
    _LIBRARY_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning("复盘库写入失败 user=%s: %s", user_id, e)


# ──────────────────────────────────────────────────────────────────────────────
# 公开 API
# ──────────────────────────────────────────────────────────────────────────────


def add_entry(
    user_id: str,
    selected_text: str,
    rejected_texts: list[str],
    context_fingerprint: str,
    llm_context: LLMContext,
) -> None:
    """
    记录用户本次的话术选择。
    最多保留最新 200 条，超出时淘汰最旧条目。
    """
    entries = _load_user_entries(user_id)

    entry = ReviewEntry(
        user_id=user_id,
        selected_text=selected_text,
        rejected_texts=rejected_texts,
        context_fingerprint=context_fingerprint,
        j_series_snapshot={
            "j28_trend": llm_context.j28_trend,
            "j29_naked_punct": llm_context.j29_naked_punct,
            "j30_triggered": llm_context.j30_triggered,
        },
        timestamp=datetime.now(UTC),
    )

    entries.append(entry.model_dump(mode="json"))

    # FIFO 截断
    if len(entries) > 200:
        entries = entries[-200:]

    _save_user_entries(user_id, entries)


def get_few_shot(
    user_id: str,
    context_fingerprint: str,
    llm_context: LLMContext | None = None,
    top_k: int = 3,
) -> list[dict]:
    """
    检索相似历史条目。

    优先精确匹配 context_fingerprint；
    如果不足 top_k，以 j_series_snapshot 相似度补足。
    """
    entries = _load_user_entries(user_id)
    if not entries:
        return []

    exact: list[dict] = [
        e for e in entries if e.get("context_fingerprint") == context_fingerprint
    ]

    if len(exact) >= top_k:
        return exact[-top_k:]

    # 相似度补足：J 系列状态匹配
    if llm_context is not None:
        target_snapshot = {
            "j28_trend": llm_context.j28_trend,
            "j29_naked_punct": llm_context.j29_naked_punct,
            "j30_triggered": llm_context.j30_triggered,
        }
        similar: list[dict] = []
        for e in entries:
            snap = e.get("j_series_snapshot", {})
            score = sum(
                1 for k, v in target_snapshot.items() if snap.get(k) == v
            )
            if score >= 2 and e not in exact:
                similar.append(e)

        combined = exact + similar[-(top_k - len(exact)) :]
        return combined[-top_k:]

    return exact[-top_k:]
