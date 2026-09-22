# jev-openrouter

A small CLI/library for calling [TypeSafe's Jev](https://openrouter.ai/typesafe) decision model through OpenRouter.

Jev is a "System One" model: instead of generating text, it takes a `state` (context/text) plus a set of typed `questions` and returns typed decisions with confidence scores. It's routed through OpenRouter's alpha decisions endpoint, not the standard chat completions API — which is why it can't be plugged into chat-based coding agents (e.g. OpenCode) as a normal model.

## Setup

```bash
export OPENROUTER_API_KEY=sk-...
```

No third-party dependencies — uses only the Python standard library (`urllib`).

## Usage

CLI:

```bash
python3 ask_jev.py \
  --state "I was charged twice for my subscription." \
  --questions '{"refund": {"type": "noul", "instructions": "Is the customer asking for money back?"}}'
```

Returns JSON, e.g.:

```json
{
  "model": "typesafe/jev-1.13-20260917",
  "answers": {
    "refund": { "type": "noul", "noul": 0.77 }
  },
  "usage": { "input_tokens": 282, "output_tokens": 20, "cost": 1.1844e-05 },
  "id": "gen-dec-...",
  "provider": "TypeSafe"
}
```

As a library:

```python
from ask_jev import ask_jev

result = ask_jev(
    state="I was charged twice for my subscription.",
    questions={"refund": {"type": "noul", "instructions": "Is the customer asking for money back?"}},
)
```

## Question types

- `noul` — Yes/No/Uncertain/Likely, returned as a 0–1 confidence score.
- `choice` — categorical decision from a set of options.

See [OpenRouter's TypeSafe SDK guide](https://openrouter.ai/docs/guides/community/typesafe-sdk) for the full schema.

## Notes

- `--model` defaults to `typesafe/jev-1.13` (the pinned version). The `typesafe/jev-latest` alias shown on OpenRouter's model page is **not** a valid value for the `model` field in decision requests — it 400s.
- `--endpoint` / `JEV_ENDPOINT` override the API URL if OpenRouter changes the alpha path.
