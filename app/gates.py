from __future__ import annotations

from app.config import (
    MANIPULATION_PATTERNS,
    NO_CONTACT_PATTERNS,
    PROMPT_INJECTION_PATTERNS,
    SENSITIVE_CONTEXT_PATTERNS,
)
from app.contracts import GateDecision, Issue, PreparedUpload, SafetyBlock, SafetyStatus, Tier
from app.entitlement_service import check_and_lock_entitlement, release_entitlement_lock


def detect_sensitive_context(texts: list[str]) -> list[str]:
    hits: list[str] = []
    lowered = "\n".join(texts).lower()
    for pattern in SENSITIVE_CONTEXT_PATTERNS:
        if pattern in lowered:
            hits.append(pattern)
    return hits


def detect_prompt_injection(texts: list[str]) -> list[str]:
    hits: list[str] = []
    lowered = "\n".join(texts).lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern in lowered:
            hits.append(pattern)
    return hits


def assess_safety(texts: list[str], user_goal_mode: str | None = None) -> SafetyBlock:
    lowered = "\n".join(texts).lower()
    if any(pattern in lowered for pattern in NO_CONTACT_PATTERNS):
        return SafetyBlock(
            status=SafetyStatus.BLOCKED,
            block_reason="NO_CONTACT",
            allowed_to_generate_messages=False,
            note="为避免局面恶化，当前已暂时关闭话术生成功能，建议先暂停而不是继续加码。",
        )
    if user_goal_mode and any(pattern in user_goal_mode for pattern in MANIPULATION_PATTERNS):
        return SafetyBlock(
            status=SafetyStatus.BLOCKED,
            block_reason="MANIPULATION",
            allowed_to_generate_messages=False,
            note="检测到高压或操控意图，系统不会生成推进型话术。",
        )
    if detect_prompt_injection(texts):
        return SafetyBlock(
            status=SafetyStatus.CAUTION,
            block_reason="PROMPT_INJECTION",
            allowed_to_generate_messages=True,
            note="已忽略输入中的命令型文本，只把聊天内容当作证据，不把它当系统指令。",
        )
    return SafetyBlock(
        status=SafetyStatus.SAFE,
        block_reason=None,
        allowed_to_generate_messages=True,
        note="当前未命中硬阻断，可继续给出低压力建议。",
    )


async def resolve_gate_decision(
    *,
    user_id: str,
    prepared: PreparedUpload,
    tier: Tier,
    ad_proof_token: str | None,
    use_emergency_pack: bool,
    consent_sensitive: bool,
    texts: list[str],
    user_goal_mode: str | None = None,
) -> tuple[GateDecision, SafetyBlock, list[Issue], str | None]:
    # Layer 1: inherit module-1 physical/input gates
    inherited_issues = list(prepared.issues)
    if prepared.status != "READY":
        decision = GateDecision.BLOCK if any(issue.severity == "error" for issue in inherited_issues) else GateDecision.DEGRADE
        return decision, _safety_from_decision(decision, "INPUT_NOT_READY"), inherited_issues, None

    # Layer 2: consent-first for sensitive context
    sensitive_hits = detect_sensitive_context(texts)
    if sensitive_hits and not consent_sensitive:
        issue = Issue(
            code="CONSENT_REQUIRED",
            message="当前涉及高敏语境，需先完成知情同意后才可继续。",
            severity="error",
        )
        return GateDecision.BLOCK, _safety_from_decision(GateDecision.BLOCK, "CONSENT_REQUIRED"), [issue], None

    # Layer 3: commercial gate check&lock only (no deduct yet)
    entitlement_result = await check_and_lock_entitlement(
        user_id=user_id,
        scope=prepared.mode.value.lower(),
        tier=tier,
        screenshot_count=prepared.screenshot_count,
        ad_proof_token=ad_proof_token,
        use_emergency_pack=use_emergency_pack,
    )
    if entitlement_result.decision == GateDecision.BLOCK:
        reason = entitlement_result.issues[0].code if entitlement_result.issues else "COMMERCIAL_GATE_BLOCKED"
        return (
            GateDecision.BLOCK,
            _safety_from_decision(GateDecision.BLOCK, reason),
            entitlement_result.issues,
            None,
        )

    # Layer 4: red-line safety gate
    safety = assess_safety(texts, user_goal_mode)
    if safety.block_reason in {"NO_CONTACT", "MANIPULATION"}:
        await release_entitlement_lock(entitlement_result.check_id)
        issue = Issue(
            code=safety.block_reason,
            message=safety.note,
            severity="error",
        )
        return GateDecision.BLOCK, safety, [issue], None

    # Layer 5: injection gate
    if safety.block_reason == "PROMPT_INJECTION":
        issue = Issue(
            code="PROMPT_INJECTION",
            message="检测到命令型输入干扰，已降级到保守模式。",
            severity="warning",
        )
        return GateDecision.DEGRADE, safety, [issue], entitlement_result.check_id

    return GateDecision.ALLOW, safety, [], entitlement_result.check_id


def _safety_from_decision(decision: GateDecision, reason: str | None) -> SafetyBlock:
    if decision == GateDecision.BLOCK:
        return SafetyBlock(
            status=SafetyStatus.BLOCKED,
            block_reason=reason,
            allowed_to_generate_messages=False,
            note="当前请求被门禁拦截，已停止输出可发送话术。",
        )
    if decision == GateDecision.DEGRADE:
        return SafetyBlock(
            status=SafetyStatus.CAUTION,
            block_reason=reason,
            allowed_to_generate_messages=True,
            note="当前请求进入降级通道，仅允许保守输出。",
        )
    return SafetyBlock(
        status=SafetyStatus.SAFE,
        block_reason=None,
        allowed_to_generate_messages=True,
        note="当前请求通过门禁，可继续执行。",
    )
