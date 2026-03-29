from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import asyncio
from uuid import uuid4

from app.config import (
    AD_PROOF_TOKEN_MIN_LEN,
    AD_PROOF_TOKEN_PREFIX,
    FREE_RELATIONSHIP_DAILY_LIMIT,
    FREE_RELATIONSHIP_MAX,
    FREE_RELATIONSHIP_MIN,
    FREE_REPLY_AD_BONUS,
    FREE_REPLY_DAILY_LIMIT,
    VIP_RELATIONSHIP_MAX,
    VIP_RELATIONSHIP_MIN,
)
from app.contracts import GateDecision, Issue, Tier
from app.audit_service import write_audit_event
from app.storage import EntitlementPendingDeduct, EntitlementState, STORE


@dataclass
class EntitlementCheckResult:
    decision: GateDecision
    issues: list[Issue]
    check_id: str | None = None


def validate_ad_proof_token(ad_proof_token: str | None) -> bool:
    if not ad_proof_token:
        return False
    if not ad_proof_token.startswith(AD_PROOF_TOKEN_PREFIX):
        return False
    if len(ad_proof_token) < AD_PROOF_TOKEN_MIN_LEN:
        return False
    return True


async def check_and_lock_entitlement(
    *,
    user_id: str,
    scope: str,
    tier: Tier,
    screenshot_count: int,
    ad_proof_token: str | None,
    use_emergency_pack: bool,
) -> EntitlementCheckResult:
    lock = STORE.entitlement_user_locks.setdefault(user_id, _new_lock())
    async with lock:
        state = _get_or_create_state(user_id)
        if use_emergency_pack:
            emergency_issues = _check_emergency_pack(state=state, screenshot_count=screenshot_count, scope=scope)
            if emergency_issues:
                return EntitlementCheckResult(decision=GateDecision.BLOCK, issues=emergency_issues)
            return _create_pending_check(user_id=user_id, state=state, scope=scope, use_emergency_pack=True)

        if scope == "reply":
            return _check_reply_entitlement(
                user_id=user_id,
                tier=tier,
                state=state,
                ad_proof_token=ad_proof_token,
            )
        if scope == "relationship":
            return _check_relationship_entitlement(
                user_id=user_id,
                tier=tier,
                state=state,
                screenshot_count=screenshot_count,
                ad_proof_token=ad_proof_token,
            )
        return EntitlementCheckResult(
            decision=GateDecision.BLOCK,
            issues=[Issue(code="ENTITLEMENT_SCOPE_INVALID", message="未知权益检查范围。", severity="error")],
        )


async def commit_entitlement_deduct(check_id: str | None) -> None:
    if not check_id:
        return
    pending = STORE.entitlement_pending_deducts.get(check_id)
    if pending is None:
        return
    lock = STORE.entitlement_user_locks.setdefault(pending.user_id, _new_lock())
    async with lock:
        pending = STORE.entitlement_pending_deducts.pop(check_id, None)
        if pending is None:
            return
        key = _state_key(pending.user_id, pending.day)
        state = STORE.entitlement_state_by_user_day.setdefault(key, EntitlementState(day=pending.day))
        if pending.use_emergency_pack:
            state.emergency_pack_credits = max(0, state.emergency_pack_credits - 1)
        elif pending.scope == "reply":
            state.reply_used += 1
        elif pending.scope == "relationship":
            state.relationship_used += 1
        write_audit_event(
            event="entitlement_commit",
            user_id=pending.user_id,
            mode=pending.scope.upper(),
            payload={
                "check_id": check_id,
                "scope": pending.scope,
                "status": "committed",
            },
        )


async def release_entitlement_lock(check_id: str | None) -> None:
    if not check_id:
        return
    pending = STORE.entitlement_pending_deducts.get(check_id)
    if pending is None:
        return
    lock = STORE.entitlement_user_locks.setdefault(pending.user_id, _new_lock())
    async with lock:
        removed = STORE.entitlement_pending_deducts.pop(check_id, None)
        if removed:
            write_audit_event(
                event="entitlement_release",
                user_id=removed.user_id,
                mode=removed.scope.upper(),
                payload={
                    "check_id": check_id,
                    "scope": removed.scope,
                    "status": "released",
                },
            )


def build_usage_snapshot(user_id: str) -> dict:
    state = _get_or_create_state(user_id)
    return {
        "day": state.day,
        "reply_used": state.reply_used,
        "relationship_used": state.relationship_used,
        "emergency_pack_credits": state.emergency_pack_credits,
        "object_slots_active": state.object_slots_active,
        "pending_deducts": sum(1 for item in STORE.entitlement_pending_deducts.values() if item.user_id == user_id),
    }


def _count_pending_for_user(user_id: str, scope: str, day: str) -> int:
    return sum(
        1
        for p in STORE.entitlement_pending_deducts.values()
        if p.user_id == user_id and p.scope == scope and p.day == day and not p.use_emergency_pack
    )


def _check_reply_entitlement(
    *,
    user_id: str,
    tier: Tier,
    state: EntitlementState,
    ad_proof_token: str | None,
) -> EntitlementCheckResult:
    if tier == Tier.VIP:
        return _create_pending_check(user_id=user_id, state=state, scope="reply", use_emergency_pack=False)

    pending_count = _count_pending_for_user(user_id, "reply", state.day)
    effective_used = state.reply_used + pending_count
    free_limit = FREE_REPLY_DAILY_LIMIT
    bonus_limit = FREE_REPLY_DAILY_LIMIT + FREE_REPLY_AD_BONUS
    if effective_used < free_limit:
        return _create_pending_check(user_id=user_id, state=state, scope="reply", use_emergency_pack=False)

    if effective_used >= bonus_limit:
        return EntitlementCheckResult(
            decision=GateDecision.BLOCK,
            issues=[Issue(code="DAILY_LIMIT_REACHED", message="今日回话次数已达上限。", severity="error")],
        )

    if not ad_proof_token:
        return EntitlementCheckResult(
            decision=GateDecision.BLOCK,
            issues=[Issue(code="ADS_REQUIRED", message="免费层额外回话次数需先完成广告解锁。", severity="error")],
        )
    if not validate_ad_proof_token(ad_proof_token):
        return EntitlementCheckResult(
            decision=GateDecision.BLOCK,
            issues=[Issue(code="ADS_PROOF_INVALID", message="广告凭证无效，请重新完成广告解锁。", severity="error")],
        )
    return _create_pending_check(user_id=user_id, state=state, scope="reply", use_emergency_pack=False)


def _check_relationship_entitlement_limit(user_id: str, state: EntitlementState) -> int:
    """返回关系判断的 pending 次数（含当日）"""
    return _count_pending_for_user(user_id, "relationship", state.day)


def _check_relationship_entitlement(
    *,
    user_id: str,
    tier: Tier,
    state: EntitlementState,
    screenshot_count: int,
    ad_proof_token: str | None,
) -> EntitlementCheckResult:
    if screenshot_count > VIP_RELATIONSHIP_MAX:
        if tier == Tier.VIP:
            return EntitlementCheckResult(
                decision=GateDecision.BLOCK,
                issues=[
                    Issue(
                        code="MAX_SCREENSHOTS_EXCEEDED",
                        message="VIP 关系判断最多支持 9 张截图，请先裁剪后再提交。",
                        severity="error",
                    )
                ],
            )
        return EntitlementCheckResult(
            decision=GateDecision.BLOCK,
            issues=[Issue(code="SCREENSHOT_TOO_MANY", message="截图数量超过当前版本上限，请裁剪到 9 张以内。", severity="error")],
        )

    if tier == Tier.FREE and FREE_RELATIONSHIP_MAX < screenshot_count <= VIP_RELATIONSHIP_MAX:
        return EntitlementCheckResult(
            decision=GateDecision.BLOCK,
            issues=[Issue(code="UPGRADE_REQUIRED", message="当前为免费层，上传 5-9 张截图需要升级 VIP。", severity="error")],
        )

    if tier == Tier.FREE and screenshot_count in range(FREE_RELATIONSHIP_MIN, FREE_RELATIONSHIP_MAX + 1):
        pending_count = _check_relationship_entitlement_limit(user_id, state)
        effective_used = state.relationship_used + pending_count
        if effective_used >= FREE_RELATIONSHIP_DAILY_LIMIT:
            return EntitlementCheckResult(
                decision=GateDecision.BLOCK,
                issues=[Issue(code="DAILY_LIMIT_REACHED", message="今日免费关系判断次数已用完。", severity="error")],
            )
        if not ad_proof_token:
            return EntitlementCheckResult(
                decision=GateDecision.BLOCK,
                issues=[Issue(code="ADS_REQUIRED", message="免费关系判断需要先解锁广告权益。", severity="error")],
            )
        if not validate_ad_proof_token(ad_proof_token):
            return EntitlementCheckResult(
                decision=GateDecision.BLOCK,
                issues=[Issue(code="ADS_PROOF_INVALID", message="广告凭证无效，请重新完成广告解锁。", severity="error")],
            )
        return _create_pending_check(user_id=user_id, state=state, scope="relationship", use_emergency_pack=False)

    if tier == Tier.VIP and screenshot_count in range(VIP_RELATIONSHIP_MIN, VIP_RELATIONSHIP_MAX + 1):
        return _create_pending_check(user_id=user_id, state=state, scope="relationship", use_emergency_pack=False)

    return EntitlementCheckResult(
        decision=GateDecision.BLOCK,
        issues=[Issue(code="RELATIONSHIP_INPUT_INVALID", message="当前关系判断材料不满足范围要求。", severity="error")],
    )


def _check_emergency_pack(*, state: EntitlementState, screenshot_count: int, scope: str) -> list[Issue]:
    if state.emergency_pack_credits <= 0:
        return [Issue(code="EMERGENCY_PACK_REQUIRED", message="急救包余额不足。", severity="error")]
    if scope == "relationship" and screenshot_count not in range(VIP_RELATIONSHIP_MIN, VIP_RELATIONSHIP_MAX + 1):
        return [Issue(code="RELATIONSHIP_INPUT_INVALID", message="急救包关系判断需上传 2-9 张截图。", severity="error")]
    return []


def _create_pending_check(
    *,
    user_id: str,
    state: EntitlementState,
    scope: str,
    use_emergency_pack: bool,
) -> EntitlementCheckResult:
    check_id = f"ent_{uuid4().hex}"
    STORE.entitlement_pending_deducts[check_id] = EntitlementPendingDeduct(
        user_id=user_id,
        day=state.day,
        scope=scope,
        use_emergency_pack=use_emergency_pack,
    )
    return EntitlementCheckResult(decision=GateDecision.ALLOW, issues=[], check_id=check_id)


def _get_or_create_state(user_id: str) -> EntitlementState:
    day = datetime.now(UTC).date().isoformat()
    key = _state_key(user_id, day)
    return STORE.entitlement_state_by_user_day.setdefault(key, EntitlementState(day=day))


def _state_key(user_id: str, day: str) -> str:
    return f"{user_id}:{day}"


def _new_lock():
    return asyncio.Lock()
