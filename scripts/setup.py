"""Create an isolated environment and prepare all current Campus Sentinel modules."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from shutil import copyfile, which

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


def cuda_wheel_index() -> str | None:
    """Return the best supported PyTorch CUDA wheel index for the NVIDIA driver."""

    executable = which("nvidia-smi")
    if executable is None:
        return None
    result = subprocess.run(
        [executable],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    match = re.search(r"CUDA Version:\s*(\d+)\.(\d+)", result.stdout)
    if result.returncode != 0 or match is None:
        return None
    version = tuple(int(part) for part in match.groups())
    if version >= (13, 0):
        return "cu130"
    if version >= (12, 6):
        return "cu126"
    return None


def install_cuda_torch(python: str) -> None:
    """Replace a CPU-only Torch install when a compatible NVIDIA driver is present."""

    index = cuda_wheel_index()
    if index is None:
        print("NVIDIA CUDA compatível não detectado; mantendo o fallback de CPU.")
        return
    cuda_ready = subprocess.run(
        [python, "-c", "import torch; raise SystemExit(not torch.cuda.is_available())"],
        cwd=PROJECT_ROOT,
        check=False,
    ).returncode == 0
    if cuda_ready:
        print(f"PyTorch CUDA já está ativo ({index}).")
        return
    run(
        python,
        "-m",
        "pip",
        "install",
        "--force-reinstall",
        "--no-deps",
        "--resume-retries",
        "20",
        "--timeout",
        "60",
        "torch==2.14.0",
        "torchvision==0.29.0",
        "--index-url",
        f"https://download.pytorch.org/whl/{index}",
    )


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
        f"{PROJECT_ROOT}[dev,perception,decision,interface]",
    )
    install_cuda_torch(python)
    run(python, str(PROJECT_ROOT / "scripts" / "download_models.py"))
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        copyfile(PROJECT_ROOT / ".env.example", env_path)
        print(f"Created local configuration: {env_path}")
    run(python, "-m", "pytest")

    print("\nSetup complete.")
    print(f"Run the web interface with: {python} -m interface")
    print("Then open: http://127.0.0.1:8000")
    print("Optional OpenCV diagnostic: python scripts/run.py --source 0")
    print("Run the offline Jev simulation with the .venv Python and -m decision.examples.simulated")


if __name__ == "__main__":
    main()
