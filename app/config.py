from __future__ import annotations

from datetime import timedelta

APP_NAME = "JoyPilot"
CONTRACT_VERSION = "v1.0.0"
SESSION_DURATION = timedelta(hours=24)

FREE_REPLY_DAILY_LIMIT = 3
FREE_REPLY_AD_BONUS = 3
FREE_RELATIONSHIP_DAILY_LIMIT = 2
AD_PROOF_TOKEN_PREFIX = "adp_"
AD_PROOF_TOKEN_MIN_LEN = 16

FREE_RELATIONSHIP_MIN = 2
FREE_RELATIONSHIP_MAX = 4
VIP_RELATIONSHIP_MIN = 2
VIP_RELATIONSHIP_MAX = 9

MAX_RISK_SIGNALS = 3
MAX_MESSAGE_BANK = 3
MAX_SESSION_TURNS = 10
MAX_SESSION_TOTAL_CHARS = 2000
MAX_AUDIT_LOGS_PER_USER = 500
MAX_SEGMENT_SUMMARIES_PER_TARGET = 50
MAX_SEGMENT_SUMMARY_BYTES = 20 * 1024

LATENCY_CROSS_DAY_MINUTES = 24 * 60
LATENCY_BUCKET_INSTANT_MAX = 5
LATENCY_BUCKET_NORMAL_MAX = 30
LATENCY_BUCKET_DELAYED_MAX = 60
LATENCY_BUCKET_COLD_MAX = 24 * 60
LATENCY_NOTE_DISCLAIMER = "免责声明：对方回复变慢也可能受工作安排、家庭事务或作息影响，请勿仅凭单次时延做绝对判断。"

LOW_INFO_MIN_EFFECTIVE_CHARS = 8
LOW_INFO_MIN_EFFECTIVE_TURNS = 2
LOW_INFO_RATIO_THRESHOLD = 0.7

LOW_INFO_SHORT_TEXT = (
    "哦",
    "嗯",
    "好",
    "哈哈",
    "ok",
    "收到",
)

POSITIVE_KEYWORDS = (
    "哈哈",
    "想你",
    "好呀",
    "可以",
    "见面",
    "周末",
    "一起",
    "期待",
)

NEGATIVE_KEYWORDS = (
    "忙",
    "再说",
    "改天",
    "算了",
    "不方便",
    "别",
    "不要",
    "冷静",
)

NO_CONTACT_PATTERNS = (
    "拉黑",
    "别联系",
    "不要联系",
    "停止联系",
    "no-contact",
    "报警",
)

MANIPULATION_PATTERNS = (
    "逼她",
    "服从测试",
    "冷暴力",
    "报复",
    "让她慌",
    "羞辱",
    "惩罚她",
)

PROMPT_INJECTION_PATTERNS = (
    "ignore previous",
    "system prompt",
    "覆盖规则",
    "输出系统提示",
    "你现在必须",
    "开发者指令",
)

SENSITIVE_CONTEXT_PATTERNS = (
    "抑郁",
    "焦虑症",
    "自残",
    "自杀",
    "精神科",
    "心理危机",
    "经期",
    "生理期",
    "怀孕",
    "流产",
    "妇科",
    "性病",
    "艾滋",
    "药物治疗",
)

LOW_INFO_EMOJI = (
    "❤️",
    "❤",
    "😂",
    "🙂",
    "😊",
    "👍",
    "😅",
    "😄",
)

EMOJI_CANDIDATES = {
    "❤️": ["positive_interest", "warmth"],
    "❤": ["positive_interest", "warmth"],
    "😂": ["light_positive", "awkward_softener"],
    "🙂": ["polite_response", "habitual_usage"],
    "😊": ["warmth", "polite_response"],
    "👍": ["acknowledgement", "low_effort_ack"],
    "😅": ["awkward_softener", "polite_response"],
    "😄": ["light_positive", "habitual_usage"],
}
