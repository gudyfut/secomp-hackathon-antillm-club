"""Run the local Campus Sentinel web dashboard."""

from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Campus Sentinel MVP dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    uvicorn.run("interface.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
