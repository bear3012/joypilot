# JoyPilot 变更影响矩阵（module-1 / module-2）

> 目的：任何改动后，快速确定“必须跑哪些回归”，避免口径漂移和安全漏检。

## 1) module-1 输入整理链路

| 变更类型 | 受影响区域 | 必跑回归 | 通过标准 |
|---|---|---|---|
| 截图数量范围/档位变更 | `FREE/VIP` 截图门禁、升级提示 | `test_module_1_red_team_regression_fixtures` | `UPGRADE_REQUIRED`、范围错误码与预期一致 |
| 文本直传策略变更 | `/upload/prepare` 关系模式入口 | `test_module_1_red_team_regression_fixtures` | `TEXT_DIRECT_NOT_ALLOWED` 仍可命中 |
| 低信息熵阈值/算法变更 | 证据质量计算 | `test_module_1_red_team_regression_fixtures` + `test_relationship_flags_insufficient_evidence_for_low_info_content` | `evidence_quality=INSUFFICIENT` 且触发 `INSUFFICIENT_EVIDENCE` |
| 角色映射逻辑变更 | `LEFT/RIGHT -> SELF/OTHER` | `test_module_1_red_team_regression_fixtures` + `test_role_unconfirmed_keeps_left_right_labels` | 未确认角色时仅允许 `LEFT/RIGHT` |

## 2) module-2 门禁与安全链路

| 变更类型 | 受影响区域 | 必跑回归 | 通过标准 |
|---|---|---|---|
| 洋葱短路顺序变更 | `resolve_gate_decision` | `test_module_2_red_team_regression_fixtures` + `test_sensitive_context_blocks_before_prompt_injection` | 高敏+注入时优先 `CONSENT_REQUIRED` |
| 商业门禁策略变更 | `ADS_REQUIRED / UPGRADE_REQUIRED` | `test_module_2_red_team_regression_fixtures` + `test_relationship_requires_ads_for_free_tier` | 必须 `BLOCK`，不允许降级继续生成 |
| reply 门禁接入变更 | `/reply/analyze` | `test_module_2_red_team_regression_fixtures` + `test_reply_blocks_sensitive_context_without_consent` | 高敏未同意必须 `BLOCKED` |
| 注入降级策略变更 | `CAUTION -> DEGRADE` | `test_module_2_red_team_regression_fixtures` + `test_reply_injection_degrades_and_removes_bold_route` | `BOLD_HONEST` 必须被剥夺 |
| 序列化兜底变更 | API 网关输出 | `test_module_2_red_team_regression_fixtures` + `test_safety_block_clears_message_bank` | `BLOCK` 时 `message_bank=[]` |

## 3) 最小发布前检查（建议）

1. 先跑：`test_module_1_red_team_regression_fixtures`
2. 再跑：`test_module_2_red_team_regression_fixtures`
3. 最后跑：全量 `pytest`

若任一步骤失败，禁止进入发布动作，先修复再重跑。

## 4) module-10 验收与红队闭环

| 变更类型 | 受影响区域 | 必跑回归 | 通过标准 |
|---|---|---|---|
| fixture runner 能力变更（GET/POST 分发、golden schema 适配） | `tests/test_api.py` 的 `_run_fixture_pack/_run_golden_fixture_pack` | `test_m10_golden_contract_fixtures` + `test_m10_smoke_fixture_pack` | module-0/minimal 与 module-10/smoke 均通过，且 GET 端点可执行 |
| smoke 用例集变更 | `fixtures/module-10/smoke_fixtures.json` | `test_m10_smoke_fixture_pack` | `/health`、`/api/state`、`/upload/prepare`、`/reply/analyze`、`/relationship/analyze` 全部通过 |
| negative 用例集变更 | `fixtures/module-10/negative_api_fixtures.json` | `test_m10_negative_fixture_pack` | 非法输入统一返回 `422` |
| red-team 扩展用例变更 | `fixtures/module-10/red_team_extended_fixtures.json` | `test_m10_red_team_fixture_pack` + `test_module_1_red_team_regression_fixtures` + `test_module_2_red_team_regression_fixtures` | 新增对抗场景通过，既有 m1/m2 红队回归不退化 |
| 发布前总回归（module-10 改动后） | 全仓库 API 与静态断言 | 全量 `pytest` | 全量通过；若失败先清端口再重跑 |
