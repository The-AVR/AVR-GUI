import argparse
import os
import subprocess

THIS_DIR = os.path.abspath(os.path.dirname(__file__))


def main(version: str) -> None:
    cmd = [
        "pyinstaller",
        os.path.join(THIS_DIR, "app.py"),
        "--onefile",
        "--noconfirm",
        "--name",
        "AVRGUI",
        "--icon",
        os.path.join(THIS_DIR, "assets", "img", "logo.ico"),
        "--add-data",
        f"{os.path.join(THIS_DIR, 'assets')}{os.pathsep}{os.path.join('assets')}",
        "--hidden-import",
        "PySide6.QtSvg",
    ]

    print(cmd)
    subprocess.check_call(cmd, cwd=THIS_DIR)

    # rename executable when running in CI
    if os.environ["CI"] == "true":
        os.rename(
            os.path.join(THIS_DIR, "dist", "AVRGUI.exe"),
            os.path.join(THIS_DIR, "dist", f"AVRGUI.{version}.exe"),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        default=subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip(),
    )
    args = parser.parse_args()

    main(args.version)
