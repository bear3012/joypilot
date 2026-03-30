# JoyPilot 前端实施方案（后端口径对齐版）

> **文档定位**：本文档是面向前端开发者的口径锁定文档。
> 所有字段名、枚举值、请求结构、响应结构均以 `MASTER_PLAN_CONSOLIDATED.md` 和后端代码为唯一真相源。
> **前端不得自行发明字段名、枚举值、接口路径，一律以本文档为准。**
>
> 技术栈：Next.js 15 (App Router) + React + Tailwind CSS + shadcn/ui
> 后端 Base URL：通过 `.env.local` 中 `NEXT_PUBLIC_API_BASE_URL` 配置（开发环境 `http://localhost:8000`）

---

## 第一章：类型契约（前端 TypeScript 类型定义口径）

> 以下类型定义必须与后端 `contracts.py` 完全对齐，不得增删字段，不得修改枚举值大小写。

### 1.1 枚举类型（全部大写字符串）

```
Tier          = "FREE" | "VIP"
Mode          = "REPLY" | "RELATIONSHIP"
GateDecision  = "ALLOW" | "DEGRADE" | "BLOCK"
SafetyStatus  = "SAFE" | "CAUTION" | "BLOCKED"
Recommendation = "YES" | "WAIT" | "NO"
EvidenceQuality = "SUFFICIENT" | "LOW_INFO" | "INSUFFICIENT"
RouteTone     = "STABLE" | "NATURAL" | "BOLD_HONEST"
MySide        = "LEFT" | "RIGHT"
ConstraintRiskLevel = "LOW" | "MEDIUM" | "HIGH"
ConstraintStrategyHint = "PUSH" | "MAINTAIN" | "DEGRADE" | "WAIT"
```

### 1.2 核心请求类型

**`ScreenshotFrame`**（`POST /upload/prepare` 的截图子项）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image_id` | string | ✅ | 前端生成的唯一 ID（推荐 UUID） |
| `upload_index` | number \| null | 否 | 用户在相册选图的顺序编号（从 1 开始），前端负责生成 |
| `timestamp_hint` | string \| null | 否 | ISO 8601 格式时间字符串，作为排序备用（无 upload_index 时后端使用） |
| `left_text` | string | 否 | 截图左侧对话文字，默认空字符串 |
| `right_text` | string | 否 | 截图右侧对话文字，默认空字符串 |

**`UploadPrepareRequest`**（`POST /upload/prepare` 请求体）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | ✅ | 用户唯一 ID（前端从 localStorage 取） |
| `target_id` | string | ✅ | 当前分析对象 ID（前端从 localStorage 取） |
| `tier` | Tier | ✅ | 用户层级，前端传 `"FREE"` 或 `"VIP"` |
| `mode` | Mode | ✅ | `"RELATIONSHIP"` 或 `"REPLY"` |
| `screenshots` | ScreenshotFrame[] | 否 | 截图列表，回话模式可为空 |
| `text_input` | string \| null | 否 | 仅回话模式可传，关系判断模式传此字段会被后端拒绝 |
| `timeline_confirmed` | boolean | 否 | 关系判断模式必须传 `true`，否则后端返回 error |
| `my_side` | MySide \| null | 否 | 关系判断模式必须传，否则后端返回 error |

**`ReplyAnalyzeRequest`**（`POST /reply/analyze` 请求体）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | ✅ | |
| `target_id` | string | ✅ | |
| `tier` | Tier | 否 | 默认 `"FREE"` |
| `text_input` | string \| null | 否 | 对方发来的文字（直接输入模式） |
| `prepared_upload` | PreparedUpload \| null | 否 | 已整理的截图材料（截图辅助模式） |
| `ad_proof_token` | string \| null | 否 | 广告凭证，FREE 层用完 3 次后需要 |
| `use_emergency_pack` | boolean | 否 | 是否使用急救包（默认 false） |
| `consent_sensitive` | boolean | 否 | 是否已同意处理敏感内容（默认 false） |
| `user_goal_mode` | string | 否 | 默认 `"MAINTAIN"`，不传操控词即可 |
| `style_mode` | RouteTone | 否 | 默认 `"NATURAL"` |
| `force_new_session` | boolean | 否 | 强制新建 Session（默认 false） |
| `reply_session_now` | string \| null | 否 | 注入时间（测试用），生产环境不传 |
| `relationship_constraints` | RelationshipConstraints \| null | 否 | 仅模式3串联时传入；FREE 传入会被后端剥离并返回 `MODE3_VIP_REQUIRED` warning |

**`RelationshipConstraints`**（模式3桥接约束包）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source_mode` | string | 否 | 固定 `"RELATIONSHIP_ONLY"` |
| `risk_level` | ConstraintRiskLevel \| null | 否 | 风险等级，推荐由模式2结果映射 |
| `strategy_hint` | ConstraintStrategyHint \| null | 否 | 话术策略提示；`WAIT/DEGRADE` 会触发后端强制降压 |
| `reply_guardrails` | string[] | 否 | 额外护栏文案 |
| `summary_ref` | string \| null | 否 | 模式3摘要引用（可选） |

### 1.2.1 模式2 -> 模式3 前端转译规范（必须实现）

> 说明：模式2输出是 `Recommendation(YES/WAIT/NO)`，模式3约束包使用 `ConstraintStrategyHint`。
> 前端必须做一层显式转译，禁止把模式2枚举原样透传给模式1。

| 模式2 `send_recommendation` | 补充条件 | 写入 `strategy_hint` | 写入 `risk_level` |
|---|---|---|---|
| `YES` | 无明显负向风险 | `PUSH` | `LOW` |
| `YES` | 有负向信号但未达高风险 | `MAINTAIN` | `MEDIUM` |
| `WAIT` | 普通降压场景 | `DEGRADE` | `MEDIUM` |
| `WAIT` 或 `NO` | 高风险/硬阻断 | `WAIT` | `HIGH` |

**`RelationshipAnalyzeRequest`**（`POST /relationship/analyze` 请求体）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | ✅ | |
| `target_id` | string | ✅ | |
| `tier` | Tier | ✅ | |
| `prepared_upload` | PreparedUpload | ✅ | **必须来自 `/upload/prepare` 的响应，不可前端自构** |
| `need_full_report` | boolean | 否 | VIP 层可传 true 获取完整 J27 报告 |
| `ad_proof_token` | string \| null | 否 | FREE 层每次关系判断都需要 |
| `use_emergency_pack` | boolean | 否 | 默认 false |
| `consent_sensitive` | boolean | 否 | 默认 false |

### 1.3 核心响应类型

**`PreparedUpload`**（`POST /upload/prepare` 响应体，也是 `/relationship/analyze` 的输入）

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | `"READY"` \| `"NEEDS_REVIEW"` | READY 表示可进入分析，NEEDS_REVIEW 表示有问题需处理 |
| `screenshot_count` | number | 有效截图数量 |
| `tier` | Tier | |
| `mode` | Mode | |
| `timeline_confirmed` | boolean | |
| `my_side` | MySide \| null | |
| `evidence_quality` | EvidenceQuality | 证据质量评级 |
| `effective_turn_count` | number | 有效对话轮数 |
| `effective_char_count` | number | 有效字符数 |
| `low_info_ratio` | number | 低信息轮数占比（0-1） |
| `duplicate_content_suspected` | boolean | 目前始终为 false（后端技术债） |
| `issues` | Issue[] | 问题列表，前端需按 severity 区分处理 |
| `ocr_preview` | OCRPreviewItem[] | 按序号排列的截图预览 |
| `dialogue_turns` | DialogueTurn[] | 结构化对话（已映射 SELF/OTHER） |

**`Issue`**（`issues[]` 的子项）

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 错误码，见「错误码对照表」 |
| `message` | string | 后端返回的中文描述 |
| `severity` | `"error"` \| `"warning"` | **error 级必须阻止继续操作；warning 级可提示后允许继续** |

**`ReplyAnalyzeResponse`**（`POST /reply/analyze` 响应体）

| 字段 | 类型 | 说明 |
|------|------|------|
| `contract_version` | string | 固定 `"v1.0.0"` |
| `mode` | Mode | 固定 `"REPLY"` |
| `dashboard` | Dashboard | 含 `message_bank`，BLOCK 时为空数组 |
| `safety` | SafetyBlock | 安全状态 |
| `explain_card` | ExplainCard | 解释卡 |
| `reply_session` | ReplySessionMeta | Session 元数据 |
| `structured_diagnosis` | StructuredDiagnosis | 结构化诊断 |
| `signals` | SignalCandidate[] | 信号列表 |

**`RelationshipAnalyzeResponse`**（`POST /relationship/analyze` 响应体）

| 字段 | 类型 | 说明 |
|------|------|------|
| `contract_version` | string | 固定 `"v1.0.0"` |
| `mode` | Mode | 固定 `"RELATIONSHIP"` |
| `gate_decision` | GateDecision | 门禁决策 |
| `dashboard` | Dashboard | 含 `message_bank`，BLOCK 时为空数组 |
| `safety` | SafetyBlock | |
| `explain_card` | ExplainCard | |
| `structured_diagnosis` | StructuredDiagnosis | |
| `signals` | SignalCandidate[] | |
| `recovery_protocol` | object | J22 恢复协议（见下方字段说明） |
| `ledger` | LedgerSummary | J24 不对等账本 |
| `sop_filter` | SopFilterSummary | J25 SOP 过滤 |
| `probes` | ProbePackage | J26 探针（BLOCK 时 `available=false`，`items=[]`） |
| `progress_validation` | ProgressValidation | J26 跟进规则 |
| `reality_anchor_report` | RealityAnchorReport | J27 现实锚点 |
| `gating_issues` | Issue[] | 门禁产生的问题列表 |

---

## 第二章：API 接口规格

### 2.1 接口列表

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/health` | 服务健康检查，返回版本号与限额配置 | 无 |
| GET | `/api/state` | 服务内存状态快照（仅调试用） | 无 |
| POST | `/upload/prepare` | 截图上传整理 | 无 |
| POST | `/reply/analyze` | 回话分析 | 无 |
| POST | `/relationship/analyze` | 关系判断 | 无 |
| GET | `/entitlement/state/{user_id}` | 查询用户当日权益状态 | 无 |

### 2.2 `/health` 响应字段

| 字段 | 类型 | 含义 |
|------|------|------|
| `status` | string | 固定 `"ok"` |
| `app` | string | 固定 `"JoyPilot"` |
| `contract_version` | string | 固定 `"v1.0.0"` |
| `reply_free_limit` | number | 免费回话次数（当前 3） |
| `reply_ad_bonus` | number | 广告加成次数（当前 3） |
| `relationship_free_limit` | number | 免费关系判断次数（当前 2） |

> **前端用途**：应用启动时调用，将 `reply_free_limit`、`reply_ad_bonus`、`relationship_free_limit` 存入全局状态，用于权益展示，**不得前端硬编码这三个数值**。

### 2.3 `/entitlement/state/{user_id}` 响应字段

| 字段 | 类型 | 含义 |
|------|------|------|
| `day` | string | 当前 UTC 日期（如 `"2026-03-29"`） |
| `reply_used` | number | 今日回话已用次数 |
| `relationship_used` | number | 今日关系判断已用次数 |
| `emergency_pack_credits` | number | 急救包余额（v1 始终为 0） |
| `object_slots_active` | number | 对象位数量（v1 始终为 0） |
| `pending_deducts` | number | 待扣费中的请求数（正常流程下为 0） |

### 2.4 统一错误处理规范

- HTTP 422：Pydantic 校验失败，`detail` 字段含具体原因，前端展示通用提示"请求格式有误"
- HTTP 200 但 `status = "NEEDS_REVIEW"`：业务层错误，读取 `issues[]` 展示具体原因
- HTTP 200 但 `gate_decision = "BLOCK"`：安全/权益拦截，读取 `safety.note` 展示
- HTTP 500：后端内部错误，展示通用错误页

---

## 第三章：错误码对照表（前端本地化翻译）

> 后端 `issues[].code` 的中文翻译，**前端负责翻译，不得修改 code 值本身**。

### 3.1 module-1 产生的 issues（`/upload/prepare` 阶段）

| code | severity | 前端展示文字 | 是否阻止继续 |
|------|----------|------------|------------|
| `NO_SCREENSHOTS` | error | 关系判断需要至少上传 1 张截图 | ✅ 阻止 |
| `TIMELINE_UNCONFIRMED` | error | 请先确认截图的时间顺序 | ✅ 阻止 |
| `ROLE_UNCONFIRMED` | error | 请确认哪一方是你 | ✅ 阻止 |
| `OCR_EMPTY` | error | 截图内容为空，请填写对话文字 | ✅ 阻止 |
| `INSUFFICIENT_EVIDENCE` | error | 截图中有效内容太少，建议补充更多截图或对话 | ✅ 阻止 |
| `TEXT_DIRECT_NOT_ALLOWED` | error | 关系判断不支持纯文字输入，请上传截图 | ✅ 阻止 |
| `FREE_TIER_RANGE` | error | 免费层关系判断需要 2-4 张截图 | ✅ 阻止 |
| `UPGRADE_REQUIRED` | error | 5-9 张截图需要升级 VIP | ✅ 阻止 |
| `SCREENSHOT_TOO_MANY` | error | 截图超出上限（最多 9 张），请删减后重试 | ✅ 阻止 |
| `VIP_TIER_RANGE` | error | VIP 关系判断需要 2-9 张截图 | ✅ 阻止 |
| `MAX_SCREENSHOTS_EXCEEDED` | error | VIP 最多支持 9 张截图 | ✅ 阻止 |
| `MODE_MISMATCH` | error | 材料模式与请求模式不匹配 | ✅ 阻止 |
| `ROLE_MAPPING_LOCKED` | warning | 角色未确认，对话仅显示左/右（不影响继续） | ❌ 仅提示 |
| `UPLOAD_INDEX_INVALID` | warning | 截图顺序编号异常，已自动按时间戳重新排列 | ❌ 仅提示 |

### 3.2 module-2 产生的 issues（`/reply/analyze` 或 `/relationship/analyze` 阶段）

| code | severity | 前端展示文字 | 是否阻止继续 |
|------|----------|------------|------------|
| `INPUT_NOT_READY` | error | 输入材料不完整，请重新整理截图 | ✅ 阻止 |
| `CONSENT_REQUIRED` | error | 当前内容涉及敏感话题，请先确认知情同意后继续 | ✅ 阻止（展示同意按钮后可重试） |
| `NO_CONTACT` | error | 当前材料显示对方要求停止联系，系统已停止生成话术 | ✅ 阻止 |
| `MANIPULATION` | error | 检测到高压或操控意图，系统不会生成推进型话术 | ✅ 阻止 |
| `PROMPT_INJECTION` | warning | 检测到命令型输入，已切换保守模式 | ❌ 降级继续 |

> ⚠️ **`INPUT_NOT_READY` 的读取方式补充说明**：
> 当 `/upload/prepare` 的 `status !== "READY"` 时，后端直接将 module-1 产生的 `issues[]` 原样继承并传回，同时将 `safety.note` 设为 `"INPUT_NOT_READY"` 相关说明。
> 因此前端必须**同时检查**两个位置：
> - `issues[]`：读取具体 code 并展示对应中文翻译（如 `OCR_EMPTY`、`NO_SCREENSHOTS` 等，见 3.1）
> - `safety.note`：若 issues[] 为空但 gate_decision 仍为 BLOCK/DEGRADE，则展示 `safety.note` 兜底文案
> 不得仅凭 `INPUT_NOT_READY` 这一个 code 作为单一判断源。

### 3.3 module-8 产生的 issues（权益相关）

| code | severity | 前端展示文字 | 处理方式 |
|------|----------|------------|---------|
| `DAILY_LIMIT_REACHED` | error | 今日免费次数已用完 | 展示广告解锁入口 |
| `ADS_REQUIRED` | error | 需要先解锁广告权益 | 展示广告解锁入口 |
| `ADS_PROOF_INVALID` | error | 广告凭证无效，请重新完成广告解锁 | 重新触发广告流程 |
| `EMERGENCY_PACK_REQUIRED` | error | 急救包余额不足 | 展示充值引导 |
| `RELATIONSHIP_INPUT_INVALID` | error | 关系判断材料不满足范围要求 | 引导返回上传步骤 |

---

## 第四章：前端与后端的分工边界

### 4.1 前端负责生成，后端不生成

| 数据 | 前端责任 | 说明 |
|------|---------|------|
| `user_id` | localStorage 中生成并持久化 UUID | 无登录系统，首次访问自动生成 |
| `target_id` | 用户填写或选择后存入 localStorage | v1 单对象 |
| `image_id` | 每张图片的 UUID，前端生成 | 用于后端去重和排序兜底 |
| `upload_index` | 用户选图顺序自动赋值（第1张=1，第2张=2...） | **这是核心功能，后端依赖此字段排序** |
| `left_text` / `right_text` | 用户手动录入每张截图的对话内容 | 后端无 OCR 能力，文字必须由前端传入 |
| `timeline_confirmed` | 用户在时间线确认步骤点击确认后设为 true | 未确认不得发送关系判断请求 |
| `my_side` | 用户在角色确认步骤选择后传入 | 未选择不得发送关系判断请求 |

### 4.2 后端负责生成，前端只读取展示

| 数据 | 禁止前端改写 | 说明 |
|------|------------|------|
| `status` (`READY`/`NEEDS_REVIEW`) | ✅ 禁止 | 由 issues 列表决定，前端只读 |
| `evidence_quality` | ✅ 禁止 | 由后端算法计算 |
| `dialogue_turns[].speaker` | ✅ 禁止 | SELF/OTHER 映射由后端完成 |
| `ocr_preview[].ordered_index` | ✅ 禁止 | 由后端按 upload_index 排序后分配 |
| `gate_decision` | ✅ 禁止 | 门禁决策由后端执行 |
| `message_bank` | ✅ 禁止 | 话术由后端生成，前端只展示和复制 |
| `sop_filter.footer` | ✅ 禁止 | 固定为「模式提示不等于定罪。」，后端写死 |

### 4.3 `PreparedUpload` 的传递规则

**核心约束：`RelationshipAnalyzeRequest.prepared_upload` 必须使用 `/upload/prepare` 的原始响应体，前端不得自行构造或修改。**

正确流程：
```
调用 /upload/prepare → 缓存响应体 → 将完整响应体传给 /relationship/analyze
```

错误做法：
```
❌ 前端自己构造 PreparedUpload 对象传给 /relationship/analyze
❌ 修改 PreparedUpload 中的任何字段后再传
❌ 复用上次的 PreparedUpload 传给新的 target_id
```

---

## 第五章：关键渲染规则（必须严格遵守）

### 5.1 BLOCK 态强制规则

当 `gate_decision === "BLOCK"` 或 `safety.status === "BLOCKED"` 时：

| 元素 | 处理方式 | 原因 |
|------|---------|------|
| `dashboard.message_bank` 区域 | **完全不挂载到 DOM** | 后端已清空，但防止 UI 层意外展示 |
| J26 探针（`probes` 区域） | **完全不挂载到 DOM** | `probes.available === false`，BLOCK 时不得展示 |
| J27 full_text | 不展示（`access === "ALERT_ONLY"`） | 仅展示 `brief_points` |
| `safety.note` | **必须展示** | 告知用户当前被拦截的原因 |

> ⚠️ 注意：是"不挂载"而不是"灰显"或"隐藏（display:none）"，防止用户通过开发者工具看到受限内容。

### 5.2 DEGRADE 态规则

当 `gate_decision === "DEGRADE"` 时：

- 展示橙色降级提示横幅
- J26 探针仍可展示（`available` 可能为 true）
- `message_bank` 的条数按接口类型分别处理（**不得用一条规则覆盖两个接口**）：

| 接口 | DEGRADE 时 message_bank 行为 | 说明 |
|------|----------------------------|------|
| `POST /relationship/analyze` | 最多 1 条（STABLE，recommendation=WAIT） | 后端硬编码固定 1 条降级话术 |
| `POST /reply/analyze` | 最多 2 条（STABLE + NATURAL，均 recommendation=WAIT） | 后端 `_build_wait_safe_routes` 返回 2 条，受 `MAX_MESSAGE_BANK` 限制 |

> **前端正确做法**：直接渲染后端返回的 `message_bank` 数组长度，**不得前端再做截断**；橙色横幅始终显示。

> **J28 / J29 / J30 与 `message_bank`（非 DEGRADE，`ALLOW` 场景，以当前后端为准）：**  
> - **J28（终结词趋势）**：HOT→COLD 或 COLD→HOT 覆写时，当前实现仍将 `message_bank` 置为 `[]`（与 mode2 仅报告、由后续链路生成话术的设计一致）。  
> - **J29（裸标点）**、**J30（连续性打断）**：覆写为 WAIT 时**不**清空 `message_bank`，由基础链路已生成的话术保留，避免「诊断要求降压」与「话术区全空」矛盾；前端按数组实际长度渲染即可。  
> - **矛盾场景**（J28 COLD→HOT + Part_B 裸标点）：J29 静默回退基础结论，`message_bank` 与基础链路一致，前端无需区分。  
> 诊断文案以 `ledger.note` / `structured_diagnosis.one_line_explanation` 为准。

### 5.3 J25 免责声明强制规则

`sop_filter.footer` 的值（`"模式提示不等于定罪。"`）**必须在 J25 面板中展示**，不得省略、折叠或以其他文案替换。

### 5.4 Explain Card 展示规则

`explain_card.note` 必须全程可见，不得折叠到用户看不到的位置。内容来自后端，前端不得修改。

### 5.5 话术复制规则

`message_bank[].text` 可提供一键复制功能，但：
- 不得在前端二次编辑话术内容
- 不得拼接或修改 `text` 字段后再显示

### 5.6 J27 访问权限规则

| `reality_anchor_report.access` 值 | 前端处理 |
|----------------------------------|---------|
| `"FREE_BRIEF"` | 仅展示 `brief_points` 列表 |
| `"PREMIUM_FULL"` | 展示 `brief_points` + `full_text` |
| `"ALERT_ONLY"` | 仅展示 `brief_points`（内容为告警信息） |

---

## 第六章：权益状态与广告流程

### 6.1 额度展示逻辑

| 场景 | 前端展示 |
|------|---------|
| 回话 `reply_used < 3`（FREE） | 显示剩余次数：`3 - reply_used` 次 |
| 回话 `reply_used >= 3 且 < 6`（FREE） | 显示"今日额度已用完，看广告可解锁 3 次" |
| 回话 `reply_used >= 6`（FREE） | 显示"今日回话次数已达上限，明日重置" |
| 关系判断（FREE，任何次数） | 每次关系判断均需广告凭证，展示"看广告解锁本次关系判断"入口 |
| 关系判断 `relationship_used >= 2`（FREE） | 今日次数已达上限，额外显示"明日重置"提示 |
| VIP 任何情况 | 不显示次数限制，无需广告凭证 |

> ⚠️ **关系判断无"免费 N 次"概念**：后端代码中，FREE 层每次关系判断都必须携带有效 `ad_proof_token`，否则直接返回 `ADS_REQUIRED`（BLOCK）。
> `relationship_used` 的作用仅是判断是否达到每日上限（`FREE_RELATIONSHIP_DAILY_LIMIT`），**不代表前几次可免广告**。
> 前端**不得展示"还剩 X 次免费关系判断"**的文案，正确文案是"每次关系判断需解锁广告权益"。

> **每日重置时间**：UTC 0 点（非本地时间），后端以 UTC 日期为 key 隔离。

### 6.2 广告凭证规则

- 广告凭证字段名：`ad_proof_token`
- 格式要求：必须以 `"adp_"` 开头，总长度 ≥ 16 字符
- v1 技术债：后端仅做格式校验，无真实广告 SDK 验证
- 前端接入广告 SDK 后，将 SDK 回调的凭证字符串直接传入 `ad_proof_token` 字段

### 6.3 权益状态刷新时机

以下时机必须重新调用 `GET /entitlement/state/{user_id}`：
- 应用启动时
- 每次回话分析或关系判断成功后
- 用户主动点击刷新按钮时

---

## 第七章：Session 行为规范

### 7.1 Session 对前端的影响

- 每个 `(user_id, target_id)` 组合有独立的 24 小时 Session
- `reply_session.is_new_session === true`：本次是新建 Session（首次或过期后）
- `reply_session.active === false`：Session 已过期（理论上不应出现，后端会自动新建）
- `reply_session.expires_at`：可用于前端显示"当前对话到期时间"

### 7.2 前端不得操作的 Session 内容

- 前端不得读取、存储或修改 `context_snippets`（仅后端维护）
- 前端不得将 Session 数据传入 `/relationship/analyze`（后端有断言保护，传入会报 500）

### 7.3 `force_new_session` 使用时机

仅在用户主动点击"重新开始对话"时传 `true`，其他情况不传（默认 false）。

---

## 第八章：截图整理流程的前端状态机

关系判断的截图整理流程必须按以下顺序执行，**不允许跳步**：

```
Step 1: 选图（生成 upload_index）
    ↓
Step 2: 文字录入（填写 left_text / right_text）
    ↓
Step 3: 时间线预览与确认（timeline_confirmed = true）
    ↓
Step 4: 角色确认（my_side = LEFT | RIGHT）
    ↓
Step 5: 调用 POST /upload/prepare → 接收 PreparedUpload
    ↓
Step 6a: status === "READY" → 直接调用 POST /relationship/analyze
Step 6b: status === "NEEDS_REVIEW" → 展示 issues，error 级阻止，warning 级提示后可继续
```

### 8.1 Step 1 — 选图规则

- 用户每次点击选图，按**选择动作的先后顺序**自动赋值 `upload_index`
  - 第 1 个被选中的图 → `upload_index = 1`
  - 第 2 个被选中的图 → `upload_index = 2`
  - 以此类推
- 支持拖拽调整顺序后重新计算 `upload_index`（重新从 1 开始连续编号）
- 支持删除单张后后续编号自动补位（保持连续无间隔）
- **图片仅在前端内存中保留，不上传至后端**（后端不接受图片文件）

**张数前置校验（在选图阶段即可提示，不等后端）：**
- FREE 层：1 张 → 不满足（需要至少 2 张）
- FREE 层：≥ 5 张 → 超出 FREE 限额（需升级 VIP 或删减到 4 张以内）
- VIP 层：≥ 10 张 → 超出上限（最多 9 张）

### 8.2 Step 2 — 文字录入规则

- 每张截图对应独立的录入区，展示图片缩略图供参照
- 两个输入框：左侧对话（→ `left_text`）、右侧对话（→ `right_text`）
- 允许留空（某张图没有文字是合法的）
- **至少一张图片的任意一侧有文字才允许进入下一步**（否则后端会返回 `OCR_EMPTY`）

### 8.3 Step 3 — 时间线确认规则

- 展示所有截图按当前 `upload_index` 顺序的竖向时间轴预览
- 用户可在此步调整顺序（拖拽），调整后重新计算 `upload_index`
- **必须有用户显式确认动作**（勾选复选框或点击确认按钮），才将 `timeline_confirmed` 设为 `true`
- 未确认时「下一步」按钮不可点

### 8.4 Step 4 — 角色确认规则

- 展示第一张截图的左/右对话预览
- 两个互斥选项：「左边是我」（→ `my_side = "LEFT"`）、「右边是我」（→ `my_side = "RIGHT"`）
- **未选择时「开始分析」按钮不可点**

### 8.5 Step 5 — 调用 `/upload/prepare` 规则

- 在步骤 4 完成后自动调用，不需要用户再点击额外的按钮
- 请求体中的 `screenshots` 字段按当前 `upload_index` 顺序排列（前端传序，后端也会排序，两者应一致）
- 调用期间显示加载状态，禁止重复提交

### 8.6 Step 6 — 处理 `PreparedUpload` 结果

**`status === "READY"` 时：**
- 将完整 `PreparedUpload` 响应体缓存到 React Context（或 sessionStorage）
- 自动导航至关系判断结果页，同时调用 `/relationship/analyze`

**`status === "NEEDS_REVIEW"` 时：**
- 展示 issues 列表，每项显示中文翻译（见「错误码对照表」）
- `severity === "error"` 的 issue → 红色，阻止继续，必须返回修改
- `severity === "warning"` 的 issue → 橙色，显示后允许用户选择"忽略并继续"

---

## 第九章：全局状态管理规范

### 9.1 持久化存储（localStorage）

| key | 类型 | 说明 | 初始化时机 |
|-----|------|------|-----------|
| `joypilot_user_id` | string | 用户 UUID | 首次访问自动生成 |
| `joypilot_target_id` | string | 当前对象 ID | 用户设置后写入 |
| `joypilot_tier` | `"FREE"` \| `"VIP"` | 用户层级 | 默认 `"FREE"` |

### 9.2 会话状态（React Context，内存中）

| 状态 | 类型 | 说明 |
|------|------|------|
| `healthConfig` | object | `/health` 的响应，含限额配置 |
| `entitlementState` | object | `/entitlement/state` 的响应 |
| `preparedUpload` | PreparedUpload \| null | 当前整理好的截图材料 |
| `screenshotDraft` | ScreenshotFrame[] | 截图录入步骤中的草稿（未提交到后端） |

### 9.3 状态清理规则

- 切换 `target_id` 时：清空 `preparedUpload` 和 `screenshotDraft`
- 关系判断成功后：保留 `preparedUpload`（用于用户回看），但下次重新上传时清空

---

## 第十章：v1 明确不做项

> 以下功能在 v1 前端范围内**明确不做**，不得在开发过程中自行扩展。

| 不做的功能 | 说明 |
|-----------|------|
| 真实 OCR（图片转文字） | 后端无此能力，前端只能手动录入文字 |
| 用户注册 / 登录 | localStorage UUID 代替，无身份系统 |
| 广告 SDK 真实接入 | v1 后端仅做格式校验，SDK 对接留到 v2 |
| 历史记录持久化 | 后端内存存储，重启清零，无持久化意义 |
| 多对象同时分析 | v1 单 target 口径 |
| 深色/浅色主题切换 | 固定深色主题 |
| 国际化（多语言） | 全中文界面 |
| Push 通知 | 无服务端推送能力 |
| 分享功能 | v1 不支持 |
| 图片标注/框选 | v1 文字由用户手动录入 |

---

## 附录 A：关键字段展示对照表

| 后端字段 | 展示方式 | 注意事项 |
|---------|---------|---------|
| `structured_diagnosis.current_stage` | 大字标题（拉近/试探/模糊/冷/回避） | 直接显示后端返回的字符串 |
| `structured_diagnosis.send_recommendation` | 配色标签（YES=绿/WAIT=橙/NO=红） | 枚举值直接映射颜色 |
| `structured_diagnosis.one_line_explanation` | 副标题文字 | 直接展示，不做二次加工 |
| `structured_diagnosis.risk_signals` | 标签列表 | 最多3个（后端已截断） |
| `ledger.asymmetric_risk` | 风险等级（LOW/MEDIUM/HIGH） | 不显示数字，只显示等级 |
| `ledger.evidence` | 纯文本列表 | 后端已过滤数字，直接展示 |
| `sop_filter.footer` | 固定显示在 J25 区域底部 | 不可省略：「模式提示不等于定罪。」 |
| `probes.items[].template` | 低压力话术模板 | BLOCK 时整个区域不渲染 |
| `reality_anchor_report.brief_points` | 要点列表 | 全层级均展示 |
| `reality_anchor_report.full_text` | 完整报告正文 | 仅 `access === "PREMIUM_FULL"` 时展示 |
| `reply_session.expires_at` | 小字：Session 到期时间 | 可选展示，格式化为本地时间 |
| `dashboard.action_light` | 顶部横幅颜色（GREEN=绿/YELLOW=橙/RED=红） | 直接映射配色 |

---

## 附录 B：与后端的口径漂移风险清单

> 以下是前端开发中最容易发生口径偏移的位置，开发时逐项自查。

| 风险点 | 错误做法 | 正确做法 |
|--------|---------|---------|
| 枚举值大小写 | 传 `"free"` / `"block"` | 必须全大写：`"FREE"` / `"BLOCK"` |
| upload_index 起始值 | 从 0 开始编号 | 必须从 1 开始（后端校验 > 0） |
| PreparedUpload 来源 | 前端自构 PreparedUpload | 必须使用 `/upload/prepare` 的原始响应 |
| BLOCK 下的 message_bank | 灰显或 display:none | 完全不挂载到 DOM |
| sop_filter.footer | 省略或自定义文案 | 必须展示后端返回的原始文字 |
| 广告凭证格式 | 传任意字符串 | 必须以 `"adp_"` 开头且长度 ≥ 16 |
| 权益次数硬编码 | 前端写死 `3次/日` | 从 `/health` 接口取值 |
| 关系判断时传 text_input | 前端传 text_input 到关系判断 | 关系判断模式不可传 text_input（后端报错） |
| target_id 跨次复用 PreparedUpload | 换了对象但 PreparedUpload 不清空 | 切换 target_id 时必须清空 preparedUpload |
| 每日重置时间 | 按本地时间 0 点重置 | 按 UTC 0 点重置（后端以 UTC 日期为 key） |
| 关系判断"免费次数"文案 | 显示"还剩 X 次免费关系判断" | FREE 层每次关系判断必须有广告凭证，无"免费次数"概念 |
| DEGRADE 下 message_bank 截断 | 统一前端截为 1 条 | 关系模式 1 条、回复模式最多 2 条，直接用后端返回长度 |
| INPUT_NOT_READY 拦截文案来源 | 只读 issues[].code 匹配 | 需同时检查 issues[] 和 safety.note 两个位置 |

---

*文档生成时间：2026-03-29 | 基准文档：MASTER_PLAN_CONSOLIDATED.md | 后端测试：80 passed, 0 failed*
