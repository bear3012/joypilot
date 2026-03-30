#!/usr/bin/env python3
"""
实施后文档清单（代码路径 → 应核对/更新的文档）

用法（项目根目录）：
  uv run python tools/implement_doc_report.py
  uv run python tools/implement_doc_report.py --files app/foo.py app/bar.py

无 git 仓库时须使用 --files 显式传入变更路径。

与 field_sync 分工：
  - field_sync：contracts.py 字段 vs FIELD_REGISTRY
  - 本脚本：业务代码路径 vs README / FRONTEND / MASTER_PLAN / log 等收尾清单
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# (正则, [(文档路径相对项目根, 说明), ...])
# 同一文件命中多条规则时合并去重。
CODE_DOC_RULES: list[tuple[re.Pattern[str], list[tuple[str, str]]]] = [
    (
        re.compile(r"^app/relationship_service\.py$"),
        [
            ("README.md", "module-6 关系判断：算法链、覆写、message_bank 行为"),
            (
                "docs_control_center/FRONTEND_PLAN_ALIGNED.md",
                "J28/J29/J30 与 message_bank、send_recommendation",
            ),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^app/input_service\.py$"),
        [
            ("README.md", "module-1 上传预处理 / 时延与对话回合构造"),
            (
                "docs_control_center/FIELD_REGISTRY.md",
                "若 DialogueTurn 等字段在 input 层被引用，核对 field_sync --check",
            ),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^app/contracts\.py$"),
        [
            (
                "docs_control_center/FIELD_REGISTRY.md",
                "uv run python tools/field_sync.py --check / --apply",
            ),
            ("README.md", "涉及契约输出的 module 描述节"),
            ("docs_control_center/FRONTEND_PLAN_ALIGNED.md", "响应路径字段展示口径"),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^app/config\.py$"),
        [
            ("README.md", "若新增业务常量，检查相关 module 说明是否需同步"),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^app/gates\.py$"),
        [
            ("README.md", "module-2 门禁"),
            ("docs_control_center/FRONTEND_PLAN_ALIGNED.md", "BLOCK / DEGRADE 与 UI"),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^app/reply_service\.py$"),
        [
            ("README.md", "module-3 回复分析：回复路由、message_bank 生成"),
            (
                "docs_control_center/FRONTEND_PLAN_ALIGNED.md",
                "reply 接口与 message_bank / DEGRADE 行为",
            ),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^app/reply_session_service\.py$"),
        [
            ("README.md", "module-3 回复分析：Session 管理"),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^app/signal_service\.py$"),
        [
            ("README.md", "module-5 信号提取：SignalCandidate 逻辑"),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^app/entitlement_service\.py$"),
        [
            ("README.md", "module-8 权益/配额：扣减与免广告逻辑"),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^app/audit_service\.py$"),
        [
            ("README.md", "module-9 审计写入：write_audit_event / write_segment_summary"),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^app/storage\.py$"),
        [
            ("README.md", "数据存储层：内存/持久化结构"),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^app/main\.py$"),
        [
            ("README.md", "API 路由与启动入口"),
            ("docs_control_center/FRONTEND_PLAN_ALIGNED.md", "路由变更影响前端调用路径"),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(
            r"^tools/field_sync\.py$"
            r"|^tools/field_sync_config\.json$"
            r"|^tools/implement_doc_report\.py$"
        ),
        [
            (".cursor/rules/field-registry-sync.mdc", "治理规则与示例命令"),
            ("docs_control_center/FIELD_SYNC_UV_RUN.md", "若命令示例变更"),
            ("docs_control_center/log.md", "记录实施命令与测试原始输出"),
        ],
    ),
    (
        re.compile(r"^tests/.*\.py$"),
        [
            ("docs_control_center/log.md", "回归命令与原始输出摘要"),
        ],
    ),
    # 兜底：任何 app/*.py（未被上方规则精确覆盖时也至少提醒记录 log）
    (
        re.compile(r"^app/[^/]+\.py$"),
        [
            ("docs_control_center/log.md", "记录实施命令与测试原始输出（通配兜底）"),
        ],
    ),
]


def _normalize_path(s: str) -> str:
    return s.strip().replace("\\", "/")


def collect_git_changed_files() -> list[str] | None:
    """返回相对项目根的路径列表；非 git 或 git 命令均失败返回 None；成功但无变更返回 []。"""
    files: set[str] = set()
    any_ok = False
    for args in (
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "diff", "--name-only", "--cached"],
    ):
        try:
            r = subprocess.run(
                args,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return None
        if r.returncode != 0:
            continue
        any_ok = True
        for line in r.stdout.splitlines():
            p = _normalize_path(line)
            if p:
                files.add(p)
    if not any_ok:
        return None
    return sorted(files)


def suggestions_for_paths(paths: list[str]) -> list[tuple[str, str]]:
    by_doc: dict[str, list[str]] = {}
    seen_pairs: set[tuple[str, str]] = set()
    for raw in paths:
        norm = _normalize_path(raw)
        for pattern, tasks in CODE_DOC_RULES:
            if pattern.match(norm):
                for doc, reason in tasks:
                    key = (doc, reason)
                    if key in seen_pairs:
                        continue
                    seen_pairs.add(key)
                    by_doc.setdefault(doc, []).append(reason)
    return [(doc, "；".join(reasons)) for doc, reasons in sorted(by_doc.items())]


def run_report(paths: list[str] | None, *, allow_missing_git: bool = False) -> int:
    if paths is None:
        git_files = collect_git_changed_files()
        if git_files is None:
            if allow_missing_git:
                print(
                    "[CODE-PATH REPORT] 已跳过：当前目录不是 git 仓库或未安装 git。\n"
                    "  如需清单请执行：uv run python tools/implement_doc_report.py --files <路径...>"
                )
                return 0
            print(
                "[implement_doc_report] 未能从 git 获取变更列表（非仓库或未安装 git）。\n"
                "请使用：uv run python tools/implement_doc_report.py --files path1 path2",
                file=sys.stderr,
            )
            return 1
        paths = git_files

    if not paths:
        print("[implement_doc_report] 没有可分析的变更文件。")
        return 0

    sug = suggestions_for_paths(paths)
    print("[CODE-PATH REPORT] 根据变更文件建议跟进的文档（请人工逐条核对并补写）")
    print("  变更文件：")
    for p in paths:
        print(f"    - {p}")
    if not sug:
        print("\n  （未匹配到预设规则：请自行补充 README / FRONTEND / log 等）")
        return 0
    print("\n  建议更新：")
    for doc, reason in sug:
        print(f"    - {doc:<50} → {reason}")
    print(
        "\n  说明：本清单不自动改文件；完成后请在 docs_control_center/log.md 记录命令与输出。"
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="代码变更 → 文档收尾清单")
    parser.add_argument(
        "--files",
        nargs="+",
        default=None,
        metavar="PATH",
        help="显式指定变更路径（相对项目根，至少 1 个），无 git 时必用",
    )
    args = parser.parse_args()
    sys.exit(run_report(paths=args.files))


if __name__ == "__main__":
    main()
