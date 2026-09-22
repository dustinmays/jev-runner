import json
import os
import urllib.error
import urllib.request

ENDPOINT = os.environ.get("JEV_ENDPOINT", "https://openrouter.ai/api/alpha/decisions")
MODEL = os.environ.get("JEV_MODEL", "typesafe/jev-1.13")


def jev_ask(args: dict, **kwargs) -> str:
    state = args.get("state", "")
    questions = args.get("questions", {})
    if not state or not questions:
        return json.dumps({"error": "both 'state' and 'questions' are required"})

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return json.dumps({"error": "OPENROUTER_API_KEY is not set"})

    body = json.dumps({"model": MODEL, "state": state, "questions": questions}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.dumps({"error": f"Jev request failed: {e.code} {e.read().decode('utf-8', 'replace')}"})
    except urllib.error.URLError as e:
        return json.dumps({"error": f"Request to {ENDPOINT} failed: {e.reason}"})

    return json.dumps(result.get("answers", result))
