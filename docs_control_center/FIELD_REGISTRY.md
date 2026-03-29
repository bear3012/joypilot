# JoyPilot FIELD_REGISTRY

## Active Fields

### Field: `contract_version`
- Type: `string`
- Owner Module: `module-0`
- Lifecycle: `Active`
- Description & Constraints: API 契约版本号，所有响应必须返回，当前固定为 `v1.0.0`。

### Field: `prepared_upload.status`
- Type: `string`
- Owner Module: `module-1`
- Lifecycle: `Active`
- Description & Constraints: 上传整理状态，只允许 `READY` 或 `NEEDS_REVIEW`。

### Field: `prepared_upload.dialogue_turns`
- Type: `array<object>`
- Owner Module: `module-1`
- Lifecycle: `Active`
- Description & Constraints: 结构化对话列表，元素必须包含 `speaker/text/source_image_id`，并可携带 `timestamp_hint`（可空）供 J24 时延分析纯函数使用；供回话与关系判断共用。

### Field: `prepared_upload.evidence_quality`
- Type: `string`
- Owner Module: `module-1`
- Lifecycle: `Active`
- Description & Constraints: 输入证据质量标签，只允许 `SUFFICIENT`、`LOW_INFO`、`INSUFFICIENT`，供下游降级使用。

### Field: `prepared_upload.effective_turn_count`
- Type: `int`
- Owner Module: `module-1`
- Lifecycle: `Active`
- Description & Constraints: 有效文本轮次数，低于阈值时触发证据不足策略。

### Field: `prepared_upload.effective_char_count`
- Type: `int`
- Owner Module: `module-1`
- Lifecycle: `Active`
- Description & Constraints: 有效文本字符数，用于识别“全表情/超短词”低信息输入。

### Field: `prepared_upload.low_info_ratio`
- Type: `float`
- Owner Module: `module-1`
- Lifecycle: `Active`
- Description & Constraints: 低信息轮次占比，达到阈值时不允许进入关系判断。

### Field: `screenshot.upload_index`
- Type: `int|null`
- Owner Module: `module-9`
- Lifecycle: `Active`
- Description & Constraints: 前端按用户选图点击顺序写入（1,2,3...）。若所有截图都为正整数则后端按 `(upload_index, image_id)` 排序；若部分缺失或非正整数，则返回 `UPLOAD_INDEX_INVALID`（warning）并回退 `(timestamp_hint, image_id)`。

### Field: `screenshot.timestamp_hint`
- Type: `string|null`
- Owner Module: `module-1`
- Lifecycle: `Active`
- Description & Constraints: 截图时间提示，支持 `HH:MM` 或 ISO 时间字符串。关系判断链路用于 J24 时延分桶；FREE 缺失时可跳过时延算法，VIP 至少需要 2 条可解析时间，否则返回 `TIMESTAMP_REQUIRED_VIP`（error）。

### Field: `safety.status`
- Type: `string`
- Owner Module: `module-2`
- Lifecycle: `Active`
- Description & Constraints: 安全门状态，只允许 `SAFE`、`CAUTION`、`BLOCKED`。

### Field: `gate_decision`
- Type: `string`
- Owner Module: `module-2`
- Lifecycle: `Active`
- Description & Constraints: 门禁总裁决，只允许 `ALLOW`、`DEGRADE`、`BLOCK`；下游必须先判断该字段再执行生成。

### Field: `reply_session.start_at`
- Type: `datetime`
- Owner Module: `module-3`
- Lifecycle: `Active`
- Description & Constraints: 回话 session 起点；固定 24 小时有效，不允许滑动续期。

### Field: `reply_session.expires_at`
- Type: `datetime`
- Owner Module: `module-3`
- Lifecycle: `Active`
- Description & Constraints: `start_at + 24h`，仅在创建 session 时计算；后续请求不得滑动续期。

### Field: `reply_session.context_snippets`
- Type: `array<string>`
- Owner Module: `module-3`
- Lifecycle: `Active`
- Description & Constraints: 回话上下文仅保留当前 session；必须执行 FIFO 截断，最大轮次 `10`，总字符数上限 `2000`。

### Field: `dashboard.message_bank`
- Type: `array<object>`
- Owner Module: `module-4`
- Lifecycle: `Active`
- Description & Constraints: 当前可编辑回复路线，最多 3 条；`Safety Block` 命中时必须为空；`send_recommendation=NO` 时必须降为单条安全解释路线；`send_recommendation=WAIT` 时不得包含 `BOLD_HONEST`。

### Field: `dashboard.message_bank[].reason`
- Type: `string`
- Owner Module: `module-4`
- Lifecycle: `Active`
- Description & Constraints: 每条路线短解释必须具备现实锚点价值（情绪点或风险点）；禁止同义复读；低质量时由系统修复为中性模板文案。

### Field: `reply_request.relationship_constraints`
- Type: `object|null`
- Owner Module: `module-11`
- Lifecycle: `Active`
- Description & Constraints: 模式3串联时由前端携带的关系约束包。仅 VIP 可生效；非 VIP 传入时后端强制剥离为 `None` 并平滑回退普通 REPLY_ONLY，同时记录审计并可返回 `MODE3_VIP_REQUIRED` warning。

### Field: `reply_response.gating_issues`
- Type: `array<object>`
- Owner Module: `module-11`
- Lifecycle: `Active`
- Description & Constraints: 回话模式下的附加门禁/降级问题列表。用于提示模式3越权剥离等非阻断风险，不影响主流程返回 200。

### Field: `signals[].candidate_interpretations`
- Type: `array<string>`
- Owner Module: `module-5`
- Lifecycle: `Active`
- Description & Constraints: emoji / sticker 的多候选解释，只能表达候选，不得写成最终真相；贴图占位符必须输出 `非文本情绪表达/低信息回应/话题缓冲` 三候选。

### Field: `signals[].frequency`
- Type: `int`
- Owner Module: `module-5`
- Lifecycle: `Active`
- Description & Constraints: 同类信号的出现频次（去重保密度）；用于识别单点符号过密风险，默认最小值 `1`。

### Field: `structured_diagnosis`
- Type: `object`
- Owner Module: `module-6`
- Lifecycle: `Active`
- Description & Constraints: 固定结构化诊断，必须包含 `current_stage/risk_signals/strategy/send_recommendation/one_line_explanation`。

### Field: `probes.available`
- Type: `bool`
- Owner Module: `module-6`
- Lifecycle: `Active`
- Description & Constraints: J26 探针总开关；`gate_decision=BLOCK` 时必须为 `false`。

### Field: `probes.items`
- Type: `array<object>`
- Owner Module: `module-6`
- Lifecycle: `Active`
- Description & Constraints: J26 下一步低压核验动作列表；仅可给 next-action，不得倒推过往关系；`BLOCK` 时必须为空数组。

### Field: `sop_filter.footer`
- Type: `string`
- Owner Module: `module-6`
- Lifecycle: `Active`
- Description & Constraints: J25 固定免责声明，API 序列化出口必须强制追加：`模式提示不等于定罪。`

### Field: `reality_anchor_report`
- Type: `object`
- Owner Module: `module-6`
- Lifecycle: `Active`
- Description & Constraints: J27 输出；仅基于当前截图事实，严禁预测未来；免费层只给 brief，VIP 可给 full；`BLOCK` 时无视层级强制降级为 `ALERT_ONLY`。

### Field: `frontend.render_state`
- Type: `string`
- Owner Module: `module-7`
- Lifecycle: `Active`
- Description & Constraints: 前端请求状态机，固定 `idle/loading/success/error`；请求发起 0ms 必须进入 `loading`，并执行旧视图原子清空。

### Field: `frontend.explain_disclaimer`
- Type: `string`
- Owner Module: `module-7`
- Lifecycle: `Active`
- Description & Constraints: Explain 核心免责提示必须常驻外露，不得折叠；仅证据映射明细允许折叠展示。

### Field: `frontend.safe_text_render`
- Type: `rule`
- Owner Module: `module-7`
- Lifecycle: `Active`
- Description & Constraints: 所有文本渲染点禁止 `innerHTML`，必须使用 `textContent/innerText`，防止模型输出或用户原文触发 XSS。

### Field: `gating_issues`
- Type: `array<object>`
- Owner Module: `module-10`
- Lifecycle: `Active`
- Description & Constraints: 门禁、材料不足、广告权益等问题清单；必须如实返回，不得静默吞掉。

### Field: `reply_request.consent_sensitive`
- Type: `bool`
- Owner Module: `module-2`
- Lifecycle: `Active`
- Description & Constraints: 回话模式高敏语境同意标记；当检测到高敏语境且该值为 `false` 时，必须触发 `CONSENT_REQUIRED` 并阻断生成。

### Field: `request.ad_proof_token`
- Type: `string|null`
- Owner Module: `module-8`
- Lifecycle: `Active`
- Description & Constraints: 广告权益凭证，替代客户端布尔解锁；必须通过前缀+长度校验，校验失败返回 `ADS_PROOF_INVALID`。

### Field: `request.use_emergency_pack`
- Type: `bool`
- Owner Module: `module-8`
- Lifecycle: `Active`
- Description & Constraints: 是否使用单次急救包；仅在余额充足且范围合法时可进入 check&lock，两阶段提交后才真正扣减。
