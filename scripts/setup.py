"""Create an isolated environment and prepare all current Campus Sentinel modules."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from shutil import copyfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_PATH = PROJECT_ROOT / ".venv"


def venv_python() -> Path:
    """Return the virtual-environment interpreter path for the current platform."""

    directory = "Scripts" if sys.platform == "win32" else "bin"
    executable = "python.exe" if sys.platform == "win32" else "python"
    return VENV_PATH / directory / executable


def run(*command: str) -> None:
    """Run one setup step from the project root and fail immediately on errors."""

    print(f"\n> {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    """Install all dependencies, obtain the model, prepare env, and run offline tests."""

    if sys.version_info < (3, 11):  # noqa: UP036 - setup runs before package installation
        raise RuntimeError("Campus Sentinel requires Python 3.11 or newer")
    if not VENV_PATH.exists():
        run(sys.executable, "-m", "venv", str(VENV_PATH))

    python = str(venv_python())
    run(
        python,
        "-m",
        "pip",
        "install",
        "-e",
        f"{PROJECT_ROOT}[dev,perception,decision]",
    )
    run(python, str(PROJECT_ROOT / "scripts" / "download_models.py"))
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        copyfile(PROJECT_ROOT / ".env.example", env_path)
        print(f"Created local configuration: {env_path}")
    run(python, "-m", "pytest")

    print("\nSetup complete.")
    print("Run the webcam with: python scripts/run.py --source 0")
    print("Run the offline Jev simulation with the .venv Python and -m decision.examples.simulated")


if __name__ == "__main__":
    main()
