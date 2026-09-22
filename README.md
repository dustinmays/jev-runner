# jev-runner

A small CLI/library for calling [TypeSafe's Jev](https://openrouter.ai/typesafe) decision model through OpenRouter, plus a [Hermes Agent](https://hermes-agent.nousresearch.com/) plugin that exposes it as a native tool.

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

## Hermes Agent plugin

`hermes-plugin/jev/` is a self-contained [Hermes plugin](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins) exposing a single generic tool, `jev_ask(state, questions)`, so Hermes can call Jev directly for quick decisions instead of reasoning it out itself. It's deliberately not wired to the top-level `ask_jev.py` — plugins are self-contained by Hermes convention, so `hermes-plugin/jev/tools.py` carries its own copy of the same stdlib-only request logic.

### Install on the Hermes VPS (Docker)

Hermes stores plugins under `~/.hermes/plugins/` on the host, which is bind-mounted into the container at `/opt/data/plugins/`. Clone this repo somewhere on the host (or wherever your Hermes container already has file access) and symlink the plugin folder in, rather than copying it, so `git pull` here is enough to update it:

```bash
git clone https://github.com/dustinmays/jev-runner.git ~/repos/jev-runner
ln -s ~/repos/jev-runner/hermes-plugin/jev ~/.hermes/plugins/jev
```

Then set the key. `plugin.yaml` declares `requires_env: OPENROUTER_API_KEY`, so Hermes will prompt for it on next plugin load if it's missing; you can also add it directly to the same `.env` Hermes already uses for its other provider keys:

```bash
echo "OPENROUTER_API_KEY=sk-..." >> ~/.hermes/.env
```

Restart the gateway (`docker compose restart hermes`, or however you run it) and `jev_ask` should show up as an available tool.

### Tool contract

- **Input:** `state` (string) + `questions` (map of `question_key` → `{type: "noul"|"choice", instructions, choices?}`)
- **Output:** JSON string of the `answers` map (e.g. `{"refund": {"type": "noul", "noul": 0.77}}`), or `{"error": "..."}` on failure — handlers never raise, per Hermes's tool contract.
- **Model/endpoint overrides:** `JEV_MODEL` / `JEV_ENDPOINT` env vars, same defaults as the CLI.
