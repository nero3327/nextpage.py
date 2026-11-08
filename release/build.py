"""打包发布脚本：用 PyInstaller 把程序打成 Windows 可执行文件。

用法：python release/build.py
产物：release/dist/nextpage.exe
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE = Path(__file__).resolve().parent
ENTRY = ROOT / "main.py"
APP_NAME = "nextpage"


def main():
    version = (RELEASE / "version.txt").read_text(encoding="utf-8").strip()

    if not ENTRY.exists():
        sys.exit(f"错误：入口文件不存在：{ENTRY}\n请先在项目根目录创建 main.py（tk GUI 入口）。")

    if shutil.which("pyinstaller") is None:
        try:
            subprocess.run(
                [sys.executable, "-m", "PyInstaller", "--version"],
                check=True, capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            sys.exit(
                "错误：未安装 PyInstaller。\n"
                "请手动执行：python -m pip install pyinstaller\n"
                "安装后重新运行本脚本。"
            )

    for sub in ("build", "dist"):
        shutil.rmtree(RELEASE / sub, ignore_errors=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile", "--windowed",
        "--name", APP_NAME,
        "--distpath", str(RELEASE / "dist"),
        "--workpath", str(RELEASE / "build"),
        "--specpath", str(RELEASE / "build"),
        str(ENTRY),
    ]
    print(f"打包 {APP_NAME} v{version} ...")
    subprocess.run(cmd, check=True, cwd=ROOT)
    print(f"\n完成：{RELEASE / 'dist' / (APP_NAME + '.exe')}（v{version}）")


if __name__ == "__main__":
    main()