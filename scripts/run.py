"""Run the live demo with the isolated environment created by setup.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_PATH = PROJECT_ROOT / ".venv"


def main() -> None:
    """Forward CLI arguments to main.py using the prepared interpreter."""

    directory = "Scripts" if sys.platform == "win32" else "bin"
    executable = "python.exe" if sys.platform == "win32" else "python"
    python = VENV_PATH / directory / executable
    if not python.is_file():
        raise RuntimeError("Environment not found. Run: python scripts/setup.py")
    subprocess.run(
        [str(python), str(PROJECT_ROOT / "main.py"), *sys.argv[1:]],
        cwd=PROJECT_ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
