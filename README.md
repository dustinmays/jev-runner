# jev-runner

Tools for calling [TypeSafe's Jev](https://docs.typesafe.ai/) decision model — a "System One" model that, instead of generating text, takes a `state` (context/text or structured data) plus a set of typed `questions` and returns typed decisions (probabilities, categorical choices, scored ratings) rather than prose.

This repo has two independent pieces, hitting two different backends:

- **`jev-eval`** — the primary tool. A generic Unix filter (`state + questions in, typed answers out`) against TypeSafe's own direct, documented API. No policy baked in — it's meant to be the fuzzy-judgment primitive that any script, cron job, or agent (Hermes, OpenCode, shell) pipes JSON through.
- **`ask_jev.py` + Hermes plugin** — an earlier prototype that goes through OpenRouter's undocumented alpha decisions endpoint instead. Kept because the Hermes plugin already depends on it; see below.

## jev-eval

```bash
export TYPESAFE_API_KEY=...
cat examples/model-routing.json | ./jev-eval
```

stdin is one JSON object, stdout is JSON only (logs go to stderr, exit code is nonzero on validation/API failure) — safe to pipe straight into `jq`.

**Input:**

```json
{
  "state": { "...": "string, object, or array — whatever context Jev needs" },
  "questions": {
    "some_key": { "type": "noul", "instructions": "Is X true?" },
    "other_key": { "type": "choice", "instructions": "...", "criteria": {"a": "...", "b": "..."} },
    "third_key": { "type": "score", "instructions": "...", "criteria": ["low", "medium", "high"] }
  }
}
```

**Output:**

```json
{
  "ok": true,
  "model": "jev-1.13.0",
  "answers": {
    "some_key": { "type": "noul", "value": 0.91 },
    "other_key": { "type": "choice", "value": "a", "confidence": 0.81, "probabilities": {"a": 0.78, "b": 0.22}, "ranking": [["a", 0.78], ["b", 0.22]] },
    "third_key": { "type": "score", "value": 1.6, "confidence": 0.7, "probabilities": {"0": 0.1, "1": 0.3, "2": 0.6}, "legend": {"0": "low", "1": "medium", "2": "high"} }
  },
  "usage": { "input_tokens": 842, "output_tokens": 84 },
  "raw": { "...": "unmodified TypeSafe response, for debugging" }
}
```

Three primitives, used as-is — no invented "rank" abstraction yet. If you need "which of these is best" use `choice` and read `ranking`; if you need "is each of these independently adequate" (they might all be, or none), issue one `noul` per candidate and sort the results yourself — a single `choice` always produces a winner even when nothing is actually good enough.

**Architectural boundary:** `jev-eval` returns fuzzy judgments only. It deliberately does not decide what to do with them (which model to route to, what threshold counts as "adequate," whether to interrupt a human) — that policy belongs in the calling workflow, not in this tool. Example use case (`examples/model-routing.json`): feed an agent's task state + available agents/models in, get back typed probabilities, let your own code apply the threshold.

No third-party dependencies — stdlib `urllib` only.

## ask_jev.py (OpenRouter route)

### Setup

```bash
export OPENROUTER_API_KEY=sk-...
```

No third-party dependencies — uses only the Python standard library (`urllib`).

### Usage

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

### Question types

- `noul` — Yes/No/Uncertain/Likely, returned as a 0–1 confidence score.
- `choice` — categorical decision from a set of options.

See [OpenRouter's TypeSafe SDK guide](https://openrouter.ai/docs/guides/community/typesafe-sdk) for the full schema.

### Notes

- `--model` defaults to `typesafe/jev-1.13` (the pinned version). The `typesafe/jev-latest` alias shown on OpenRouter's model page is **not** a valid value for the `model` field in decision requests — it 400s.
- `--endpoint` / `JEV_ENDPOINT` override the API URL if OpenRouter changes the alpha path.

### Hermes Agent plugin

`hermes-plugin/jev/` is a self-contained [Hermes plugin](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins) exposing a single generic tool, `jev_ask(state, questions)`, so Hermes can call Jev directly for quick decisions instead of reasoning it out itself. It's deliberately not wired to the top-level `ask_jev.py` — plugins are self-contained by Hermes convention, so `hermes-plugin/jev/tools.py` carries its own copy of the same stdlib-only request logic.

#### Install on the Hermes VPS (Docker)

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

#### Tool contract

- **Input:** `state` (string) + `questions` (map of `question_key` → `{type: "noul"|"choice", instructions, choices?}`)
- **Output:** JSON string of the `answers` map (e.g. `{"refund": {"type": "noul", "noul": 0.77}}`), or `{"error": "..."}` on failure — handlers never raise, per Hermes's tool contract.
- **Model/endpoint overrides:** `JEV_MODEL` / `JEV_ENDPOINT` env vars, same defaults as the CLI.
