# JoyPilot v1.0.0

> 基于截图的恋爱关系判断与回话建议工具。用户上传聊天截图，系统输出"关系状态判断"与"现在怎么回"两大核心能力，所有判断均在本地内存完成，不依赖外部 AI 调用。

---

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务（默认端口 8000）
uvicorn app.main:app --reload

# 运行全量测试（80个测试用例）
python -m pytest
```

访问 `http://localhost:8000` 打开前端界面。

---

## 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 前端主页面 |
| GET | `/health` | 服务健康检查，返回版本与限额配置 |
| POST | `/upload/prepare` | 截图上传预处理（排序、OCR预览、对话结构化） |
| POST | `/reply/analyze` | 回话分析（生成3条回复建议 + YES/WAIT/NO 建议） |
| POST | `/relationship/analyze` | 关系判断（输出关系状态 + 结构化诊断） |
| GET | `/entitlement/state/{user_id}` | 查询用户当日权益使用状态 |
| GET | `/api/state` | 查询服务内存状态快照（仅调试用） |

---

## 项目结构

```
joypilot/
├── app/
│   ├── main.py                  # FastAPI 入口，路由注册
│   ├── config.py                # 全局配置常量
│   ├── contracts.py             # Pydantic 数据模型（请求/响应契约）
│   ├── storage.py               # 内存存储（InMemoryStore 单例）
│   ├── input_service.py         # module-1：截图上传整理链路
│   ├── gates.py                 # module-2：门禁与安全规则
│   ├── reply_session_service.py # module-3：回话 Session 管理
│   ├── reply_service.py         # module-4：回话主链
│   ├── signal_service.py        # module-5：信号解析
│   ├── relationship_service.py  # module-6：关系判断主链
│   ├── entitlement_service.py   # module-8：权益与商业化
│   ├── audit_service.py         # module-9：审计日志与对象摘要
│   └── static/
│       ├── index.html           # module-7：Web/PWA 主界面
│       ├── manifest.webmanifest
│       └── service-worker.js
├── fixtures/
│   ├── module-0/minimal_contract_fixtures.json
│   ├── module-1/red_team_regression_fixtures.json
│   ├── module-2/red_team_regression_fixtures.json
│   └── module-10/               # 11个红队 fixture 文件
├── tests/test_api.py            # 全量测试（80个用例）
├── docs_control_center/
│   ├── DEV_WORKFLOW.md          # 端到端开发工作流（与 module + 治理脚本对齐）
│   ├── FIELD_REGISTRY.md
│   ├── CHANGE_IMPACT_MATRIX.md
│   └── log.md
└── requirements.txt
```

---

## 各模块详细说明

开发顺序、治理命令（`field_sync` / `implement_doc_report`）与交付检查清单见 **[docs_control_center/DEV_WORKFLOW.md](docs_control_center/DEV_WORKFLOW.md)**。

---

### module-0 — 项目骨架与唯一真相源

**涉及文件：** `app/config.py` · `app/contracts.py` · `app/storage.py`

#### 1. 能做什么（核心能力）

定义全系统共用的枚举、Pydantic 数据模型、配置常量、内存存储结构，作为所有模块的唯一口径来源。

**核心数据模型（`contracts.py`）：**

| 模型 | 用途 |
|------|------|
| `UploadPrepareRequest` | `POST /upload/prepare` 请求体 |
| `PreparedUpload` | `POST /upload/prepare` 响应体，也是后续关系判断的输入 |
| `ReplyAnalyzeRequest` | `POST /reply/analyze` 请求体 |
| `ReplyAnalyzeResponse` | `POST /reply/analyze` 响应体 |
| `RelationshipAnalyzeRequest` | `POST /relationship/analyze` 请求体 |
| `RelationshipAnalyzeResponse` | `POST /relationship/analyze` 响应体 |
| `Dashboard` | 所有分析响应中的通用面板字段（17个字段） |

**核心枚举：** `Tier(FREE/VIP)` · `Mode(REPLY/RELATIONSHIP)` · `GateDecision(ALLOW/DEGRADE/BLOCK)` · `SafetyStatus(SAFE/CAUTION/BLOCKED)` · `Recommendation(YES/WAIT/NO)` · `EvidenceQuality(SUFFICIENT/LOW_INFO/INSUFFICIENT)`

#### 2. 能做到什么地步（边界与限制）

- 所有模型用 Pydantic v2 强制校验，字段类型非法直接返回 422
- 枚举值均为字符串枚举（`str, Enum`），序列化后直接输出字符串值
- `InMemoryStore` 是进程级单例，重启后全部清零，无持久化

#### 3. 核心防御与兜底

- `RelationshipAnalyzeRequest.prepared_upload` 为必填字段（非 Optional），关系判断接口强制要求先经过 `/upload/prepare`

#### 4. 工作流程

无运行时逻辑，纯定义层。所有模块启动时 import 各自需要的模型/常量。`STORE = InMemoryStore()` 在模块级实例化，全局共享。

---

### module-1 — 输入整理链路

**涉及文件：** `app/input_service.py`
**输入模型：** `UploadPrepareRequest` → **输出模型：** `PreparedUpload`

#### 1. 能做什么（核心能力）

接收截图列表，输出结构化的"可判断材料"，包括：
- 截图排序（按 `upload_index` 或时间戳）
- OCR 预览结构化（将 `left_text` / `right_text` 映射为带序号的预览列表）
- 对话结构化（`DialogueTurn` 列表，区分 `SELF` / `OTHER` / `LEFT` / `RIGHT`）
- 证据质量评估（`EvidenceQuality`）
- 问题清单汇总（`issues` 列表，含 error / warning 两个等级）

#### 2. 能做到什么地步（边界与限制）

**截图数量限制（关系判断模式）：**
- FREE：最少2张，最多4张
- VIP：最少2张，最多9张
- 超出任何上限直接输出 `SCREENSHOT_TOO_MANY` 或 `MAX_SCREENSHOTS_EXCEEDED` error

**截图排序规则：**
- 所有截图的 `upload_index` 全部合法（非 None 且 > 0）→ 按 `upload_index` 升序，同值按 `image_id` 兜底
- 任意一张 `upload_index` 非法或缺失 → 回退到按 `timestamp_hint` + `image_id` 排序，并附加 `UPLOAD_INDEX_INVALID` warning
- 全部无 `upload_index` → 静默按 `timestamp_hint` 排序，不产生 warning

**证据质量判定阈值（三条件任一触发 → INSUFFICIENT）：**
- 有效轮数 < 2（`LOW_INFO_MIN_EFFECTIVE_TURNS`）
- 有效字符数 < 8（`LOW_INFO_MIN_EFFECTIVE_CHARS`）
- 低信息轮数占比 ≥ 70%（`LOW_INFO_RATIO_THRESHOLD`）

低信息文本判断：空字符、长度 ≤ 2 的字符串，或命中白名单短语（"哦/嗯/好/哈哈/ok/收到"）。

**关系判断模式的强制前置门禁（缺一不可）：**

| 门禁条件 | 错误码 |
|---------|--------|
| 至少1张截图 | `NO_SCREENSHOTS` |
| `timeline_confirmed = true` | `TIMELINE_UNCONFIRMED` |
| `my_side` 已指定 | `ROLE_UNCONFIRMED` |
| OCR 预览非全空 | `OCR_EMPTY` |
| 证据质量不为 INSUFFICIENT | `INSUFFICIENT_EVIDENCE` |
| 不允许纯文本直传（v1） | `TEXT_DIRECT_NOT_ALLOWED` |

- 🚧 **OCR 并非真实识别**：`left_text` / `right_text` 必须由调用方（前端）直接传入，后端无图像识别能力，`OCRPreviewItem` 只是字段的结构化映射

#### 3. 核心防御与兜底

- `status = "READY"` 当且仅当 `issues` 列表为空；任何 issue 存在时均输出 `"NEEDS_REVIEW"`
- `dedupe_issues()` 全局去重，同一 `(code, message)` 只保留一条
- `duplicate_content_suspected` 字段硬编码为 `False`（🚧 检测逻辑未实现）

#### 4. 工作流程

```
UploadPrepareRequest
  → _sort_frames()           # 判断排序策略，生成 order_issues
  → 生成 OCRPreviewItem 列表  # 按序号映射 left/right text
  → 生成 DialogueTurn 列表   # 根据 my_side 映射 SELF/OTHER
  → _build_prepare_issues()  # 截图数量/时间线/角色/OCR/文本直传校验
  → _build_evidence_metrics() → _build_evidence_quality()
  → mode_requires_evidence_guard() # 如为 RELATIONSHIP 且 INSUFFICIENT → 追加 error
  → dedupe_issues()
  → status = "READY" / "NEEDS_REVIEW"
  → 返回 PreparedUpload
```

---

### module-2 — 门禁与安全规则层

**涉及文件：** `app/gates.py`
**依赖：** `app/entitlement_service.py`（调用 `check_and_lock_entitlement`）

#### 1. 能做什么（核心能力）

对进入回话/关系判断主链之前的请求执行多层过滤，输出 `(GateDecision, SafetyBlock, issues, check_id)` 四元组。

- 继承 module-1 的物理/输入门禁
- 检测高敏语境（14种词汇，含抑郁/自残/生理期等）
- 检测操控意图（user_goal_mode 含"逼她/服从测试/冷暴力"等8个词）
- 检测 Prompt 注入（6种模式）
- 检测 No-Contact 场景（"拉黑/别联系/报警"等6个词）
- 商业化次数校验与锁定

#### 2. 能做到什么地步（边界与限制）

**检测能力：** 全部为关键词字符串匹配（`in lowered`），无语义理解，无正则，无 NLP 模型。

- 覆盖词汇固定写死在 `config.py` 中，无动态更新机制
- 只匹配中文词汇（部分英文模式如 `no-contact`、`ignore previous` 有覆盖）
- 高敏语境检测范围：传入 `texts` 列表中的全部文本拼合后匹配

🚧 **广告凭证验证：** `validate_ad_proof_token` 只校验：① 是否以 `"adp_"` 开头；② 字符串长度 ≥ 16。无真实广告 SDK 对接，任何满足格式的字符串均视为合法。

#### 3. 核心防御与兜底

**五层过滤顺序（短路执行）：**

| 层级 | 触发条件 | 决策 | 是否扣费 |
|------|---------|------|---------|
| 1 | `prepared.status != "READY"` | BLOCK（有 error）/ DEGRADE（无 error） | 否 |
| 2 | 高敏语境命中 + `consent_sensitive=False` | BLOCK | 否 |
| 3 | 商业化校验失败 | BLOCK | 否（lock 直接不创建） |
| 4 | No-Contact / 操控意图 | BLOCK | 否（已创建的 lock 被 release） |
| 5 | Prompt 注入 | DEGRADE | 是（check_id 保留） |

- **BLOCK 场景**：`allowed_to_generate_messages = False`，主链强制将 `message_bank` 清空为 `[]`
- **DEGRADE 场景**：只保留 STABLE tone 路线，强制 `Recommendation.WAIT`

#### 4. 工作流程

```
resolve_gate_decision(user_id, prepared, tier, ad_proof_token, ...)
  → Layer 1: prepared.status != "READY" → 短路返回 BLOCK/DEGRADE
  → Layer 2: detect_sensitive_context(texts)
             命中 + consent=False → BLOCK("CONSENT_REQUIRED")
  → Layer 3: check_and_lock_entitlement()
             返回 BLOCK → 短路返回，不创建 check_id
  → Layer 4: assess_safety(texts, user_goal_mode)
             NO_CONTACT / MANIPULATION → release_entitlement_lock(check_id) + BLOCK
  → Layer 5: PROMPT_INJECTION → DEGRADE（保留 check_id，后续仍然扣费）
  → 全部通过 → ALLOW + check_id
```

---

### module-3 — 回话 Session 管理

**涉及文件：** `app/reply_session_service.py`
**存储：** `STORE.reply_sessions: dict[str, ReplySessionState]`

#### 1. 能做什么（核心能力）

为每个 `(user_id, target_id)` 维护一个独立的 24 小时会话，在会话期内保存对话上下文片段（用于回话生成的语义参考）。

- `get_or_create_session()` 原子性地获取或新建 session，返回 `(session, is_new: bool)`
- `update_session_after_reply()` 在每次回话成功后将本次文本写入 session
- session key 使用 `json.dumps([user_id, target_id])` 构造，防止分隔符碰撞攻击

#### 2. 能做到什么地步（边界与限制）

- **会话有效期：** 固定 24 小时，不滑动续期。`expires_at = start_at + timedelta(hours=24)`
- **上下文容量双重上限（FIFO 淘汰）：**
  - 轮数上限：最多 10 条 snippet（`MAX_SESSION_TURNS`）
  - 字符上限：所有 snippet 总字符 ≤ 2000（`MAX_SESSION_TOTAL_CHARS`）
  - 超出时从最旧条目开始淘汰
- **并发安全：** 使用 `threading.Lock`（不是 asyncio.Lock）实现每个 session key 独立的细粒度锁
- **强制新建：** `force_new_session=True` 无条件创建新 session，即使旧 session 尚未过期
- **session 不持久化：** 进程重启全部清零

#### 3. 核心防御与兜底

- `update_session_after_reply()` 在 session 不存在时静默返回（无异常）
- 单条 snippet 写入前先做截断：`text = text[:MAX_SESSION_TOTAL_CHARS]`（2000字符）
- session key 拼接用 JSON 序列化而非字符串拼接，防止 `user_id = "a:b"` 与 `target_id = "c"` 碰撞

#### 4. 工作流程

```
get_or_create_session(user_id, target_id, now, force_new)
  → key = json.dumps([user_id, target_id])
  → 获取 key 对应的 threading.Lock（无则创建）
  → with lock:
      existing = STORE.reply_sessions.get(key)
      if existing AND existing.expires_at > now AND not force_new:
          return (existing, is_new=False)
      else:
          新建 ReplySessionState(uuid, start_at=now, expires_at=now+24h)
          STORE.reply_sessions[key] = 新 session
          return (新 session, is_new=True)

update_session_after_reply(user_id, target_id, snippet, message_bank)
  → with lock:
      session = STORE.reply_sessions.get(key)
      if session is None: return
      _append_context(session, snippet)
          → 截断到 MAX_SESSION_TOTAL_CHARS
          → append 到 context_snippets
          → while len > MAX_SESSION_TURNS: pop(0)（轮数 FIFO）
          → while total_chars > MAX_SESSION_TOTAL_CHARS: pop(0)（字符 FIFO）
      session.last_message_bank = message_bank
```

---

### module-4 — 回话主链

**涉及文件：** `app/reply_service.py`
**输入模型：** `ReplyAnalyzeRequest` → **输出模型：** `ReplyAnalyzeResponse`

#### 1. 能做什么（核心能力）

接收用户当前输入（文本或 prepared_upload），经过门禁、信号解析、Session 上下文注入，输出结构化建议：
- 最多3条回话路线（STABLE / NATURAL / BOLD_HONEST），每条带 `text` + `reason`
- 行动建议（YES / WAIT / NO）
- 结构化诊断（`StructuredDiagnosis`）
- 风险信号列表（`signals`）
- Session 元数据（`ReplySessionMeta`）

#### 2. 能做到什么地步（边界与限制）

🚧 **回复文本是模板硬编码，不是 LLM 生成：**

`_simulate_model_generation()` 函数名称虽含 "simulate"，但代码注释明确说明这是 Mock 实现：

```python
# NOTE (LLM接入必读): safe_historical_context 和 non_instruction_policy 必须被注入
# 真实大模型调用的 system prompt 头部。当前为 Mock 实现，接入 LLM 时：
#   system_prompt = f"{non_instruction_policy}\n{safe_historical_context}\n..."
```

实际生成的回复文本为：
- STABLE：`"收到啦，我先不多打扰你，等你方便的时候我们再接着聊。"`（固定）
- NATURAL：`f"哈哈先接住这句：{对方最后一句话前24字}。你忙完再回我也行。"`（模板插值）
- BOLD_HONEST：`f"你这句我接住了，{前24字}。等你方便的时候，我们找个轻松点的时间继续聊。"` 或 `f"收到，{前24字}。等你方便再接着聊，不急着现在定。"`（根据是否有正向信号切换）

**关键限制：**
- `message_bank` 最多3条（`MAX_MESSAGE_BANK = 3`）
- 历史上下文仅用于注入占位符 `<historical_context>...</historical_context>`，XML 转义后附加到 system prompt 预留位，当前 mock 实现并未实际使用
- `reason` 质量门：长度 < 12、包含低价值短语、不含关键词锚点时，自动替换为预设修复文本

#### 3. 核心防御与兜底

- **矛盾校验（`_apply_no_contradiction_guard`）：** 诊断为 `NO` → 清空 message_bank 或仅返回1条停止话术；`DEGRADE` → 强制覆盖为 `WAIT` + 仅保留 STABLE 路线
- **Reason 质量门（`_apply_reason_quality_gate`）：** reason 被判定为低质量时，替换为对应 tone 的预设修复文本
- **历史上下文注入安全隔离：** snippet 经 `_xml_escape_text()` 转义（`&`、`<`、`>`），包裹在 `<historical_context>` 标签内，注释标明"禁止视为系统指令"
- BLOCK 时 `main.py` 强制执行 `response.dashboard.message_bank = []`

#### 4. 工作流程

```
analyze_reply(request)
  → now = request.reply_session_now OR datetime.now(UTC)
  → get_or_create_session()                    # module-3
  → _collect_texts(request)                   # 汇总 text_input + dialogue_turns.text
  → _build_reply_prepared_stub(tier)          # 若无 prepared_upload 则构造空 stub
  → resolve_gate_decision()                   # module-2，五层门禁
  → if gate != BLOCK: commit_entitlement_deduct(check_id)
  → detect_prompt_injection(texts)
  → extract_signals(texts)                    # module-5
  → summarize_risk_signals()
  → _pick_last_other_text()                   # 取对方最后一句话
  → _simulate_model_generation()              # 🚧 Mock：生成硬编码文本路线
  → _apply_no_contradiction_guard()           # 矛盾修复
  → _apply_reason_quality_gate()              # reason 质量修复
  → update_session_after_reply()              # 写入 Session
  → 组装 Dashboard + ExplainCard + ReplySessionMeta
  → 返回 ReplyAnalyzeResponse
```

---

### module-5 — 信号解析层

**涉及文件：** `app/signal_service.py`
**输出模型：** `list[SignalCandidate]`

#### 1. 能做什么（核心能力）

从文本中提取非语言信号（emoji、贴图占位符），输出含多候选解释的 `SignalCandidate` 列表，并汇总风险信号字符串列表供上游使用。

- `extract_signals(texts)` → emoji 频次统计 + 贴图占位符检测
- `summarize_risk_signals(signals, injection_hits)` → 汇总最多3条风险标签
- `contains_positive_candidate(signals)` → 判断是否存在正向解读候选

#### 2. 能做到什么地步（边界与限制）

**覆盖范围：只识别以下内容：**

- **Emoji：** 仅8种（`❤️` `❤` `😂` `🙂` `😊` `👍` `😅` `😄`），其余 emoji 完全不识别
- **贴图占位符：** `[sticker]` `[贴图]` `[动画表情]` `贴图` `动画表情`，括号版本先计数后替换，避免双计

**不覆盖：**
- 文字语义（如"好喜欢你"之类的明确正向表达不产生信号）
- 图片实体（需前端预先转换为占位符）
- 语气词、标点等其他非文本信号

**风险信号上限：** 最多3条（`MAX_RISK_SIGNALS = 3`），优先级顺序：注入风险 > 贴图盲区 > emoji 密度 > 低信息过度解读

#### 3. 核心防御与兜底

- 同一 (signal_type, raw_value) 组合做去重 + 频次累加（`_upsert_signal`），不重复输出同类信号
- `low_info` 标记采用"只升不降"策略（`existing.low_info or low_info`）
- 每条 `SignalCandidate` 均附 `note` 字段，明确标注"只作为候选信号，不直接作为关系定论"

#### 4. 工作流程

```
extract_signals(texts)
  → 遍历每条 text:
      for emoji in LOW_INFO_EMOJI(8种):
          if emoji in text:
              _upsert_signal(EMOJI, emoji, frequency, EMOJI_CANDIDATES[emoji])
      sticker_count = _count_sticker_placeholders(text)
          → 先计数括号版本并替换，再计数纯文本版本（避免双计）
      if sticker_count > 0:
          _upsert_signal(STICKER, "STICKER_PLACEHOLDER", low_info=True, ...)
  → 按首次出现顺序返回去重后的 SignalCandidate 列表

summarize_risk_signals(signals, injection_hits)
  → 优先级追加: 注入 > 贴图 > emoji密度(frequency>3) > 低信息
  → 截断到 MAX_RISK_SIGNALS(3)
```

---

### module-6 — 关系判断主链

**涉及文件：** `app/relationship_service.py`
**输入模型：** `RelationshipAnalyzeRequest` → **输出模型：** `RelationshipAnalyzeResponse`

#### 1. 能做什么（核心能力）

基于 `PreparedUpload` 中的对话结构，输出完整的关系状态诊断包，包含：
- 关系阶段标签（拉近 / 试探 / 模糊 / 冷 / 回避）
- 行动建议（YES / WAIT / NO）
- 不对等风险（J24 Ledger，定性：LOW / MEDIUM / HIGH）
- SOP 模式过滤（J25，检测推脱词）
- 探针动作建议（J26，低压力下一步）
- 现实锚点报告（J27，仅基于截图事实）
- **J28 终结词切片趋势分析**：以 "晚安/去忙" 等终结词为切片点，比较前后半段 OTHER 的时延状态；HOT→COLD 强制 WAIT，COLD→HOT 强制 YES（`gate_decision=DEGRADE` 时不触发）；覆写时当前实现仍会清空 `message_bank`（与基础 WAIT 分支不同，见 FRONTEND 口径）
- **J29 裸标点投资矩阵**：检测当前活跃窗口（Part_B 或全量）内 OTHER 的裸标点回复；触发则强制 WAIT + 文案；与 J28 矛盾时静默回退基础结论（不写任何文案），`gate_decision=DEGRADE` 时不触发；**WAIT 时不清空 `message_bank`，话术交由下游按 WAIT 语义降级生成**
- **J30 连续性打断检测**：无中段终结词、且末条为 SELF 时，由 `input_service.scan_flow_interruptions()` 统计「SELF→OTHER 间距 >3h 且 OTHER 窗口拼接文本为低价值或裸标点」次数；≥2 次则强制 WAIT 并写入 ledger【靠谱度警报】；**不清空 `message_bank`**，`gate_decision=DEGRADE` 时不触发
- 信号列表、门禁决策、审计写入

#### 2. 能做到什么地步（边界与限制）

🚧 **关系判断是关键词计数逻辑，不是 LLM：**

```python
positive_hits = _count_keywords(texts, POSITIVE_KEYWORDS)  # 8个正向词
negative_hits = _count_keywords(texts, NEGATIVE_KEYWORDS)  # 8个负向词
stage = _pick_stage(safety_status, positive_hits, negative_hits, low_info)
```

阶段判断规则（硬编码 if/else）：
- BLOCKED → "回避"
- negative > positive + 1 → "冷"
- positive > negative 且非低信息 → "拉近"
- low_info 为 True → "模糊"
- 其他 → "试探"

**J24 Ledger（不对等评估）：** 按 SELF/OTHER 对话总字符数比较，字符数 > 对方 × 1.5 → HIGH，否则定性降级。内部用字符数，输出禁止出现数字（`_enforce_j24_qualitative_only` 过滤伪量化表达）。

**J25 SOP 过滤：** 只检测5个推脱词（"改天/再说/忙完/下次/回头"），命中 ≥ 2 个 → MEDIUM，否则 LOW。

🚧 **J27 full_text：** 仅在 `tier=VIP` + `need_full_report=True` + `gate_decision≠DEGRADE` 时生成，内容为硬编码模板插值，不是 LLM 生成。

🚧 **`_write_audit_stub` 中 `gate_decision` 字段硬编码为 `"UNKNOWN"`：**
```python
payload={"safety_status": safety_status, "issue_codes": issue_codes, "gate_decision": "UNKNOWN"}
```

**隔离强制：** 函数首行检测 `session_data` 属性，若存在直接 `raise RuntimeError`，确保关系判断链路绝对不读取 Session 数据。

#### 3. 核心防御与兜底

- `_enforce_j24_qualitative_only`：过滤含数字比例、百分比、时长的表达
- `_enforce_j26_next_action_only`：过滤含"之前/历史证明"等回溯推断词
- `_enforce_j27_past_fact_only`：过滤含"将会/未来/迟早会"等未来预测词
- `_force_sop_footer`：强制将 `SopFilterSummary.footer` 写死为 `"模式提示不等于定罪。"`
- `_contains_pseudo_math()`：正则检测比例/数字/时长（5种模式），命中则替换为通用中性描述
- BLOCK 场景走独立 `_build_blocked_response()`，短路整个主链，`probes.available = False`，`message_bank = []`，`reality_anchor_report.access = "ALERT_ONLY"`

#### 4. 工作流程

```
analyze_relationship(request)
  → 检测 session_data 属性（存在则 RuntimeError，隔离保障）
  → resolve_gate_decision()                   # module-2 五层门禁
  → if BLOCK: return _build_blocked_response() # 短路，不执行主链
  → commit_entitlement_deduct(check_id)
  → detect_prompt_injection(texts)
  → extract_signals(texts)                    # module-5
  → validate_relationship_material(prepared)  # module-1 材料二次校验
  → _count_keywords(texts, POSITIVE/NEGATIVE) # 关键词计数
  → _pick_stage()                             # 5分支阶段判断
  → _pick_strategy()                          # 策略 + Recommendation
  → if DEGRADE: 强制覆盖为 WAIT + 维持
  → summarize_risk_signals()
  → _build_probes() → _enforce_j26_next_action_only()
  → _build_reality_anchor_report() → _enforce_j27_past_fact_only()
  → message_bank 生成（DEGRADE→1条稳妥; ALLOW+YES→1条低压探针; 其他→空）
  → _build_ledger() → _enforce_j24_qualitative_only()
  → _calculate_j28_trend()      # J28 终结词切片：HOT->COLD 强制 WAIT；COLD->HOT 强制 YES
  → _calculate_j29_matrix()     # J29 裸标点矩阵：当前窗口 OTHER 裸标点强制 WAIT；与 J28 矛盾时静默回退基础结论
  → scan_flow_interruptions()   # J30（input_service）：无终结词 + 末条 SELF 时统计长间隔低价值回应；≥2 → WAIT + 靠谱度警报
  → _build_sop_filter() → _force_sop_footer()
  → _write_summary_stub()                     # module-9 审计写入
  → _write_audit_stub()                       # module-9 审计写入
  → 返回 RelationshipAnalyzeResponse
```

---

### module-7 — 前端控制台（Web/PWA）

**涉及文件：** `app/static/index.html` · `manifest.webmanifest` · `service-worker.js`

#### 1. 能做什么（核心能力）

单页面应用（SPA），直接调用后端 REST API，提供以下操作面板：
- 截图上传预处理（调用 `POST /upload/prepare`）
- 回话分析（调用 `POST /reply/analyze`）
- 关系判断（调用 `POST /relationship/analyze`）
- 服务状态查看（调用 `GET /api/state`）
- 可安装为 PWA（桌面/移动端）

#### 2. 能做到什么地步（边界与限制）

🚧 **无真实图片上传能力：** 前端无文件选择器和图像上传逻辑。截图的 `left_text` / `right_text` 需要用户手动在 `<textarea>` 里填写 JSON。前端不做 OCR。

🚧 **截图数据格式：** 用户必须直接输入符合 `ScreenshotFrame` 格式的 JSON 数组，门槛较高。

- **PWA 缓存：** `service-worker.js` 仅缓存静态资源（`/` 和 `/static/`），API 请求不缓存
- **响应渲染：** 直接 `JSON.stringify(data, null, 2)` 格式化输出到 `<pre>` 元素，无字段映射
- **样式：** 纯暗色主题（`#0f172a` 背景），原生 CSS Grid 布局，无外部 UI 框架

#### 3. 核心防御与兜底

- fetch 请求统一 `try/catch`，错误在页面上以红色文字展示
- BLOCK 场景的 `message_bank = []` 由后端保证，前端仅透传展示

#### 4. 工作流程

```
用户填写 JSON → 点击按钮
  → fetch POST/GET 对应接口
  → try/catch:
      成功 → JSON.stringify 渲染到 <pre>
      失败 → 红色错误提示
```

---

### module-8 — 权益与商业化

**涉及文件：** `app/entitlement_service.py`
**存储：** `STORE.entitlement_state_by_user_day` · `STORE.entitlement_pending_deducts` · `STORE.entitlement_user_locks`

#### 1. 能做什么（核心能力）

管理用户每日使用次数，实现"先锁后扣"的幂等扣费机制：

- `check_and_lock_entitlement()` — 检查余量并创建 pending 记录（不立即扣费）
- `commit_entitlement_deduct(check_id)` — 主链成功后真正扣减计数
- `release_entitlement_lock(check_id)` — 主链在 BLOCK 前释放 pending 锁
- `build_usage_snapshot(user_id)` — 返回当日用量快照
- 每日额度自动按 UTC 日期重置（key 包含日期，新的一天自动隔离）

#### 2. 能做到什么地步（边界与限制）

**免费层额度：**
- 回话：每日3次，看广告后可多3次（上限6次）
- 关系判断：每日2次，每次必须提供广告凭证

**VIP 层：** 回话无限制（直接 ALLOW），关系判断 2-9 张截图范围内无次数限制

🚧 **广告验证仅做格式校验：** 只检查 `ad_proof_token` 是否以 `"adp_"` 开头且长度 ≥ 16，无真实广告 SDK 接入。任何满足格式的字符串（如 `"adp_1234567890abcd"`）均视为合法凭证。

🚧 **急救包积分：** `EntitlementState.emergency_pack_credits` 字段存在，但无充值入口（没有任何 API 可以增加积分），初始值为0。测试中直接赋值 `state.emergency_pack_credits = 1` 模拟。

🚧 **对象位（`object_slots_active`）：** 字段定义在 `EntitlementState` 中，但始终为0，无相关业务逻辑。

**并发安全：** 每个 `user_id` 一把 `asyncio.Lock`，commit 和 release 都在锁内执行，防止并发重复扣费。

**幂等保障：** `commit_entitlement_deduct` 在扣费时先从 `STORE.entitlement_pending_deducts` pop 出记录（`pop(check_id, None)`），已 pop 或不存在时直接返回，自动幂等。

#### 3. 核心防御与兜底

- 扣费前检查 pending 记录是否存在（`pop` 操作天然幂等）
- `_count_pending_for_user()` 将 in-flight 的 pending 次数计入 effective_used，防止并发请求绕过限额
- BLOCK 情况下 `release_entitlement_lock()` 写入 `entitlement_release` 审计事件

#### 4. 工作流程

```
check_and_lock_entitlement(user_id, scope, tier, screenshot_count, ad_proof_token, use_emergency_pack)
  → async with asyncio.Lock(user_id):
      state = _get_or_create_state(user_id)   # key = "user_id:2026-03-29"（UTC日期）
      if use_emergency_pack:
          检查 emergency_pack_credits > 0
          → 通过: _create_pending_check() → EntitlementCheckResult(ALLOW, check_id)
          → 失败: EntitlementCheckResult(BLOCK, "EMERGENCY_PACK_REQUIRED")
      if scope == "reply":
          VIP → 直接 ALLOW
          FREE:
            effective_used = reply_used + pending_count
            < 3 → ALLOW
            3-5 → 需要广告凭证（格式校验）
            ≥ 6 → BLOCK("DAILY_LIMIT_REACHED")
      if scope == "relationship":
          截图数量超出 VIP 上限(9) → BLOCK
          FREE + 5-9张 → BLOCK("UPGRADE_REQUIRED")
          FREE + 2-4张 + 超额 → BLOCK("DAILY_LIMIT_REACHED")
          FREE + 2-4张 + 未超额 → 需要广告凭证
          VIP + 2-9张 → ALLOW

commit_entitlement_deduct(check_id)
  → pending = STORE.entitlement_pending_deducts.pop(check_id)  # 幂等
  → async with Lock(pending.user_id):
      更新 state: reply_used++ / relationship_used++ / emergency_pack_credits--
      write_audit_event("entitlement_commit", ...)
```

---

### module-9 — 审计日志与对象摘要预留层

**涉及文件：** `app/audit_service.py`
**存储：** `STORE.audit_entries` · `STORE.audit_entries_by_user` · `STORE.segment_summaries` · `STORE.segment_summaries_by_target`

#### 1. 能做什么（核心能力）

提供两个写入接口，供 module-6 和 module-8 在业务成功后异步旁路记录：

- `write_audit_event()` — 写入审计事件（事件名、用户、模式、元数据）
- `write_segment_summary()` — 写入对象摘要（target 的关系阶段、不对等风险、摘要文本）

#### 2. 能做到什么地步（边界与限制）

🚧 **v1 仅写不读：** 写入的审计日志和摘要数据在 v1 中没有任何接口可以读取，不参与关系判断，不对外暴露。完全是预留给未来版本的数据基础设施。

**容量上限（双轨存储）：**

| 存储 | 结构 | 上限 | 淘汰方式 |
|------|------|------|---------|
| `audit_entries_by_user[user_id]` | `deque(maxlen=500)` | 500条/用户 | 自动 FIFO |
| `STORE.audit_entries`（全局列表） | `list` | 500条/用户（手动清理） | 标记空dict后过滤 |
| `segment_summaries_by_target[target_id]` | `deque(maxlen=50)` | 50条/target | 自动 FIFO |
| `STORE.segment_summaries`（全局列表） | `list` | 50条/target（手动清理） | 标记空dict后过滤 |

**摘要体积上限：** 单条摘要序列化为 UTF-8 JSON 后不超过 20KB（`MAX_SEGMENT_SUMMARY_BYTES = 20480`）。

超限处理：先尝试截断（`summary` 文本截到 2000 字符，`payload` 条目截到20个），截断后仍超限则写入拒绝告警事件并 `return False`。

**审计敏感字段脱敏（白名单机制）：**
- 允许字段白名单 `_AUDIT_ALLOWLIST_KEYS`（48个字段）：仅状态码、决策、模式、规则等元数据
- 禁止字段黑名单 `_AUDIT_BLOCK_KEYS`：`ocr_preview` / `dialogue_turns` / `text_input` / `left_text` / `right_text`
- 字符串值截断到 512 字符，列表截断到 20 个元素

#### 3. 核心防御与兜底

- **全局 `try/except Exception`：** `write_audit_event` 和 `write_segment_summary` 最外层捕获所有异常，失败时静默 `return False`，绝不向上抛出，不影响主业务流程
- 摘要写入两道体积检查：第一道触发截断，第二道触发拒绝（双保险）
- legacy list（全局 `STORE.audit_entries`）的手动截断用"标记空dict后列表过滤"实现，不影响 deque 主存储

#### 4. 工作流程

```
write_audit_event(event, user_id, target_id, mode, payload)
  → try:
      构造 entry dict（时间戳 + 基础字段）
      if payload:
          sanitize_audit_payload(payload)
              → 遍历 key: 命中 BLOCK_KEYS → 跳过; 不在 ALLOWLIST → 跳过
              → value 截断到 512 字符
      _append_audit_entry(entry, user_id)
          → deque(maxlen=500) 自动 FIFO
          → STORE.audit_entries.append(entry)（同时写入全局列表）
          → _trim_legacy_audit_list()（手动修剪全局列表超量部分）
      return True
  → except Exception: return False（静默失败）

write_segment_summary(target_id, source_type, stage, summary, asymmetric_risk, payload)
  → try:
      构造 entry dict
      if payload: _sanitize_summary_payload(payload)
      if size > 20KB: _trim_segment_entry()（截断 summary + payload）
      if size still > 20KB:
          write_audit_event("SEGMENT_SUMMARY_TOO_LARGE", ...)
          return False
      _append_segment_summary(entry, target_id)
      return True
  → except Exception: return False（静默失败）
```

---

### module-10 — 验收与红队（测试框架）

**涉及文件：** `tests/test_api.py` · `fixtures/module-10/`（11个 JSON 文件）

#### 1. 能做什么（核心能力）

提供可重复执行的自动化测试套件：
- fixture 驱动的通用测试跑手（JSON 定义场景 → 自动断言）
- 支持 POST / GET 两种请求方法
- 支持7种断言类型：`http_status` / `path_equals` / `required_fields` / `contains_issue_codes` / `not_contains_issue_codes` / `message_bank_empty` / `speaker_set_equals`

全量测试：**80个测试用例，全部通过**（截至最后一次全量回归）

#### 2. 能做到什么地步（边界与限制）

**测试分层（18个 module-10 入口）：**

| 层级 | 入口测试 | fixture 文件 | 场景数 |
|------|---------|-------------|-------|
| 契约 | `test_m10_golden_contract_fixtures` | 自定义格式 | — |
| 冒烟 | `test_m10_smoke_fixture_pack` | `smoke_fixtures.json` | 5 |
| 负向 | `test_m10_negative_fixture_pack` | `negative_api_fixtures.json` | 4 |
| 红队第1轮 | `test_m10_red_team_fixture_pack` | `red_team_extended_fixtures.json` | — |
| 红队第2轮 | `test_m10_red_team_combined_fixture_pack` | `red_team_combined_fixtures.json` | 5步 |
| 红队第3轮 | `test_m10_red_team_timing_fixture_pack` | `red_team_timing_fixtures.json` | 4步 |
| 红队第4轮 | `test_m10_red_team_robustness_fixture_pack` | `red_team_robustness_fixtures.json` | — |
| 红队第5轮 | `test_m10_red_team_state_isolation_fixture_pack` | `red_team_state_isolation_fixtures.json` | — |
| 并发隔离 | `test_m10_concurrency_same_user_cross_target_session_isolation` | 无 fixture | 内联代码 |
| 幂等重试 | `test_m10_entitlement_commit_release_are_idempotent_under_retry` | 无 fixture | 内联代码 |
| 跨日重置 | `test_m10_entitlement_daily_limit_resets_on_new_utc_day` | 无 fixture | 内联代码 |
| 性能稳定 | `test_m10_reply_stays_stable_under_repeated_long_inputs` | 无 fixture | 内联代码 |
| 降级可用 | `test_m10_fail_safe_segment_write_error_does_not_break_relationship_flow` | 无 fixture | monkeypatch |
| 红队第11轮 | `test_m10_red_team_boundary_combo_fixture_pack` | `red_team_boundary_combo_fixtures.json` | — |
| 红队第12轮 | `test_m10_red_team_replay_order_fixture_pack` | `red_team_replay_order_fixtures.json` | — |
| 红队第13轮 | `test_m10_red_team_multitarget_replay_fixture_pack` | `red_team_multitarget_replay_fixtures.json` | — |
| 红队第14轮 | `test_m10_red_team_high_frequency_alternate_fixture_pack` | `red_team_high_frequency_alternate_fixtures.json` | — |
| 收口第15轮 | `test_m10_round15_closure_high_risk_suite` | 7个高风险包串联 | — |

**收口套件隔离机制：** 第15轮收口测试在每个 pack 执行前调用 `_reset_store_for_pack()`，清空 STORE 全部9个属性，确保跨 pack 无状态污染。

#### 3. 核心防御与兜底

- `_dispatch_request` 不支持 PUT/PATCH/DELETE（当前 API 无此类接口）
- GET 请求的路径参数硬编码在 fixture 的 `endpoint` 字段中（如 `"GET /entitlement/state/user-1"`）
- `_pick_path` 支持点号路径（如 `"reply_session.is_new_session"`）和数组索引（如 `"issues[0].code"`）

#### 4. 工作流程

```
_run_fixture_pack(fixture_path)
  → JSON.load(fixture_path)
  → for scenario in scenarios:
      _dispatch_request(endpoint_spec, payload)
          → split "POST /reply/analyze" → method="POST", path="/reply/analyze"
          → client.post(path, json=payload) 或 client.get(path)
      _assert_standard_assertions(scenario_id, response, data, assertions)
          → http_status 校验
          → path_equals: _pick_path(data, path) == expected
          → required_fields: _pick_path(data, path) 不抛异常即通过
          → issue_codes: 集合包含/不包含校验
          → message_bank_empty / speaker_set_equals 校验

test_m10_round15_closure_high_risk_suite()
  → for pack_name in [7个高风险pack]:
      _reset_store_for_pack()   # 清空全部 STORE 字段
      _run_fixture_pack(fixture_dir / pack_name)
```

---

## 核心配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `FREE_REPLY_DAILY_LIMIT` | 3 | 免费用户每日回话次数 |
| `FREE_REPLY_AD_BONUS` | 3 | 看广告后额外获得的回话次数 |
| `FREE_RELATIONSHIP_DAILY_LIMIT` | 2 | 免费用户每日关系判断次数 |
| `SESSION_DURATION` | 24小时 | 回话 Session 有效期（硬过期，不续期） |
| `MAX_SESSION_TURNS` | 10 | 单个 Session 最大对话轮数（FIFO） |
| `MAX_SESSION_TOTAL_CHARS` | 2000 | 单个 Session 最大总字符数（FIFO） |
| `MAX_MESSAGE_BANK` | 3 | 单次回话最多生成话术条数 |
| `MAX_RISK_SIGNALS` | 3 | 风险信号汇总上限条数 |
| `MAX_AUDIT_LOGS_PER_USER` | 500 | 每用户审计日志上限（FIFO 淘汰） |
| `MAX_SEGMENT_SUMMARIES_PER_TARGET` | 50 | 每对象摘要条数上限（FIFO 淘汰） |
| `MAX_SEGMENT_SUMMARY_BYTES` | 20480（20KB） | 单条摘要物理体积上限 |
| `FREE_RELATIONSHIP_MIN/MAX` | 2 / 4 | 免费层关系判断截图数量范围 |
| `VIP_RELATIONSHIP_MIN/MAX` | 2 / 9 | VIP 层关系判断截图数量范围 |
| `CONTRACT_VERSION` | v1.0.0 | API 响应中携带的契约版本号 |

---

## 依赖

```
fastapi     # Web 框架
uvicorn     # ASGI 服务器
pytest      # 测试框架
httpx       # 测试客户端（TestClient）
```
