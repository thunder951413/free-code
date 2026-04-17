#!/usr/bin/env python3
"""HTTP test client for the optional FastAPI bridge server."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


def http_json(method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test the free-code Python API server.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL.")
    parser.add_argument(
        "--message",
        default="请只回复 API bridge OK",
        help="Prompt sent to the API server.",
    )
    parser.add_argument(
        "--session-id",
        default="web-test-session",
        help="Session ID used for the test.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="Request timeout forwarded to the backend.",
    )
    parser.add_argument(
        "--fail-on-result-error",
        action="store_true",
        help="Exit non-zero if result.is_error is true.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    base_url = args.base_url.rstrip("/")

    try:
        health = http_json("GET", f"{base_url}/health")
        print("health:", json.dumps(health, ensure_ascii=False))

        created = http_json(
            "POST",
            f"{base_url}/sessions",
            {"session_id": args.session_id},
        )
        print("session:", json.dumps(created, ensure_ascii=False))

        reply = http_json(
            "POST",
            f"{base_url}/chat/{args.session_id}",
            {"message": args.message, "timeout": args.timeout},
        )
        print("assistant_text:", reply.get("assistant_text", ""))
        print("result:", json.dumps(reply.get("result"), ensure_ascii=False))

        result = reply.get("result") or {}
        if args.fail_on_result_error and result.get("is_error"):
            print("Final result contains is_error=true", file=sys.stderr)
            return 2
        return 0
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error {exc.code}: {detail}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"API test failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
