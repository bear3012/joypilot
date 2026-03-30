"""
JoyPilot 交付前一键检查脚本。

使用方法（项目根目录）：
    uv run python tools/deliver.py

步骤顺序（任一失败即停）：
    0. Git 状态预检 —— 确保工作区有未提交改动（否则 --report --with-code 无效）
    1. 字段闸门       —— uv run python tools/field_sync.py --check
    2. 文档待办       —— uv run python tools/field_sync.py --report --with-code
    3. 全量测试       —— uv run pytest tests/test_api.py -q
"""

import os
import subprocess
import sys

os.environ.setdefault("PYTHONPATH", ".")


def run(cmd: list[str], step: str) -> None:
    print(f"\n=== {step} ===")
    # check=True：非零退出码直接抛 CalledProcessError，不依赖 shell 的退出码变量
    subprocess.run(cmd, check=True)


def check_git_dirty() -> None:
    """步骤 0：工作区必须有未提交改动，否则 --report --with-code 读不到 diff。"""
    print("\n=== [0/3] Git 状态预检 ===")
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # 非 git 仓库，跳过预检（implement_doc_report --files 模式仍可用）
        print("[WARN] 当前目录非 git 仓库，跳过 git 状态预检。")
        print("       --report --with-code 将无 diff 输出；如需完整文档报告请手动传 --files：")
        print("       uv run python tools/implement_doc_report.py --files <改动文件>")
        return
    if not result.stdout.strip():
        print("[BLOCKED] 工作区干净（无未提交改动）。")
        print("          --report --with-code 依赖 git diff，现在运行将输出空报告，可能漏更文档。")
        print("          请确认改动尚未 commit；若已 commit，请改用：")
        print("          uv run python tools/implement_doc_report.py --files <改动文件>")
        sys.exit(1)
    print("[OK] 工作区有未提交改动，可继续。")


def main() -> None:
    check_git_dirty()
    run(
        ["uv", "run", "python", "tools/field_sync.py", "--check"],
        "[1/3] 字段闸门",
    )
    run(
        ["uv", "run", "python", "tools/field_sync.py", "--report", "--with-code"],
        "[2/3] 文档待办",
    )
    run(
        ["uv", "run", "pytest", "tests/test_api.py", "-q"],
        "[3/3] 全量测试",
    )
    print("\n=== 全部通过，可以 git commit ===")


if __name__ == "__main__":
    main()
