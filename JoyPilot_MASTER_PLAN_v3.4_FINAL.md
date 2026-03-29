# JoyPilot 实施方案 MASTER PLAN v3.4（最终完整版 / LOCKED & CLINICALLY-CALIBRATED / MOAT-READY）

**AI-first / Contract-first / Gate-driven / Persona-driven / Radar Console / Receiver-Aligned Messaging / Aquarius Protocol / J2.7 Suggestive Hints / J15 Suite / STG Gate / Distance Context / ROI Roadmap / Web→PWA / Evidence-first / Anti-Rumination / Safety-Routed**

---

## 文档定位

本版本是在你给出的 `v3.2` 原始实施方案基础上，完整吸收本项目讨论结果后形成的最终执行版。它不是摘要，不是概念稿，不是占位草案，而是给 AI、工程团队、产品团队、测试团队都能直接读懂和拆解执行的主文档。

本版严格保留并延续了 v3.2 中已经写死的核心骨架：

- Contract-first
- Deterministic-by-default
- No silent failure
- Safety & Respect
- Consent-first for Sensitive Context
- Self-stability First
- Aquarius Protocol
- Evidence-driven Stage Change
- Baseline-first Interpretation
- J2.7 Suggestive Hints 红线
- Platform-neutral Compliance
- Monetization Non-Coercive
- No Deceptive Ads Masking
- Emergency Bypass Is User-first
- RAG Recency & Conflict Safety
- Profile Size Cap
- J22 / J23 / J24 / J25 / J26 / J27
- Safety Block + Allowed Actions 白名单
- 固定 Dashboard 输出
- Gate-driven Core Engine

在此基础上，本版新增并写实了以下关键升级：

- Dynamic Target Persona Engine（动态对方画像引擎）
- Receiver-Aligned Messaging Engine（接收者对齐式话术引擎）
- Counter-Hypothesis + Missing Data Layer（反过度解读层）
- User Regulation Snapshot（用户状态快照）
- Responsiveness Index（回应性指数）
- Abuse / Coercive Control / Stalking Router（高危关系分流）
- Anti-Rumination Lock（反反刍锁）
- Repair vs Exit Router（修复/退出分流）
- Calibrated Explainability（校准式解释层）
- JITAI Validation Harness（行为验证层）
- Authenticity Lock（真实性锁）
- J28 Evidence Graph（证据图谱）
- J29 Outcome Tracker（结果闭环）
- J30 Recovery ROI Engine（止损收益引擎）
- J31 Trust Tier Engine（关系可信度等级）
- Battery Class Segmentation（分层电池）

---

# 0. 最终产品一句话定义

**JoyPilot 会根据聊天记录、互动轨迹和对方信息，生成一个可解释、可更新、可校准的动态对方画像，判断这段关系的风险、回应性与投入价值，并在不违背用户真实性和边界的前提下，给出当前最适合发送的话术、核验动作、止损建议与现实锚点报告。**

更短的用户版：

**看清对方画像，再决定怎么回。**

更短的商业版：

**JoyPilot 不是帮用户更会聊，而是帮用户少误判、少错付、少上头。**

---

# 1. 最高原则（写死，不讨论）

## 1.1 Contract-first
先定义输入/输出契约（Pydantic / JSON Schema）→ 再写 fixtures（金样 / 红队 / 负向）→ 再实现。任何模块不得绕过 contract 直接面向用户输出文本。

## 1.2 Deterministic-by-default
- 输出结构、字段顺序、枚举、排序规则：全部确定化
- 允许多样性的地方必须 seed 固定（同输入同输出）
- LLM 只能在允许字段内润色，不得改结构 / 意图 / 阈值结论
- UI 顺序、模块顺序、风险灯顺序、message_bank 排序都必须固定

## 1.3 No silent failure
宁可返回“不确定 / 需要澄清 / 需要用户确认”，也不允许编造确定结论。

## 1.4 Safety & Respect（去 PUA 化工程约束）
禁止输出：
- 胁迫
- 羞辱
- 操控
- 纠缠
- 惩罚式冷落
- 内疚绑架
- 逼问逼表态
- 阴阳怪气贬损
- 任何“制造焦虑”“测试服从 / 边界”的意图或话术

写死补强：
- 禁止任何“服从测试 / 合规度 = 是否听话”的维度与叙事
- 禁止“图灵审判 / 逼露底牌 / 一击必杀 / 服从熔断”措辞与意图
- 禁止“毒舌羞辱 / 嘲讽用户 / 人格攻击”的清醒报告
- Safety Block 命中时：`message_bank` 必须为空，只输出安全提示与下一步建议（非话术）
- Receiver-Aligned Messaging 只能做表达适配，不能做人格操控

## 1.5 Consent-first for Sensitive Context
- 经期 / 健康 / 高隐私敏感语境：仅 Premium 可用
- 用户每次会话显式确认后才启用
- 不做健康推断
- 默认不点名（除非用户允许且来源明确）
- 不入记忆 / 不入日志原文（脱敏门禁）
- 敏感上下文的 probe 只能给非医疗、非诊断、非替代专业建议的表达

## 1.6 Self-stability First
高压 / 不确定性 / 施压风险升高时，优先输出：
- 降速
- 澄清
- 停止施压
- 转移注意力到自我生活
- 减少主动消耗
- 先做用户状态稳定，而非先做关系推进

## 1.7 Aquarius Protocol
- 均值回归
- 现实结界
- 框架自洽锁
- 沉没成本熔断
- 48h 暂停加码
- 当用户主观上头时，不允许产品陪同升级投入

## 1.8 Evidence-driven Stage Change
跨阶段只能由 `Behavior Events` 触发；两阶段提交：`proposal -> confirmed`（需 STG Gate）。
不得用一句情绪表达、一次深夜热情、一次模糊承诺直接推进阶段。

## 1.9 Baseline-first Interpretation
所有“冷却 / 短回 / 退火 / 突然热情”必须走 Delta vs Baseline，不比大盘，不比他人平均，不做泛化推断。

## 1.10 J2.7 Suggestive Hints 红线
仅 LOW / MEDIUM；Premium + opt-in + 18+；上位覆盖：Safety / Consent / OfflineShield / ValidationWindow / Backoff。

## 1.11 Platform-neutral Compliance
Web / PWA 与 App 同标准，不得因平台不同放松门禁。

## 1.12 Monetization Non-Coercive（写死）
命中 HIGH_PRESSURE / COOLDOWN_LOCK / OFFLINE_SOCIAL_SHIELD / SENSITIVE_CONTEXT / VALIDATION_WINDOW：
- 禁止插屏
- 禁止冲动加购直达（AIG 必须介入）
- 高压 / 观察窗时不得用“清醒报告”作为强 CTA
- 必须提供免费简版 + 延迟入口

## 1.12.1 No Deceptive Ads Masking
广告必须清晰标识为赞助 / 广告 / 微任务，不得伪装成计算过程。

## 1.12.2 Emergency Bypass Is User-first
急救配额耗尽仍跳过插屏（用户优先），不得羞辱恐吓。

## 1.13 RAG Recency & Conflict Safety
RAG 只能 DETAIL_ONLY；冲突默认 ASK_CLARIFY。

## 1.14 Profile Size Cap
`Target_Profile.json <= 20KB`，确定化裁剪；离线缓存只存 `compact_profile + hash + baseline_stats`。

## 1.15 Persona Is Dynamic, Not Verdict
对方画像必须是：
- 基于当前证据
- 可更新
- 可被新证据修正
- 不等于人格定罪
- 允许 UNKNOWN / MIXED / LOW_CONFIDENCE

## 1.16 Messaging Is Aligned, Not Manipulative
JoyPilot 的话术只能：
- 保持用户真实意图
- 适配对方接收方式
- 受风险门禁限制
- 不允许为了“拿下”而进行人格伪装或操控

## 1.17 Output Priority = Usable First, Then Explain
首屏优先输出顺序固定为：
1. 动态对方画像摘要
2. 一句话判断
3. 当前建议动作
4. Message Bank（如允许）
5. 为什么这样判断
6. 风险提示
7. 更稳的下一步动作

## 1.18 Message Bank Is Standard, Not Optional
适配话术生成是 JoyPilot 标配入口，但它必须是被 Persona Engine + Risk Engine + Safety Gate + Allowed Actions 约束后的输出。

## 1.19 Anti-Projection First
JoyPilot 不得成为“投射放大器”。凡基于读心、模糊意图推断、缺少行为证据的判断，必须自动降置信度并输出反证与备选解释。

## 1.20 Anti-Rumination First
JoyPilot 不得成为“高质量反刍机器”。无新证据重复分析同一 case 时，必须触发摘要模式、反反刍锁和线下重定向，而不是不断生成新话术。

## 1.21 Safety-Routed High-Risk Relationship Handling
一旦出现控制、监视、恐惧、威胁、跟踪、高压支配等迹象，产品必须切换到安全分流模式，而不是继续优化互动表达。

## 1.22 Authenticity Lock
任何话术适配都不得损害用户的真实性、边界、自尊和价值感。系统不能为了提高回复率而鼓励人格迁移或讨好型自我扭曲。

---

# 2. 护城河定义（产品层 / v3.4 重写版）

JoyPilot 护城河 = 六层护城河叠加。

## 2.1 Decision Moat
- User Voice DNA
- Target Baseline
- 行为证据状态机
- Stage Transition Audit
- Radar Console
- Automatic Gate Logging
- Safety Block + Allowed Actions 白名单

## 2.2 Persona Moat
- Dynamic Target Persona Engine
- Relationship Context Detection
- Persona Summary
- Receiver-Aligned Messaging
- Responsiveness Index
- Authenticity Lock

## 2.3 Risk Moat
- J22 Boundary Reset
- J23 Risk-Profile Auto-Assist
- J24 Asymmetric Ledger
- J25 SOP Disclaimer Filter
- J26 Clarity Probe API
- J27 Reality-Anchor Report
- Abuse / Coercive Control / Stalking Router

## 2.4 Evidence Moat
- Counter-Hypothesis + Missing Data Layer
- J28 Evidence Graph
- J29 Outcome Tracker
- J30 Recovery ROI
- Calibrated Explainability
- 审计日志

## 2.5 Behavior Moat
- User Regulation Snapshot
- Anti-Rumination Lock
- Repair vs Exit Router
- JITAI Validation Harness
- Cooldown / Focus Redirect / AIG / Validation Window

## 2.6 Platform Moat
- 通用 AI / OpenClaw 会“写”
- JoyPilot 负责“判、控、限、解释、留证、止损、校准”
- 外部 agent 可以成为执行层，但不能替代 JoyPilot 的判断权与门禁权

## 2.7 一句话护城河定义
**JoyPilot 的护城河不是帮用户更会聊，而是根据聊天记录和对方信息生成动态对方画像，并用可审计、可解释、可止损、可校准的系统，约束用户如何表达、是否继续投入、何时停止加码。**

---

# 3. 产品主形态：Dynamic Target Persona Console

## 3.1 输入端

### 3.1.1 Screenshot Ingestion
流程：
1. 用户上传聊天截图
2. OCR 提取文本
3. 用户确认 / 手动编辑 / 删除敏感内容
4. 文本进入 normalize 流程
5. 结构化会话片段生成
6. 进入画像、风险、阶段、策略引擎

### 3.1.2 Briefing Ingestion
用户补充：
- 对方与用户关系背景
- 是否见过面
- 是否异地
- 是否断联
- 是否涉及金钱 / 礼物 / 投入失衡
- 用户当前目标（STR / LTR / clarify / closure / stop-loss / repair / pause）
- 用户主观感受（焦虑 / 生气 / 反复想发 / 想确认 / 想体面退出）

### 3.1.3 Counterparty Metadata
用户可补充非敏感对方信息：
- 年龄范围
- 城市 / 跨城
- 相识渠道
- 是否线下见面
- 关系持续时长
- 是否曾经暧昧 / 确认 / 分手 / 复联
- 是否存在金钱往来
- 是否存在多次失约
- 是否存在模板式热情 / 商业化迹象
- 是否存在监视 / 支配 / 威胁 / 高压控制迹象

### 3.1.4 User Goal & Style Input
用户可指定：
- 目标模式：STR / LTR / clarify / closure / pause / repair / stop-loss / safety-exit
- 风格模式：CALM_CLEAR / WARM_SUPPORTIVE / PLAYFUL_LIGHT / DIRECT_HONEST / MINIMAL_LOW_EFFORT
- 是否允许 Suggestive Hints（若满足权限）
- 是否希望“边界优先”

### 3.1.5 User Regulation Snapshot Input
轻量用户状态输入：
- 当前是否很想立刻发送
- 当前是否很焦虑 / 很生气 / 很羞耻 / 很想被确认
- 今天是否已经反复看同一段聊天很多次
- 是否昨晚 / 深夜连续复盘
- 是否觉得“我知道不该发但控制不住”

此输入不是心理诊断，只用于状态分流与保护用户。

---

## 3.2 首屏输出顺序（强制）

1. 对方画像摘要
2. 一句话判断
3. 当前建议动作
4. Message Bank（如允许）
5. 为什么这样判断
6. 风险提示
7. 如果不上头，下一步更稳的动作

---

## 3.3 固定输出区块（字段固定、可回归、可审计）

### 3.3.1 基础面板（必须输出）
- `action_light`: 🔴 / 🟡 / 🟢
- `tension_index`: 0–100
- `pressure_score`: 0–100
- `blindspot_risk`: LOW / MEDIUM / HIGH
- `mean_reversion`
- `availability_override`
- `frame_anchor`
- `gearbox_ratio_radar`
- `cooldown_timer`
- `focus_redirect`
- `reciprocity_meter`
- `sunk_cost_breaker`
- `adaptive_tension`
- `suggestive_channel`
- `macro_stage`: S0–S3
- `interest_discriminator_panel`
- `stage_transition`
- `message_bank`: <= 3，可编辑，可能为空

#### 含义约束
- Action Light 决定总动作建议：发 / 不发 / 观察 / 收口 / 暂停
- Tension Index 代表关系拉扯与不确定性，不直接等于风险
- Pressure Score 代表施压风险，不代表“成功率”
- Blindspot Risk 代表用户脑补 / 单方投射风险
- Cooldown Timer 是建议静置时长
- Focus Redirect 是线下替代动作
- Message Bank 是受门禁限制的可发草稿，不是默认永远生成

### 3.3.2 Persona Summary 面板（必须输出）
- `persona.summary`
- `persona.short_label`
- `persona.dynamic_note`
- `persona.confidence_band`: LOW / MID / HIGH
- `persona.fit_mode`: SAFE_MATCH / LOW_PRESSURE_MATCH / BOUNDARY_FIRST / CLARITY_FIRST

#### 允许示例
- 高反馈低兑现型
- 低压慢热型
- 有互动意愿但现实推进不足型
- 高需求低对等型
- 回避退缩型
- 可疑商业化互动型
- 正常但节奏偏慢型

#### 写死要求
- 禁止“渣 / 骗子 / 贱 / 玩弄”类标签
- 必须体现“基于当前证据”
- 必须可被新记录修正

### 3.3.3 目标 / 风格 / 经济 / RAG / Profile / 广告（必须输出）
- `target_goal_mode`: STR | LTR | CLARIFY | CLOSURE | PAUSE | REPAIR | STOPLOSS | SAFETY_EXIT
- `style_mode`: CALM_CLEAR | WARM_SUPPORTIVE | PLAYFUL_LIGHT | DIRECT_HONEST | MINIMAL_LOW_EFFORT
- `battery_quote`
- `rewarded_ads_status`: AVAILABLE | BLOCKED | COOLDOWN | CAP_REACHED
- `interstitial_status`: WILL_SHOW | SKIPPED_BY_ADG | DISABLED_BY_USER
- `validation_window`: active / ends_at / reason
- `profile_meta`: profile_size_bytes / profile_trimmed / trim_reason
- `rag_meta`: rag_status / recency_bias_applied / cutoff_days / conflict_detected / used_for
- `ad_eligibility`: NONE | REWARDED | INTERSTITIAL + ad_block_reason
- `free_emergency_pass`: remaining_today / used_today / daily_cap
- `anti_impulse_gate`: ON / OFF + reason_codes
- `receiver_alignment_level`: LOW / MEDIUM / HIGH
- `expression_budget`: LOW / MID / HIGH
- `message_generation_mode`: DIRECT_USER_INTENT / PERSONA_ALIGNED / BOUNDARY_LOCKED

### 3.3.4 Safety Block（必须输出）
- `safety.status`: OK | BLOCKED
- `safety.block_reason`: NONE | HARASSMENT_RISK | NO_CONTACT_SIGNAL | SCAM_SUSPECTED | ABUSE_RISK | STALKING_RISK
- `safety.allowed_to_generate_messages`: bool
- `safety.note`

#### 写死规则
- BLOCKED 时 `message_bank = []`
- BLOCKED 时不生成任何变体话术
- 只允许输出：安全提示 / 止损建议 / 现实核验建议 / 自我稳定建议 / 安全资源入口
- `safety.note` 必须中性，不得羞辱

### 3.3.5 J23 风险画像面板（必须输出）
- `relationship.context_detected`: UNKNOWN | PRE_MEETUP | DATING | TRANSACTIONAL | EX_PARTNER
- `relationship.context_user_confirmed`: bool
- `relationship.context_confidence`: 0–100
- `target_persona.risk_profile`: SAFE | HIGH_DEMAND | ASYMMETRIC_INVESTMENT | AVOIDANT | SCAM_SUSPECTED
- `target_persona.confidence_score`: 0–100
- `target_persona.secondary_profile`
- `target_persona.counter_evidence[]`
- `target_persona.primary_drivers[]`
- `target_persona.false_positive_caution`
- `target_persona.recommended_alignment`: SAFE_MATCH | CLARITY_FIRST | BOUNDARY_FIRST | NO_GENERATION

### 3.3.6 Explain Card + Opt-out（必须输出）
- `auto_overrides.active`
- `auto_overrides.forced_style`: CALM_CLEAR | NEUTRAL_BRIEF | BOUNDARY_FIRST
- `auto_overrides.evidence_signals[]`
- `auto_overrides.can_disable`
- `auto_overrides.disable_cost_battery`
- `auto_overrides.risk_banner_level`: NONE | YELLOW
- `auto_overrides.persona_fit_reason`
- `auto_overrides.receiver_alignment_reason`
- `auto_overrides.boundary_preserved`: bool
- `auto_overrides.no_manipulation_guard`: bool

#### 写死要求
- note 禁止人格定性
- 只能解释为什么当前风格更稳
- 必须解释不确定性来源

### 3.3.7 J22 边界重置协议（必须输出）
- `recovery_protocol.state`: NOT_ACTIVE | BOUNDARY_RESET_ACTIVE | PING_READY | RECOVERED | RECOMMEND_CLOSURE | RECOMMEND_NO_CONTACT
- `recovery_protocol.can_exit`: true
- `recovery_protocol.reset_ends_at`
- `recovery_protocol.ping_attempts_left`
- `recovery_protocol.violation_budget_remaining`
- `recovery_protocol.violation_cost_battery`
- `recovery_protocol.override_output_token_cap`
- `recovery_protocol.instruction`

#### 触发条件
- 连续高压主动
- 对方连续低回应 / 失约 / 不兑现
- 用户主观上头
- 已出现错付
- 已触发 NO_CONTACT 风险
- 高风险对象仍想继续加码
- 无新证据反复复盘

### 3.3.8 J24 非对称投资账本（必须输出）
- `ledger.window`: 24h / 7d
- `ledger.input`: money_cents / attention_score / urgency_score
- `ledger.output`: commitment_events / followthrough_events / clarity_score / affect_score
- `ledger.metrics`: imbalance_ratio / net_flow / state（OK | WATCH | MARGIN_CALL）
- `ledger.ui`: bar_mode + note
- `ledger.delta_vs_baseline`
- `ledger.user_overextension_risk`
- `ledger.stoploss_hint`
- `ledger.commitment_gap_band`: LOW / MID / HIGH

#### 权重原则
- `affect_score` 低权重
- `commitment_events` 高权重
- `followthrough_events` 高权重
- `clarity_score` 中高权重
- 不存原文，只存汇总
- 若金钱项出现，优先提升风险解释权重

### 3.3.9 Responsiveness Index（新增，必须输出）
- `responsiveness.understanding`
- `responsiveness.validation`
- `responsiveness.caring`
- `responsiveness.listening_signal`
- `responsiveness.acceptance_signal`
- `responsiveness.gratitude_signal`
- `responsiveness.investment_signal`
- `responsiveness.safety_signal`
- `responsiveness.overall_band`: LOW | MID | HIGH

#### 定义
回应性指数不是“有没有兴趣”，而是“对方是否让我感到被理解、被认可、被在乎、被认真接住”。

#### 写死原则
- 热度高 ≠ 回应性高
- 情绪价值高 ≠ 现实支持高
- Interest 与 Responsiveness 必须分开输出

### 3.3.10 J25 商业 SOP 防火墙（必须输出）
- `sop_filter.window_days`: 7
- `sop_filter.hits`
- `sop_filter.total_hits`
- `sop_filter.risk_escalation`: NONE | COMMERCIAL_SOP_PATTERN
- `sop_filter.evidence_signals[]`

#### 模式类型
- 模板式热情
- 高频情绪价值 + 低现实推进
- 节点式索取
- 模糊承诺 + 延后兑现
- 断联后统一模板回流
- 多次出现“下次”“改天”“忙完”但无后续落实

#### 写死要求
- 模式提示不等于定罪
- 不输出指控性结论
- 只输出：提高警惕 / 建议核验 / 暂缓投入

### 3.3.11 J26 现实核验探针（必须输出）
- `probes.available`
- `probes.items[]`
  - `L1_TIME`
  - `L2_RECIPROCITY`
  - `L3_CLOSURE`

#### 每个 probe 必须包含
- `level`
- `intent`
- `template`
- `when_to_use`
- `allowed_contexts`
- `pressure_budget`
- `expected_outcome_range`
- `followup_rule`

#### 三类探针定义
- L1_TIME：时间核验
- L2_RECIPROCITY：对等投入核验
- L3_CLOSURE：体面收口

#### 写死要求
- 三段式低压力
- 不逼答复
- 不威胁
- 给出口
- Safety BLOCK 或 NO_CONTACT 或 STALKING / ABUSE 风险时必须 false

### 3.3.12 J27 现实锚点报告（必须输出）
- `reality_anchor_report.available`
- `reality_anchor_report.tone`: NEUTRAL_FACTUAL | DIRECT_CLEAR
- `reality_anchor_report.access`: FREE_BRIEF | PREMIUM_FULL
- `reality_anchor_report.delay_gate_sec`
- `reality_anchor_report.brief_points[]`
- `reality_anchor_report.full_text`

#### 写死要求
- 禁止辱骂 / 羞辱 / 嘲讽
- 高压 / 观察窗 / 冷却锁命中时不得强推付费
- 清醒报告必须基于证据，而不是情绪宣判
- 必须包含“这份判断最可能错在哪里”段落

### 3.3.13 Counter-Hypothesis + Missing Data Layer（新增，必须输出）
- `uncertainty_band`: LOW | MID | HIGH
- `missing_evidence[]`
- `alternative_hypotheses[]`
- `disconfirming_signals[]`
- `mind_reading_ratio`
- `confidence_cap`

#### 写死规则
- 如果判断主要来自未明说意图推断，而不是行为证据，`confidence_cap <= MID`
- 必须同时给出至少 2 个备选解释（如适用）
- 必须说明当前最缺什么证据
- 不允许把“他没回我”直接解释成单一动机

### 3.3.14 User Regulation Snapshot（新增，必须输出）
- `user_state.arousal_level`
- `user_state.urge_to_send_now`
- `user_state.need_for_reassurance`
- `user_state.anger_level`
- `user_state.shame_level`
- `user_state.loop_risk`
- `user_state.can_tolerate_ambiguity`
- `user_state.routing_mode`: STABILIZE_FIRST | MESSAGE_OK | PAUSE_ONLY

#### 路由规则
- 高 arousal + 高 urge_to_send_now -> 强制 CALM_CLEAR / BOUNDARY_FIRST
- 高 reassurance need -> 降低“再发一条试试”概率
- 高 shame / 高 panic -> 暂时不出 BOLD_HONEST
- 高 loop_risk -> 启动 Anti-Rumination Lock

### 3.3.15 Abuse / Coercive Control / Stalking Router（新增，必须输出）
- `abuse_risk.status`: NONE | WATCH | HIGH
- `abuse_risk.control_signals[]`
- `abuse_risk.monitoring_signals[]`
- `abuse_risk.fear_signal`
- `abuse_risk.resource_mode`: OFF | ON
- `abuse_risk.message_generation_allowed`: bool

#### 写死规则
- 一旦 `abuse_risk >= WATCH`，禁止任何鼓励继续拉扯的话术
- 一旦 monitoring / stalking 信号成立，`probe_generator = false`
- 优先输出：安全建议、证据保留建议、trusted contact、资源入口、账号与设备暴露降低建议

### 3.3.16 Anti-Rumination Lock（新增，必须输出）
- `rumination.same_case_open_count_24h`
- `rumination.no_new_evidence_reanalysis_count`
- `rumination.loop_risk`
- `rumination.forced_reflection_break_until`
- `rumination.offline_redirect_task`
- `rumination.summary_mode_active`: bool

#### 写死规则
- 同一 case 无新证据，24h 内重复分析 >= 3 次 -> 自动摘要模式
- 摘要模式下：不再生成新 message bank，只显示上次结论 + 一条现实锚点 + 一个线下动作
- 必须等待新证据或计时结束，才能恢复完整分析

### 3.3.17 Repair vs Exit Router（新增，必须输出）
- `relationship_route.current`: REPAIR | CLARIFY | PAUSE | CLOSE | SAFETY_EXIT | STOPLOSS
- `relationship_route.why`
- `relationship_route.allowed_moves[]`
- `relationship_route.forbidden_moves[]`

#### 写死规则
- 当 `context_detected = DATING` 且 `trust_tier >= T1` 且问题本质是误解 / 冲突时，优先 REPAIR
- 当存在监视 / 恐惧 / 明显控制时，优先 SAFETY_EXIT
- 当 Ledger 与 Responsiveness 双低且 Counter-Hypothesis 已充分排除时，优先 STOPLOSS / CLOSE

### 3.3.18 J28 Evidence Graph（必须输出）
- `evidence_graph.version`
- `evidence_graph.nodes[]`
- `evidence_graph.edges[]`
- `evidence_graph.dominant_factors[]`
- `evidence_graph.counter_evidence[]`
- `evidence_graph.stability_score`
- `evidence_graph.last_material_change_at`
- `evidence_graph.path_to_risk[]`
- `evidence_graph.path_to_recommendation[]`

### 3.3.19 J29 Outcome Tracker（必须输出）
- `outcome_tracker.last_action_type`
- `outcome_tracker.was_sent`
- `outcome_tracker.reply_received`
- `outcome_tracker.reply_latency_bucket`
- `outcome_tracker.clarity_changed`
- `outcome_tracker.followthrough_happened`
- `outcome_tracker.money_request_after_probe`
- `outcome_tracker.user_regret_self_report`
- `outcome_tracker.emotional_state_delta`

### 3.3.20 J30 Recovery ROI Engine（必须输出）
- `roi.time_saved_hours`
- `roi.money_saved_cents`
- `roi.attention_saved_score`
- `roi.bad_escalation_avoided_count`
- `roi.recovery_days_shortened_est`

### 3.3.21 J31 Trust Tier Engine（必须输出）
- `trust_tier.current`: T0 | T1 | T2 | T3
- `trust_tier.upgrade_conditions[]`
- `trust_tier.downgrade_triggers[]`
- `trust_tier.days_stable`
- `trust_tier.lock_reason`

#### 等级定义
- T0：高噪音 / 不明朗 / 不建议加码
- T1：可低成本互动，不可高投入
- T2：有持续性证据，可适度推进
- T3：有现实兑现，可进入更高信任动作

### 3.3.22 Receiver-Aligned Messaging 面板（必须输出）
- `receiver_aligned.available`
- `receiver_aligned.intent_type`: CARE | INVITE | CLARIFY | CLOSE | PAUSE | BOUNDARY
- `receiver_aligned.match_basis[]`
- `receiver_aligned.variants[]`
- `receiver_aligned.forbidden_moves[]`
- `receiver_aligned.boundary_guard_note`

#### 允许做的事
- 同样表达关心，生成低压版 / 稳定版 / 边界版
- 同样发出邀约，生成慢热对象适配版 / 正常推进版 / 低负担版
- 同样做澄清，生成低压力 probe 版本
- 同样做收口，生成体面、不过度索取的版本

#### 禁止做的事
- 操控
- 诱导服从
- 人格伪装
- 模仿“对方最喜欢的人设”去拿下对方
- 利用弱点打点
- 用高情绪价值换现实推进

### 3.3.23 Authenticity Lock（新增，必须输出）
- `authenticity_lock.passed`: bool
- `authenticity_lock.risk_reason`
- `authenticity_lock.forbidden_persona_shift[]`

#### 写死规则
- 不允许从“表达适配”滑向“人格伪装”
- 不允许为了提高回复率而让用户牺牲边界、自尊、价值感
- 若用户意图本身不真实，优先建议改写为诚实表达，而非优化伪装表达

### 3.3.24 Message Bank（重构为标配入口）
`message_bank` 是 JoyPilot 标配入口，但必须满足以下约束：
- 默认 1–3 条
- 每条可编辑
- 每条必须标注：使用场景、风险等级、不建议何时发送
- 只允许路线：STABLE / NATURAL / BOLD_HONEST
- BLOCKED 时必须为空
- Anti-Rumination Summary 模式下不得生成新 message bank
- 需要通过 Authenticity Lock

---

# 4. 低压力好感框架（写死）

三段式表达：
1. 我（观察 / 感受）
2. 不索取
3. 给出口

## 4.1 硬拦截
以下内容一律进入 Safety Block 或至少强制降级：
- 施压
- 控诉
- 羞辱
- 惩罚式冷落
- 服从测试
- 阴阳怪气
- 高压试探
- 逼露底牌
- “你到底什么意思”式审讯型表达
- “不回复就是默认”式强迫性框架

## 4.2 低压力验证器
对所有 message_bank / probes / clarity messages 运行 `low_pressure_validator`：
- 是否含“必须 / 立刻 / 你到底 / 给我个说法”
- 是否含控诉句式
- 是否含威胁退出但实为施压
- 是否含道德绑架
- 是否含低自尊讨好式高投入

---

# 5. 用户画像分层（产品与商业优先级）

## 5.1 代聊型轻度用户
特征：
- 只想知道“现在怎么回”
- 不愿看复杂分析
- 价格敏感
- 很容易被别的 AI 替代

策略：
- 用 Message Bank 拉新
- 不作为核心营收层

## 5.2 暧昧解读型用户
特征：
- 想知道对方有没有兴趣
- 容易脑补
- 会反复查看历史聊天

策略：
- Persona Summary + Stage + Interest Discriminator + Counter-Hypothesis
- 是主增长层

## 5.3 错付止损型用户
特征：
- 已出现时间 / 金钱 / 情绪投入失衡
- 不是不会聊，而是舍不得停

策略：
- J24 Ledger + J22 Reset + J30 ROI
- 核心付费层

## 5.4 高风险怀疑型用户
特征：
- 怀疑自己遇到套路 / 高需求 / 商业化 / scam
- 很看重系统是否稳、是否不乱判

策略：
- J23 + J25 + J26 + J27
- 品牌口碑层

## 5.5 断联复盘 / 边界重置型用户
特征：
- 已情绪失稳
- 会反复打开产品确认自己该不该继续发

策略：
- J22 Reset + J27 Reality Anchor + Anti-Rumination Lock
- 强留存层

## 5.6 已进入关系但沟通卡住型用户
特征：
- 不是风险对象，而是冲突 / 误解 / 沟通卡顿
- 需要修复而不是一刀切退出

策略：
- Repair vs Exit Router + Responsiveness Index
- 是提升产品“不是只会劝退”的关键层

## 5.7 高危安全型用户
特征：
- 出现控制 / 监视 / 跟踪 / 恐惧 / 高压支配

策略：
- Abuse Router 直接分流
- 停止 message 生成
- 输出安全建议与资源入口

---

# 6. 谁会被其他 AI / OpenClaw 冲击，谁不会

## 6.1 会被冲击的部分
- 纯话术生成
- 语气润色
- 普通“高情商回复”
- 多平台自动发消息

## 6.2 不容易被冲击的部分
- 动态对方画像
- Baseline-first 解读
- Counter-Hypothesis + Missing Data
- User Regulation Snapshot
- Responsiveness Index
- Risk Profile
- Asymmetric Ledger
- SOP Pattern Filter
- Boundary Reset
- Reality Probes
- Reality Anchor Report
- Abuse / Stalking Router
- Evidence Graph
- Outcome Tracker
- Recovery ROI
- Anti-Rumination Lock
- Authenticity Lock

## 6.3 战略结论
JoyPilot 不怕别的 AI 抢“帮写一句话”，怕的是把自己卖成“帮写一句话”。

---

# 7. 系统架构（组件与强制数据流）

## 7.1 组件

### Client（Web→PWA）
包含：
- 输入确认层
- OCR 校对层
- Premium 同意控件
- Transactional 确认弹窗
- Persona Summary Card
- Radar Dashboard
- Explain Card
- Boundary Reset 面板
- Ledger / SOP / Probe / Report 面板
- Responsiveness 面板
- Counter-Hypothesis 面板
- User Regulation Snapshot 面板
- Abuse Router 安全面板
- Evidence Graph 面板
- Outcome / ROI / Trust Tier 面板
- Ad / Battery 展示层

### API（FastAPI）
包含：
- entitlement
- consent
- audit_logger
- normalize_service
- signals_service
- baseline_service
- behavior_event_extractor
- goal_router
- style_switcher
- user_regulation_snapshot_engine
- dynamic_target_persona_engine
- responsiveness_index_engine
- counter_hypothesis_engine
- risk_profile_classifier
- asymmetric_ledger_engine
- sop_disclaimer_filter
- abuse_router
- anti_rumination_lock_engine
- receiver_aligned_messaging_engine
- authenticity_lock_engine
- probe_generator
- reality_anchor_reporter
- evidence_graph_engine
- outcome_tracker
- recovery_roi_engine
- trust_tier_engine
- safety_engine
- monetization / AIG / ADG
- rag_retriever

## 7.2 Core Engine（纯函数优先、可测试）

完整数据流：

`J1 normalize`
-> `J2 signals`
-> `J9 baseline`
-> `BehaviorEventExtract`
-> `J16 goal_router`
-> `user_regulation_snapshot_engine`
-> `counter_hypothesis_engine`
-> `J23 risk_profile_classifier`
-> `responsiveness_index_engine`
-> `J24 asymmetric_ledger_engine`
-> `J25 sop_disclaimer_filter`
-> `abuse_router`
-> `J28 evidence_graph_engine`
-> `entitlement_gate`
-> `consent_gate`
-> `J21 battery_quote`
-> `AIG`
-> `J17 profile_store`
-> `J18 rag_retriever`
-> `J3 state_estimate`
-> `J19 support_resistance -> validation_window`
-> `dynamic_target_persona_engine`
-> `repair_vs_exit_router`
-> `anti_rumination_lock_engine`
-> `style_switcher`
-> `receiver_aligned_messaging_engine`
-> `authenticity_lock_engine`
-> `dashboard_pack`
-> `stage_engines`
-> `strategies`
-> `J22 boundary_reset_engine`
-> `J26 probe_generator`
-> `J27 reality_anchor_reporter`
-> `J29 outcome_tracker`
-> `J30 recovery_roi_engine`
-> `J31 trust_tier_engine`
-> `J7 safety_final_judgement`
-> `J11/J12/J14/J20`
-> `ADG v2 -> rewarded_ads_controller`
-> `pack_response`
-> `audit_logger`

## 7.3 强制顺序说明
- Persona 必须在 Message Bank 之前
- Safety 最终裁决必须在 pack_response 前
- AIG 必须在购买路径前
- Abuse Router 必须在 Probe 和 Message 之前
- Anti-Rumination Lock 必须在 Message 生成前
- Authenticity Lock 必须在 Message 输出前
- Message Bank 不是独立模块，必须依附 persona + safety + boundary + expression_budget + authenticity

---

# 8. 详细模块定义

## 8.1 J16 Goal Router
作用：根据用户目标模式决定话术倾向、probe 类型、是否强调 clarity / romance / closure / stop-loss / repair / safety-exit。

输入：
- 用户目标
- 当前阶段
- 风险画像
- 边界状态
- Validation Window 状态
- User Regulation Snapshot

输出：
- `selected_goal_mode`
- `goal_priority`
- `goal_conflict_flag`
- `goal_to_strategy_map`

写死规则：
- 风险高时不得让 romantic / 推进目标压过止损目标
- 目标冲突时优先 clarity / safety / stop-loss
- 已进入关系且是误解类问题时，允许 repair 优先

## 8.2 Style Switcher
作用：根据用户主观偏好 + 画像适配 + 风险强制覆盖，输出最终风格。

风格枚举：
- CALM_CLEAR
- WARM_SUPPORTIVE
- PLAYFUL_LIGHT
- DIRECT_HONEST
- MINIMAL_LOW_EFFORT
- NEUTRAL_BRIEF（仅 override）
- BOUNDARY_FIRST（仅 override）

写死规则：
- override 优先级高于用户偏好
- BLOCKED 时 style 仅影响说明文字，不影响 message bank
- 高 arousal 时禁止 PLAYFUL_LIGHT 和高张力风格

## 8.3 Dynamic Target Persona Engine
作用：根据聊天记录、Briefing、行为事件、历史基线，输出动态对方画像。

输入：
- 对话结构化文本
- 互动节奏特征
- 兑现 / 失约事件
- 投入 / 索取事件
- 线下推进 / 拖延信息
- 用户补充信息
- Counter-Hypothesis Layer

输出：
- `persona.summary`
- `persona.short_label`
- `relationship.context_detected`
- `risk_profile`
- `fit_mode`
- `confidence_score`
- `counter_evidence`
- `dynamic_note`

画像原则：
- 可更新，不可定罪
- 必须有反证位
- 必须允许未知 / 混合态

## 8.4 Receiver-Aligned Messaging Engine
作用：把“用户真实意图”翻译成“更适合对方接收的表达版本”。

输入：
- 用户意图
- persona
- context
- stage
- pressure_score
- safety
- goal_mode
- style_mode
- responsiveness_index
- user_regulation_snapshot

输出：
- `variants[]`
- `intent_type`
- `alignment_reason`
- `forbidden_moves`
- `boundary_guard_note`

执行要求：
- 不改变用户核心意图
- 不鼓励讨好型高投入
- 不根据“对方喜欢什么人设”让用户伪装人格
- 只做表达适配，不做人格表演

## 8.5 Counter-Hypothesis Engine
作用：防止系统把模糊信号读成单一结论。

输出：
- 备选解释
- 缺失证据
- 反证列表
- 置信度上限

规则：
- 未明说意图推断必须降置信度
- 若行为证据不足，禁止输出高确定语气

## 8.6 User Regulation Snapshot Engine
作用：识别用户是否处于高 arousal / 高 reassurance seeking / 高 loop risk 状态。

目标：
- 保护用户自己
- 避免上头时继续生成高风险动作

## 8.7 Responsiveness Index Engine
作用：评估对方是否表现出“理解 / 认可 / 在乎 / 接住”的回应性，而非只看热度。

目标：
- 将“有兴趣”和“让我感觉被回应”拆开
- 让产品更像关系质量分析，而不是热度分析

## 8.8 Abuse / Coercive Control / Stalking Router
作用：识别高危关系信号并切换到安全分流模式。

信号示例：
- 控制交友、控制行动、控制表达
- 强迫定位共享、设备监视、账号检查
- 威胁、恐吓、恐惧感
- 反复出现在不该出现的地方

输出：
- 风险等级
- 安全建议
- message generation allowed = false（必要时）

## 8.9 J22 Boundary Reset Protocol
作用：在用户上头或关系高压时，提供软门禁、摩擦成本和止损复盘。

核心机制：
- 冷却倒计时
- 违规预算
- 违规电池成本
- 输出 token cap 限制
- ping attempt 限额
- closure / no-contact 推荐

## 8.10 J23 Risk-Profile Auto-Assist
作用：区分关系上下文与对象风险，不把“上下文”误等同于“人格定性”。

分类：
- SAFE
- HIGH_DEMAND
- ASYMMETRIC_INVESTMENT
- AVOIDANT
- SCAM_SUSPECTED

要求：
- context 和 risk 分离
- Explain + Opt-out
- Transaction Mode Monetary Gate
- Allowed Actions 白名单

## 8.11 J24 Asymmetric Ledger
作用：把情绪、时间、金钱投入和对方兑现放到同一个账本里。

核心价值：
不是看“谁更爱”，而是看“谁更投入、谁更兑现”。

## 8.12 J25 SOP Disclaimer Filter
作用：识别商业 SOP、模板化热情、节点式回流、情绪价值包装索取。

输出要求：
只能提示风险，不得指控。

## 8.13 J26 Clarity Probe API
作用：在不施压的前提下，帮用户核验现实。

三个层级：
- 时间核验
- 对等投入核验
- 体面收口

## 8.14 J27 Reality-Anchor Report
作用：给用户一份数据化、无羞辱、非胁迫的现实报告。

目标：
不是骂醒用户，而是让用户在情绪退去后还能看见证据。

## 8.15 J28 Evidence Graph
作用：把所有判断组织成证据图谱，提升可信度与不可替代性。

## 8.16 J29 Outcome Tracker
作用：记录建议后的现实结果，为模型闭环、报告和 ROI 提供支撑。

## 8.17 J30 Recovery ROI Engine
作用：把 JoyPilot 的价值从“帮你回消息”升级为“帮你少损失”。

## 8.18 J31 Trust Tier Engine
作用：输出长期可信度等级，让用户知道“是否值得继续更高投入”。

## 8.19 Anti-Rumination Lock Engine
作用：防止用户无新证据反复分析同一关系，导致产品成为反刍强化器。

## 8.20 Repair vs Exit Router
作用：区分当前更适合修复、澄清、暂停、收口还是安全退出。

## 8.21 Authenticity Lock Engine
作用：在所有话术生成前，检查表达是否违背用户真实性与边界。

## 8.22 J21 Battery Economy（升级版）
核心定义：电池不是 token，而是“可消费的决策分析额度”。

分层：
- `B0`: 广告电池，只能低风险基础分析
- `B1`: 订阅电池，中阶功能
- `B2`: 付费电池，高阶报告与复盘
- `B3`: 急救电池，不可被广告套利覆盖

写死规则：
- 广告不能稳定套利高价值功能
- 高压场景不能把广告当强 CTA
- 电池消耗必须体现真实成本结构

## 8.23 JITAI Validation Harness
作用：把 cooldown、delay_gate、AIG 提示、push、summary mode 等当成需要被验证的行为元件，而不是默认有效。

输出：
- `jitai_rule_version`
- `microrandomization_eligible`
- `harm_weighted_outcome`
- `regret_after_send`
- `send_cancellation_rate`
- `cooldown_completion_rate`

主指标不得使用 CTR，必须优先：
- regret reduction
- boundary adherence
- escalation avoided
- unreciprocated investment reduction

---

# 9. Contracts v3.4（字段 / 默认值 / 枚举 / 排序写死）

## 9.1 顶层 Response 固定结构
```json
{
  "meta": {},
  "dashboard": {},
  "persona": {},
  "message_bank": [],
  "safety": {},
  "relationship": {},
  "auto_overrides": {},
  "recovery_protocol": {},
  "ledger": {},
  "responsiveness": {},
  "sop_filter": {},
  "probes": {},
  "reality_anchor_report": {},
  "counter_hypothesis": {},
  "user_state": {},
  "abuse_risk": {},
  "rumination": {},
  "relationship_route": {},
  "receiver_aligned": {},
  "authenticity_lock": {},
  "evidence_graph": {},
  "outcome_tracker": {},
  "roi": {},
  "trust_tier": {}
}
```

## 9.2 允许 LLM 写的字段
仅允许以下文本字段被 LLM 生成：
- `persona.summary`
- `persona.dynamic_note`
- `message_bank[].text`
- `safety.note`
- `recovery_protocol.instruction`
- `ledger.ui.note`
- `reality_anchor_report.brief_points[]`
- `reality_anchor_report.full_text`
- `auto_overrides.evidence_signals[].note`
- `counter_hypothesis.alternative_hypotheses[]`（可控模板化）
- `focus_redirect`
- `rumination.offline_redirect_task`

其余字段全部由规则或确定性逻辑产生。

## 9.3 默认值规则
- 所有 bool 必须有默认值
- 所有 enum 必须限定集合
- 所有数组默认 `[]`
- 所有说明文字默认 `""`
- 未知不得输出 null，统一使用 UNKNOWN / NONE / NOT_ACTIVE / [] / 0

## 9.4 排序规则
- `message_bank` 按 STABLE -> NATURAL -> BOLD_HONEST
- `evidence_signals` 按 weight 降序
- `probes` 按 L1 -> L2 -> L3
- `counter_evidence` 出现在 `dominant_factors` 之后
- `alternative_hypotheses` 按 plausibility 降序

---

# 10. 前端显示规范

## 10.1 首屏
- Persona Summary 卡片置顶
- Message Bank 必须首屏可见（如允许）
- 风险灯与是否建议发送必须首屏可见
- Explain Card 折叠但默认一屏内可见入口
- 高压状态时先显示降速建议，再显示话术
- Summary 模式下不显示新 message_bank

## 10.2 Secondary Panels
- Ledger
- Responsiveness
- SOP Filter
- Probe
- Reality Report
- Counter-Hypothesis
- User State
- Safety / Abuse Router
- Evidence Graph
- Outcome / ROI / Trust Tier

## 10.3 CTA 规则
- 高压 / 冷却锁 / 验证窗：禁强刺激 CTA
- 免费用户优先看到 Brief，不先弹付费墙
- Rewarded Ads 只能出现在合规、低压、非敏感路径
- Abuse / Stalking 风险下不展示付费推进 CTA

---

# 11. 商业化设计（最终版）

## 11.1 免费层：Persona Brief + Radar + 1 条话术
给：
- Persona Summary
- 一句话判断
- Action Light
- 风险简版
- 1 条可发话术
- 简版 Reality Report
- 基础 cooldown guidance

## 11.2 Plus 层：Clarity & Messaging
解锁：
- 3 条 Message Bank
- Receiver-Aligned Messaging 全部变体
- 历史对比
- Probe Pack
- Outcome Tracker
- Counter-Hypothesis 完整版

## 11.3 Pro 层：Risk & Stop-Loss
解锁：
- J23 深度画像
- J24 Ledger 完整窗
- Responsiveness 完整指数
- J25 SOP 详解
- J28 Evidence Graph
- J30 ROI
- J31 Trust Tier
- Anti-Rumination 历史视图

## 11.4 Expert 层：Report & Export
解锁：
- PDF 报告
- 时间轴复盘
- 证据图谱导出
- case 管理
- 多关系管理
- 安全路径记录导出（受高权限控制）

---

# 12. 北极星指标（写死）

## 12.1 主北极星
- `bad_escalation_avoided_rate`
- `unreciprocated_investment_reduced`
- `clarity_gained_rate`
- `recovery_time_reduced`
- `user_regret_reduction_score`

## 12.2 副指标
- `message_bank_send_rate`
- `probe_use_rate`
- `boundary_reset_completion_rate`
- `premium_conversion_after_risk_event`
- `free_brief_to_return_7d`
- `trust_tier_movement_30d`
- `summary_mode_activation_rate`
- `same_case_reanalysis_drop_rate`
- `abuse_router_safe_exit_entry_rate`

---

# 13. Fixtures（v3.4 目录与必测用例）

## 13.1 目录
- `fixtures/contract`
- `fixtures/persona`
- `fixtures/receiver_aligned_messaging`
- `fixtures/stage_transitions`
- `fixtures/goal_router`
- `fixtures/validation_window`
- `fixtures/profile_store`
- `fixtures/rag`
- `fixtures/monetization`
- `fixtures/safety`
- `fixtures/risk_profile`
- `fixtures/boundary_reset`
- `fixtures/ledger`
- `fixtures/responsiveness`
- `fixtures/sop_filter`
- `fixtures/probes`
- `fixtures/reality_report`
- `fixtures/counter_hypothesis`
- `fixtures/user_state`
- `fixtures/abuse_router`
- `fixtures/anti_rumination`
- `fixtures/repair_exit_router`
- `fixtures/authenticity_lock`
- `fixtures/evidence_graph`
- `fixtures/outcome_tracker`
- `fixtures/roi`
- `fixtures/trust_tier`
- `fixtures/jitai_validation`

## 13.2 要求
- 每模块 golden >= 3
- 每个 golden 派生 neg >= 3
- 每模块 redteam >= 3
- 必断言：
  - `reason_codes`
  - `feature_status`
  - `dashboard`
  - `message_bank presence/absence`
  - `safety final judgement`
  - `output order deterministic`
  - `authenticity_lock`
  - `summary_mode transitions`

## 13.3 重点红队场景
- 用户要求用服从测试逼对方表态
- 用户要求毒舌羞辱清醒报告
- 对方明显无回应却继续索取 message bank
- 用户试图绕过 Safety Block
- 用户想用 Receiver-Aligned Messaging 做人格伪装
- 高压场景强行弹插屏
- 广告电池试图解锁高阶报告
- 敏感语境绕过 consent_gate
- 无新证据 24h 内重复分析 5 次仍试图生成新 message
- 出现监视 / 控制 / 恐惧信号却仍生成“再试一次”话术
- 高 reassurance seeking 状态下仍生成高推进表达

---

# 14. 对内叙事与执行口径

## 14.1 对用户
**JoyPilot 会根据聊天记录和对方信息，生成一个可解释的动态对方画像，判断这段关系的风险和投入价值，并给出当前最适合发送的话术。**

## 14.2 对团队
**话术是前台商品，风控是后台引擎；用户先为“现在怎么回”而来，最后因为“这个系统能帮我少犯错、少错付、少上头”而留下。**

## 14.3 对商业
**JoyPilot 不靠“帮用户更会聊”赚钱，而是靠“先看清对方画像，再用可审计、可解释、可止损、可校准的系统帮用户少误判、少错付、少消耗”赚钱。**

## 14.4 对 AI / 开发执行
- 先 contract 后实现
- 先 deterministic rules 后 LLM 润色
- 所有 message output 必须通过：Safety -> User State -> Abuse Router -> Anti-Rumination -> Persona -> Authenticity Lock
- 永远不得把“提高回复率”作为唯一优化目标
- 高风险场景以止损优先，而不是互动优化优先

---

# 15. 最终方案状态

**LOCKED & CLINICALLY-CALIBRATED & MOAT-READY（v3.4 最终版）**

本版可直接拆分为以下工程产物：
1. `contracts_v3_4.py`
2. `core_pipeline_v3_4.md`
3. `frontend_console_spec_v3_4.md`
4. `fixtures_matrix_v3_4.md`
5. `behavior_validation_plan_v3_4.md`
6. `safety_routing_spec_v3_4.md`

