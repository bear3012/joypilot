# field_sync 必须用 `uv run`（治理硬规定）

主规则已写入 `.cursor/rules/field-registry-sync.mdc` 首节「运行环境硬规定（field_sync 必遵）」。本文作备查与复制粘贴示例。

## 硬规定

- 所有 `tools/field_sync.py` 子命令（`--check` / `--apply` / `--report` / `--add-model`、以及与 `--check` 联用的 `--strict`）**一律**使用：

  ```powershell
  # Windows PowerShell，项目根目录
  $env:PYTHONPATH='.'
  uv run python tools/field_sync.py --check
  ```

  ```bash
  # Unix，项目根目录
  PYTHONPATH=. uv run python tools/field_sync.py --check
  ```

- **禁止**仅用系统自带的 `python tools/field_sync.py ...` 执行治理闸门。  
  原因：系统环境常缺少 `pydantic` 等项目依赖，会导致「运行时导入失败」等**假阻断**，与真实 FIELD_REGISTRY 口径无关。

- `log.md` 记录实施命令时，应写 `uv run python ...` 形式，避免后人照抄失效。

## AI 行为

- 规划/执行/交付前跑 field_sync 时，默认命令前缀为 `uv run python`，不得改为裸 `python` 以“凑 exit 0”。

## 算法收尾：字段报告 + 代码路径报告

纯算法改动（未改 `contracts.py` 被追踪字段）时，`--report` 的字段段可能显示「无待处理」，仍需跑代码路径清单：

```powershell
$env:PYTHONPATH='.'
uv run python tools/field_sync.py --report --with-code
# 或：uv run python tools/implement_doc_report.py --files app/relationship_service.py
```
