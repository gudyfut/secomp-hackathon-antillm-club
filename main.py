"""Executable live validation of perception-to-feature pipeline boundary."""

from __future__ import annotations

import argparse

from features import TemporalFeaturePipeline
from perception import run_live


def _source(value: str) -> str | int:
    return int(value) if value.isdigit() else value


def main() -> None:
    """Start webcam or video-file validation with YOLO26 pose and ByteTrack."""
    parser = argparse.ArgumentParser(description="Campus Sentinel live pipeline validation")
    parser.add_argument("--source", default="0", help="Webcam index or video path; default: 0")
    parser.add_argument(
        "--model",
        default="models/yolo26n-pose.pt",
        help="YOLO pose weights path; default: models/yolo26n-pose.pt",
    )
    args = parser.parse_args()
    run_live(_source(args.source), TemporalFeaturePipeline(), args.model)


if __name__ == "__main__":
    main()
