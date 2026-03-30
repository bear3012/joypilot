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

J30_GAP_MINUTES = 180
J30_MIN_INTERRUPTION_COUNT = 2
J30_WARN = (
    "【靠谱度警报】诊断依据：对方在多次长时间间隔后仅以低价值内容回应，"
    "显示出明显的「推脱 + 拖延」模式。建议暂停主动推进，转入冷静观察期。"
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

# ─────────────────────────────────────────────
# LLM 接入配置
# ─────────────────────────────────────────────

LLM_PROVIDER = "gemini"
GEMINI_MODEL = "gemini-1.5-pro"
LLM_MAX_REPLY_TOKENS = 512
REVIEW_LIBRARY_PATH = "data/review_library"

# 话术负面规则（System Prompt 注入，写死单一常量）
NEGATIVE_RULES: str = """
【话术生成铁律 — 不可违背】

一、字数与格式
• 所有话术强制限制在 20 字以内（战略性小作文除外，但须在 strategy 字段注明原因）
• 禁止句号结尾；可不加标点、用空格、波浪号（~）或省略号（…）结尾
• 禁止括号说明、markdown 格式、emoji 堆砌

二、语气与措辞
• 禁止「您好」「很抱歉」「感谢」「希望」「建议您」「不用担心」「冷静」等客服用语
• 禁止四字成语、书面语、正式解释
• 禁止主动道歉（对方明确受伤害的场景除外）

三、两性关系专属雷区
• 禁止讲逻辑/讲道理：绝对禁止「因为……所以……」「客观来说」等逻辑推演句式；\
恋爱不讲对错，只讲情绪
• 禁止暴露极高可得性：禁止「随时都在」「等你消息」「我都行听你的」等\
暴露高需求感的舔狗话术
• 禁止强行推进关系：当对方冷淡或打断时，禁止主动发起邀约（如「要不要出来吃饭」）、\
禁止反问追问（如「你到底怎么想的」）
""".strip()

# 心理学框架映射：算法结论 → (框架名, 面向用户的一句话解释)
PSYCHOLOGY_FRAME_MAP: dict[str, tuple[str, str]] = {
    "HOT_TO_COLD": (
        "防御机制（精神分析）",
        "对方采用情感退缩作为回避亲密的防御策略，强行追问只会加剧其退缩。",
    ),
    "COLD_TO_HOT": (
        "间歇强化（行为主义）",
        "偶发正向回应形成间歇强化，当前窗口可进行低压力试探，但避免过度投入。",
    ),
    "J29_NAKED_PUNCT": (
        "投资博弈（亲密关系博弈论）",
        "奖惩比失衡，对方低投入回应强化了单边依赖结构，需主动降低追投密度。",
    ),
    "J30_INTERRUPTED": (
        "回避型依附（依附理论）",
        "通过间歇性断联维持心理安全距离，属于回避型依附特征，施压只会触发更强回避。",
    ),
    "BASELINE": (
        "社会交换理论",
        "当前互动处于成本-收益评估期，对方尚未形成明确投入意向。",
    ),
}
