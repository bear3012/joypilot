"""LLM 服务抽象层。

提供统一接口 LLMProvider.generate(prompt, schema)，默认实现为 GeminiProvider。
通过 config.LLM_PROVIDER 控制实际提供商，便于未来切换。

fallback 链：
  1. Gemini structured output（response_schema）
  2. Gemini 普通文本 + JSON 提取
  3. MockProvider（硬编码最小化输出）
"""
from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

from app.config import GEMINI_MODEL, LLM_PROVIDER

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# 抽象接口
# ──────────────────────────────────────────────────────────────────────────────


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, schema: dict[str, Any] | None = None) -> dict:
        """
        调用 LLM 并返回解析后的 dict。

        Args:
            prompt: 完整的用户侧 prompt（已包含 system prompt）
            schema: 期望的 JSON 结构（用于 structured output 提示）

        Returns:
            解析后的 dict；生成失败时抛出 LLMGenerationError
        """
        ...


class LLMGenerationError(Exception):
    """LLM 调用或解析失败时抛出。"""


# ──────────────────────────────────────────────────────────────────────────────
# Mock 实现（无网络依赖，用于测试和降级）
# ──────────────────────────────────────────────────────────────────────────────


class MockProvider(LLMProvider):
    """本地 Mock，用于测试和网络不可用时的 fallback。"""

    def generate(self, prompt: str, schema: dict[str, Any] | None = None) -> dict:
        return {
            "replies": [
                {
                    "text": "嗯，随你",
                    "tone": "STABLE",
                    "internal_reason": "mock fallback: neutral hold",
                    "psychology_rationale": "保持低调，不主动暴露需求感。",
                },
                {
                    "text": "最近忙什么",
                    "tone": "NATURAL",
                    "internal_reason": "mock fallback: soft probe",
                    "psychology_rationale": "轻度开放式提问，测试对方回应意愿。",
                },
                {
                    "text": "那周末有没有空",
                    "tone": "PROACTIVE",
                    "internal_reason": "mock fallback: light invitation",
                    "psychology_rationale": "低压力邀约，不强迫表态，保留对方主动权。",
                },
            ],
            "strategy": "MAINTAIN",
        }


# ──────────────────────────────────────────────────────────────────────────────
# Gemini 实现
# ──────────────────────────────────────────────────────────────────────────────


class GeminiProvider(LLMProvider):
    """
    使用 google-generativeai SDK 调用 Gemini。

    两级 fallback：
      1. response_mime_type="application/json" + response_schema 强制结构化输出
      2. 纯文本生成 + 正则提取 JSON 块
    """

    def __init__(self, model: str = GEMINI_MODEL) -> None:
        self._model_name = model
        self._client = None  # lazy init

    def _get_client(self):
        if self._client is None:
            try:
                import google.generativeai as genai  # type: ignore
                import os

                api_key = os.environ.get("GEMINI_API_KEY", "")
                if not api_key:
                    raise LLMGenerationError("GEMINI_API_KEY 未设置")
                genai.configure(api_key=api_key)
                self._client = genai.GenerativeModel(self._model_name)
            except ImportError as e:
                raise LLMGenerationError(
                    f"google-generativeai 未安装：{e}"
                ) from e
        return self._client

    def generate(self, prompt: str, schema: dict[str, Any] | None = None) -> dict:
        # 阶段 1：structured output
        try:
            return self._generate_structured(prompt, schema)
        except Exception as e:
            logger.warning("Gemini structured output 失败，尝试文本 fallback: %s", e)

        # 阶段 2：文本 + JSON 提取
        try:
            return self._generate_text_fallback(prompt)
        except Exception as e:
            logger.warning("Gemini 文本 fallback 也失败: %s", e)

        raise LLMGenerationError("Gemini 两级生成均失败")

    def _generate_structured(self, prompt: str, schema: dict | None) -> dict:
        import google.generativeai as genai  # type: ignore
        from google.generativeai.types import GenerationConfig  # type: ignore

        client = self._get_client()
        gen_cfg = GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ) if schema else GenerationConfig(response_mime_type="application/json")

        response = client.generate_content(prompt, generation_config=gen_cfg)
        return json.loads(response.text)

    def _generate_text_fallback(self, prompt: str) -> dict:
        client = self._get_client()
        response = client.generate_content(prompt)
        raw = response.text
        # 提取第一个 JSON 代码块或裸 JSON
        match = re.search(r"```json\s*([\s\S]+?)\s*```", raw)
        if match:
            return json.loads(match.group(1))
        # 裸 JSON
        json_match = re.search(r"\{[\s\S]+\}", raw)
        if json_match:
            return json.loads(json_match.group(0))
        raise LLMGenerationError("无法从 Gemini 文本响应中提取 JSON")


# ──────────────────────────────────────────────────────────────────────────────
# 工厂函数
# ──────────────────────────────────────────────────────────────────────────────


def get_llm_provider() -> LLMProvider:
    """根据 config.LLM_PROVIDER 返回对应实现。未知 provider 默认 Mock。"""
    if LLM_PROVIDER == "gemini":
        try:
            provider = GeminiProvider()
            # 检查环境变量，无 key 则直接降级到 Mock 避免运行时报错
            import os
            if not os.environ.get("GEMINI_API_KEY"):
                logger.warning("GEMINI_API_KEY 未设置，降级为 MockProvider")
                return MockProvider()
            return provider
        except Exception as e:
            logger.warning("GeminiProvider 初始化失败，降级为 MockProvider: %s", e)
            return MockProvider()
    logger.warning("未知 LLM_PROVIDER=%s，降级为 MockProvider", LLM_PROVIDER)
    return MockProvider()
