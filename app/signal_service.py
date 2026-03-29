from __future__ import annotations

from app.config import EMOJI_CANDIDATES, LOW_INFO_EMOJI, MAX_RISK_SIGNALS
from app.contracts import SignalCandidate

BRACKETED_STICKER_PLACEHOLDERS = ("[sticker]", "[贴图]", "[动画表情]")
PLAIN_STICKER_PLACEHOLDERS = ("贴图", "动画表情")
STICKER_INTERPRETATIONS = ["非文本情绪表达", "低信息回应", "话题缓冲"]
STICKER_BLINDSPOT_RISK = "包含未解析的图像贴图，当前文本信息量存在盲区，切勿过度解读。"
EMOJI_DENSITY_RISK = "单点情绪符号过度密集，存在情绪释放或敷衍可能"
LOW_INFO_OVERINTERPRET_RISK = "过度解读风险"
PROMPT_INJECTION_RISK = "命令型文本干扰"


def extract_signals(texts: list[str]) -> list[SignalCandidate]:
    signals_by_key: dict[tuple[str, str], SignalCandidate] = {}
    ordered_keys: list[tuple[str, str]] = []
    for text in texts:
        stripped = text.strip()
        if not stripped:
            continue
        for emoji in LOW_INFO_EMOJI:
            frequency = stripped.count(emoji)
            if frequency > 0:
                _upsert_signal(
                    signals_by_key=signals_by_key,
                    ordered_keys=ordered_keys,
                    signal_type="EMOJI",
                    raw_value=emoji,
                    low_info=_is_low_info_emoji_text(stripped),
                    frequency=frequency,
                    candidate_interpretations=EMOJI_CANDIDATES.get(emoji, ["ambiguous_signal"]),
                    note="只作为候选信号，不直接作为关系定论。",
                )
        sticker_frequency = _count_sticker_placeholders(stripped)
        if sticker_frequency > 0:
            _upsert_signal(
                signals_by_key=signals_by_key,
                ordered_keys=ordered_keys,
                signal_type="STICKER",
                raw_value="STICKER_PLACEHOLDER",
                low_info=True,
                frequency=sticker_frequency,
                candidate_interpretations=STICKER_INTERPRETATIONS,
                note="贴图占位符属于非文本候选信号，必须结合上下文看，不能单点定性。",
            )
    return [signals_by_key[key] for key in ordered_keys]


def summarize_risk_signals(signals: list[SignalCandidate], prompt_injection_hits: list[str]) -> list[str]:
    ordered_risks: list[str] = []
    # Priority: injection > sticker blindspot > emoji density > generic low-info.
    if prompt_injection_hits:
        ordered_risks.append(PROMPT_INJECTION_RISK)
    if any(signal.signal_type == "STICKER" for signal in signals):
        ordered_risks.append(STICKER_BLINDSPOT_RISK)
    if any(signal.signal_type == "EMOJI" and signal.frequency > 3 for signal in signals):
        ordered_risks.append(EMOJI_DENSITY_RISK)
    if any(signal.low_info for signal in signals):
        ordered_risks.append(LOW_INFO_OVERINTERPRET_RISK)
    return ordered_risks[:MAX_RISK_SIGNALS]


def contains_positive_candidate(signals: list[SignalCandidate]) -> bool:
    return any("positive_interest" in signal.candidate_interpretations for signal in signals)


def _upsert_signal(
    *,
    signals_by_key: dict[tuple[str, str], SignalCandidate],
    ordered_keys: list[tuple[str, str]],
    signal_type: str,
    raw_value: str,
    low_info: bool,
    frequency: int,
    candidate_interpretations: list[str],
    note: str,
) -> None:
    key = (signal_type, raw_value)
    existing = signals_by_key.get(key)
    if existing is None:
        ordered_keys.append(key)
        signals_by_key[key] = SignalCandidate(
            signal_type=signal_type,
            raw_value=raw_value,
            low_info=low_info,
            frequency=frequency,
            candidate_interpretations=candidate_interpretations,
            note=note,
        )
        return
    signals_by_key[key] = existing.model_copy(
        update={
            "frequency": existing.frequency + frequency,
            "low_info": existing.low_info or low_info,
        }
    )


def _count_sticker_placeholders(text: str) -> int:
    lowered = text.lower()
    count = 0
    # Count bracketed placeholders first, then strip them to avoid double count
    # from overlapping plain tokens (e.g. "[贴图]" and "贴图").
    for token in BRACKETED_STICKER_PLACEHOLDERS:
        hits = lowered.count(token)
        count += hits
        if hits:
            lowered = lowered.replace(token, " ")
    for token in PLAIN_STICKER_PLACEHOLDERS:
        count += lowered.count(token)
    return count


def _is_low_info_emoji_text(text: str) -> bool:
    stripped = text
    for emoji in LOW_INFO_EMOJI:
        stripped = stripped.replace(emoji, "")
    return not stripped.strip()
