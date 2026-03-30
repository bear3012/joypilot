from __future__ import annotations

import re

from app.config import (
    CONTRACT_VERSION,
    J30_GAP_MINUTES,
    J30_MIN_INTERRUPTION_COUNT,
    J30_WARN,
    LATENCY_NOTE_DISCLAIMER,
    NEGATIVE_KEYWORDS,
    POSITIVE_KEYWORDS,
)
from app.contracts import (
    Dashboard,
    ExplainCard,
    GateDecision,
    Issue,
    LLMContext,
    MessageBankItem,
    Mode,
    ProgressValidation,
    ProbeItem,
    ProbePackage,
    Recommendation,
    RelationshipAnalyzeRequest,
    RelationshipAnalyzeResponse,
    RealityAnchorReport,
    SopFilterSummary,
    StructuredDiagnosis,
    LedgerSummary,
)
from app.gates import detect_prompt_injection, resolve_gate_decision
from app.entitlement_service import commit_entitlement_deduct
from app.input_service import (
    CONVERSATION_ENDERS,
    analyze_latency_from_turns,
    dedupe_issues,
    scan_flow_interruptions,
    validate_relationship_material,
)
from app.signal_service import extract_signals, summarize_risk_signals
from app.audit_service import write_audit_event, write_segment_summary

SOP_DISCLAIMER_FOOTER = "模式提示不等于定罪。"
FUTURE_PREDICTION_TOKENS = (
    "会好转",
    "会恶化",
    "将会",
    "未来",
    "以后会",
    "接下来会",
    "后续会",
    "迟早会",
    "最终会",
    "会更好",
    "会变差",
)
J28_HOT_BUCKETS = {"INSTANT", "NORMAL"}
J28_COLD_BUCKETS = {"DELAYED", "COLD", "DEAD"}
J28_DODGE_TOKENS = (
    # NOTE: 关键词规则存在语义歧义（如“改天我们约”），v1 仅作保守候选信号。
    "改天",
    "再说",
    "忙完",
    "下次",
    "回头",
    "先忙",
    "去忙",
    "不方便",
    "先这样",
)

# J29: one-veto note appended only when NOT in a COLD->HOT contradiction scenario.
J29_NAKED_PUNCT_WARN = (
    "【投资失衡】对方的回应中出现了「极简标点回复（裸标点）」，"
    "这是典型的敷衍或回避态度，请立刻停止长篇大论或连续提问，切勿继续单向追加投资。"
)
# J29_HIGH_VALUE_SIGNAL is reserved for future LLM integration; not wired in v1.


async def analyze_relationship(request: RelationshipAnalyzeRequest) -> RelationshipAnalyzeResponse:
    session_data = getattr(request, "session_data", None)
    if session_data is not None:
        raise RuntimeError("FATAL: Relationship pipeline MUST NOT read reply session!")

    prepared = request.prepared_upload
    texts = [turn.text for turn in prepared.dialogue_turns]
    gate_decision, safety, gate_issues, entitlement_check_id = await resolve_gate_decision(
        user_id=request.user_id,
        prepared=prepared,
        tier=request.tier,
        ad_proof_token=request.ad_proof_token,
        use_emergency_pack=request.use_emergency_pack,
        consent_sensitive=request.consent_sensitive,
        texts=texts,
    )
    if gate_decision == GateDecision.BLOCK:
        return _build_blocked_response(request, safety, gate_issues)
    await commit_entitlement_deduct(entitlement_check_id)

    prompt_injection_hits = detect_prompt_injection(texts)
    signals = extract_signals(texts)
    issues = validate_relationship_material(prepared)
    issues.extend(gate_issues)
    issues = dedupe_issues(issues)

    positive_hits = _count_keywords(texts, POSITIVE_KEYWORDS)
    negative_hits = _count_keywords(texts, NEGATIVE_KEYWORDS)
    low_info = any(signal.low_info for signal in signals)
    stage = _pick_stage(safety.status.value, positive_hits, negative_hits, low_info)
    strategy, send_recommendation = _pick_strategy(stage, safety.status.value, issues)
    if gate_decision == GateDecision.DEGRADE:
        strategy = "维持"
        send_recommendation = Recommendation.WAIT
    risk_signals = summarize_risk_signals(signals, prompt_injection_hits)
    if negative_hits:
        risk_signals.append("现实推进不足")
    risk_signals = risk_signals[:3] or ["当前材料有限，先按保守策略处理。"]

    probes_items = _build_probes(stage, safety.status.value, low_info)
    probes_items = _enforce_j26_next_action_only(probes_items)
    progress_validation = ProgressValidation(
        probe_type=probes_items[0].probe_type if probes_items else None,
        intent=probes_items[0].intent if probes_items else None,
        followup_rule="正常接球可轻微推进；模糊拖延转观察；明确回避不重复测试。",
    )
    report = _build_reality_anchor_report(
        tier=request.tier.value,
        stage=stage,
        low_info=low_info,
        need_full_report=request.need_full_report,
        gate_decision=gate_decision,
    )
    report = _enforce_j27_past_fact_only(report)

    # Mode2（关系分析）：不向 dashboard.message_bank 输出可复制单句回复。
    # 态度与宏观策略见 structured_diagnosis、ledger.note、probes（探针为「下一步动作模板」，非针对当前一句的直接回复）。
    message_bank: list[MessageBankItem] = []

    diagnosis = StructuredDiagnosis(
        current_stage=stage,
        risk_signals=risk_signals,
        strategy=strategy,
        send_recommendation=send_recommendation,
        one_line_explanation=_build_one_line(stage, low_info, issues, gate_decision),
    )
    dashboard = Dashboard(
        action_light=_action_light(send_recommendation),
        tension_index=58 if stage in {"模糊", "试探"} else 36,
        pressure_score=78 if safety.status.value == "BLOCKED" else 32,
        blindspot_risk="HIGH" if low_info else "MEDIUM",
        mean_reversion="inactive",
        availability_override="none",
        frame_anchor="relationship_guardrails",
        gearbox_ratio_radar="relationship_mode",
        cooldown_timer="24h" if send_recommendation != Recommendation.YES else "6h",
        focus_redirect="先看证据量，再决定要不要推进。",
        reciprocity_meter=_reciprocity_meter(prepared),
        sunk_cost_breaker="on",
        adaptive_tension="soft",
        suggestive_channel="probe_only" if probes_items else "hold",
        macro_stage=stage,
        interest_discriminator_panel="单点信号只算候选证据",
        stage_transition="observe" if send_recommendation != Recommendation.YES else "light_probe",
        message_bank=message_bank,
    )
    sop_filter = _force_sop_footer(_build_sop_filter(texts))
    ledger = _enforce_j24_qualitative_only(_build_ledger(prepared))
    if gate_decision == GateDecision.DEGRADE:
        ledger = ledger.model_copy(
            update={
                "note": _append_ledger_note(
                    ledger.note,
                    "【策略提示】当前处于输入降级模式：建议维持低压力互动、避免主动推进与押码式表白，"
                    "等信息与证据更完整后再判断；本报告不提供针对单句的逐字可用回复话术。",
                )
            }
        )

    # Capture base state before J28/J29 overrides so the COLD->HOT contradiction
    # scenario can perform a silent rollback without leaving partial overrides.
    _base_send_recommendation = send_recommendation
    _base_diagnosis = diagnosis
    _base_dashboard = dashboard
    _base_ledger = ledger

    j28_trend = _calculate_j28_trend(prepared, self_mode="SELF", other_mode="OTHER")
    if j28_trend and gate_decision != GateDecision.DEGRADE:
        if j28_trend["trend"] == "HOT_TO_COLD":
            send_recommendation = Recommendation.WAIT
            strategy = "降压"
            diagnosis = diagnosis.model_copy(
                update={
                    "strategy": strategy,
                    "send_recommendation": send_recommendation,
                    "one_line_explanation": "【趋势警报】对话跨越终结词后对方回流变慢，建议先停止追问并进入冷却观察。",
                }
            )
            dashboard = dashboard.model_copy(
                update={
                    "action_light": _action_light(send_recommendation),
                    "cooldown_timer": "24h",
                    "stage_transition": "observe",
                    # mode2 不生成话术，仅在报告说明趋势结论。
                    "message_bank": [],
                }
            )
            ledger = ledger.model_copy(
                update={
                    "note": _append_ledger_note(
                        ledger.note,
                        "【趋势警报】诊断依据：在上次话题结束（如道晚安/去忙）后，对方的新回复响应时延显著拉长或趋于冷淡，且无主动解释。局势已冷却，请立即停止追问，进入冷却状态，切忌暴露需求感。",
                    )
                }
            )
        elif j28_trend["trend"] == "COLD_TO_HOT":
            send_recommendation = Recommendation.YES
            strategy = "推进"
            diagnosis = diagnosis.model_copy(
                update={
                    "strategy": strategy,
                    "send_recommendation": send_recommendation,
                    "one_line_explanation": "【窗口提示】跨越终结词后回流变快，可尝试一次低压力试探。",
                }
            )
            dashboard = dashboard.model_copy(
                update={
                    "action_light": _action_light(send_recommendation),
                    "cooldown_timer": "6h",
                    "stage_transition": "light_probe",
                    # mode2 不生成话术，仅在报告说明趋势结论。
                    "message_bank": [],
                }
            )
            if ledger.asymmetric_risk == "HIGH":
                note_text = (
                    "【测试建议】互动虽有回温，但全局存在高危/敷衍特征（警惕情绪价值陷阱）。切勿直接暴露需求感或提供物质承诺，建议使用「轻度试探话术」测试其真实意图。若试探后对方再次消失，请立即止损。"
                )
            else:
                note_text = (
                    "【窗口提示】诊断依据：在跨越上次话题后，对方当前的响应速度明显提升，投入度回温。当前出现沟通窗口，建议进行一次低压力的好感试探或轻度邀约。"
                )
            ledger = ledger.model_copy(
                update={
                    "note": _append_ledger_note(
                        ledger.note,
                        note_text,
                    )
                }
            )
    # J29 Matrix: scoped to current active window (Part_B if ender found, else all turns).
    # Finds the ender independently so that scoping is correct even when J28 did not fire.
    # Runs AFTER J28 so it can silently cancel a COLD->HOT upgrade when signals conflict.
    j29_ender_index = _find_last_mid_conversation_ender_index(list(prepared.dialogue_turns))
    j29_result = _calculate_j29_matrix(prepared, j29_ender_index)
    if j29_result and gate_decision != GateDecision.DEGRADE:
        j28_was_cold_to_hot = j28_trend is not None and j28_trend["trend"] == "COLD_TO_HOT"
        if j28_was_cold_to_hot:
            # Contradictory signals (Part_B shows both warm-up and naked-punct):
            # silently roll back all J28 overrides — treat as no relationship progress.
            send_recommendation = _base_send_recommendation
            diagnosis = _base_diagnosis
            dashboard = _base_dashboard
            ledger = _base_ledger
        else:
            # J29 one-veto: naked punct in current window → force WAIT + note.
            send_recommendation = Recommendation.WAIT
            diagnosis = diagnosis.model_copy(
                update={
                    "strategy": "降压",
                    "send_recommendation": send_recommendation,
                    "one_line_explanation": "【投资失衡】当前活跃窗口检测到裸标点回复，建议立即降压观察。",
                }
            )
            # J29 WAIT 不清空 message_bank，下游话术生成链按 WAIT 语义降级输出，
            # 与 J30 契约统一（只有 BLOCK 才硬清空 message_bank）。
            dashboard = dashboard.model_copy(
                update={
                    "action_light": _action_light(send_recommendation),
                    "cooldown_timer": "24h",
                    "stage_transition": "observe",
                }
            )
            ledger = ledger.model_copy(
                update={
                    "note": _append_ledger_note(ledger.note, J29_NAKED_PUNCT_WARN),
                }
            )

    # J30 Flow Interruption：仅在无终结词场景运行（有终结词时由 J28/J29 负责）
    j30_actually_triggered = False
    if j29_ender_index is None and gate_decision != GateDecision.DEGRADE:
        last_speaker = (
            prepared.dialogue_turns[-1].speaker
            if prepared.dialogue_turns else None
        )
        if last_speaker == "SELF":
            interruptions = scan_flow_interruptions(
                list(prepared.dialogue_turns), J30_GAP_MINUTES
            )
            if len(interruptions) >= J30_MIN_INTERRUPTION_COUNT:
                j30_actually_triggered = True
                send_recommendation = Recommendation.WAIT
                diagnosis = diagnosis.model_copy(
                    update={
                        "strategy": "降压",
                        "send_recommendation": send_recommendation,
                        "one_line_explanation": "【靠谱度警报】对方存在多次长间隔低价值回应，建议暂停追投。",
                    }
                )
                # WAIT 不清空 message_bank，只修改灯号与冷却标签，
                # 话术生成权留给下游（BLOCK 才硬清空）
                dashboard = dashboard.model_copy(
                    update={
                        "action_light": _action_light(send_recommendation),
                        "cooldown_timer": "24h",
                        "stage_transition": "observe",
                    }
                )
                ledger = ledger.model_copy(
                    update={
                        "note": _append_ledger_note(ledger.note, J30_WARN),
                    }
                )

    # 心理学框架注入：使用各算法实际触发标记，避免用 send_recommendation 反推造成误报
    _j30_triggered = j30_actually_triggered
    _j29_naked = j29_result is not None and gate_decision != GateDecision.DEGRADE
    _j28_trend_str: str | None = (
        j28_trend["trend"] if j28_trend and gate_decision != GateDecision.DEGRADE else None
    )
    _llm_ctx = LLMContext(
        j28_trend=_j28_trend_str,
        j29_naked_punct=_j29_naked,
        j30_triggered=_j30_triggered,
        risk_signals=risk_signals,
    )
    try:
        from app.prompt_builder import get_psychology_frame
        psych_frame = get_psychology_frame(_llm_ctx)
        ledger = ledger.model_copy(
            update={"note": _append_ledger_note(ledger.note, psych_frame)}
        )
    except Exception:
        pass  # 心理学框架注入失败不影响主流程

    probes = ProbePackage(available=bool(probes_items), items=probes_items)

    explain_card = ExplainCard(
        active=True,
        forced_style="STABLE" if gate_decision == GateDecision.DEGRADE else "SAFE_RELATIONSHIP",
        evidence_signals=[signal.raw_value for signal in signals] + prompt_injection_hits,
        risk_banner_level="HIGH" if low_info or issues else "MEDIUM",
        note="v1 关系判断只读本次上传的截图，不读取历史上下文、reply session、对象摘要层。",
    )

    _write_summary_stub(request, diagnosis.one_line_explanation, stage, ledger.asymmetric_risk)
    _write_audit_stub(request, safety.status.value, [issue.code for issue in issues])

    return RelationshipAnalyzeResponse(
        contract_version=CONTRACT_VERSION,
        mode=Mode.RELATIONSHIP,
        gate_decision=gate_decision,
        dashboard=dashboard,
        safety=safety,
        explain_card=explain_card,
        structured_diagnosis=diagnosis,
        signals=signals,
        recovery_protocol={
            "state": "pause" if send_recommendation != Recommendation.YES else "observe",
            "can_exit": True,
            "reset_ends_at": None,
            "ping_attempts_left": 1,
            "violation_budget_remaining": 1,
            "violation_cost_battery": "LOW",
            "override_output_token_cap": 0,
            "instruction": "当前以低压力为先，不做高压推进。",
        },
        ledger=ledger,
        sop_filter=sop_filter,
        probes=probes,
        progress_validation=progress_validation,
        reality_anchor_report=report,
        gating_issues=issues,
    )


def _count_keywords(texts: list[str], keywords: tuple[str, ...]) -> int:
    return sum(1 for text in texts for keyword in keywords if keyword in text)


def _calculate_j28_trend(prepared, self_mode: str, other_mode: str) -> dict[str, str | int] | None:
    turns = list(prepared.dialogue_turns)
    if len(turns) < 2:
        return None

    ender_index = _find_last_mid_conversation_ender_index(turns)
    if ender_index is None:
        return None

    part_a = turns[: ender_index + 1]
    part_b = turns[ender_index + 1 :]
    part_a_state = _classify_j28_part_state(part_a, self_mode=self_mode, other_mode=other_mode)
    part_b_state = _classify_j28_part_state(part_b, self_mode=self_mode, other_mode=other_mode)
    if "UNKNOWN" in {part_a_state, part_b_state}:
        return None

    if part_a_state == "HOT" and part_b_state == "COLD":
        trend = "HOT_TO_COLD"
    elif part_a_state == "COLD" and part_b_state == "HOT":
        trend = "COLD_TO_HOT"
    else:
        return None

    return {
        "trend": trend,
        "ender_index": ender_index,
        "part_a_state": part_a_state,
        "part_b_state": part_b_state,
    }


def _calculate_j29_matrix(prepared, ender_index: int | None) -> dict | None:
    """J29 Dominance Matrix: detect naked-punctuation replies in the current active window.

    Scoping rule: if an ender was found by J28, scan only Part_B (turns after the ender)
    so historical Part_A punctuation does not trigger false alarms.  When no ender exists,
    scan the full dialogue.

    Returns a dict with trigger info, or None if no naked-punct signal is present.
    """
    turns = list(prepared.dialogue_turns)
    window = turns[ender_index + 1 :] if ender_index is not None else turns
    naked_count = sum(
        1 for turn in window if turn.speaker == "OTHER" and turn.is_naked_punctuation
    )
    if naked_count >= 1:
        return {"trigger": "NAKED_PUNCT", "naked_punct_count": naked_count}
    return None


def _find_last_mid_conversation_ender_index(turns: list[Any]) -> int | None:
    candidate_index: int | None = None
    for idx, turn in enumerate(turns[:-1]):
        normalized = re.sub(r"\s+", "", (turn.text or "").strip())
        if normalized and any(token in normalized for token in CONVERSATION_ENDERS):
            candidate_index = idx
    return candidate_index


def _classify_j28_part_state(part_turns: list[Any], *, self_mode: str, other_mode: str) -> str:
    _ = self_mode
    latency = analyze_latency_from_turns(part_turns)
    other_bucket = latency.get("other_bucket")
    if bool(latency.get("insufficient")) or other_bucket in {None, "UNKNOWN"}:
        return "UNKNOWN"

    if _count_j28_other_dodge_hits(part_turns, other_mode=other_mode) > 0:
        return "COLD"
    if other_bucket in J28_HOT_BUCKETS:
        return "HOT"
    if other_bucket in J28_COLD_BUCKETS:
        return "COLD"
    return "UNKNOWN"


def _count_j28_other_dodge_hits(part_turns: list[Any], *, other_mode: str) -> int:
    hits = 0
    for turn in part_turns:
        if turn.speaker != other_mode:
            continue
        normalized = re.sub(r"\s+", "", (turn.text or "").strip())
        if normalized and any(token in normalized for token in J28_DODGE_TOKENS):
            hits += 1
    return hits


def _append_ledger_note(base: str, addition: str) -> str:
    cleaned = (base or "").strip()
    sanitized_addition = _sanitize_qualitative_text(addition)
    if not cleaned:
        return sanitized_addition
    return f"{cleaned} {sanitized_addition}"


def _pick_stage(safety_status: str, positive_hits: int, negative_hits: int, low_info: bool) -> str:
    if safety_status == "BLOCKED":
        return "回避"
    if negative_hits > positive_hits + 1:
        return "冷"
    if positive_hits > negative_hits and not low_info:
        return "拉近"
    if low_info:
        return "模糊"
    return "试探"


def _pick_strategy(stage: str, safety_status: str, issues: list[Issue]) -> tuple[str, Recommendation]:
    if safety_status == "BLOCKED":
        return "暂停", Recommendation.NO
    if any(issue.severity == "error" for issue in issues):
        return "降压", Recommendation.WAIT
    if issues:
        return "维持", Recommendation.WAIT
    if stage == "拉近":
        return "推进", Recommendation.YES
    if stage == "模糊":
        return "维持", Recommendation.WAIT
    if stage == "冷":
        return "降压", Recommendation.WAIT
    return "降压", Recommendation.WAIT


def _build_ledger(prepared) -> LedgerSummary:
    self_chars = sum(len(turn.text) for turn in prepared.dialogue_turns if turn.speaker == "SELF")
    other_chars = sum(len(turn.text) for turn in prepared.dialogue_turns if turn.speaker == "OTHER")
    # IMPORTANT: Keep evidence qualitative only. Do not expose numeric counts/ratios
    # in output strings even though internal heuristics use character volume.
    if self_chars > other_chars * 1.5:
        risk = "HIGH"
        evidence = ["你的表达量明显高于对方。", "当前更像你在主动托举互动。"]
    elif other_chars == 0 or self_chars == other_chars:
        risk = "MEDIUM"
        evidence = ["当前互动证据有限，需要继续观察。"]
    else:
        risk = "LOW"
        evidence = ["当前投入看起来没有明显失衡。"]
    latency = analyze_latency_from_turns(prepared.dialogue_turns)
    note = "J24 在 v1 只做定性红灯，不做精确账本。"
    if bool(latency.get("insufficient")):
        evidence.append("当前时间证据不足，时延维度仅作保守参考。")
    elif bool(latency.get("triggered")):
        risk = "HIGH"
        evidence.extend(
            [
                "对方回复节奏明显偏慢，你与对方在响应时延上存在失衡。",
                "当前更适合降低预期与推进强度，先维持中性观察。",
            ]
        )
        note = f"{note} {LATENCY_NOTE_DISCLAIMER}"
    if bool(latency.get("other_ender_warning")):
        evidence.append("检测到对方多次主动收束对话，建议降低单次长间隔的负面解读强度。")
    return LedgerSummary(
        asymmetric_risk=risk,
        evidence=evidence,
        note=note,
    )


def _build_sop_filter(texts: list[str]) -> SopFilterSummary:
    phrases = ["改天", "再说", "忙完", "下次", "回头"]
    hits = [phrase for phrase in phrases if any(phrase in text for text in texts)]
    return SopFilterSummary(
        total_hits=len(hits),
        hits=hits,
        risk_escalation="MEDIUM" if len(hits) >= 2 else "LOW",
        evidence_signals=hits[:2],
    )


def _build_probes(stage: str, safety_status: str, low_info: bool) -> list[ProbeItem]:
    if safety_status == "BLOCKED":
        return []
    if low_info:
        return [
            ProbeItem(
                probe_type="RECIPROCITY_CHECK",
                intent="核验回流意愿",
                template="你最近应该也挺忙的，等你方便的时候再继续聊就行。",
                when_to_use="只看到 emoji / sticker 等低信息回应时。",
                risk_level="LOW",
                expected_signal="是否愿意继续接球",
                do_not_overinterpret="有回应不等于稳定好感，无回应也不自动判死。",
                followup_rule="若继续模糊，转观察，不重复测试。",
            )
        ]
    if stage == "拉近":
        return [
            ProbeItem(
                probe_type="LIGHT_INVITE",
                intent="核验现实推进接受度",
                template="如果你这周方便，我们找个轻松点的时间见一面，不方便也没关系。",
                when_to_use="已有一定正向证据且安全门未触发时。",
                risk_level="LOW",
                expected_signal="是否愿意给时间或替代方案",
                do_not_overinterpret="答应见面也不等于关系已定。",
                followup_rule="若模糊拖延，转观察，不追打。",
            )
        ]
    return []


def _build_reality_anchor_report(
    *,
    tier: str,
    stage: str,
    low_info: bool,
    need_full_report: bool,
    gate_decision: GateDecision,
) -> RealityAnchorReport:
    brief_points = [
        "当前判断只基于这次上传的截图，不读取历史上下文。",
        "单个正向符号不等于稳定好感。",
        "更适合低压力核验，而不是高压表白。",
    ]
    full_text = None
    if gate_decision != GateDecision.DEGRADE and tier == "VIP" and need_full_report:
        full_text = (
            f"当前更偏 {stage}。系统看到的证据量仍有限，所以建议先用低压力现实动作核验。"
            "如果后续只有 emoji、贴图或模糊拖延，不建议把它升级成明确关系判断。"
        )
    return RealityAnchorReport(
        available=True,
        tone="neutral",
        access="PREMIUM_FULL" if full_text else "FREE_BRIEF",
        delay_gate_sec=0,
        brief_points=brief_points if not low_info else brief_points + ["当前信号信息量偏低，不建议过度解读。"],
        full_text=full_text,
    )


def _enforce_j24_qualitative_only(ledger: LedgerSummary) -> LedgerSummary:
    sanitized_evidence = [_sanitize_qualitative_text(item) for item in ledger.evidence]
    sanitized_note = _sanitize_qualitative_text(ledger.note)
    return ledger.model_copy(update={"evidence": sanitized_evidence, "note": sanitized_note})


def _enforce_j26_next_action_only(probes: list[ProbeItem]) -> list[ProbeItem]:
    fixed: list[ProbeItem] = []
    for item in probes:
        fixed.append(
            item.model_copy(
                update={
                    "intent": _sanitize_j26_next_action_text(item.intent),
                    "template": _sanitize_j26_next_action_text(item.template),
                    "when_to_use": _sanitize_j26_next_action_text(item.when_to_use),
                    "followup_rule": _sanitize_j26_next_action_text(item.followup_rule),
                }
            )
        )
    return fixed


def _enforce_j27_past_fact_only(report: RealityAnchorReport) -> RealityAnchorReport:
    brief_points = [_sanitize_qualitative_text(point) for point in report.brief_points]
    full_text = _sanitize_qualitative_text(report.full_text) if report.full_text else None
    return report.model_copy(update={"brief_points": brief_points, "full_text": full_text})


def _force_sop_footer(sop_filter: SopFilterSummary) -> SopFilterSummary:
    return sop_filter.model_copy(update={"footer": SOP_DISCLAIMER_FOOTER})


def _sanitize_qualitative_text(text: str) -> str:
    if _contains_pseudo_math(text):
        return "当前证据显示投入不对等，建议先维持观察，不做数字化定性。"
    if any(token in text for token in FUTURE_PREDICTION_TOKENS):
        return "仅基于当前截图事实：当前更适合低压力核验与观察。"
    return text


def _sanitize_j26_next_action_text(text: str) -> str:
    past_inference_tokens = ("之前", "过去", "一直", "从前", "历史证明", "早就")
    if any(token in text for token in past_inference_tokens):
        return "仅给下一步低压力动作选项，不对过往关系做倒推定性。"
    if any(token in text for token in FUTURE_PREDICTION_TOKENS):
        return "仅给下一步低压力动作选项，不对未来结果做预测。"
    return _sanitize_qualitative_text(text)


def _contains_pseudo_math(text: str) -> bool:
    patterns = (
        r"\d+\s*[:：]\s*\d+",
        r"\d+(?:\.\d+)?\s*%",
        r"\d+\s*(字|分钟|小时|天|周|月)",
        r"(比例|比值)\s*\d",
        r"\d+\s*比\s*\d+",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _build_one_line(stage: str, low_info: bool, issues: list[Issue], gate_decision: GateDecision) -> str:
    if gate_decision == GateDecision.DEGRADE:
        return "检测到输入干扰风险，已切换稳妥模式并限制高风险策略输出。"
    if any(issue.severity == "error" for issue in issues):
        return "当前材料不足，先补齐时间线、OCR 预览和角色确认，再做关系判断。"
    if low_info:
        return "当前更像候选正向或低信息信号，先观察，不要把单点信号当成关系结论。"
    return f"当前更偏 {stage}，建议继续用低压力方式核验，而不是直接上强推进。"


def _build_blocked_response(
    request: RelationshipAnalyzeRequest,
    safety,
    gate_issues: list[Issue],
) -> RelationshipAnalyzeResponse:
    fallback_issue = gate_issues[0] if gate_issues else Issue(
        code="GATE_BLOCKED",
        message="请求已被门禁拦截。",
        severity="error",
    )
    diagnosis = StructuredDiagnosis(
        current_stage="模糊",
        risk_signals=[fallback_issue.code],
        strategy="暂停",
        send_recommendation=Recommendation.NO,
        one_line_explanation=fallback_issue.message,
    )
    dashboard = Dashboard(
        action_light="RED",
        tension_index=70,
        pressure_score=90,
        blindspot_risk="HIGH",
        mean_reversion="inactive",
        availability_override="none",
        frame_anchor="gate_blocked",
        gearbox_ratio_radar="relationship_mode",
        cooldown_timer="24h",
        focus_redirect="当前先暂停推进，先完成必要门禁条件。",
        reciprocity_meter="unknown",
        sunk_cost_breaker="on",
        adaptive_tension="safe_only",
        suggestive_channel="blocked",
        macro_stage="模糊",
        interest_discriminator_panel="门禁拦截中",
        stage_transition="blocked",
        message_bank=[],
    )
    return RelationshipAnalyzeResponse(
        contract_version=CONTRACT_VERSION,
        mode=Mode.RELATIONSHIP,
        gate_decision=GateDecision.BLOCK,
        dashboard=dashboard,
        safety=safety,
        explain_card=ExplainCard(
            active=True,
            forced_style="STABLE",
            evidence_signals=[issue.code for issue in gate_issues],
            risk_banner_level="HIGH",
            note="当前请求被门禁阻断，需先满足前置条件后再继续。",
        ),
        structured_diagnosis=diagnosis,
        signals=[],
        recovery_protocol={
            "state": "pause",
            "can_exit": True,
            "reset_ends_at": None,
            "ping_attempts_left": 0,
            "violation_budget_remaining": 0,
            "violation_cost_battery": "LOW",
            "override_output_token_cap": 0,
            "instruction": "门禁阻断场景下不输出推进策略。",
        },
        ledger=LedgerSummary(
            asymmetric_risk="MEDIUM",
            evidence=["门禁已拦截请求，未进入关系判断主链。"],
            note="BLOCK 场景不执行关系判断模型链路。",
        ),
        sop_filter=_force_sop_footer(SopFilterSummary(
            total_hits=0,
            hits=[],
            risk_escalation="LOW",
            evidence_signals=[],
        )),
        probes=ProbePackage(
            available=False,
            items=[],
        ),
        progress_validation=ProgressValidation(
            followup_rule="先满足门禁条件，再重新提交分析请求。",
        ),
        reality_anchor_report=RealityAnchorReport(
            available=True,
            tone="alert",
            access="ALERT_ONLY",
            delay_gate_sec=0,
            brief_points=[fallback_issue.message],
            full_text=None,
        ),
        gating_issues=gate_issues or [fallback_issue],
    )


def _reciprocity_meter(prepared) -> str:
    self_turns = sum(1 for turn in prepared.dialogue_turns if turn.speaker == "SELF")
    other_turns = sum(1 for turn in prepared.dialogue_turns if turn.speaker == "OTHER")
    if other_turns == 0:
        return "weak"
    if abs(self_turns - other_turns) <= 1:
        return "balanced"
    return "imbalanced"


def _write_summary_stub(request: RelationshipAnalyzeRequest, summary: str, stage: str, asymmetric_risk: str) -> None:
    write_segment_summary(
        target_id=request.target_id,
        source_type="relationship_v1",
        stage=stage,
        summary=summary,
        asymmetric_risk=asymmetric_risk,
        payload={
            "mode": "RELATIONSHIP",
            "status": "ok",
        },
    )


def _write_audit_stub(request: RelationshipAnalyzeRequest, safety_status: str, issue_codes: list[str]) -> None:
    write_audit_event(
        event="relationship_analyze",
        user_id=request.user_id,
        target_id=request.target_id,
        mode="RELATIONSHIP",
        payload={
            "safety_status": safety_status,
            "issue_codes": issue_codes,
            "gate_decision": "UNKNOWN",
        },
    )


def _action_light(recommendation: Recommendation) -> str:
    if recommendation == Recommendation.NO:
        return "RED"
    if recommendation == Recommendation.WAIT:
        return "YELLOW"
    return "GREEN"
