#!/usr/bin/env python3
"""Run the optional FastAPI bridge server."""

from __future__ import annotations

import argparse
from typing import Any, Dict, Optional

try:
    from .api_server import create_app
except ImportError:
    from api_server import create_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the free-code Python API server.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    parser.add_argument("--port", type=int, default=8000, help="Bind port.")
    parser.add_argument("--cli", help="Path to CLI executable.")
    parser.add_argument("--cwd", help="Working directory for CLI sessions.")
    parser.add_argument(
        "--cli-arg",
        action="append",
        default=[],
        help="Extra CLI arg, repeatable.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("Please install uvicorn first: pip install uvicorn fastapi") from exc

    app = create_app(
        cli_path=args.cli,
        cwd=args.cwd,
        extra_args=args.cli_arg,
    )
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
