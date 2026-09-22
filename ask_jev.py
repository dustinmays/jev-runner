#!/usr/bin/env python3
"""Query TypeSafe's Jev decision model via OpenRouter with structured in/out."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_ENDPOINT = os.environ.get("JEV_ENDPOINT", "https://openrouter.ai/api/alpha/decisions")
DEFAULT_MODEL = "typesafe/jev-1.13"


def ask_jev(
    state: str,
    questions: dict[str, dict[str, Any]],
    *,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_ENDPOINT,
    api_key: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Send state + typed questions to Jev, return the parsed JSON response."""
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENROUTER_API_KEY (or pass api_key=)")

    body = json.dumps({"model": model, "state": state, "questions": questions}).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Jev request failed: {e.code} {e.read().decode('utf-8', 'replace')}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Request to {endpoint} failed: {e.reason}") from e


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask Jev a structured decision question via OpenRouter.")
    parser.add_argument("--state", required=True, help="Context/text for Jev to evaluate.")
    parser.add_argument(
        "--questions",
        required=True,
        help='JSON map, e.g. \'{"refund": {"type": "noul", "instructions": "Is the customer asking for money back?"}}\'',
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    args = parser.parse_args()

    try:
        questions = json.loads(args.questions)
    except json.JSONDecodeError as e:
        sys.exit(f"--questions must be valid JSON: {e}")

    try:
        result = ask_jev(args.state, questions, model=args.model, endpoint=args.endpoint)
    except RuntimeError as e:
        sys.exit(str(e))

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
