# JoyPilot v1 模块依赖关系图 + 验收清单（下载版）

本文件为整理后的可下载版本，包含：

1.  模块依赖关系图
2.  两条主链说明（回话 / 关系判断）
3.  每模块验收清单
4.  跨模块总验收清单
5.  核心执行原则

------------------------------------------------------------------------

## 一、核心主链

### 回话链路

输入 → OCR → 结构化 → reply_rules → session → 输出3条话术 + 短解释 +
YES/WAIT/NO

### 关系判断链路

截图 → 时间线 → OCR → 角色确认 → relationship_rules → report →
输出结构化判断

------------------------------------------------------------------------

## 二、关键硬规则

-   回话必须3条输出
-   每条必须有短解释
-   必须输出 YES / WAIT / NO
-   session = 首次触发 + 24小时固定窗口
-   不滑动续期
-   不按自然日
-   关系判断不读历史上下文
-   免费：2--4张 / 2次 / 需广告
-   VIP：2--9张

------------------------------------------------------------------------

## 三、模块分层

### 真相源层

-   enums
-   config (tiers / session / safety / styles)

### 契约层

-   reply_input / output
-   relationship_input / output
-   session_schema
-   upload_schema

### 门禁层

-   session_rules
-   entitlement_rules
-   timeline_rules
-   role_rules
-   safety_rules
-   emoji_rules

### 输入转换层

-   upload_service
-   ocr_service
-   dialogue_structure_service

### 回话主链

-   reply_rules
-   reply_session_service
-   reply_service
-   reply_routes

### 关系判断主链

-   relationship_rules
-   report_service
-   relationship_service
-   relationship_routes

### 权益层

-   usage_counter_repo
-   entitlement_service

------------------------------------------------------------------------

## 四、核心验收（必须全部成立）

### 回话

-   3条输出 ✔
-   每条短解释 ✔
-   session 24h ✔
-   不滑动 ✔
-   safety 生效 ✔

### 关系判断

-   FREE / VIP 门槛正确 ✔
-   时间线 gate ✔
-   角色确认 gate ✔
-   不读历史 ✔
-   有结构化输出 ✔

### 安全

-   BLOCKED 清空输出 ✔
-   no-contact 不推进 ✔

------------------------------------------------------------------------

## 五、执行原则

-   API 不写逻辑
-   Core 不做 I/O
-   Service 只编排
-   Schema 必须稳定
-   不允许多真相源
-   不允许关系判断读 session
-   不允许后补 gate

------------------------------------------------------------------------

## 六、一句话总结

先锁规则 → 再跑回话 → 再做关系判断 → 最后接商业层
