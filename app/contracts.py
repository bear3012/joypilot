from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Tier(str, Enum):
    FREE = "FREE"
    VIP = "VIP"


class Mode(str, Enum):
    REPLY = "REPLY"
    RELATIONSHIP = "RELATIONSHIP"


class MySide(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class Recommendation(str, Enum):
    YES = "YES"
    WAIT = "WAIT"
    NO = "NO"


class SafetyStatus(str, Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    BLOCKED = "BLOCKED"


class GateDecision(str, Enum):
    ALLOW = "ALLOW"
    DEGRADE = "DEGRADE"
    BLOCK = "BLOCK"


class RouteTone(str, Enum):
    STABLE = "STABLE"
    NATURAL = "NATURAL"
    BOLD_HONEST = "BOLD_HONEST"


class EvidenceQuality(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    LOW_INFO = "LOW_INFO"
    INSUFFICIENT = "INSUFFICIENT"


class Issue(BaseModel):
    code: str
    message: str
    severity: str = "warning"


class ScreenshotFrame(BaseModel):
    image_id: str
    upload_index: int | None = None
    timestamp_hint: str | None = None
    left_text: str = ""
    right_text: str = ""


class OCRPreviewItem(BaseModel):
    image_id: str
    ordered_index: int
    timestamp_hint: str | None = None
    left_text: str = ""
    right_text: str = ""


class DialogueTurn(BaseModel):
    speaker: str
    text: str
    source_image_id: str
    timestamp_hint: str | None = None
    is_naked_punctuation: bool = False
    # Semantic feature reserved for future LLM integration; always False in v1 rule engine.
    shows_personal_interest: bool = False


class PreparedUpload(BaseModel):
    status: str
    screenshot_count: int
    tier: Tier
    mode: Mode
    timeline_confirmed: bool
    my_side: MySide | None = None
    evidence_quality: EvidenceQuality = EvidenceQuality.SUFFICIENT
    effective_turn_count: int = 0
    effective_char_count: int = 0
    low_info_ratio: float = 0.0
    duplicate_content_suspected: bool = False
    issues: list[Issue] = Field(default_factory=list)
    ocr_preview: list[OCRPreviewItem] = Field(default_factory=list)
    dialogue_turns: list[DialogueTurn] = Field(default_factory=list)


class UploadPrepareRequest(BaseModel):
    user_id: str
    target_id: str
    tier: Tier
    mode: Mode
    screenshots: list[ScreenshotFrame] = Field(default_factory=list)
    text_input: str | None = None
    timeline_confirmed: bool = False
    my_side: MySide | None = None


class SignalCandidate(BaseModel):
    signal_type: str
    raw_value: str
    low_info: bool
    frequency: int = 1
    candidate_interpretations: list[str]
    note: str


class SafetyBlock(BaseModel):
    status: SafetyStatus
    block_reason: str | None = None
    allowed_to_generate_messages: bool
    note: str


class MessageBankItem(BaseModel):
    """???????text / tone / psychology_rationale ?????internal_reason ???????"""

    text: str
    tone: str  # STABLE | NATURAL | PROACTIVE
    internal_reason: str = ""
    psychology_rationale: str = ""


class Dashboard(BaseModel):
    action_light: str
    tension_index: int
    pressure_score: int
    blindspot_risk: str
    mean_reversion: str
    availability_override: str
    frame_anchor: str
    gearbox_ratio_radar: str
    cooldown_timer: str
    focus_redirect: str
    reciprocity_meter: str
    sunk_cost_breaker: str
    adaptive_tension: str
    suggestive_channel: str
    macro_stage: str
    interest_discriminator_panel: str
    stage_transition: str
    message_bank: list[MessageBankItem] = Field(default_factory=list)


class ExplainCard(BaseModel):
    active: bool
    forced_style: str | None = None
    evidence_signals: list[str] = Field(default_factory=list)
    can_disable: bool = True
    disable_cost_battery: int = 0
    risk_banner_level: str = "LOW"
    note: str


class ReplySessionMeta(BaseModel):
    session_id: str
    start_at: datetime
    expires_at: datetime
    is_new_session: bool
    active: bool


class StructuredDiagnosis(BaseModel):
    current_stage: str
    risk_signals: list[str]
    strategy: str
    send_recommendation: Recommendation
    one_line_explanation: str


class ReplyRoute(BaseModel):
    route_id: str
    tone: RouteTone
    recommendation: Recommendation
    text: str
    reason: str


class ConstraintRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConstraintStrategyHint(str, Enum):
    PUSH = "PUSH"
    MAINTAIN = "MAINTAIN"
    DEGRADE = "DEGRADE"
    WAIT = "WAIT"


class RelationshipConstraints(BaseModel):
    source_mode: str = "RELATIONSHIP_ONLY"
    risk_level: ConstraintRiskLevel | None = None
    strategy_hint: ConstraintStrategyHint | None = None
    reply_guardrails: list[str] = Field(default_factory=list)
    summary_ref: str | None = None


class ReplyAnalyzeRequest(BaseModel):
    user_id: str
    target_id: str
    tier: Tier = Tier.FREE
    text_input: str | None = None
    prepared_upload: PreparedUpload | None = None
    ad_proof_token: str | None = None
    use_emergency_pack: bool = False
    consent_sensitive: bool = False
    user_goal_mode: str = "MAINTAIN"
    style_mode: RouteTone = RouteTone.NATURAL
    force_new_session: bool = False
    reply_session_now: datetime | None = None
    relationship_constraints: RelationshipConstraints | None = None


class ReplyAnalyzeResponse(BaseModel):
    contract_version: str
    mode: Mode = Mode.REPLY
    dashboard: Dashboard
    safety: SafetyBlock
    explain_card: ExplainCard
    reply_session: ReplySessionMeta
    structured_diagnosis: StructuredDiagnosis
    signals: list[SignalCandidate]
    gating_issues: list[Issue] = Field(default_factory=list)


class ProbeItem(BaseModel):
    probe_type: str = Field(description="J26 ?????")
    intent: str = Field(description="?????????????????????????")
    template: str = Field(description="?????????????????????????")
    when_to_use: str = Field(description="?????????????????")
    risk_level: str = Field(description="?????????????????")
    expected_signal: str = Field(description="????????/??/???????")
    do_not_overinterpret: str = Field(description="?????????????????")
    followup_rule: str = Field(description="?????????????????")


class ProbePackage(BaseModel):
    available: bool = Field(description="J26 ?????BLOCK ????? false?")
    items: list[ProbeItem] = Field(
        default_factory=list,
        description="J26 ????????????????BLOCK ???????",
    )


class ProgressValidation(BaseModel):
    probe_type: str | None = None
    intent: str | None = None
    followup_rule: str


class RealityAnchorReport(BaseModel):
    available: bool
    tone: str = Field(description="J27 ???????????????")
    access: str = Field(description="J27 ?????BLOCK ????? ALERT_ONLY?")
    delay_gate_sec: int
    brief_points: list[str] = Field(
        description="?????????????????????????????????"
    )
    full_text: str | None = Field(
        default=None,
        description="??????????????????????????",
    )


class LedgerSummary(BaseModel):
    asymmetric_risk: str = Field(description="J24 ?????????? LOW/MEDIUM/HIGH?")
    evidence: list[str] = Field(
        description="J24 ?????????????????????????????????"
    )
    note: str = Field(description="J24 ????????????????????")


class SopFilterSummary(BaseModel):
    total_hits: int
    hits: list[str]
    risk_escalation: str
    evidence_signals: list[str]
    footer: str = Field(default="??????????", description="J25 ???????????????????")


class LLMContext(BaseModel):
    """?? LLM ????????????? context ???"""

    j28_trend: str | None = None  # HOT_TO_COLD | COLD_TO_HOT | NONE
    j29_naked_punct: bool = False
    j30_triggered: bool = False
    risk_signals: list[str] = Field(default_factory=list)
    dialogue_window: list[dict] = Field(default_factory=list)


class ReviewEntry(BaseModel):
    """??????????????????? Few-Shot ????"""

    user_id: str
    selected_text: str
    rejected_texts: list[str] = Field(default_factory=list)
    context_fingerprint: str
    j_series_snapshot: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RelationshipAnalyzeRequest(BaseModel):
    user_id: str
    target_id: str
    tier: Tier
    prepared_upload: PreparedUpload
    need_full_report: bool = False
    ad_proof_token: str | None = None
    use_emergency_pack: bool = False
    consent_sensitive: bool = False


class RelationshipAnalyzeResponse(BaseModel):
    contract_version: str
    mode: Mode = Mode.RELATIONSHIP
    gate_decision: GateDecision = GateDecision.ALLOW
    dashboard: Dashboard
    safety: SafetyBlock
    explain_card: ExplainCard
    structured_diagnosis: StructuredDiagnosis
    signals: list[SignalCandidate]
    recovery_protocol: dict
    ledger: LedgerSummary
    sop_filter: SopFilterSummary
    probes: ProbePackage
    progress_validation: ProgressValidation
    reality_anchor_report: RealityAnchorReport
    gating_issues: list[Issue] = Field(default_factory=list)
