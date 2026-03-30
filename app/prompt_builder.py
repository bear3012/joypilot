"""Prompt 构建层。

负责：
  1. 将 NEGATIVE_RULES 和心理框架常量注入 system prompt
  2. 根据 tier（Mode1 轻量 / Mode3 密集）组装 context 块
  3. 拼接 few-shot 历史示例

与 config.py 的分工：常量定义在 config，组装逻辑在此模块。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import NEGATIVE_RULES, PSYCHOLOGY_FRAME_MAP
from app.contracts import DialogueTurn, LLMContext

if TYPE_CHECKING:
    pass

# ──────────────────────────────────────────────────────────────────────────────
# LLM 结构化输出 Schema（告知 Gemini 期望 JSON 格式）
# ──────────────────────────────────────────────────────────────────────────────

REPLY_OUTPUT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "replies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "tone": {"type": "string"},
                    "internal_reason": {"type": "string"},
                    "psychology_rationale": {"type": "string"},
                },
                "required": ["text", "tone", "internal_reason", "psychology_rationale"],
            },
        },
        "strategy": {"type": "string"},
    },
    "required": ["replies", "strategy"],
}


# ──────────────────────────────────────────────────────────────────────────────
# System Prompt 构建
# ──────────────────────────────────────────────────────────────────────────────


def build_system_prompt() -> str:
    return (
        "你是 JoyPilot 的专属两性关系话术策略师。\n"
        "你的风格：克制、自信、不依赖、不解释、有品位。\n\n"
        f"{NEGATIVE_RULES}\n\n"
        "输出格式：严格 JSON，不得输出任何 markdown 或自然语言解释。"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Context 注入（Mode1 轻量 / Mode3 密集）
# ──────────────────────────────────────────────────────────────────────────────


def build_context_injection(
    dialogue_turns: list[DialogueTurn],
    llm_context: LLMContext,
    dense: bool = False,
) -> str:
    """
    组装 context 块。

    Args:
        dialogue_turns: 完整对话轮次
        llm_context: J28/J29/J30 算法状态快照
        dense: True = Mode3 密集模式（完整对话 + 全量算法结论）；
               False = Mode1 轻量模式（最近 5 轮 + 核心信号）
    """
    lines: list[str] = []

    # 对话摘要
    turns_to_show = dialogue_turns if dense else dialogue_turns[-5:]
    if turns_to_show:
        lines.append("【对话记录】")
        for t in turns_to_show:
            label = "我" if t.speaker == "SELF" else "对方"
            lines.append(f"  {label}：{t.text}")
        lines.append("")

    # J 系列算法结论
    lines.append("【算法状态】")
    if llm_context.j28_trend:
        frame, explanation = PSYCHOLOGY_FRAME_MAP.get(
            llm_context.j28_trend, ("未知框架", "")
        )
        lines.append(f"  趋势信号(J28): {llm_context.j28_trend} — {explanation}")
    if llm_context.j29_naked_punct:
        _, explanation = PSYCHOLOGY_FRAME_MAP.get("J29_NAKED_PUNCT", ("", ""))
        lines.append(f"  裸标点警报(J29): 是 — {explanation}")
    if llm_context.j30_triggered:
        _, explanation = PSYCHOLOGY_FRAME_MAP.get("J30_INTERRUPTED", ("", ""))
        lines.append(f"  断联警报(J30): 是 — {explanation}")
    if llm_context.risk_signals:
        lines.append(f"  风险信号: {'; '.join(llm_context.risk_signals)}")

    if dense and llm_context.dialogue_window:
        lines.append("")
        lines.append("【当前分析窗口（Part_B）】")
        for item in llm_context.dialogue_window:
            label = "我" if item.get("speaker") == "SELF" else "对方"
            lines.append(f"  {label}：{item.get('text', '')}")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Few-Shot 拼接
# ──────────────────────────────────────────────────────────────────────────────


def build_few_shot_block(examples: list[dict]) -> str:
    """
    将 review_library 取出的历史条目格式化为 few-shot 示例块。

    Args:
        examples: ReviewEntry.model_dump() 列表（最多 3 条）

    Returns:
        格式化文本，空列表时返回空字符串
    """
    if not examples:
        return ""

    lines = ["【历史偏好示例 — 仅供参考风格，不要原文复制】"]
    for i, ex in enumerate(examples[:3], 1):
        lines.append(f"  示例 {i}：用户选择了「{ex.get('selected_text', '')}」")
        rejected = ex.get("rejected_texts", [])
        if rejected:
            lines.append(f"    拒绝了：{', '.join(f'「{r}」' for r in rejected[:2])}")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# 组装完整 prompt
# ──────────────────────────────────────────────────────────────────────────────


def build_full_prompt(
    dialogue_turns: list[DialogueTurn],
    llm_context: LLMContext,
    few_shot_examples: list[dict],
    dense: bool = False,
    extra_instruction: str = "",
    session_context: str = "",
    non_instruction_policy: str = "",
) -> str:
    """
    组装最终传给 LLM 的完整 prompt（system + 历史隔离声明 + context + few-shot + 指令）。

    Args:
        session_context: 已 XML 转义的历史 session 片段（来自 reply_service）。
        non_instruction_policy: 非指令化隔离声明（来自 NON_INSTRUCTION_CONTEXT_POLICY）。
    """
    parts: list[str] = [build_system_prompt()]

    # 历史上下文注入：先放非指令化声明，再放标签包裹的历史内容
    if non_instruction_policy:
        parts += ["", non_instruction_policy]
    if session_context:
        parts += ["", session_context]

    parts += ["", build_context_injection(dialogue_turns, llm_context, dense=dense)]

    few_shot = build_few_shot_block(few_shot_examples)
    if few_shot:
        parts += ["", few_shot]

    parts += [
        "",
        "【任务指令】",
        "根据以上对话和算法状态，生成 2-3 条差异化话术。",
        "每条话术必须包含 text / tone / internal_reason / psychology_rationale 四个字段。",
        "tone 取值范围：STABLE（保守稳妥）/ NATURAL（自然克制）/ PROACTIVE（主动试探）。",
        "strategy 说明本轮整体策略（MAINTAIN / DEGRADE / PROBE / HOLD）。",
    ]

    if extra_instruction:
        parts += ["", extra_instruction]

    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────────────
# 心理学框架：从算法结论生成 ledger.note 追加文本
# ──────────────────────────────────────────────────────────────────────────────


def get_psychology_frame(llm_context: LLMContext) -> str:
    """
    根据 J 系列状态返回适合追加到 ledger.note 的心理学框架说明。
    优先级：J30 > J29 > J28 > baseline。
    """
    if llm_context.j30_triggered:
        frame, explanation = PSYCHOLOGY_FRAME_MAP["J30_INTERRUPTED"]
    elif llm_context.j29_naked_punct:
        frame, explanation = PSYCHOLOGY_FRAME_MAP["J29_NAKED_PUNCT"]
    elif llm_context.j28_trend and llm_context.j28_trend != "NONE":
        frame, explanation = PSYCHOLOGY_FRAME_MAP.get(
            llm_context.j28_trend, PSYCHOLOGY_FRAME_MAP["BASELINE"]
        )
    else:
        frame, explanation = PSYCHOLOGY_FRAME_MAP["BASELINE"]

    return f"【心理学框架·{frame}】{explanation}"
