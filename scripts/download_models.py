"""Download and verify the external model weights required by the live demo."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "yolo26n-pose.pt"
EXPECTED_SHA256 = "eb3bb8268828aeaf515cec23a4bfafd793944a86fe9af94ba7823609c14522a9"


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest without loading the whole model into memory."""

    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    """Obtain the official YOLO26n-pose weight and validate task and integrity."""

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(MODEL_PATH))
    if not MODEL_PATH.is_file():
        raise RuntimeError(f"Model download did not create {MODEL_PATH}")
    actual_sha256 = file_sha256(MODEL_PATH)
    if actual_sha256 != EXPECTED_SHA256:
        raise RuntimeError(
            "Unexpected yolo26n-pose.pt checksum. "
            f"Expected {EXPECTED_SHA256}, received {actual_sha256}."
        )
    if model.task != "pose":
        raise RuntimeError(f"Expected a pose model, received task {model.task!r}")
    print(f"Model ready: {MODEL_PATH}")
    print(f"SHA-256: {actual_sha256}")


if __name__ == "__main__":
    main()
