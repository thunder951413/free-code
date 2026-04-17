#!/usr/bin/env python3
"""Manual integration test for the Python <-> free-code CLI bridge."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional

from free_code_cli_client import FreeCodeCliClient, extract_assistant_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send one prompt to the free-code CLI through stream-json.",
    )
    parser.add_argument("--cli", help="Path to the built CLI executable.")
    parser.add_argument("--cwd", help="Working directory for the CLI process.")
    parser.add_argument(
        "--message",
        default="请用一句话回复：Python bridge OK",
        help="User message to send.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="Timeout in seconds for the full turn.",
    )
    parser.add_argument(
        "--cli-arg",
        action="append",
        default=[],
        help="Extra CLI arg, repeatable. Example: --cli-arg=--dangerously-skip-permissions",
    )
    parser.add_argument(
        "--auto-approve-tools",
        action="store_true",
        help="Automatically allow can_use_tool permission requests.",
    )
    parser.add_argument(
        "--fail-on-result-error",
        action="store_true",
        help="Exit non-zero if the final result event contains is_error=true.",
    )
    return parser


def auto_permission_handler(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    request = event.get("request")
    if not isinstance(request, dict):
        return None
    if request.get("subtype") != "can_use_tool":
        return None
    return {
        "behavior": "allow",
        "updatedInput": request.get("input", {}),
    }


def print_event(event: Dict[str, Any]) -> None:
    event_type = event.get("type")

    if event_type in {"assistant", "assistant_partial"}:
        text = extract_assistant_text(event)
        if text:
            print(f"[{event_type}] {text}")
            return

    if event_type == "stream_event":
        inner = event.get("event")
        if isinstance(inner, dict):
            print(f"[stream_event] {json.dumps(inner, ensure_ascii=False)}")
            return

    if event_type == "control_request":
        request = event.get("request")
        if isinstance(request, dict):
            subtype = request.get("subtype")
            print(f"[control_request:{subtype}] {json.dumps(request, ensure_ascii=False)}")
            return

    if event_type == "control_response":
        print(f"[control_response] {json.dumps(event.get('response'), ensure_ascii=False)}")
        return

    if event_type == "system":
        subtype = event.get("subtype")
        print(f"[system:{subtype}] {json.dumps(event, ensure_ascii=False)}")
        return

    if event_type == "result":
        print(f"[result] {json.dumps(event, ensure_ascii=False)}")
        return

    print(f"[{event_type}] {json.dumps(event, ensure_ascii=False)}")


def main() -> int:
    args = build_parser().parse_args()

    handler = auto_permission_handler if args.auto_approve_tools else None

    try:
        with FreeCodeCliClient(
            cli_path=args.cli,
            cwd=args.cwd,
            extra_args=args.cli_arg,
            auto_permission_handler=handler,
        ) as client:
            print(f"CLI: {client.cli_path}")
            print(f"CWD: {client.cwd}")
            print(f"Session ID: {client.session_id}")
            print(f"Prompt: {args.message}")
            print("")

            events = client.ask(
                args.message,
                timeout=args.timeout,
                on_event=print_event,
            )

            result = events[-1]
            if args.fail_on_result_error and result.get("is_error"):
                print("Final result contains is_error=true", file=sys.stderr)
                return 2

            return 0
    except Exception as exc:
        print(f"Bridge test failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
