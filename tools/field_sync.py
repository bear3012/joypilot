"""
tools/field_sync.py — JoyPilot FIELD_REGISTRY 同步闸门 v2

用法：
  python tools/field_sync.py --check              # 只读校验，exit 1 阻断
  python tools/field_sync.py --check --strict     # 严格模式：WARN 也升级为 exit 1
  python tools/field_sync.py --apply              # 自动补全草稿条目 + 别名行
  python tools/field_sync.py --report             # 输出本次变更影响的文档更新清单（字段维度）
  python tools/field_sync.py --report --with-code # 追加「代码路径 → README/FRONTEND/log」收尾清单
  python tools/field_sync.py --add-model ModelName  # 注册新追踪模型到配置文件

设计依据（红队审计修复）：
  RT-1: 动态导入 + Pydantic model_fields，自动追踪继承链，无 AST 静态解析盲区。
  RT-2: 所有写入通过 HTML 注释锚点定位，不破坏文档结构。
  RT-3: exit 1 时打印明确阻断原因，调用方（AI/CI）不得绕过。
  RT-4: ALIAS_CONFLICT / ALIAS_SHADOW 均为 exit 1；ALIAS_DUPLICATE 由 --apply 自动去重。
  RT-5: BASELINE_STALE（字段已删除但仍在豁免表）exit 1；BASELINE_REDUNDANT（字段已登记仍在豁免表）warn。
  RT-6: 双层守卫：py_compile 语法预检 + 运行时 import 异常捕获，AI 可读错误信息。
  RT-7: TRACKED_MODELS 和 REGISTRY_BASELINE 从 field_sync_config.json 读取，支持 --add-model。
  RT-8: TODO_STALE 检测；--apply 幂等写入 generated 注释，不重复叠加。
  RT-9: ALIAS_UNCONFIRMED 检测；--apply 别名行首次写时间戳，已有行不触碰。
"""

from __future__ import annotations

import importlib
import importlib.util  # _append_code_path_report 动态加载 implement_doc_report
import json
import py_compile
import re
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_MODULE = "app.contracts"
REGISTRY_PATH = PROJECT_ROOT / "docs_control_center" / "FIELD_REGISTRY.md"
CONFIG_PATH = Path(__file__).parent / "field_sync_config.json"

# ---------------------------------------------------------------------------
# 幂等标签正则（RT-8）
# ---------------------------------------------------------------------------
GENERATED_TAG_RE = re.compile(r"<!--\s*field_sync:generated:\d{4}-\d{2}-\d{2}\s*-->")
UNCONFIRMED_TAG_RE = re.compile(r"待确认\s*\(field_sync:")

# ---------------------------------------------------------------------------
# 锚点标记（RT-2）
# ---------------------------------------------------------------------------
ANCHOR_ACTIVE_START = "<!-- FIELD_REGISTRY_ACTIVE_START -->"
ANCHOR_ACTIVE_END = "<!-- FIELD_REGISTRY_ACTIVE_END -->"
ANCHOR_ALIAS_START = "<!-- FIELD_REGISTRY_ALIAS_START -->"
ANCHOR_ALIAS_END = "<!-- FIELD_REGISTRY_ALIAS_END -->"

# ---------------------------------------------------------------------------
# --report 规则字典（MVP 阶段硬编码；模块数 > 10 或接入前端组件栈后迁移至 .mdc）
# ---------------------------------------------------------------------------
REPORT_RULES: dict[str, list[tuple[str, str]]] = {
    "dialogue_turn": [("README.md", "dialogue_turn 模型有新字段，检查 module-1 描述节")],
    "prepared_upload": [("README.md", "prepared_upload 模型有新字段，检查 module-1 描述节")],
    "dashboard": [("docs_control_center/FRONTEND_PLAN_ALIGNED.md", "dashboard 有新字段，检查 message_bank 相关说明")],
}


# ===========================================================================
# 配置加载（RT-7）
# ===========================================================================

def _load_config() -> dict:
    """从 field_sync_config.json 读取配置，文件不存在则返回空 dict（脚本回退硬编码默认值）。"""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            _abort(f"field_sync_config.json 格式错误，请修复：{e}")
    return {}


def _save_config(config: dict) -> None:
    """将配置写入 JSON，强制 indent=2 + sort_keys + 数组排序（Git 友好，RT-7 防御）。"""
    if "tracked_models" in config:
        config["tracked_models"] = sorted(set(config["tracked_models"]))
    if "baseline_fields" in config:
        config["baseline_fields"] = sorted(set(config["baseline_fields"]))
    CONFIG_PATH.write_text(
        json.dumps(config, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# 运行时常量：从配置文件读取，回退到硬编码默认值
# ---------------------------------------------------------------------------
_cfg = _load_config()

TRACKED_MODELS: set[str] = set(_cfg.get("tracked_models", [
    "DialogueTurn",
    "PreparedUpload",
    "Dashboard",
]))

REGISTRY_BASELINE: set[str] = set(_cfg.get("baseline_fields", [
    # DialogueTurn — 4 个基础字段
    "dialogue_turn.speaker",
    "dialogue_turn.text",
    "dialogue_turn.source_image_id",
    "dialogue_turn.timestamp_hint",
    # PreparedUpload — 8 个字段
    "prepared_upload.screenshot_count",
    "prepared_upload.tier",
    "prepared_upload.mode",
    "prepared_upload.timeline_confirmed",
    "prepared_upload.my_side",
    "prepared_upload.duplicate_content_suspected",
    "prepared_upload.issues",
    "prepared_upload.ocr_preview",
    # Dashboard — 17 个字段
    "dashboard.action_light",
    "dashboard.tension_index",
    "dashboard.pressure_score",
    "dashboard.blindspot_risk",
    "dashboard.mean_reversion",
    "dashboard.availability_override",
    "dashboard.frame_anchor",
    "dashboard.gearbox_ratio_radar",
    "dashboard.cooldown_timer",
    "dashboard.focus_redirect",
    "dashboard.reciprocity_meter",
    "dashboard.sunk_cost_breaker",
    "dashboard.adaptive_tension",
    "dashboard.suggestive_channel",
    "dashboard.macro_stage",
    "dashboard.interest_discriminator_panel",
    "dashboard.stage_transition",
]))


# ===========================================================================
# 1. 字段提取：双层守卫 + 动态导入（RT-1, RT-6）
# ===========================================================================

def _to_snake(name: str) -> str:
    """PascalCase / camelCase → snake_case"""
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()


def extract_contracts_fields() -> dict[str, str]:
    """
    返回 {canonical_key: type_str}，canonical_key 格式为 model_snake.field_snake。
    只提取 TRACKED_MODELS 中的模型字段（RT-1：动态导入保证继承字段包含）。
    RT-6：双层守卫，语法错误和运行时错误均输出 AI 可读信息。
    """
    sys.path.insert(0, str(PROJECT_ROOT))
    contracts_file = PROJECT_ROOT / "app" / "contracts.py"

    # 第一层：语法预检（捕获 SyntaxError / IndentationError）
    try:
        py_compile.compile(str(contracts_file), doraise=True)
    except py_compile.PyCompileError as e:
        _abort(f"contracts.py 语法错误，请先修复再跑本脚本：\n{e}")

    # 第二层：运行时导入守卫（捕获依赖缺失 / 循环引用 / 编码错误）
    try:
        mod = importlib.import_module(CONTRACTS_MODULE)
    except Exception as e:
        _abort(
            f"contracts.py 运行时导入失败（依赖缺失或循环引用），请修复后重试：\n"
            f"{type(e).__name__}: {e}"
        )

    from pydantic import BaseModel as _BaseModel

    fields: dict[str, str] = {}
    for cls_name, obj in vars(mod).items():
        if (
            isinstance(obj, type)
            and issubclass(obj, _BaseModel)
            and obj is not _BaseModel
            and cls_name in TRACKED_MODELS
        ):
            model_key = _to_snake(cls_name)
            for field_name, field_info in obj.model_fields.items():
                if field_name.startswith("_"):
                    continue
                ann = field_info.annotation
                type_str = getattr(ann, "__name__", str(ann))
                fields[f"{model_key}.{field_name}"] = type_str

    return fields


# ===========================================================================
# 2. FIELD_REGISTRY 解析：锚点区间提取（RT-2）
# ===========================================================================

def _read_registry() -> str:
    if not REGISTRY_PATH.exists():
        _abort(f"FIELD_REGISTRY.md 不存在：{REGISTRY_PATH}")
    return REGISTRY_PATH.read_text(encoding="utf-8")


def _extract_between_anchors(text: str, start_anchor: str, end_anchor: str) -> str | None:
    """返回两锚点之间的文本（不含锚点行本身），锚点缺失返回 None。"""
    start_idx = text.find(start_anchor)
    end_idx = text.find(end_anchor)
    if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
        return None
    return text[start_idx + len(start_anchor): end_idx]


def extract_registry_field_keys(registry_text: str) -> set[str]:
    """从 Active Fields 锚点区间解析所有已登记字段 key。"""
    active_block = _extract_between_anchors(
        registry_text, ANCHOR_ACTIVE_START, ANCHOR_ACTIVE_END
    )
    if active_block is None:
        return set()
    return set(re.compile(r"###\s+Field:\s+`([^`]+)`").findall(active_block))


def extract_registry_lifecycle(registry_text: str) -> dict[str, str]:
    """返回 {field_key: lifecycle}，仅 Active Fields 区间。"""
    active_block = _extract_between_anchors(
        registry_text, ANCHOR_ACTIVE_START, ANCHOR_ACTIVE_END
    )
    if active_block is None:
        return {}
    field_pattern = re.compile(r"###\s+Field:\s+`([^`]+)`")
    lifecycle_pattern = re.compile(r"-\s+Lifecycle:\s+`([^`]+)`")
    result: dict[str, str] = {}
    current_key: str | None = None
    for line in active_block.splitlines():
        m = field_pattern.search(line)
        if m:
            current_key = m.group(1)
            continue
        if current_key:
            lm = lifecycle_pattern.search(line)
            if lm:
                result[current_key] = lm.group(1)
                current_key = None
    return result


def extract_todo_stale_fields(registry_text: str) -> list[str]:
    """返回 Active Fields 区间内 Description 仍为 TODO 的字段 key 列表（RT-8）。"""
    active_block = _extract_between_anchors(
        registry_text, ANCHOR_ACTIVE_START, ANCHOR_ACTIVE_END
    )
    if active_block is None:
        return []
    field_pattern = re.compile(r"###\s+Field:\s+`([^`]+)`")
    todo_pattern = re.compile(r"-\s+Description\s*&\s*Constraints:\s*TODO")
    result: list[str] = []
    current_key: str | None = None
    for line in active_block.splitlines():
        m = field_pattern.search(line)
        if m:
            current_key = m.group(1)
            continue
        if current_key and todo_pattern.search(line):
            result.append(current_key)
            current_key = None
    return result


# ===========================================================================
# 3. 别名表解析与冲突检测（RT-4, RT-9）
# ===========================================================================

def extract_alias_table(registry_text: str) -> list[tuple[str, list[str]]]:
    """返回 [(canonical_key, [alias1, alias2, ...]), ...]"""
    alias_block = _extract_between_anchors(
        registry_text, ANCHOR_ALIAS_START, ANCHOR_ALIAS_END
    )
    if alias_block is None:
        return []

    rows: list[tuple[str, list[str]]] = []
    for line in alias_block.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---|") or line.startswith("| 正式"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 2:
            continue
        canonical = parts[0].strip("`").strip()
        if not canonical:
            continue
        raw_aliases = parts[1] if len(parts) > 1 else ""
        aliases = [
            a.strip().strip("`").strip("、").strip()
            for a in re.split(r"[,，、]", raw_aliases)
            if a.strip().strip("`").strip()
        ]
        rows.append((canonical, aliases))
    return rows


def extract_unconfirmed_alias_rows(registry_text: str) -> list[str]:
    """返回别名表中含"待确认 (field_sync:"标记的正式字段名列表（RT-9）。"""
    alias_block = _extract_between_anchors(
        registry_text, ANCHOR_ALIAS_START, ANCHOR_ALIAS_END
    )
    if alias_block is None:
        return []
    result: list[str] = []
    for line in alias_block.splitlines():
        if UNCONFIRMED_TAG_RE.search(line):
            parts = [p.strip() for p in line.strip("|").split("|")]
            canonical = parts[0].strip("`").strip() if parts else ""
            if canonical:
                result.append(canonical)
    return result


def check_alias_conflicts(
    alias_rows: list[tuple[str, list[str]]],
    all_canonical_keys: set[str],
) -> tuple[list[str], list[str], list[str]]:
    """返回 (ALIAS_CONFLICT_msgs, ALIAS_SHADOW_msgs, ALIAS_DUPLICATE_msgs)"""
    alias_to_canonical: dict[str, list[str]] = {}
    conflicts: list[str] = []
    shadows: list[str] = []
    duplicates: list[str] = []

    for canonical, aliases in alias_rows:
        seen_in_row: set[str] = set()
        for alias in aliases:
            if not alias:
                continue
            if alias in seen_in_row:
                duplicates.append(
                    f"[ALIAS_DUPLICATE] `{canonical}` 行中别名 `{alias}` 重复出现"
                )
            else:
                seen_in_row.add(alias)
            alias_to_canonical.setdefault(alias, []).append(canonical)

    for alias, canonicals in alias_to_canonical.items():
        if len(set(canonicals)) > 1:
            conflicts.append(
                f"[ALIAS_CONFLICT] 别名 `{alias}` 同时指向 {set(canonicals)}"
            )

    for canonical, aliases in alias_rows:
        for alias in aliases:
            if alias in all_canonical_keys and alias != canonical:
                shadows.append(
                    f"[ALIAS_SHADOW] 别名 `{alias}`（来自 `{canonical}`）与正式字段名完全相同"
                )

    return conflicts, shadows, duplicates


# ===========================================================================
# 4. --check 模式（含 --strict, RT-5, RT-8, RT-9）
# ===========================================================================

def _check_anchors(registry_text: str) -> list[str]:
    errors: list[str] = []
    for anchor in (ANCHOR_ACTIVE_START, ANCHOR_ACTIVE_END,
                   ANCHOR_ALIAS_START, ANCHOR_ALIAS_END):
        if anchor not in registry_text:
            errors.append(f"[ANCHOR_MISSING] 缺少锚点：{anchor}")
    return errors


def run_check(strict: bool = False) -> int:
    """
    执行全量核查，返回 exit code（0=通过，1=有问题）。
    strict=True 时，WARN 级别问题也升级为 exit 1。
    """
    registry_text = _read_registry()

    # 锚点检查
    anchor_errors = _check_anchors(registry_text)
    if anchor_errors:
        for e in anchor_errors:
            print(e)
        _print_block_message()
        return 1

    contracts_fields = extract_contracts_fields()
    registry_keys = extract_registry_field_keys(registry_text)
    registry_lifecycle = extract_registry_lifecycle(registry_text)

    issues: list[str] = []
    warnings: list[str] = []

    # MISSING：contracts 有，REGISTRY 无（BASELINE 豁免）
    for key in sorted(contracts_fields):
        if key not in registry_keys and key not in REGISTRY_BASELINE:
            issues.append(f"[MISSING]  {key}  → contracts.py 已定义，FIELD_REGISTRY 无对应条目")

    # STALE：REGISTRY Active，但 contracts 已删除（仅 TRACKED_MODELS 前缀）
    tracked_prefixes = tuple(_to_snake(m) + "." for m in TRACKED_MODELS)
    for key, lifecycle in sorted(registry_lifecycle.items()):
        if "[" in key:
            continue
        if lifecycle == "Active" and key.startswith(tracked_prefixes) and key not in contracts_fields:
            issues.append(
                f"[STALE]    {key}  → FIELD_REGISTRY 标注 Active，但 contracts.py 中已删除"
            )

    # RT-5：BASELINE_STALE — 豁免字段在 contracts.py 中已不存在（exit 1）
    for key in sorted(REGISTRY_BASELINE):
        model_prefix = key.split(".")[0]
        if (model_prefix + ".") not in "".join(tracked_prefixes):
            continue  # 不属于 TRACKED_MODELS 的 baseline 字段不检查
        if key not in contracts_fields:
            issues.append(
                f"[BASELINE_STALE] `{key}` 在 REGISTRY_BASELINE 中但 contracts.py 已删除，"
                f"请从 BASELINE 中移除此条目"
            )

    # RT-5：BASELINE_REDUNDANT — 豁免字段已在 FIELD_REGISTRY 登记（warn，不阻断）
    for key in sorted(REGISTRY_BASELINE):
        if key in registry_keys:
            warnings.append(
                f"[WARN] BASELINE_REDUNDANT: `{key}` 已有 FIELD_REGISTRY 条目，"
                f"可从 field_sync_config.json baseline_fields 中移除"
            )

    # 别名冲突（RT-4）
    alias_rows = extract_alias_table(registry_text)
    all_canonical_keys = registry_keys | set(contracts_fields.keys())
    conflicts, shadows, dupes = check_alias_conflicts(alias_rows, all_canonical_keys)
    issues.extend(conflicts)
    issues.extend(shadows)
    issues.extend(dupes)

    # RT-8：TODO_STALE — Description 仍为 TODO（warn）
    todo_fields = extract_todo_stale_fields(registry_text)
    for key in todo_fields:
        warnings.append(
            f"[WARN] TODO_STALE: `{key}` 的 Description & Constraints 仍为 TODO，请人工补全"
        )

    # RT-9：ALIAS_UNCONFIRMED — 别名行仍为"待确认"（warn）
    unconfirmed = extract_unconfirmed_alias_rows(registry_text)
    for key in unconfirmed:
        warnings.append(
            f"[WARN] ALIAS_UNCONFIRMED: `{key}` 的别名说明仍为\u300c待确认\u300d，请人工确认后更新"
        )

    # 输出
    has_issues = bool(issues)
    has_warnings = bool(warnings)

    for msg in issues:
        print(msg)
    for msg in warnings:
        print(msg)

    if strict and has_warnings:
        print(
            "\n[STRICT] --strict 模式：以上 WARN 升级为阻断。"
            "请清理 TODO / 别名说明 / BASELINE 冗余后重跑。",
            file=sys.stderr,
        )
        _print_block_message()
        return 1

    if has_issues:
        _print_block_message()
        return 1

    if has_warnings:
        print(
            "\n[OK] 核心字段对齐，但有上述 WARN 待处理。"
            "日常开发可继续；阶段性验收请跑 --check --strict。"
        )
    else:
        print("[OK] FIELD_REGISTRY 与 contracts.py 完全对齐，别名表无冲突。")
    return 0


# ===========================================================================
# 5. --apply 模式（RT-8 幂等 generated 标签，RT-9 首次别名时间戳）
# ===========================================================================

def run_apply() -> int:
    """自动补全草稿条目和别名行，返回 exit code。"""
    registry_text = _read_registry()
    today = date.today().isoformat()

    anchor_errors = _check_anchors(registry_text)
    if anchor_errors:
        for e in anchor_errors:
            print(e)
        print("\n[BLOCKED] 锚点注释缺失，拒绝写入任何内容。请先在 FIELD_REGISTRY.md 中添加锚点。")
        return 1

    contracts_fields = extract_contracts_fields()
    registry_keys = extract_registry_field_keys(registry_text)
    registry_lifecycle = extract_registry_lifecycle(registry_text)
    alias_rows = extract_alias_table(registry_text)
    all_canonical_keys = registry_keys | set(contracts_fields.keys())

    # 别名冲突检查：CONFLICT / SHADOW 拒绝写入
    conflicts, shadows, dupes = check_alias_conflicts(alias_rows, all_canonical_keys)
    if conflicts or shadows:
        for msg in conflicts + shadows:
            print(msg)
        print("\n[BLOCKED] 别名表存在 CONFLICT/SHADOW，拒绝写入。请人工解决后重跑 --apply。")
        return 1

    modified = False

    # ALIAS_DUPLICATE：自动去重
    if dupes:
        print("以下 ALIAS_DUPLICATE 将被自动去重：")
        for d in dupes:
            print(f"  {d}")
        registry_text = _dedup_alias_table(registry_text)
        modified = True

    # MISSING：生成草稿条目 + 别名行（RT-8 幂等 generated 标签，RT-9 首次时间戳）
    missing_keys = sorted(
        k for k in contracts_fields
        if k not in registry_keys and k not in REGISTRY_BASELINE
    )
    if missing_keys:
        draft_entries: list[str] = []
        draft_alias_rows: list[str] = []
        for key in missing_keys:
            type_str = contracts_fields[key]
            draft_entries.append(_make_field_draft(key, type_str, today))
            camel, pascal = _make_aliases(key)
            draft_alias_rows.append(
                f"| `{key}` | `{camel}`, `{pascal}` | 待确认 (field_sync:{today}) |"
            )
            print(f"[APPLY] 草稿条目已生成：{key}")

        registry_text = _insert_before_anchor(
            registry_text, ANCHOR_ACTIVE_END, "\n".join(draft_entries) + "\n"
        )
        registry_text = _insert_before_anchor(
            registry_text, ANCHOR_ALIAS_END, "\n".join(draft_alias_rows) + "\n"
        )
        modified = True

    # STALE：将 Active → Deprecated
    tracked_prefixes = tuple(_to_snake(m) + "." for m in TRACKED_MODELS)
    stale_keys = [
        k for k, lc in registry_lifecycle.items()
        if lc == "Active" and "[" not in k
        and k.startswith(tracked_prefixes) and k not in contracts_fields
    ]
    if stale_keys:
        for key in stale_keys:
            print(f"[APPLY] 标记为 Deprecated：{key}")
        registry_text = _mark_stale_deprecated(registry_text, stale_keys)
        modified = True

    if modified:
        REGISTRY_PATH.write_text(registry_text, encoding="utf-8")
        print("\n[APPLY 完成] 请重新运行 --check 确认对齐。")
    else:
        print("[APPLY] 无需变更，FIELD_REGISTRY 已是最新状态。")

    return 0


# ===========================================================================
# 6. --report 模式（文档更新清单）
# ===========================================================================

def _append_code_path_report(*, allow_missing_git: bool) -> None:
    """加载 tools/implement_doc_report.py 并打印代码路径层面的文档建议。"""
    report_path = PROJECT_ROOT / "tools" / "implement_doc_report.py"
    spec = importlib.util.spec_from_file_location("implement_doc_report", report_path)
    if spec is None or spec.loader is None:
        print(f"[WARN] 无法加载 {report_path}，跳过 --with-code 段。", file=sys.stderr)
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.run_report(None, allow_missing_git=allow_missing_git)


def run_report(*, with_code: bool = False) -> int:
    """输出本次变更影响分析和文档更新建议清单。"""
    registry_text = _read_registry()
    anchor_errors = _check_anchors(registry_text)
    if anchor_errors:
        for e in anchor_errors:
            print(e)
        return 1

    contracts_fields = extract_contracts_fields()
    registry_keys = extract_registry_field_keys(registry_text)
    alias_rows = extract_alias_table(registry_text)
    alias_canonicals = {row[0] for row in alias_rows}

    missing_keys = sorted(
        k for k in contracts_fields
        if k not in registry_keys and k not in REGISTRY_BASELINE
    )
    todo_fields = extract_todo_stale_fields(registry_text)
    unconfirmed = extract_unconfirmed_alias_rows(registry_text)
    missing_alias = sorted(
        k for k in contracts_fields
        if k not in REGISTRY_BASELINE and k not in alias_canonicals
    )

    print("[REPORT] 本次变更影响分析")
    print(f"  新增/未登记字段：{len(missing_keys)} 个")
    for k in missing_keys:
        print(f"    - {k}")

    # 文档更新建议
    must_docs: list[tuple[str, str]] = []
    optional_docs: list[tuple[str, str]] = []

    if missing_keys:
        must_docs.append(("FIELD_REGISTRY.md", "运行 --apply 生成草稿条目"))
        must_docs.append(("docs_control_center/log.md", "记录本次实施命令与原始输出"))

    # 根据 REPORT_RULES 匹配受影响的可选文档
    affected_prefixes: set[str] = set()
    for key in missing_keys:
        prefix = key.split(".")[0]
        affected_prefixes.add(prefix)

    for prefix in sorted(affected_prefixes):
        for doc, reason in REPORT_RULES.get(prefix, []):
            optional_docs.append((doc, reason))

    print("\n  建议更新文档：")
    for doc, reason in must_docs:
        print(f"    [必须] {doc:<45} → {reason}")
    for doc, reason in optional_docs:
        print(f"    [可选] {doc:<45} → {reason}")

    if missing_alias:
        print(f"\n  别名表：{len(missing_alias)} 个字段缺少别名行 → 运行 --apply 自动补全")

    if todo_fields:
        print(
            f"\n  [WARN] {len(todo_fields)} 个字段 Description 仍为 TODO"
            f"（运行 --check --strict 可强制清账）"
        )
        for k in todo_fields:
            print(f"    - {k}")

    if unconfirmed:
        print(
            f"\n  [WARN] {len(unconfirmed)} 条别名行仍为\u300c待确认\u300d"
            f"\uff08运行 --check --strict 可强制清账\uff09"
        )
        for k in unconfirmed:
            print(f"    - {k}")

    if not missing_keys and not missing_alias and not todo_fields and not unconfirmed:
        print("\n  [OK] 无待处理项，文档已全部对齐。")

    if with_code:
        print("\n" + "=" * 72)
        _append_code_path_report(allow_missing_git=True)

    return 0


# ===========================================================================
# 7. --add-model 模式（RT-7 配置文件注册）
# ===========================================================================

def run_add_model(model_name: str) -> int:
    """将新模型注册到 field_sync_config.json，使 --check 开始追踪其字段。"""
    config = _load_config()
    if not config:
        # 首次创建：从当前运行时常量初始化
        config = {
            "tracked_models": sorted(TRACKED_MODELS),
            "baseline_fields": sorted(REGISTRY_BASELINE),
        }

    tracked = set(config.get("tracked_models", []))
    if model_name in tracked:
        print(f"[ADD-MODEL] `{model_name}` 已在 tracked_models 中，无需重复添加。")
        return 0

    tracked.add(model_name)
    config["tracked_models"] = sorted(tracked)
    _save_config(config)
    print(
        f"[ADD-MODEL] `{model_name}` 已注册到 field_sync_config.json。\n"
        f"  运行 --check 查看新追踪字段状态。"
    )
    return 0


# ===========================================================================
# 辅助函数
# ===========================================================================

def _abort(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def _print_block_message() -> None:
    print(
        "\n[BLOCKED] field_sync --check 未通过。\n"
        "  允许的操作：\n"
        "    1. 运行 python tools/field_sync.py --apply 修复问题后重跑 --check\n"
        "    2. 向用户报告阻断原因，等待人工决策\n"
        "  禁止：继续修改代码、提出临时绕过方案。",
        file=sys.stderr,
    )


def _make_field_draft(key: str, type_str: str, today: str) -> str:
    """生成字段草稿 Markdown 条目（RT-8：Description 行附 generated 标签，幂等）。"""
    return (
        f"\n### Field: `{key}`\n"
        f"- Type: `{type_str}`\n"
        f"- Owner Module: `TODO`\n"
        f"- Lifecycle: `Active`\n"
        f"- Description & Constraints: TODO <!-- field_sync:generated:{today} -->\n"
    )


def _make_aliases(key: str) -> tuple[str, str]:
    """从 model.field_name 生成 camelCase 和 PascalCase 别名。"""
    field_parts = key.split(".")[-1].split("_")
    camel = field_parts[0] + "".join(p.capitalize() for p in field_parts[1:])
    pascal = "".join(p.capitalize() for p in field_parts)
    return camel, pascal


def _insert_before_anchor(text: str, anchor: str, content: str) -> str:
    """在指定锚点前插入内容（RT-2）。"""
    idx = text.find(anchor)
    if idx == -1:
        _abort(f"锚点 {anchor} 未找到，无法插入内容。")
    return text[:idx] + content + text[idx:]


def _mark_stale_deprecated(text: str, stale_keys: list[str]) -> str:
    """将锚点区间内指定字段的 Lifecycle Active → Deprecated。"""
    start_idx = text.find(ANCHOR_ACTIVE_START)
    end_idx = text.find(ANCHOR_ACTIVE_END)
    if start_idx == -1 or end_idx == -1:
        return text

    before = text[:start_idx + len(ANCHOR_ACTIVE_START)]
    active_block = text[start_idx + len(ANCHOR_ACTIVE_START): end_idx]
    after = text[end_idx:]

    for key in stale_keys:
        escaped = re.escape(f"`{key}`")
        block_pattern = re.compile(
            rf"(###\s+Field:\s+{escaped}.*?)(- Lifecycle:\s+`Active`)",
            re.DOTALL,
        )
        active_block = block_pattern.sub(r"\1- Lifecycle: `Deprecated`", active_block, count=1)

    return before + active_block + after


def _dedup_alias_table(text: str) -> str:
    """对别名表中每行去重别名（RT-4 ALIAS_DUPLICATE 自动修复）。"""
    start_idx = text.find(ANCHOR_ALIAS_START)
    end_idx = text.find(ANCHOR_ALIAS_END)
    if start_idx == -1 or end_idx == -1:
        return text

    before = text[:start_idx + len(ANCHOR_ALIAS_START)]
    alias_block = text[start_idx + len(ANCHOR_ALIAS_START): end_idx]
    after = text[end_idx:]

    new_lines: list[str] = []
    for line in alias_block.splitlines(keepends=True):
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|---|") or stripped.startswith("| 正式"):
            new_lines.append(line)
            continue
        parts = line.strip().strip("|").split("|")
        if len(parts) < 2:
            new_lines.append(line)
            continue
        canonical_col = parts[0]
        alias_col = parts[1]
        rest = parts[2:]
        raw_aliases = re.split(r"[,，、]", alias_col)
        seen: set[str] = set()
        deduped: list[str] = []
        for a in raw_aliases:
            a_stripped = a.strip()
            if a_stripped and a_stripped not in seen:
                seen.add(a_stripped)
                deduped.append(a.strip())
        new_alias_col = "、".join(deduped)
        new_line = "| " + canonical_col + " | " + new_alias_col + " | " + " | ".join(rest) + "\n"
        new_lines.append(new_line)

    return before + "".join(new_lines) + after


# ===========================================================================
# 入口
# ===========================================================================

def main() -> None:
    args = sys.argv[1:]

    if not args:
        print(
            "用法：\n"
            "  python tools/field_sync.py --check [--strict]\n"
            "  python tools/field_sync.py --apply\n"
            "  python tools/field_sync.py --report [--with-code]\n"
            "  python tools/field_sync.py --add-model ModelName",
            file=sys.stderr,
        )
        sys.exit(1)

    mode = args[0]
    strict = "--strict" in args

    if mode == "--check":
        sys.exit(run_check(strict=strict))
    elif mode == "--apply":
        sys.exit(run_apply())
    elif mode == "--report":
        sys.exit(run_report(with_code="--with-code" in args))
    elif mode == "--add-model":
        if len(args) < 2:
            print("[ERROR] --add-model 需要模型名称参数，例如：--add-model StructuredDiagnosis", file=sys.stderr)
            sys.exit(1)
        sys.exit(run_add_model(args[1]))
    else:
        print(f"[ERROR] 未知模式：{mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
