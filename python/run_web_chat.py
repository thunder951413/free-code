#!/usr/bin/env python3
"""Run the simple browser chat UI."""

from __future__ import annotations

import argparse

try:
    from .web_chat_app import create_web_chat_app
except ImportError:
    from web_chat_app import create_web_chat_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the simple free-code web chat app.")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default 0.0.0.0 for LAN access).")
    parser.add_argument("--port", type=int, default=18001, help="Bind port.")
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
    args = build_parser().parse_args()

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("Please install uvicorn first: pip install uvicorn fastapi") from exc

    app = create_web_chat_app(
        cli_path=args.cli,
        cwd=args.cwd,
        extra_args=args.cli_arg,
    )
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
