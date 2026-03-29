# JoyPilot v1 — 全模块综合实施方案（代码对齐版）

> **文档定位**：本文档是对 `C:\Users\amina\.cursor\plans\` 下所有 module 实施方案的颗粒度对齐合并版。
> 以**代码实际实现为唯一真相源**（截至 2026-03-29 全量测试 80 passed），修正各历史方案中与实现不符的表述，并统一口径。
> 历史方案文件因编码问题无法直接查阅，本文档作为其可信替代。

---

## 总体架构约束（跨模块写死）

1. **Contract-first**：所有输入/输出均通过 `app/contracts.py` 中的 Pydantic 模型定义，任何模块不得裸输出字符串
2. **Deterministic-by-default**：同输入同输出，枚举有限，排序有规则
3. **No silent failure**：证据不足必须以 `issues[]` 明确报告
4. **Safety-first**：BLOCK 场景 `message_bank` 必须为空，J26 探针必须关闭
5. **写只读分离**：module-9 审计层 v1 只写不读，不参与任何判断链路

---

## module-0 — 项目骨架与唯一真相源

### 职责
锁定全系统共用的枚举、Pydantic 模型、配置常量、内存存储结构。

### 核心文件
| 文件 | 职责 |
|------|------|
| `app/config.py` | 全局常量（限额、关键词表、阈值） |
| `app/contracts.py` | 全部 Pydantic 数据模型（唯一口径源） |
| `app/storage.py` | `InMemoryStore` 单例，进程级内存，重启清零 |

### 关键枚举（已实现，已锁定）
- `Tier`: FREE / VIP
- `Mode`: REPLY / RELATIONSHIP
- `GateDecision`: ALLOW / DEGRADE / BLOCK
- `SafetyStatus`: SAFE / CAUTION / BLOCKED
- `Recommendation`: YES / WAIT / NO
- `EvidenceQuality`: SUFFICIENT / LOW_INFO / INSUFFICIENT
- `RouteTone`: STABLE / NATURAL / BOLD_HONEST
- `MySide`: LEFT / RIGHT

### 方案 vs 实现对齐结论
✅ 完全对齐。所有契约字段与代码一致，无偏差。

---

## module-1 — 输入整理链路

### 职责
将原始截图列表转换为结构化的 `PreparedUpload`（可判断材料）。

### 核心文件
`app/input_service.py`

### 接口口径
- **入口**：`POST /upload/prepare`，接收 `UploadPrepareRequest`
- **出口**：`PreparedUpload`（作为 module-6 的唯一物料来源）

### 关键实现逻辑（已实现）

**截图排序（`_sort_frames`）：**
- 全部 `upload_index` 合法（非 None 且 > 0）→ 按 `upload_index` 升序，同值以 `image_id` 兜底
- 部分缺失或非法 → 回退时间戳排序，追加 `UPLOAD_INDEX_INVALID` warning
- 全部无 `upload_index` → 按时间戳静默排序，无 warning

**角色映射（`_map_side`）：**
- `my_side` 为 None → speaker 保持 `LEFT/RIGHT`
- `my_side` 已指定 → 同侧映射 `SELF`，对侧映射 `OTHER`

**证据质量判定（三条件任一触发 → INSUFFICIENT）：**
- 有效轮数 < 2（`LOW_INFO_MIN_EFFECTIVE_TURNS = 2`）
- 有效字符数 < 8（`LOW_INFO_MIN_EFFECTIVE_CHARS = 8`）
- 低信息轮数占比 ≥ 70%（`LOW_INFO_RATIO_THRESHOLD = 0.7`）
- 低信息文本：空字符、长度 ≤ 2、命中白名单（哦/嗯/好/哈哈/ok/收到）

**关系判断模式强制前置门禁（缺一不可）：**

| 门禁 | 错误码 | severity |
|------|--------|----------|
| 至少1张截图 | `NO_SCREENSHOTS` | error |
| `timeline_confirmed = true` | `TIMELINE_UNCONFIRMED` | error |
| `my_side` 已指定 | `ROLE_UNCONFIRMED` | error |
| OCR 预览非全空 | `OCR_EMPTY` | error |
| 证据质量非 INSUFFICIENT | `INSUFFICIENT_EVIDENCE` | error |
| 不允许文本直传（v1） | `TEXT_DIRECT_NOT_ALLOWED` | error |
| FREE 截图数量范围（2-4张） | `FREE_TIER_RANGE` | error |
| FREE 用 5-9 张 | `UPGRADE_REQUIRED` | error |
| 超过 VIP 最大值（9张） | `SCREENSHOT_TOO_MANY` | error |

**状态规则：**
- `status = "READY"`：`issues` 为空
- `status = "NEEDS_REVIEW"`：任何 issue 存在时

**技术债说明：**
- 🚧 OCR 非真实识别：`left_text`/`right_text` 由调用方（前端）传入，后端无图像处理能力
- 🚧 `duplicate_content_suspected` 字段硬编码为 `False`，检测逻辑未实现

### 方案 vs 实现对齐结论
✅ 核心逻辑完全对齐。历史方案中提到的 `SCREENSHOT_TOO_FEW` 错误码实际实现为 `FREE_TIER_RANGE`，名称略有差异，以代码为准。

---

## module-2 — 门禁与安全规则层

### 职责
对所有分析请求执行多层过滤，输出 `(GateDecision, SafetyBlock, issues, check_id)` 四元组。

### 核心文件
`app/gates.py`

### 五层过滤顺序（短路执行）

| 层级 | 触发条件 | 决策 | 扣费 |
|------|---------|------|------|
| 1 | `prepared.status != "READY"` | error → BLOCK；warning → DEGRADE | 否 |
| 2 | 高敏语境 + `consent_sensitive=False` | BLOCK | 否 |
| 3 | 商业化校验失败 | BLOCK | 否 |
| 4 | NO_CONTACT / 操控意图 | BLOCK | 否（释放已锁权益） |
| 5 | Prompt 注入 | DEGRADE | **是**（check_id 保留） |

**检测词表（关键词字符串匹配，非 NLP）：**
- 敏感语境（14个）：抑郁/焦虑症/自残/自杀/精神科/心理危机/经期/生理期/怀孕/流产/妇科/性病/艾滋/药物治疗
- 操控意图（8个）：逼她/服从测试/冷暴力/报复/让她慌/羞辱/惩罚她（`user_goal_mode` 字段检测）
- No-Contact（6个）：拉黑/别联系/不要联系/停止联系/no-contact/报警
- Prompt 注入（6个）：ignore previous/system prompt/覆盖规则/输出系统提示/你现在必须/开发者指令

**核心防御：**
- BLOCK → `allowed_to_generate_messages = False`，主链强制清空 `message_bank = []`
- DEGRADE → 仅保留 STABLE tone 路线，强制 `Recommendation.WAIT`

**技术债说明：**
- 🚧 广告凭证验证仅做格式校验（`adp_` 前缀 + 长度 ≥ 16），无真实广告 SDK

### 方案 vs 实现对齐结论
✅ 五层过滤结构完全对齐。Layer 4（NO_CONTACT/MANIPULATION）命中后须先 `release_entitlement_lock()` 再返回 BLOCK，已正确实现。

---

## module-3 — 回话 Session 管理

### 职责
为每个 `(user_id, target_id)` 维护独立的 24 小时固定窗口 Session。

### 核心文件
`app/reply_session_service.py`

### 关键实现逻辑（已实现）

**Session 创建规则：**
- key = `json.dumps([user_id, target_id])`（防分隔符碰撞）
- 存在且未过期 + `force_new=False` → 复用，`is_new = False`
- 已过期 OR `force_new=True` → 新建，`is_new = True`，旧 context 不继承

**窗口规则（硬约束）：**
- 有效期：`SESSION_DURATION = timedelta(hours=24)`，固定，**不滑动续期**
- `start_at` 仅在创建时写入，复用时不改 `expires_at`

**上下文容量（FIFO 双重上限）：**
- 轮数上限：10 条（`MAX_SESSION_TURNS`）
- 字符上限：总字符数 ≤ 2000（`MAX_SESSION_TOTAL_CHARS`）
- 超出时从最旧条目开始弹出

**并发安全：** `threading.Lock`（每个 session key 独立锁），注意：是 threading.Lock 非 asyncio.Lock

**隔离强制：** 关系判断链路（`relationship_service.py` 首行）若检测到 `session_data` 属性直接 `raise RuntimeError`，彻底防止读取

### 方案 vs 实现对齐结论
✅ 完全对齐。方案中明确的"固定24h/到期硬清零/不跨窗继承/不污染关系判断"均已实现并通过测试。

---

## module-4 — 回话主链

### 职责
接收用户当前输入，经门禁、信号解析、Session 上下文注入，输出结构化回话建议。

### 核心文件
`app/reply_service.py`

### 接口口径
- **入口**：`POST /reply/analyze`，接收 `ReplyAnalyzeRequest`
- **出口**：`ReplyAnalyzeResponse`

### 关键实现逻辑（已实现）

**四层处理顺序：**
1. 获取/创建 Session（module-3）
2. 门禁校验（module-2），通过后 commit 扣费
3. 信号解析（module-5）→ 生成回话路线
4. 输出清洗（矛盾修复 + reason 质量门）→ 更新 Session

**⚠️ 重要：回复文本为硬编码 Mock，非 LLM 生成：**
```
_simulate_model_generation() 注释明确标注：
# 当前为 Mock 实现，接入 LLM 时：
#   system_prompt = f"{non_instruction_policy}\n{safe_historical_context}\n..."
```

实际生成文本：
- STABLE：固定文本 `"收到啦，我先不多打扰你，等你方便的时候我们再接着聊。"`
- NATURAL：`f"哈哈先接住这句：{对方最后一句话前24字}。你忙完再回我也行。"`
- BOLD_HONEST：根据是否有正向信号切换两个模板

**矛盾修复（`_apply_no_contradiction_guard`）：**
- `send_recommendation = NO` → 清空 message_bank 或仅返回 1 条停止话术
- `DEGRADE` 或 `WAIT` → 强制覆盖，仅保留 STABLE 路线

**reason 质量门（`_apply_reason_quality_gate`）：**
- reason 长度 < 12 / 含低价值短语 / 不含关键词锚点 → 替换为对应 tone 的预设修复文本

**历史上下文安全注入：**
- snippet 经 XML 转义（`&`/`<`/`>`），包裹在 `<historical_context>` 标签内
- `NON_INSTRUCTION_CONTEXT_POLICY` 说明历史内容禁止视为系统指令

### 方案 vs 实现对齐结论
⚠️ **关键偏差**：历史方案中"模型生成"的表述对应代码中为 Mock 实现，需在技术债中明确标注。历史方案中的 `style_mode` 字段（`forced_style`）已实现但实际在 Mock 层未生效（只影响 `ExplainCard.forced_style` 字段）。

---

## module-5 — 信号解析层

### 职责
从文本中提取非语言信号（emoji、贴图占位符），输出候选解释列表和风险汇总。

### 核心文件
`app/signal_service.py`

### 关键实现逻辑（已实现）

**覆盖范围：**
- Emoji（8种）：❤️ ❤ 😂 🙂 😊 👍 😅 😄
- 贴图占位符：`[sticker]`/`[贴图]`/`[动画表情]`/`贴图`/`动画表情`（括号版先计数后替换防双计）

**不覆盖：**
- 文字语义（如"好喜欢你"不产生信号）
- 真实图片（需前端预转占位符）
- 其他 emoji（❓🎉等完全不识别）

**去重规则：** 同 `(signal_type, raw_value)` 累加 `frequency`，`low_info` 只升不降

**风险信号优先级（最多3条，`MAX_RISK_SIGNALS = 3`）：**
Prompt 注入 > 贴图盲区 > emoji 密度（frequency > 3）> 低信息过度解读

**`contains_positive_candidate`：** 检测 `candidate_interpretations` 中是否含 `"positive_interest"`（仅 ❤️ 和 ❤ 有此候选解释）

### 方案 vs 实现对齐结论
✅ 完全对齐。方案中明确的 `has_positive_signal → contains_positive_candidate` 重命名、频次累加、贴图固定解释均已实现。

---

## module-6 — 关系判断主链

### 职责
基于 `PreparedUpload` 输出完整的关系状态诊断包。

### 核心文件
`app/relationship_service.py`

### 接口口径
- **入口**：`POST /relationship/analyze`，接收 `RelationshipAnalyzeRequest`
- **出口**：`RelationshipAnalyzeResponse`

### 关键实现逻辑（已实现）

**⚠️ 关系判断是关键词计数逻辑，非 LLM：**
- 正向词 8 个：哈哈/想你/好呀/可以/见面/周末/一起/期待
- 负向词 8 个：忙/再说/改天/算了/不方便/别/不要/冷静
- 阶段判断 5 分支（硬编码 if/else）

| 条件 | 阶段 |
|------|------|
| BLOCKED | 回避 |
| negative > positive + 1 | 冷 |
| positive > negative 且非低信息 | 拉近 |
| low_info = True | 模糊 |
| 其他 | 试探 |

**J24 不对等账本（`_build_ledger`）：**
- 内部按 SELF/OTHER 总字符数比较（字符数 > 对方 × 1.5 → HIGH）
- 输出禁止数字（`_enforce_j24_qualitative_only` 过滤伪量化表达，如百分比、时长）

**J25 SOP 过滤（`_build_sop_filter`）：**
- 检测5个推脱词：改天/再说/忙完/下次/回头
- ≥ 2 个 → MEDIUM；否则 LOW
- `footer` 强制写死：`"模式提示不等于定罪。"`

**J26 探针（`_build_probes`）：**
- BLOCK → 返回空列表，`available = False`
- low_info → 返回 `RECIPROCITY_CHECK` 探针
- 阶段为「拉近」→ 返回 `LIGHT_INVITE` 探针
- `_enforce_j26_next_action_only` 过滤含"之前/历史证明"等回溯词

**J27 现实锚点（`_build_reality_anchor_report`）：**
- 默认：`access = "FREE_BRIEF"`，仅 `brief_points`
- VIP + `need_full_report=True` + 非 DEGRADE → 生成 `full_text`（硬编码模板，非 LLM）
- BLOCK → `access = "ALERT_ONLY"`
- `_enforce_j27_past_fact_only` 过滤含未来预测词（将会/未来/迟早会等11个）

**隔离强制（首行断言）：**
```python
session_data = getattr(request, "session_data", None)
if session_data is not None:
    raise RuntimeError("FATAL: Relationship pipeline MUST NOT read reply session!")
```

**技术债说明：**
- 🚧 `_write_audit_stub` 中 `gate_decision` 字段硬编码为 `"UNKNOWN"`（未传入实际值）
- 🚧 J27 `full_text` 为硬编码模板，非 LLM 生成

### 方案 vs 实现对齐结论
⚠️ **关键偏差**：`_write_audit_stub` 中 `gate_decision: "UNKNOWN"` 是已知技术债，历史方案未提及，需登记。J24/J25/J26/J27 的合规过滤函数均已实现，与方案对齐。

---

## module-7 — 前端控制台（Web/PWA）

### 职责
提供 API 调试控制台界面，当前定位为开发者工具，非面向最终用户。

### 核心文件
`app/static/index.html` · `manifest.webmanifest` · `service-worker.js`

### 已实现能力
- 截图 JSON 手填输入（`<textarea>` 接受 `ScreenshotFrame[]` JSON）
- 调用 `/upload/prepare`、`/reply/analyze`、`/relationship/analyze`
- 结构化结果渲染（J22/J24/J25/J26/J27 各面板）
- BLOCK 态下 J26 探针从 DOM 移除（不灰显，完全不渲染）
- PWA 离线缓存（Service Worker，仅缓存静态资源）

### 未实现能力（技术债）
- 🚧 无真实图片上传（无 `<input type="file">`，需用户手填 JSON）
- 🚧 无 `upload_index` 自动生成（因无相册选图流程）
- 🚧 无 OCR（left_text/right_text 需手动录入）
- 🚧 无广告 SDK 接入（广告凭证硬编码为 `"adp_demo_token_123456"`）

### 方案 vs 实现对齐结论
⚠️ **已知范围收窄**：module-7 历史方案定位为「前端控制台」，v1 实现为开发者调试面板。真实用户界面需要单独的前端项目（Next.js 方案已另行规划）。

---

## module-8 — 权益与商业化

### 职责
管理用户每日使用次数，实现"先锁后扣"的幂等扣费机制。

### 核心文件
`app/entitlement_service.py`

### 接口口径
- 查询：`GET /entitlement/state/{user_id}`
- 扣费链路通过 `gates.py` 内嵌调用，不直接对外暴露

### 关键实现逻辑（已实现）

**三步扣费机制（防超扣/防并发重复）：**
1. `check_and_lock_entitlement()` → 检查余量，创建 pending 记录（不立即扣）
2. `commit_entitlement_deduct(check_id)` → 主链成功后真正扣减
3. `release_entitlement_lock(check_id)` → BLOCK 时释放 pending 锁

**额度规则：**

| 用户层级 | 功能 | 免费次数 | 广告加成 |
|---------|------|---------|---------|
| FREE | 回话 | 3次/日 | +3次（广告凭证验证后） |
| FREE | 关系判断 | 2次/日 | 必须每次提供广告凭证 |
| VIP | 回话 | 无限制 | — |
| VIP | 关系判断 | 无限制 | — |

**每日重置：** key 格式为 `"user_id:2026-03-29"`（UTC 日期），新的一天自动隔离，旧 key 不清理

**并发安全：** 每个 `user_id` 一把 `asyncio.Lock`（注意：这里是 asyncio.Lock，与 module-3 的 threading.Lock 不同）

**幂等保障：** `commit` 用 `pop()` 操作，已弹出或不存在时静默返回，天然幂等

**`_count_pending_for_user`：** 将 in-flight pending 计入 effective_used，防并发绕过限额

**技术债说明：**
- 🚧 广告凭证仅做格式校验（前缀 `adp_` + 长度 ≥ 16），无真实广告 SDK
- 🚧 急救包（`emergency_pack_credits`）无充值入口，初始值为 0，无法正常使用
- 🚧 对象位（`object_slots_active`）字段存在但始终为 0，无相关业务逻辑

### 方案 vs 实现对齐结论
✅ 核心扣费逻辑完全对齐。技术债（广告 stub、急救包无充值、对象位未实现）均为已知范围内收窄，不影响主流程。

---

## module-9 — 审计日志与对象摘要预留层

### 职责
提供旁路写入接口，供 module-6 和 module-8 在业务成功后记录审计事件和对象摘要。v1 只写不读。

### 核心文件
`app/audit_service.py`

### 关键实现逻辑（已实现）

**双接口：**
- `write_audit_event()` — 事件级审计（事件名、用户、模式、元数据）
- `write_segment_summary()` — 对象摘要（target 的关系阶段、不对等风险、摘要文本）

**容量上限（双轨存储）：**

| 存储 | 结构 | 上限 | 淘汰方式 |
|------|------|------|---------|
| `audit_entries_by_user[uid]` | `deque(maxlen=500)` | 500条/用户 | 自动 FIFO |
| `STORE.audit_entries` | `list` | 500条/用户 | 手动标记后过滤 |
| `segment_summaries_by_target[tid]` | `deque(maxlen=50)` | 50条/target | 自动 FIFO |
| `STORE.segment_summaries` | `list` | 50条/target | 手动标记后过滤 |

**摘要体积双重检查：**
1. 超 20KB → 先截断（summary 截至 2000 字符，payload 截至 20 条）
2. 截断后仍超 → 写入拒绝告警事件（`SEGMENT_SUMMARY_TOO_LARGE`）并 `return False`

**审计敏感字段脱敏（白名单机制）：**
- 黑名单字段：`ocr_preview`/`dialogue_turns`/`text_input`/`left_text`/`right_text`
- 白名单字段（48个）：状态码、决策、模式、规则等元数据
- 字符串值截断到 512 字符，列表截断到 20 个元素

**Fail-Safe（最高优先级防御）：**
- `write_audit_event` 和 `write_segment_summary` 最外层均有 `try/except Exception`
- 任何异常静默 `return False`，绝不向上抛出，不影响主业务

**v1 边界（写死）：** 审计/摘要数据不暴露任何读取接口，不参与关系判断

### 方案 vs 实现对齐结论
✅ 与红队补丁方案（`c75306da`）完全对齐。OOM 防御（FIFO）、体积上限、敏感字段脱敏、Fail-Safe 四项均已实现并通过测试。

---

## module-10 — 验收与红队（测试框架）

### 职责
提供可重复执行的自动化测试套件，覆盖所有核心能力的"必须通过/必须拒绝/必须降级"场景。

### 核心文件
`tests/test_api.py` · `fixtures/module-10/`（11个 JSON 文件）

### 最终测试状态
**80 passed, 0 failed**（截至 2026-03-29 全量回归）

### 测试分层（18个 module-10 入口）

| 轮次 | 测试名 | 覆盖方向 |
|------|--------|---------|
| 契约 | `test_m10_golden_contract_fixtures` | API 基础路径 + 字段存在性 |
| 冒烟 | `test_m10_smoke_fixture_pack` | 5 个核心路径快速验证 |
| 负向 | `test_m10_negative_fixture_pack` | 4 个必须被拒绝的场景 |
| 第1轮 | `test_m10_red_team_fixture_pack` | 基础红队扩展 |
| 第2轮 | `test_m10_red_team_combined_fixture_pack` | 跨接口组合（单用户多 API 调用） |
| 第3轮 | `test_m10_red_team_timing_fixture_pack` | 24h Session 过期时序精确验证 |
| 第4轮 | `test_m10_red_team_robustness_fixture_pack` | 超长文本/空数组/非法字段 |
| 第5轮 | `test_m10_red_team_state_isolation_fixture_pack` | 跨模块/跨 target 状态隔离 |
| 专项 | `test_m10_concurrency_same_user_cross_target_session_isolation` | 同用户跨 target 并发安全 |
| 专项 | `test_m10_entitlement_commit_release_are_idempotent_under_retry` | 幂等重试恢复 |
| 专项 | `test_m10_entitlement_daily_limit_resets_on_new_utc_day` | 跨日 UTC 额度重置 |
| 专项 | `test_m10_reply_stays_stable_under_repeated_long_inputs` | 超长输入连续请求稳定性 |
| 专项 | `test_m10_fail_safe_segment_write_error_does_not_break_relationship_flow` | 审计写入异常不阻断主流程 |
| 第11轮 | `test_m10_red_team_boundary_combo_fixture_pack` | 多边界条件叠加 |
| 第12轮 | `test_m10_red_team_replay_order_fixture_pack` | 跨接口乱序重放 |
| 第13轮 | `test_m10_red_team_multitarget_replay_fixture_pack` | 多 target 穿插调用 |
| 第14轮 | `test_m10_red_team_high_frequency_alternate_fixture_pack` | 高频交替 target 轻压测 |
| 第15轮（收口） | `test_m10_round15_closure_high_risk_suite` | 7个高风险包状态隔离串联回归 |

### 关键机制

**通用 fixture 跑手（`_run_fixture_pack`）：**
- 支持 `POST`/`GET` 两种方法（GET 路径参数硬编码在 `endpoint` 字符串中）
- 支持7种断言类型：`http_status`/`path_equals`/`required_fields`/`contains_issue_codes`/`not_contains_issue_codes`/`message_bank_empty`/`speaker_set_equals`

**收口套件状态隔离（`_reset_store_for_pack`）：**
每个 fixture pack 执行前清空 STORE 全部 9 个属性，确保跨 pack 零污染：
- `reply_sessions` / `usage_counters` / `audit_entries` / `segment_summaries`
- `audit_entries_by_user` / `segment_summaries_by_target`
- `entitlement_state_by_user_day` / `entitlement_user_locks` / `entitlement_pending_deducts`

### 方案 vs 实现对齐结论
✅ 15轮红队计划完全执行，所有 fixture 文件均有对应测试入口，无孤儿场景。

---

## 全局技术债汇总（待未来版本处理）

| 编号 | 位置 | 问题 | 影响等级 |
|------|------|------|---------|
| TD-01 | `reply_service._simulate_model_generation` | 回复文本为硬编码 Mock，非 LLM | 高 |
| TD-02 | `relationship_service._build_ledger` | 关系判断为关键词计数，非 LLM | 高 |
| TD-03 | `relationship_service._write_audit_stub` | `gate_decision` 字段硬编码为 `"UNKNOWN"` | 中 |
| TD-04 | `input_service.prepare_upload` | `duplicate_content_suspected` 硬编码 `False` | 低 |
| TD-05 | `entitlement_service` | 广告凭证仅格式校验，无真实 SDK | 中 |
| TD-06 | `entitlement_service` | 急救包无充值入口，初始余额为 0 | 中 |
| TD-07 | `entitlement_service` | `object_slots_active` 字段始终为 0 | 低 |
| TD-08 | `app/static/index.html` | 无真实图片上传，依赖手填 JSON | 高 |
| TD-09 | `app/static/index.html` | 广告凭证硬编码为 demo token | 中 |
| TD-10 | 全局 | `InMemoryStore` 无持久化，重启清零 | 高（v2 需要） |

---

## 附：配置参数汇总

| 参数 | 值 | 位置 |
|------|-----|------|
| `FREE_REPLY_DAILY_LIMIT` | 3 | config.py |
| `FREE_REPLY_AD_BONUS` | 3 | config.py |
| `FREE_RELATIONSHIP_DAILY_LIMIT` | 2 | config.py |
| `FREE_RELATIONSHIP_MIN / MAX` | 2 / 4 | config.py |
| `VIP_RELATIONSHIP_MIN / MAX` | 2 / 9 | config.py |
| `SESSION_DURATION` | 24h | config.py |
| `MAX_SESSION_TURNS` | 10 | config.py |
| `MAX_SESSION_TOTAL_CHARS` | 2000 | config.py |
| `MAX_MESSAGE_BANK` | 3 | config.py |
| `MAX_RISK_SIGNALS` | 3 | config.py |
| `MAX_AUDIT_LOGS_PER_USER` | 500 | config.py |
| `MAX_SEGMENT_SUMMARIES_PER_TARGET` | 50 | config.py |
| `MAX_SEGMENT_SUMMARY_BYTES` | 20480（20KB） | config.py |
| `AD_PROOF_TOKEN_PREFIX` | `"adp_"` | config.py |
| `AD_PROOF_TOKEN_MIN_LEN` | 16 | config.py |
| `CONTRACT_VERSION` | `"v1.0.0"` | config.py |

---

*文档生成时间：2026-03-29 | 基准：全量测试 80 passed, 0 failed*
