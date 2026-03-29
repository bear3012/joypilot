JoyPilot 实施方案 MASTER PLAN v3.4-R5
最终执行版 / FAST-LAUNCH + SATELLITE / LOCKED

AI-first / Contract-first / Gate-driven / Persona-aware / Evidence-first / Safety-routed / Low-pressure / Free-reply-first / Screenshot-first / Single-target-slot / Web→PWA

文档定位

本版是在你给出的 v3.4-R4 基础上，完整吸收本轮讨论结果后形成的 当前执行版。
它不是轻量摘要，不是补丁说明，也不是替代稿，而是：

保留 v3.4-R4 的命名体系与主骨架
把本轮已经明确的 v1 产品范围收缩、关系判断免费/VIP 分层、回话功能 24 小时固定窗口 session、3 条话术输出 + 短解释 全部嵌入原结构
明确哪些是 快速上线必须做，哪些继续进入 卫星版/后续升级版

本版目标收敛为以下五个：

快速上线
v1 只跑通 截图出话术 与 截图出关系判断 两个核心功能
用免费回话建立使用习惯
用分层关系判断与升级能力做付费差异
不退化成普通 AI 回复器、开放式 AI chat 壳、或廉价恋爱算命器

并补充三个写死目标：

不把 OCR、表情、单点信号、截图噪声直接当作“稳定语义真相”，而是通过确认、降级、结构化与风险提示，把误判危险度压到最低
v1 的关系判断必须是“截图驱动、单次性的、整理后再判断”的能力，不读取额外上下文，不做历史连续推断
v1 的回话功能允许“固定 24 小时 session 上下文”，仅服务于单日连续回复体验，不参与关系判断，不跨窗继承
0. 最终产品一句话定义

JoyPilot 会围绕同一个对象，基于聊天截图提取出的结构化对话，在风险、边界、低压力规则约束下，输出当前更适合发送的话术，或输出一次性的关系判断结果。

更短的用户版：

先看清，再决定怎么回。

更短的商业版：

不是嘴替，是截图驱动的话术辅助与关系判断。

更准确的内部定义：

JoyPilot 不是“会聊天的 AI”，而是“围绕单对象的截图驱动回话辅助 + 单轮关系判断系统”。

1. 最高原则（写死，不讨论）
1.1 Contract-first

先定义输入/输出契约（Pydantic / JSON Schema）→ 再写 fixtures（金样 / 红队 / 负向）→ 再实现。
任何模块不得绕过 contract 直接面向用户裸输出文本。

1.2 Deterministic-by-default
输出结构、字段顺序、枚举、排序规则：全部确定化
同输入同输出
允许多样性的地方必须 seed 固定
LLM 只能在允许字段内润色，不得改结构 / 意图 / 阈值结论
1.3 No silent failure
证据不足必须承认不足
图片顺序无法恢复必须拒绝深判断
单句不能装作看透整段关系
OCR 提取不可靠时必须要求用户确认
单个表情、单个表情包、单个暧昧信号不能直接上升为关系定论
回话 session 到期后必须硬清零，不能半继承
宁可降级，不可编造确定结论
1.4 Safety & Respect

禁止输出：

胁迫
羞辱
操控
纠缠
惩罚式冷落
内疚绑架
高压逼表态
阴阳怪气贬损
利用焦虑制造推进
将“顺从/听话”当成关系价值指标
将“服从测试”作为产品叙事或用户训练方向

写死补强：

不允许“服从测试/合规度=是否听话”的维度与叙事
不允许“图灵审判/逼露底牌/一击必杀/服从熔断”措辞与意图
不允许“毒舌羞辱/人格攻击型清醒报告”
Safety Block 命中时，message_bank 必须为空，只输出安全提示与下一步建议（非推进话术）
1.5 Consent-first for Sensitive Context
经期 / 健康 / 高隐私敏感语境：仅高权限可用
用户每次会话显式同意后才启用
不做健康推断
默认不点名
不入长期记忆 / 不入日志原文
1.6 Self-stability First

高压 / 不确定性 / 施压风险升高时优先：

降速
澄清
停止施压
转移注意力到自我生活
不优先推进
1.7 Aquarius Protocol

保留：

均值回归
现实结界
框架自洽锁
沉没成本熔断
暂停加码
1.8 Evidence-driven Stage Change

跨阶段只能由 Behavior Events 触发；
不能因为一句暧昧、一句热情、一次深夜高反馈、一个爱心、一个贴图就自动升级。

1.9 Baseline-first Interpretation

所有：

冷却
短回
忽冷忽热
退火
推进不足
低投入回应
表情回应
贴图回应

都必须走 Delta vs Baseline，不能脱离对象自己的历史节奏乱判。

但补充写死：

v1 的关系判断不读取历史上下文与对象摘要层
v1 的回话功能只允许读取当前固定 24 小时 session 内的上下文
Baseline-first 在 v1 主要用于系统结构保留、未来升级版与回话模式的轻量 session 内判断，不构成关系判断的历史入口要求
1.10 Platform-neutral Compliance

Web / PWA 与 App 同标准，不得因平台不同放松门禁。

1.11 Monetization Non-Coercive

命中高压 / 观察窗 / 敏感语境 / 冷却建议时：

禁止插屏
禁止冲动加购直达
不得用“清醒报告”做强 CTA
必须先给免费简版
必须给延迟入口
1.12 No Deceptive Ads Masking

广告必须明确标识为：

赞助
广告
微任务

不得伪装成：

继续分析中
深度推理中
即将解锁更高推理层
1.13 Emergency Bypass Is User-first

急救配额优先用户，不得在高压状态下羞辱式阻断。

1.14 RAG Recency & Conflict Safety

RAG 只做 DETAIL_ONLY；冲突默认 ASK_CLARIFY。
v1 不作为主增长引擎，但字段与接口保留。

1.15 Profile Size Cap
Target_Profile.json <= 20KB
确定化裁剪
只存 compact_profile + hash + baseline_stats
本版新增的对象摘要层也必须受这个上限约束
1.16 Structured-before-LLM

任何进入模型层的聊天数据，必须先完成最小结构化。
图片、OCR 原始块、乱序文本、未标角色的对话，均不得直接进入关系判断主链。

1.17 AI Is Candidate Generator, Not Final Judge

AI 可以参与：

候选解释
语言润色
模糊信号归因建议

AI 不可以直接决定：

有兴趣 / 没兴趣
值不值得继续
单个表情的唯一含义
单个暧昧信号的最终关系结论
1.18 Anti-Overinterpretation

产品必须主动防用户过度解读。
凡是信号不足、歧义高、语境弱、只出现单点正向符号时，必须提示：

当前是正向候选信号，而不是确定结论
禁止用单点信号做激进推进依据
输出必须附带低压策略与风险提醒
1.19 Prompt Injection Resistance

输入中出现的命令性文本、诱导性元指令、要求 AI 改写规则的文本，不得进入结论层。
系统必须把聊天内容当作证据，而不是把聊天里的“命令”当作系统指令。

1.20 v1 Relationship Judgement Narrow Scope

v1 的关系判断能力必须收窄为：

免费层：2–4 张聊天截图
VIP 层：2–9 张聊天截图
先做时间线整理
再做 OCR 提取
再做角色确认
再进行判断

写死边界：

不做文本直传关系判断
不做最近几轮上下文关系判断
不做历史连续关系判断
不做基于对象摘要层的关系判断
不做“给一句话/给一小段文本就判断关系”的轻量深判
1.21 v1 Reply Session Scope

v1 的回话功能必须支持 固定 24 小时 session 上下文：

以用户第一次触发回话功能为起点
session 有效期 = first_reply_request_at + 24h
session 不滑动续期
超过 24 小时后必须硬清零
session 仅作用于回话功能
session 不得参与关系判断
session 不得写入长期摘要层作为关系判断前情
2. 护城河定义（产品层 / v3.4-R5 重写版）

JoyPilot 护城河不是普通“高情商回复”。

JoyPilot 护城河 =

User Voice DNA
Reply Session Window
行为证据状态机
可解释动作输出
自动门禁留证
Risk & Finance-of-Attention 体系（J23/J24/J25）
J22 Boundary Reset
J26 Clarity Probe
J27 Reality Anchor Report
Safety Block + Allowed Actions
单对象连续摘要层（relationship segment summary，仅未来版使用）
免费回复带判断味道，而不是普通润色
OCR 结构确认 + 时间线整理 + 角色确认
表情/表情包只作为“情绪信号层”，而不是直接语义真相
AI 候选解释 + 规则融合，而不是 AI 单点定性

一句话护城河定义：

JoyPilot 的护城河不是帮用户更会聊，而是围绕一个对象，用截图驱动、可解释、可限制、可核验、可止损的系统，帮用户少误判、少错付、少上头，并给出更稳的下一步动作。

再补一条内部定义：

JoyPilot 的核心不是“生成回复”，而是“控制错误判断的危险程度，同时保持当天连续可用”。

3. 产品主形态：Relationship Radar Console（重构版）
3.1 输入端
3.1.1 Screenshot Ingestion

保留原结构，但改为 弱 OCR + 强确认 方案。

流程：

用户上传聊天截图
系统先做时间线预排与顺序展示
用户完成时间线整理
系统对已确认顺序的截图执行 OCR / 视觉提取
系统展示 OCR 结果预览
用户完成角色确认
再进入关系判断或话术生成

写死规则：

OCR 是输入辅助层，不是分析真相层
第一版不追求“自动理解所有截图语义”
第一版不做重型版面语义解析系统
所有用于关系判断的截图输入都必须经过时间线整理、OCR 提取、角色确认后，才能进入关系判断主链
所有用于截图话术的输入，可走轻量结构化链路，但仍需最小可读性保证
3.1.2 Briefing Ingestion

用户可补充：

当前更想回一句，还是看关系状态
当前目标：
CONTINUE
LIGHT_PROGRESS
CLARIFY
PAUSE
CLOSE

写死限制：

Briefing 输入不构成 v1 关系判断前情
Briefing 只作为界面辅助与策略路由，不替代截图判断主链
3.1.3 Counterparty Metadata

保留最小必需集：

是否已线下见面
是否曾有暧昧推进
是否存在金钱索取
是否存在多次失约
是否有 no-contact / 拉黑 / 明确拒绝

写死限制：

这些元数据可用于安全边界与输出语气调节
但 v1 不做基于元数据的深上下文关系判断
3.1.4 User Goal & Style Input

v1 只保留轻量模式：

target_goal_mode
CONTINUE
LIGHT_PROGRESS
CLARIFY
PAUSE
CLOSE
style_mode
STABLE
NATURAL
BOLD_HONEST（仅部分场景与高阶层可用）
3.1.5 User Regulation Snapshot Input

保留最小问法：

现在是否很想立刻发
今天是否已反复看这段聊天很多次
现在更想推进还是更怕失去

用途只限：

路由
降级
保护用户状态
3.1.6 Text Direct Input

文本输入保留，但只服务于回话模式。

写死边界：

文本输入不进入 v1 关系判断模式
v1 关系判断只接受截图上传流程
文本输入可加入回话 session，但不可跨窗保留
3.2 首页交互（最终版）
3.2.1 不做开放式自由提问
不做通用 chat 输入框
不让用户自己问一大串问题
不把产品做成开放 AI 对话
3.2.2 统一上传区 + 固定动作按钮

首页主流程：

上传聊天截图 / 粘贴聊天记录文本
系统解析并预览
根据模式进入不同流程
展示固定动作按钮
3.2.3 固定动作按钮

免费可见：

回话
关系判断

付费锁定展示：

完整动作方案
VIP 关系判断
3.2.4 V0 核心使用场景

第一版最小闭环的真实使用场景写死为：

回话模式
用户上传当前对话相关截图，或输入当前局部对话文本
系统输出：
轻判断
3 条回复建议
每条对应短解释
关系判断模式
用户上传 2–9 张同一对象截图
用户完成时间线整理
系统执行 OCR 提取
用户完成角色确认
系统输出：
结构化诊断
风险提示
当前策略
关系判断解释

不做开放式随意分析，不做无上下文自由聊天陪聊。

3.3 关系判断模式（v1 分层版，强制截图流程）
3.3.1 功能定位（写死）

v1 的关系判断功能，定位为：

基于同一对象聊天截图，在用户完成时间线整理、OCR 提取文本、角色确认后，输出一次性的关系判断结果。

分层如下：

免费轻量关系判断：2–4 张截图
VIP 完整关系判断：2–9 张截图

写死边界：

只做单次截图输入后的单轮判断
不做文本直传版关系判断
不做历史连续关系判断
不做基于对象摘要层的上下文关系判断
不做“给一句话/一小段聊天就判断关系”的轻量深判
3.3.2 输入门槛（强制）

关系判断模式不接受：

单句
单张图
文本粘贴
零散聊天片段

关系判断只接受以下输入：

免费层
2–4 张同一对象的聊天截图
VIP 层
2–9 张同一对象的聊天截图

补充写死：

免费层与 VIP 层都必须走同一条基础整理链路
差异在于材料上限、判断完整度、解释完整度、输出深度
2–4 张在 VIP 内仍属于“轻量材料”
5–9 张在 VIP 内才属于“标准材料”
3.3.3 上传与整理流程（强制）
第一步：上传截图

用户上传：

免费：2–4 张同一对象聊天截图
VIP：2–9 张同一对象聊天截图
第二步：时间线整理

系统必须提供：

顺序展示
拖动排序
删除无关图片
补充缺失图片
若可识别时间戳，优先自动排序
若自动排序不可靠，提示用户手动确认

写死要求：

未完成时间线确认，不得进入后续判断。

第三步：OCR 提取文本

系统对已确认顺序的截图执行：

OCR / 视觉提取
粗分行
生成结构化文本预览

写死要求：

OCR 是关系判断前的必要步骤
OCR 提取结果必须可预览
OCR 结果明显异常时，必须提示用户返回整理，而不是直接硬判
第四步：角色确认

系统必须明确询问：

“聊天里哪一方是你？”

用户必须完成角色标记，例如：

左边是我 / 右边是对方
蓝色气泡是我 / 白色气泡是对方

写死要求：

未完成角色确认，不得进入关系判断。

第五步：进入判断

只有在以下步骤全部完成后，系统才允许进入关系判断：

截图数量满足当前层级门槛
时间线已确认
OCR 已提取
角色已确认
3.3.4 记录质量校验（强制）

若出现以下任一情况，必须拒绝关系判断，并降级提示用户重新整理：

免费层截图不足 2 张
免费层截图超过 4 张但未切换到 VIP
VIP 层截图超过 9 张且用户未裁剪
截图顺序明显混乱且无法恢复
OCR 提取失败或大面积乱码
用户未标记哪一方是自己
关键聊天内容被截断严重
大量无关图混入
时间线断裂严重
3.3.5 降级策略（强制）

当输入不足以支持关系判断时，只允许返回：

当前材料不足，无法进行关系判断
免费关系判断请上传 2–4 张同一对象聊天截图
VIP 关系判断请上传 2–9 张同一对象聊天截图
请先完成 时间线整理、OCR 提取、角色确认
当前可改用“回话模式”解决现在怎么回
3.3.6 v1 最低可信前提

只有在满足以下条件时，系统才允许输出关系判断：

上传了当前层级允许数量的同一对象截图
时间线经过用户确认
OCR 已成功提取主要文本
用户已明确标记自己是哪一方
没有严重错序、严重截断、严重噪声
3.3.7 免费层与 VIP 层差异（写死）
免费轻量关系判断
材料：2–4 张截图
频次：一天 2 次
条件：需看广告
输出：
轻量关系判断
一句话解释
2–3 条现实锚点 brief
明确材料量级提示
VIP 关系判断
材料：2–9 张截图
输出：
完整关系判断
更完整风险解释
更完整策略说明
更完整关系锚点说明
若材料为 5–9 张，则标记为标准材料判断
3.3.8 设计目的（写死说明）

关系判断模式之所以在 v1 强制要求：

2–9 张截图分层
时间线整理
OCR 提取文本
角色确认

是为了防止 AI 出现以下误判：

把用户的话当成对方的话
把聊天顺序搞反
把单次冷淡误判成关系降温
把单次热情误判成高好感
把 OCR 噪声误判成真实语义
在缺少基础整理的情况下输出看似专业但不可靠的关系结论
3.3.9 v1 明确不做（写死）

v1 的关系判断功能明确不做：

文本粘贴版关系判断
最近几轮上下文关系判断
长期上下文关系判断
基于历史摘要层的连续关系判断
基于对象 profile 的跨轮关系演化判断

一句话写死：

v1 关系判断只认当前这次上传并整理完成的截图，不读取额外上下文，不做连续记忆推断。

3.3.10 表情与表情包在关系判断模式中的规则

关系判断模式中，表情与表情包只允许作为：

情绪信号
投入强度信号
回复方式信号

不得直接作为：

单点兴趣结论
单点冷淡结论
单点人格结论

例如：

单个 ❤️ 只能视为正向候选信号之一
单个 😂 只能视为轻正向或轻化解信号之一
单个贴图只能视为存在非文本情绪表达，不能直接视为高兴趣

并补充写死：

即便在关系判断模式里，v1 也不做上下文判断；表情/表情包仅基于本次上传截图中的局部证据参与候选解释与风险提示。

3.4 回话模式

回话模式是 v1 前期最重要的增长引擎。

输入门槛：

当前一句
当前截图中的局部上下文
或一小段聊天文本
或当前对话相关截图

输出：

3 条回复路线
稳妥版
自然版
主动版
每条必须带一条短解释
并明确：
可以发
先等等
不建议发

作用：

解决“现在这句怎么回”。

3.4.1 回话 session 机制（写死）

回话模式必须支持 固定 24 小时 session：

用户第一次触发回话功能时，创建 session
记录：
reply_session_start_at
reply_session_expires_at = start_at + 24h
在该 24 小时内，回话模式可读取本 session 的上下文
超过 24 小时后：
必须清空 session
不得自动续期
不得部分继承
不得把旧 session 混入新 session
3.4.2 回话 session 作用范围（写死）

回话 session 仅允许用于：

连续回话体验
维持当下语气连续性
维持同一段对话的轻量上下文
避免用户在 24 小时内反复重复贴同样材料

回话 session 明确禁止用于：

关系判断
历史连续关系推断
长期风险画像
次日上下文继承
对象摘要层前情写回为关系判断依据
3.4.3 回话输出要求（写死）

每次回话必须输出 3 条：

稳妥版
风险最低
更适合先维持互动
自然版
更像真实日常聊天
不显得太刻意
主动版
更适合当前存在轻正向信号时轻量推进
但仍必须低压力

每条都必须附带短句解释，例如：

稳妥版：更安全，适合先维持互动
自然版：更像顺着当前聊天接下去
主动版：适合当前局面下做轻量试探
3.4.4 回话功能写死边界
回话模式可以轻
但必须保留判断味道
不能退化成纯润色器
必须至少告诉用户当前更偏向：
可发
先等等
不建议发
3.5 回复可以轻，判断必须重（v1 铁律）
“怎么回”可以基于当前句、局部上下文、以及回话 session 内的 24 小时上下文窗口
“关系判断”在 v1 必须基于截图 + 时间线整理 + OCR 提取 + 角色确认
单句、单图、极少上下文时，禁止做完整关系定论
文本输入只服务于回话模式，不服务于 v1 关系判断模式
v1 关系判断不读取历史上下文，不做连续记忆判断
v1 回话功能允许读取固定 24 小时 session，但 session 到期后必须硬清零

再补一条：

单个 emoji、单个表情包、单个暧昧信号时，只允许输出“候选解释 + 风险提示 + 低压策略”，禁止输出“确定关系判断”
4. 输出端（固定区块：字段固定、可回归）
4.1 基础面板（必须输出）
action_light
tension_index
pressure_score
blindspot_risk
mean_reversion
availability_override
frame_anchor
gearbox_ratio_radar
cooldown_timer
focus_redirect
reciprocity_meter
sunk_cost_breaker
adaptive_tension
suggestive_channel
macro_stage
interest_discriminator_panel
stage_transition
message_bank（≤3，可编辑，可能为空）
v1 含义补充
action_light：总动作建议灯
tension_index：关系拉扯与不确定性
pressure_score：当前是否存在施压风险
blindspot_risk：是否存在脑补、投射、过度解读
cooldown_timer：建议静置时长
message_bank：当前场景允许给出的回复路线；Safety Block 命中时必须为空
v1 新增解释
blindspot_risk 必须覆盖“单点信号过度解读”
若只出现单个爱心、单个贴图、单个轻正向符号，且上下文不足，必须提高 blindspot_risk 或明确输出过度解读提示
回话模式下的 message_bank 必须支持 3 条路线输出
4.2 目标 / 风格 / 经济 / RAG / Profile / 广告（必须输出）

保留原字段，并重写 v1 解释：

target_goal_mode
style_mode
battery_quote
rewarded_ads_status
interstitial_status
validation_window
profile_meta
rag_meta
ad_eligibility
free_emergency_pass
anti_impulse_gate
v1 说明
style_mode 最终只保留：
STABLE
NATURAL
BOLD_HONEST
rewarded_ads_status 用于控制广告解锁是否可用
free_emergency_pass 用于高压场景免费简版
profile_meta 与对象摘要层共同受 20KB 上限约束
4.3 Safety Block（必须输出）

字段：

safety.status
safety.block_reason
safety.allowed_to_generate_messages
safety.note
v1 规则
BLOCKED 时 message_bank = []
不再继续生成推进型、追问型、纠缠型话术
只允许输出：
风险说明
暂停建议
现实动作建议
必要时安全资源入口
v1 呈现语气

不要用道德教育语气，改为：

为避免局面恶化，当前已暂时关闭话术生成功能
当前继续推进收益低、风险高
建议先暂停，而不是继续加码
v1 新增

出现以下情况时可提高 Safety 或直接降级：

明确 no-contact / 拉黑后仍要求推进
明显报复性、惩罚性、操控性推进
用户试图用单一信号强行要求系统背书
输入中出现明显 Prompt Injection 或“强行要结论”的命令型内容
4.4 J23 风险画像面板（必须输出）

字段保留：

relationship.context_detected
relationship.context_user_confirmed
relationship.context_confidence
target_persona.risk_profile
target_persona.confidence_score
v1 解释

J23 负责区分：

当前处于什么关系上下文
风险来自哪里
风险是上下文风险，而不是人格定罪
写死规则
context 和 risk 分离
不输出“渣/骗/玩弄”式人格定罪
不用单句定人格
不用单个 emoji / 单个贴图定人格
v1 边界补充

虽然字段保留，但 v1 关系判断不做外部上下文推断；
J23 在 v1 中主要基于本次截图材料给出保守型风险画像。

4.5 Explain Card + Opt-out（必须输出）

保留：

auto_overrides.active
auto_overrides.forced_style
auto_overrides.evidence_signals[]
auto_overrides.can_disable
auto_overrides.disable_cost_battery
auto_overrides.risk_banner_level
含义

告诉用户：

为什么当前给这种风格或建议
哪些证据触发了覆盖
哪里存在不确定性
v1 新增

Explain Card 必须允许明确写出：

当前结论高度依赖有限材料
当前正向信号存在多种可能解释
当前不建议过度解读
回话模式当前是否仍在 24 小时 session 内
4.6 J22 边界重置协议（必须输出）

字段保留：

recovery_protocol.state
recovery_protocol.can_exit
recovery_protocol.reset_ends_at
recovery_protocol.ping_attempts_left
recovery_protocol.violation_budget_remaining
recovery_protocol.violation_cost_battery
recovery_protocol.override_output_token_cap
recovery_protocol.instruction
v1 改写

J22 不砍空，但只做软版：

当前是否建议 pause
建议静置时长
是否建议 closure
是否建议 no-contact
一条中性止损指令
v1 明确不做
账号级硬锁
图像 hash 去重强控
同 case 24h 强制封禁
4.7 J24 非对称投资账本（必须输出）

字段保留：

ledger.window
ledger.input
ledger.output
ledger.metrics
ledger.ui
ledger.delta_vs_baseline
ledger.user_overextension_risk
ledger.stoploss_hint
ledger.commitment_gap_band
v1 改写

J24 从精确账本降级为定性失衡红灯。

v1 真正要做
asymmetric_risk = LOW | MEDIUM | HIGH
1–2 条证据解释
中性说明
v1 不做
精确金额核算
精确等待时长比值
精确净流量公式
v1 新增

单个爱心、单个贴图、单个暧昧回复，不得直接用来冲抵长期非对等投入信号。

4.8 J25 商业 SOP 防火墙（必须输出）

字段保留：

sop_filter.window_days
sop_filter.hits
sop_filter.total_hits
sop_filter.risk_escalation
sop_filter.evidence_signals[]
含义

提示：

模板式热情
高情绪价值低现实推进
节点式索取
模糊承诺反复延后
回流模板感
写死

模式提示不等于定罪。

4.9 J26 现实核验探针（必须输出）

字段保留：

probes.available
probes.items[]
L1_TIME
L2_RECIPROCITY
L3_CLOSURE
写死规则
不逼答复
不威胁
给出口
Safety BLOCK / no-contact / 高危场景时关闭
推进核验模块

在 J26 下新增：

progress_validation

对外定义为：

低压力推进核验

不是测试“顺从”，而是核验：

回流意愿
对等投入意愿
现实推进接受度
明牌承接能力
推荐字段
probe_type
intent
template
when_to_use
risk_level
expected_signal
do_not_overinterpret
followup_rule
probe_type
RETURN_SIGNAL
LIGHT_INVITE
DIRECT_INTEREST
RECIPROCITY_CHECK
followup 规则
正常接球：可轻微推进
模糊拖延：不加压，转观察
明确回避：不重复测试
无回应：不追打，不自动脑补单一结论
v1 新增

对于由表情/表情包触发的正向候选信号，只允许进入：

低压轻探针
不得直接升级为强推进
4.10 J27 现实锚点报告（必须输出）

字段保留：

reality_anchor_report.available
reality_anchor_report.tone
reality_anchor_report.access
reality_anchor_report.delay_gate_sec
reality_anchor_report.brief_points[]
reality_anchor_report.full_text
v1 免费层

给：

FREE_BRIEF
3 条 brief points
1 句状态说明
1 个当前建议动作
v1 付费层

给：

PREMIUM_FULL
更完整状态解释
更完整风险说明
为什么建议继续 / 暂停 / 收口
为什么可能判断错
继续保留
无羞辱
无胁迫
高压/观察窗时只给简版 + 延迟入口
v1 新增

J27 必须能解释：

为什么一个正向符号不等于稳定好感
为什么一个爱心可能是正向但仍需继续观察
为什么此时更适合低压推进而不是高压表白
4.11 Training Wheels（保留并重写）

保留：

STABLE
NATURAL
BOLD_HONEST
含义
STABLE：稳一点，风险最低
NATURAL：自然一点，更接近日常互动
BOLD_HONEST：更直接表达兴趣 / 邀约 / 边界，但仍低压力
分层规则
免费层

给：

STABLE
NATURAL
付费层

解锁：

BOLD_HONEST
重要说明

BOLD_HONEST 不是高压表态工具，不允许变成操控、逼答复或强索取承诺。
即便系统观察到单个爱心、单个贴图等正向候选信号，也不得自动切入 BOLD_HONEST。

5. 低压力好感框架（保留并重写）

三段式表达继续保留：

我（观察 / 感受）
不索取
给出口
5.1 JoyPilot 必须允许推进

不能只有：

防守
降温
普通朋友式聊天

否则产品会显得“不懂两性推进”。

5.2 但推进必须低压力

允许：

轻暧昧
轻明牌
轻邀约
轻表达兴趣
轻推进核验

禁止：

高压逼问
强索取承诺
以顺从判断价值
不照做就追责
惩罚式抽离
5.3 单点正向信号的推进规则

若只看到：

单个 ❤️
单个 😊
单个贴图
单条轻正向短回应

只允许：

低压延续
轻量试探
轻度推进核验

不得：

直接表白
直接高压邀约
直接输出“她已经明显有兴趣”的强结论
6. 系统架构（组件与强制数据流）
6.1 组件
Client（Web→PWA）

包含：

上传与时间线整理层
OCR 结果预览层
角色确认层
回话 session 提示层
Explain Card
Boundary Reset 面板
Ledger / SOP / Probe / Report 面板
回话入口
关系判断入口
广告与急救简版展示层
API（FastAPI）

包含：

entitlement
consent
audit_logger
normalize_service
screenshot_ingest
timeline_ordering_service
screenshot_ocr_ingest
dialogue_structurer
reply_session_service
emoji_signal_parser
non_text_signal_parser
candidate_interpretation_service
signals_service
baseline_service
behavior_event_extractor
goal_router
style_switcher
risk_profile_classifier
asymmetric_ledger_engine
sop_disclaimer_filter
probe_generator
progress_validation_engine
reality_anchor_reporter
safety_engine
prompt_injection_filter
profile_store
segment_summary_store
rewarded_ads_controller
payment / subscription / target_slot_manager
6.2 Core Engine（纯函数优先、可测试）

保留旧骨架并新增 session 层：

回话模式链路

J1 normalize
→ reply_session_gate
→ reply_session_context_load
→ dialogue_structure_build
→ emoji_signal_parser
→ non_text_signal_parser
→ candidate_interpretation_service
→ J2 signals
→ J16 goal_router
→ prompt_injection_filter
→ dashboard
→ strategies
→ J22 boundary_reset_engine
→ J7 safety_final_judgement
→ pack_reply_response
→ reply_session_context_write
→ audit_logger

关系判断模式链路

J1 normalize
→ timeline_ordering_confirm
→ ocr_preprocess
→ dialogue_structure_build
→ role_confirm_gate
→ emoji_signal_parser
→ non_text_signal_parser
→ candidate_interpretation_service
→ J2 signals
→ BehaviorEventExtract
→ J24 asymmetric_ledger_engine
→ J25 sop_disclaimer_filter
→ J23 risk_profile_classifier
→ J16 goal_router
→ entitlement_gate
→ consent_gate
→ prompt_injection_filter
→ J3 state_estimate
→ dashboard
→ J22 boundary_reset_engine
→ J26 probe_generator
→ progress_validation_engine
→ J27 reality_anchor_reporter
→ J7 safety_final_judgement
→ pack_relationship_response
→ audit_logger

写死说明
candidate_interpretation_service 只负责候选解释，不负责最终定性
emoji_signal_parser 与 non_text_signal_parser 只输出信号，不输出“真相判决”
timeline_ordering_confirm 与 role_confirm_gate 是关系判断硬门禁，不通过不得进入判断
reply_session_gate 只用于回话模式
v1 关系判断链路不读取对象摘要层作为前情输入
v1 关系判断链路不读取 reply session
7. 后台对象摘要层（保留但不接入 v1 关系判断）

这是重要模块。
它不是完整长期历史系统，而是轻量对象级阶段摘要层。

7.1 模块定义

模块名：

relationship segment summary

作用：

每次围绕某个对象完成分析后，在后台生成一份短摘要，仅供后续产品升级版、对象位连续能力、或未来版本使用。

7.2 设计原则
存摘要，不存全文
存前情，不存完整会话 replay
做轻 baseline，不做重型时序系统
下一轮可参考，但不是永久真理
必须允许被新证据修正
7.3 每段摘要建议存储字段
基础识别
target_id
summary_version
created_at
source_type
source_window_hint
已确认上下文事实
是否已见面
当前关系上下文
当前目标模式
本轮压缩状态
当前互动状态摘要
当前 tension / pressure / blindspot 风险
当前建议动作
当前 asymmetric_risk
当前 risk_profile
当前 recovery_protocol.state
本轮关键证据 bullets
3–8 条摘要证据
不存完整原文
只存高价值、低歧义压缩信息
本轮动作产出摘要
是否生成了 message_bank
是否触发 Safety Block
是否建议 pause / closure / no-contact
是否使用了 probe / progress_validation
本轮非文本信号摘要
是否存在 emoji 主导回应
是否存在 only-sticker / only-emoji 低信息回应
当前是否触发 overinterpretation 风险
7.4 明确禁止存储
不存整段 OCR 原文
不存完整聊天时间轴
不存逐句 embedding history
不做完整 replay
不做重型关系图谱
不做跨很多天的复杂状态机
7.5 读取规则

后续同对象分析时：

先读取最近 3–5 段摘要
再做“摘要的摘要”
拼成短前情提要
总量仍受 Target_Profile.json <= 20KB 约束
7.6 v1 边界（写死）

在 v1 中：

后台对象摘要层不参与当前关系判断主链
v1 的关系判断结果只基于本次上传的截图
摘要层可以保留数据结构与存储接口
但不得作为当前关系判断的输入前情
摘要层也不得作为回话 session 的替代层
7.7 作用
为未来连续版能力预留结构
为对象位升级版预留接口
当前 v1 不作为关系判断前置依赖
当前 v1 不读取该层做上下文推断
8. 商业化设计（最终版）
8.1 前期核心战略

JoyPilot 前期不是高客单 SaaS。
前期采用：

免费回话做增长与蒸馏，免费轻量关系判断做试用入口，VIP 关系判断与升级能力做变现。

补一条：

广告是流量辅助层，不是最终价值主引擎。

8.2 免费层
回话
每天 3 次免费
每次给 3 条回复
稳妥版
自然版
主动版
每条附带短解释
广告加回话
每天看广告再加 3 次回复
仍然输出 3 条路线 + 短解释
免费回话的最低要求

免费回话不能只是改写文案，必须至少带一个轻判断：

可以发
先等等
不建议发
免费回话的 session 规则
回话功能使用固定 24 小时 session
起点为用户第一次触发回话
超过 24 小时必须清零
不按自然日
不滑动续期
8.3 免费关系判断
每天 2 次
需看广告
必须上传 2–4 张同一对象聊天截图
必须完成：
时间线整理
OCR 提取
角色确认
若门槛不足，返回“材料不足”或降级到回话

输出：

当前互动状态
一句话解释
2–3 条现实锚点 brief
轻量材料提示

写死说明：

v1 免费关系判断不支持文本直传，不支持历史上下文，不支持连续对象摘要接入。

简版关系判断新增要求

若当前判断高度依赖 emoji / sticker / 单点暧昧信号，必须明确提示：

这是候选正向信号
当前信息量偏低
不建议过度解读
8.4 单次急救包

不能只有月付，保持写死。

单次急救包

价格可选：

4.9
6.9
9.9

用途：

一次 VIP 关系判断
或一次完整动作方案

作用：

降低首单门槛
回收部分流量成本
验证用户是否愿意为“更稳判断”付费
8.5 月付对象位（升级层）
模型

19.9 / 月 = 1 个活跃对象分析位

角色
不是唯一付费模式
是升级层
卖的是围绕单对象的连续使用权与升级能力入口
解锁内容
VIP 关系判断
更多回话次数
BOLD_HONEST
低压力推进核验
完整 probe
边界建议
更完整现实锚点
后台对象摘要层与未来连续版能力预留
文案

不要写：

一个月只能弄一个对象

要写：

包含 1 个活跃对象分析位
v1 边界补充

但在当前 v1 中，即便开通对象位，关系判断仍只基于本次上传并整理完成的 2–9 张截图，不读取历史上下文。

8.6 广告层的最终角色

广告只做：

免费引流
轻体验
解锁简版功能

广告不能做：

高压状态下刺激用户反复刷
伪装成推理过程
直接解锁完整动作包
无限广告续命
v1 新增

广告不能承诺：

看完广告就能得到“更高真相”
看完广告就能得到“对方真实心意”

广告只解锁更多使用与更多视角，不得伪装成真相背书。

9. 快速上线版：必须做什么

以下是 v1 必须做的最小闭环，不得再删：

截图上传
限制关系判断输入为分层截图数量：
免费：2–4 张
VIP：2–9 张
时间线整理
OCR / 视觉提取
OCR 结果预览
用户角色确认
文本输入模式（仅回话）
截图回话模式
回话 24 小时固定 session
session 起点与过期机制
3 路话术输出
每条短解释
emoji / sticker / 非文本信号解析
候选解释层
规则融合层
免费回话
免费关系判断简版
Safety Block
Prompt Injection 过滤
J22 软版
J24 定性版
J25 简版
J26 最小探针包
progress_validation
J27 brief/full 分层
单次急救包
19.9 对象位月付
广告轻层
后台对象摘要层（仅预留，不接入 v1 关系判断）
Web / PWA
v1 明确不做
文本直传关系判断
历史上下文关系判断
连续对象关系判断
基于摘要层的关系判断
回话 session 滑动续期
回话 session 参与关系判断
重型视觉理解
开放式自由关系分析聊天
10. 卫星版（明确延后）

以下全部进入卫星版，不能偷跑进 v1：

10.1 长期追踪类
J28 Evidence Graph
J29 Outcome Tracker
J30 ROI
J31 Trust Tier
10.2 Anti-Rumination 硬锁

不做：

同 case hash 强锁
24h 强锁
账号级重复分析封禁
10.3 精确账本与复杂经济系统

不做：

精确 J24
多层电池
插屏广告系统
复杂 AIG / ADG 大系统
10.4 开放式 chat

v1 不做自由问答聊天机器人。

10.5 多对象无限月包

v1 禁止“无限对象、无限分析”。

10.6 重型视觉理解

v1 不做：

重型贴图语义识别系统
meme 图像深理解
复杂图片语义人格解读
全自动无确认 OCR 智能纠错系统
10.7 连续关系判断

v1 不做：

历史对话连续推断
跨轮关系演化判断
摘要层驱动关系判断
文本 + 历史混合型关系判断
10.8 长期回话记忆

v1 不做：

跨 24 小时 session 继承
按自然日结算的模糊 session
无上限自动续期
长期恋爱记忆脑
11. 上线前红队检查表
11.1 必须通过
单句不会硬判关系状态
免费关系判断要求 2–4 张截图
VIP 关系判断要求 2–9 张截图
未整理时间线不得进入关系判断
未完成 OCR 提取不得进入关系判断
用户必须标记“哪一方是自己”
文本直传不得进入 v1 关系判断
v1 关系判断不得读取历史上下文
v1 关系判断不得读取后台对象摘要层做前情判断
v1 关系判断不得读取 reply session
OCR 结果不可靠时会要求确认或修正
免费回话有 3 条路线，不是 1 条
每条路线都有短解释
免费层允许轻推进，但不会高压推进
单个爱心不会被系统直接判成“明确有兴趣”
单个贴图不会被系统直接判成“明确冷淡”或“明确高好感”
表情/贴图只会进入候选解释与风险融合，不会单点定性
Safety Block 命中时 message_bank = []
Safety 呈现是策略保护，不是道德说教
广告不会在高压/观察窗关键路径强弹
广告不会伪装成推理过程
单次急救包存在，不会只有月付
月付对象位是升级层，不是唯一入口
推进核验存在，但不以“服从测试”命名和建模
后台摘要层只存压缩摘要，不存完整原文
输入中的 Prompt Injection 文本不会影响系统规则
输出能明确提示“过度解读风险”
回话 session 以首次触发为起点
回话 session 为固定 24 小时，不按自然日
回话 session 不得滑动续期
回话 session 到期后必须硬清零
11.2 必须拒绝
逼人表态
对 no-contact 对象继续推进
用羞辱或冷暴力测试好感
把顺从当成价值指标
人设伪装
把试探做成命令服从
把单个爱心包装成“几乎确定喜欢你”
把单个贴图包装成“她明显在敷衍你”
把聊天里的命令文本当作系统指令
11.3 必须降级
单句要求深判断
文本输入要求关系判断
免费层截图不足 2 张要求关系判断
免费层截图超过 4 张但未走 VIP
VIP 层截图超过 9 张但未裁剪
图片混乱要求完整关系判断
OCR 失败却要求继续判断
未做角色确认却要求关系判断
高压状态要求刺激性推进
OCR 噪声过大但用户未确认
只有 emoji / sticker 的低信息回应却要求深结论
reply session 已过期却继续要求按旧上下文输出
12. 表情与表情包处理专项规则（本版新增完整写死）
12.1 基本原则

表情与表情包不是“无用噪声”，也不是“直接真相”，而是：

情绪信号
回复方式信号
投入强度信号
歧义较高的辅助证据
12.2 三层处理结构
第一层：原始信号层

必须先记录客观事实，例如：

是否出现 emoji
是否只有 emoji
是否出现非文本贴图
是否伴随短文本
是否只有单个低信息回应

这一层只记录事实，不做解释。

第二层：候选解释层

AI 可以参与给出多候选解释，例如：

positive_interest
polite_response
habitual_usage
awkward_softener
low_effort_ack

规则：

必须多候选
必须低置信表达
禁止单结论
禁止“这就是她真实意思”的话术
第三层：规则融合层

结合：

回话模式
当前 24 小时 session 内的相邻材料
当前句前后的局部顺序
当前 session 内的回复密度
当前 session 内是否重复出现类似表达方式
关系判断模式
本次截图中的局部顺序
当前材料内的回复密度
当前阶段
近几轮投入质量
是否存在现实推进
是否在本次材料中重复出现类似表达方式

最后输出：

当前信号更偏正向 / 更偏模糊 / 更偏低信息
是否存在过度解读风险
当前适合的下一步策略
12.3 only-emoji / only-sticker 规则

若一轮回复只有：

单 emoji
单贴图
单图片式情绪表达

默认视为：

信息量低
需要结合当前模式允许的相邻内容
不得直接形成高强度正负判断
12.4 heart 特例

即使是 ❤️，也只允许作为：

正向候选信号之一

不得自动推导为：

明确喜欢
明确想升级关系
明确接受更强推进

必须结合：

当前模式允许读取的相邻语气
当前材料内的互动连续性
当前材料内的回应质量
12.5 输出话术要求

系统输出必须优先采用类似风格：

这是一个偏正向信号，但信息量仍有限
这个回应有好感可能，但还不足以单独下定论
当前更适合低压延续，而不是高压升级
建议继续观察后续回应质量，而不是只盯住一个符号
13. OCR 与截图输入专项规则（本版新增完整写死）
13.1 第一版的 OCR 定位

OCR 的价值是：

帮用户少手打
帮用户快速进入分析

OCR 不是：

全自动语义真相提取器
无需确认的高可靠输入系统
13.2 第一版必须做的 OCR 能力
图片转文本
粗分行
基础顺序预估
支持用户确认
支持删除错误识别项
支持最小角色校正
13.3 第一版明确不做
重型聊天布局语义重建
自动完全可靠角色识别
自动完全可靠顺序拼接
重型贴图内容语义解析
13.4 核心原则

所有进入关系判断分析层的对话，必须是结构确定的。

也就是：

至少顺序大体可靠
至少能区分谁说了什么
至少角色已确认

否则就不能关系判断。

14. 单轮分析 V0 边界（本版新增完整写死）
14.1 V0 定义

JoyPilot V0 =

单对象
单次输入
单轮分析
不依赖重型长期记忆
输出结构化诊断 + 回复建议
14.2 V0 禁止事项

第一版禁止：

多对象自由切换深分析
长期复杂关系演化图谱
大型开放式 AI 聊天
让模型自由发挥关系结论
文本直传关系判断
历史连续关系判断
回话长期记忆系统
14.3 V0 必须保证
不退化为普通 AI 回复器
不输出单点绝对判断
不基于单信号做结论
所有输出必须结构化
所有高风险解释必须给出风险提示
关系判断必须走“截图 → 时间线整理 → OCR → 角色确认 → 判断”链路
回话功能必须走“首次触发 → 固定 24 小时 session → 到期硬清零”链路
15. 固定结构化诊断要求（本版新增完整写死）

每次完整分析必须至少包含以下结构：

15.1 当前阶段判断

枚举示例：

冷
试探
拉近
模糊
回避
15.2 风险信号

最多 3 条，例如：

低投入回应
回避
延迟
情绪模糊
过度解读风险
15.3 当前策略

只能给一个主策略，例如：

推进
降压
维持
暂停
15.4 回复建议

回话模式必须至少 3 条：

稳妥版
自然版
主动版

每条必须带短解释。

关系判断模式可不强制输出 3 条话术，但必须输出结构化策略与解释。

15.5 是否建议发送

枚举：

YES
WAIT
NO
15.6 一句话解释

必须短、可读、非废话。

15.7 写死说明

若系统只输出“回复文案”，没有结构化诊断、短解释或风险提示，则视为产品退化，不允许上线。

16. 回话 session 专项规则（本版新增完整写死）
16.1 创建规则

当用户第一次触发回话功能时，系统必须创建 reply session，并写入：

reply_session_id
reply_session_start_at
reply_session_expires_at = start_at + 24h
16.2 有效期规则
session 自首次触发起固定 24 小时有效
不允许因为继续使用而刷新起点
不允许滑动延长
16.3 到期规则

当当前时间超过 reply_session_expires_at 时：

必须清空 session
必须新建 session 才能继续回话
旧 session 内容不得自动继承到新 session
16.4 用户提示规则

界面必须明确提示：

已为你保留本次回话上下文（24 小时内有效）
超过 24 小时将自动清空
16.5 存储范围

session 仅可存储：

当前回话必要上下文
当前回话已生成的话术
当前回话内的轻量状态信息

不得存储为：

长期对象关系记忆
持久关系画像
关系判断前情事实库
16.6 与关系判断隔离

必须写死：

关系判断不得读取 reply session
reply session 不得影响关系判断阈值
reply session 不得写入对象摘要层作为当前关系判断前情
17. 最终方案状态
JoyPilot v3.4-R5 状态

LOCKED / FAST-LAUNCH / FREE-REPLY-FIRST / SCREENSHOT-FIRST / SOLO-DEV-READY

这版的真正含义是：

保留 v3.4-R4 的命名体系与核心骨架
把本轮确定的 v1 范围收缩、关系判断分层规则、回话 24 小时 session、3 路话术输出与短解释全部嵌回原结构
v1 只跑通两个核心功能：
截图出话术
截图出关系判断
用免费回话做增长和蒸馏
用免费轻量关系判断做试用入口
用 VIP 关系判断、动作升级、对象位做变现
用 J22/J23/J24/J25/J26/J27 + Safety Block + OCR confirm + timeline ordering + reply session + signal fusion 作为最小 moat
把重图谱、硬锁、长期追踪、复杂经济系统、重型视觉理解、连续关系判断、长期回话记忆全部延后到卫星版