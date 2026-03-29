from __future__ import annotations

import re
from datetime import datetime

from app.config import (
    FREE_RELATIONSHIP_MAX,
    FREE_RELATIONSHIP_MIN,
    LOW_INFO_MIN_EFFECTIVE_CHARS,
    LOW_INFO_MIN_EFFECTIVE_TURNS,
    LOW_INFO_RATIO_THRESHOLD,
    LOW_INFO_SHORT_TEXT,
    VIP_RELATIONSHIP_MAX,
    VIP_RELATIONSHIP_MIN,
)
from app.contracts import (
    DialogueTurn,
    EvidenceQuality,
    Issue,
    Mode,
    OCRPreviewItem,
    PreparedUpload,
    ScreenshotFrame,
    Tier,
    UploadPrepareRequest,
)

CONVERSATION_ENDERS = (
    "晚安",
    "拜拜",
    "先睡了",
    "去洗澡",
    "去吃饭",
    "明天聊",
    "去忙",
)
OTHER_ENDER_WARNING_THRESHOLD = 4
LONG_GAP_MINUTES = 60
MIN_CONTINUOUS_GAP_MINUTES = 1


def prepare_upload(request: UploadPrepareRequest) -> PreparedUpload:
    sorted_frames, order_issues = _sort_frames(request.screenshots)
    preview = [
        OCRPreviewItem(
            image_id=frame.image_id,
            ordered_index=index,
            timestamp_hint=frame.timestamp_hint,
            left_text=frame.left_text.strip(),
            right_text=frame.right_text.strip(),
        )
        for index, frame in enumerate(sorted_frames, start=1)
    ]

    dialogue_turns: list[DialogueTurn] = []
    for frame in preview:
        left_text = frame.left_text.strip()
        right_text = frame.right_text.strip()
        if left_text:
            dialogue_turns.append(
                DialogueTurn(
                    speaker=_map_side("LEFT", request.my_side),
                    text=left_text,
                    source_image_id=frame.image_id,
                    timestamp_hint=frame.timestamp_hint,
                )
            )
        if right_text:
            dialogue_turns.append(
                DialogueTurn(
                    speaker=_map_side("RIGHT", request.my_side),
                    text=right_text,
                    source_image_id=frame.image_id,
                    timestamp_hint=frame.timestamp_hint,
                )
            )

    issues = order_issues + _build_prepare_issues(
        mode=request.mode,
        tier=request.tier,
        screenshot_count=len(sorted_frames),
        timeline_confirmed=request.timeline_confirmed,
        my_side=request.my_side.value if request.my_side else None,
        preview=preview,
        text_input=request.text_input,
        dialogue_turns=dialogue_turns,
    )
    evidence_metrics = _build_evidence_metrics(dialogue_turns)
    evidence_quality = _build_evidence_quality(evidence_metrics)

    if mode_requires_evidence_guard(request.mode, evidence_quality):
        issues.append(
            Issue(
                code="INSUFFICIENT_EVIDENCE",
                message="当前截图多为低信息响应，证据不足，不能进入关系判断。",
                severity="error",
            )
        )
    issues = dedupe_issues(issues)

    status = "READY" if not issues else "NEEDS_REVIEW"

    return PreparedUpload(
        status=status,
        screenshot_count=len(sorted_frames),
        tier=request.tier,
        mode=request.mode,
        timeline_confirmed=request.timeline_confirmed,
        my_side=request.my_side,
        evidence_quality=evidence_quality,
        effective_turn_count=evidence_metrics["effective_turn_count"],
        effective_char_count=evidence_metrics["effective_char_count"],
        low_info_ratio=evidence_metrics["low_info_ratio"],
        duplicate_content_suspected=False,
        issues=issues,
        ocr_preview=preview,
        dialogue_turns=dialogue_turns,
    )


def validate_relationship_material(prepared: PreparedUpload) -> list[Issue]:
    issues = list(prepared.issues)
    if prepared.mode != Mode.RELATIONSHIP:
        issues.append(
            Issue(
                code="MODE_MISMATCH",
                message="关系判断只接受关系判断模式的整理结果。",
                severity="error",
            )
        )
    issues.extend(
        _build_tier_range_issues(
            mode=prepared.mode,
            tier=prepared.tier,
            screenshot_count=prepared.screenshot_count,
        )
    )
    return dedupe_issues(issues)


def dedupe_issues(issues: list[Issue]) -> list[Issue]:
    seen: set[tuple[str, str]] = set()
    output: list[Issue] = []
    for issue in issues:
        key = (issue.code, issue.message)
        if key not in seen:
            seen.add(key)
            output.append(issue)
    return output


def _build_prepare_issues(
    *,
    mode: Mode,
    tier: Tier,
    screenshot_count: int,
    timeline_confirmed: bool,
    my_side: str | None,
    preview: list[OCRPreviewItem],
    text_input: str | None,
    dialogue_turns: list[DialogueTurn],
) -> list[Issue]:
    issues: list[Issue] = []
    if mode == Mode.RELATIONSHIP and screenshot_count == 0 and (text_input or "").strip():
        issues.append(
            Issue(
                code="TEXT_DIRECT_NOT_ALLOWED",
                message="v1 关系判断不支持文本直传，请上传截图后再整理。",
                severity="error",
            )
        )
    if mode == Mode.RELATIONSHIP and screenshot_count == 0 and not (text_input or "").strip():
        issues.append(
            Issue(
                code="NO_SCREENSHOTS",
                message="关系判断模式必须先上传截图。",
                severity="error",
            )
        )
    if mode == Mode.RELATIONSHIP and not timeline_confirmed:
        issues.append(
            Issue(
                code="TIMELINE_UNCONFIRMED",
                message="未完成时间线确认，不能进入关系判断。",
                severity="error",
            )
        )
    if mode == Mode.RELATIONSHIP and my_side is None:
        issues.append(
            Issue(
                code="ROLE_UNCONFIRMED",
                message="请先确认聊天里哪一方是你。",
                severity="error",
            )
        )
    if mode == Mode.RELATIONSHIP and not any(item.left_text or item.right_text for item in preview):
        issues.append(
            Issue(
                code="OCR_EMPTY",
                message="OCR 预览为空，当前材料不足以进入关系判断。",
                severity="error",
            )
        )
    if mode == Mode.RELATIONSHIP and tier == Tier.VIP and not _has_enough_valid_time_hints(preview):
        issues.append(
            Issue(
                code="TIMESTAMP_REQUIRED_VIP",
                message="VIP 关系判断需要补齐可解析的时间信息（至少 2 条有效时间）。",
                severity="error",
            )
        )
    issues.extend(_build_tier_range_issues(mode=mode, tier=tier, screenshot_count=screenshot_count))
    if mode == Mode.RELATIONSHIP and my_side is None and dialogue_turns:
        issues.append(
            Issue(
                code="ROLE_MAPPING_LOCKED",
                message="角色未确认，当前仅保留 LEFT/RIGHT，不会映射 SELF/OTHER。",
                severity="warning",
            )
        )
    return dedupe_issues(issues)


def _map_side(side: str, my_side) -> str:
    if my_side is None:
        return side
    if side == my_side.value:
        return "SELF"
    return "OTHER"


def _build_tier_range_issues(*, mode: Mode, tier: Tier, screenshot_count: int) -> list[Issue]:
    if mode != Mode.RELATIONSHIP:
        return []

    issues: list[Issue] = []
    if tier == Tier.FREE and screenshot_count < FREE_RELATIONSHIP_MIN:
        issues.append(
            Issue(
                code="FREE_TIER_RANGE",
                message="免费关系判断只接受 2-4 张截图。",
                severity="error",
            )
        )
    if tier == Tier.FREE and FREE_RELATIONSHIP_MAX < screenshot_count <= VIP_RELATIONSHIP_MAX:
        issues.append(
            Issue(
                code="UPGRADE_REQUIRED",
                message="当前为免费层，上传 5-9 张截图需要升级 VIP。",
                severity="error",
            )
        )
    if tier == Tier.FREE and screenshot_count > VIP_RELATIONSHIP_MAX:
        issues.append(
            Issue(
                code="SCREENSHOT_TOO_MANY",
                message="截图数量超过当前版本上限，请裁剪到 9 张以内。",
                severity="error",
            )
        )
    if tier == Tier.VIP and screenshot_count < VIP_RELATIONSHIP_MIN:
        issues.append(
            Issue(
                code="VIP_TIER_RANGE",
                message="VIP 关系判断只接受 2-9 张截图。",
                severity="error",
            )
        )
    if tier == Tier.VIP and screenshot_count > VIP_RELATIONSHIP_MAX:
        issues.append(
            Issue(
                code="MAX_SCREENSHOTS_EXCEEDED",
                message="VIP 关系判断最多支持 9 张截图，请先裁剪后再提交。",
                severity="error",
            )
        )
    return issues


def _normalize_text(text: str) -> str:
    lowered = text.strip().lower()
    lowered = re.sub(r"[\s\W_]+", "", lowered, flags=re.UNICODE)
    return lowered


def _is_low_info_text(text: str) -> bool:
    normalized = _normalize_text(text)
    if not normalized:
        return True
    if normalized in LOW_INFO_SHORT_TEXT:
        return True
    if len(normalized) <= 2:
        return True
    return False


def _build_evidence_metrics(dialogue_turns: list[DialogueTurn]) -> dict[str, float | int]:
    if not dialogue_turns:
        return {
            "effective_turn_count": 0,
            "effective_char_count": 0,
            "low_info_ratio": 1.0,
        }

    effective_turn_count = 0
    effective_char_count = 0
    low_info_turns = 0
    for turn in dialogue_turns:
        normalized = _normalize_text(turn.text)
        if not _is_low_info_text(turn.text):
            effective_turn_count += 1
            effective_char_count += len(normalized)
        else:
            low_info_turns += 1

    return {
        "effective_turn_count": effective_turn_count,
        "effective_char_count": effective_char_count,
        "low_info_ratio": round(low_info_turns / len(dialogue_turns), 3),
    }


def _build_evidence_quality(metrics: dict[str, float | int]) -> EvidenceQuality:
    effective_turn_count = int(metrics["effective_turn_count"])
    effective_char_count = int(metrics["effective_char_count"])
    low_info_ratio = float(metrics["low_info_ratio"])

    if (
        effective_turn_count < LOW_INFO_MIN_EFFECTIVE_TURNS
        or effective_char_count < LOW_INFO_MIN_EFFECTIVE_CHARS
        or low_info_ratio >= LOW_INFO_RATIO_THRESHOLD
    ):
        return EvidenceQuality.INSUFFICIENT
    if low_info_ratio >= 0.4:
        return EvidenceQuality.LOW_INFO
    return EvidenceQuality.SUFFICIENT


def mode_requires_evidence_guard(mode: Mode, quality: EvidenceQuality) -> bool:
    return mode == Mode.RELATIONSHIP and quality == EvidenceQuality.INSUFFICIENT


def _sort_frames(frames: list[ScreenshotFrame]) -> tuple[list[ScreenshotFrame], list[Issue]]:
    if not frames:
        return [], []

    has_any_upload_index = any(frame.upload_index is not None for frame in frames)
    all_upload_index_valid = all(
        frame.upload_index is not None and frame.upload_index > 0 for frame in frames
    )
    if all_upload_index_valid:
        sorted_frames = sorted(
            frames,
            key=lambda frame: (frame.upload_index, frame.image_id),
        )
        return sorted_frames, []

    sorted_frames = sorted(
        frames,
        key=lambda frame: (frame.timestamp_hint or "", frame.image_id),
    )
    if has_any_upload_index:
        return sorted_frames, [
            Issue(
                code="UPLOAD_INDEX_INVALID",
                message="上传顺序编号不完整或不合法，已回退到时间戳排序。",
                severity="warning",
            )
        ]
    return sorted_frames, []


def _has_enough_valid_time_hints(preview: list[OCRPreviewItem]) -> bool:
    valid_count = 0
    for item in preview:
        if not (item.left_text or item.right_text):
            continue
        if parse_time_hint_to_minutes(item.timestamp_hint) is not None:
            valid_count += 1
    return valid_count >= 2


def parse_time_hint_to_minutes(timestamp_hint: str | None) -> int | None:
    if timestamp_hint is None:
        return None
    raw = timestamp_hint.strip()
    if not raw:
        return None

    hhmm = re.search(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)", raw)
    if hhmm:
        hour = int(hhmm.group(1))
        minute = int(hhmm.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour * 60 + minute

    normalized = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return dt.hour * 60 + dt.minute


def analyze_latency_from_turns(dialogue_turns: list[DialogueTurn]) -> dict[str, str | int | bool | None]:
    windows = _build_turn_windows(dialogue_turns)
    if len(windows) < 2:
        return {
            "self_bucket": None,
            "other_bucket": None,
            "triggered": False,
            "insufficient": True,
            "other_ender_count": 0,
            "other_ender_warning": False,
        }

    delay_by_speaker: dict[str, list[int]] = {"SELF": [], "OTHER": []}
    ender_by_window: list[dict[str, str | bool]] = [
        _classify_conversation_ender(str(window["tail_text"])) for window in windows
    ]
    other_ender_count = sum(
        1
        for window, ender in zip(windows, ender_by_window)
        if window["speaker"] == "OTHER" and bool(ender["is_conversation_ender"])
    )

    for idx, (prev, curr) in enumerate(zip(windows, windows[1:])):
        if prev["speaker"] == curr["speaker"]:
            continue

        ender = ender_by_window[idx]

        delta, explicit_gap = _derive_gap_minutes(prev["last_minute"], curr["first_minute"])

        if explicit_gap and delta > LONG_GAP_MINUTES:
            if ender["is_conversation_ender"]:
                continue
            if prev["speaker"] != "SELF":
                delta = MIN_CONTINUOUS_GAP_MINUTES

        delay_by_speaker.setdefault(curr["speaker"], []).append(delta)

    self_bucket = _major_latency_bucket(delay_by_speaker.get("SELF", []))
    other_bucket = _major_latency_bucket(delay_by_speaker.get("OTHER", []))
    insufficient = self_bucket is None or other_bucket is None
    triggered = bool(
        not insufficient
        and self_bucket in {"INSTANT", "NORMAL"}
        and other_bucket in {"COLD", "DEAD"}
    )

    return {
        "self_bucket": self_bucket,
        "other_bucket": other_bucket,
        "triggered": triggered,
        "insufficient": insufficient,
        "other_ender_count": other_ender_count,
        "other_ender_warning": other_ender_count >= OTHER_ENDER_WARNING_THRESHOLD,
    }


def _build_turn_windows(dialogue_turns: list[DialogueTurn]) -> list[dict[str, str | int | None]]:
    windows: list[dict[str, str | int | None]] = []
    for turn in dialogue_turns:
        minute = parse_time_hint_to_minutes(turn.timestamp_hint)
        if not windows or windows[-1]["speaker"] != turn.speaker:
            windows.append(
                {
                    "speaker": turn.speaker,
                    "first_minute": minute,
                    "last_minute": minute,
                    "tail_text": turn.text,
                }
            )
            continue
        if windows[-1]["first_minute"] is None and minute is not None:
            windows[-1]["first_minute"] = minute
        if minute is not None:
            windows[-1]["last_minute"] = minute
        windows[-1]["tail_text"] = turn.text
    return windows


def _derive_gap_minutes(prev_last: int | None, curr_first: int | None) -> tuple[int, bool]:
    if prev_last is None or curr_first is None:
        return MIN_CONTINUOUS_GAP_MINUTES, False
    delta = curr_first - prev_last
    if delta < 0:
        delta += 24 * 60
    if delta <= 0:
        return MIN_CONTINUOUS_GAP_MINUTES, True
    return delta, True


def _classify_conversation_ender(text: str) -> dict[str, str | bool]:
    # LLM 接入点预留：后续可替换为外部语义判定，
    # 但必须保留 is_conversation_ender/confidence/reason_tag 固定结构。
    normalized = re.sub(r"\s+", "", (text or "").strip())
    if not normalized:
        return {"is_conversation_ender": False, "confidence": "LOW", "reason_tag": "NOT_END"}
    if any(token in normalized for token in CONVERSATION_ENDERS):
        return {"is_conversation_ender": True, "confidence": "HIGH", "reason_tag": "END_RULE_LIST"}

    semantic_patterns = (
        r"(先|我先).{0,6}(睡|忙|撤|走)",
        r"(明天|改天|回头|下次).{0,4}(聊|说)",
        r"先这样",
        r"先到这",
        r"不聊了",
    )
    if any(re.search(pattern, normalized) for pattern in semantic_patterns):
        return {"is_conversation_ender": True, "confidence": "MEDIUM", "reason_tag": "END_SEMANTIC"}

    uncertain_patterns = (
        r"(晚点|一会|稍后).{0,4}(回|聊)",
        r"(再说吧|看情况)",
    )
    if any(re.search(pattern, normalized) for pattern in uncertain_patterns):
        return {"is_conversation_ender": False, "confidence": "LOW", "reason_tag": "UNCERTAIN"}

    return {"is_conversation_ender": False, "confidence": "LOW", "reason_tag": "NOT_END"}


def _major_latency_bucket(delays: list[int]) -> str | None:
    if not delays:
        return None
    order = {"INSTANT": 0, "NORMAL": 1, "DELAYED": 2, "COLD": 3, "DEAD": 4}
    counts: dict[str, int] = {}
    for delay in delays:
        bucket = _bucket_delay(delay)
        counts[bucket] = counts.get(bucket, 0) + 1
    return max(counts.keys(), key=lambda item: (counts[item], order[item]))


def _bucket_delay(delay_minutes: int) -> str:
    if delay_minutes < 5:
        return "INSTANT"
    if delay_minutes <= 30:
        return "NORMAL"
    if delay_minutes <= 60:
        return "DELAYED"
    if delay_minutes <= 24 * 60:
        return "COLD"
    return "DEAD"


