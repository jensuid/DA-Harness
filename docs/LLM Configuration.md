# LLM Configuration

The AI planner prefers an LLM when a key is configured and falls back to a
deterministic planner otherwise, so the analysis loop never blocks on a missing
or misbehaving backend. This page covers how to enable the LLM path.

The planner talks to any **OpenAI-compatible** endpoint, so any third-party or
self-hosted provider that exposes that API works - set the base URL and model
and it is agnostic to what is behind them.

## Variables

The planner reads these from the **server process environment**. There is no
dotenv auto-loading - the `.env` file must be sourced into the shell that
starts uvicorn (see below).

| Variable | Required | Purpose |
|----------|----------|---------|
| `DAH_LLM_API_KEY` | yes | The API key for your provider. Falls back to `OPENAI_API_KEY` if this is absent. |
| `DAH_LLM_BASE_URL` | no | The provider's OpenAI-compatible endpoint. Defaults to `https://api.openai.com/v1`. **Set this for any third-party provider.** |
| `DAH_LLM_MODEL` | no | The model name your provider expects. Defaults to `gpt-4o-mini`. |

## Setup with a `.env` file (recommended)

Configuration lives in `server/.env` - already gitignored - so it persists
across sessions without retyping anything in the terminal.

### 1. Create the file

```bash
cd /Volumes/JensData/Jensu-Projects/DA-Harness/server
cat > .env <<'ENV'
# Third-party / self-hosted OpenAI-compatible provider
DAH_LLM_API_KEY="your-provider-key"
DAH_LLM_BASE_URL="https://your-provider.example.com/v1"
DAH_LLM_MODEL="their-model-name"
ENV
chmod 600 .env
```

Only `DAH_LLM_API_KEY` is required. Drop the last two lines if you are using
OpenAI itself (the defaults already point there).

### 2. Start the server with the file loaded

```bash
set -a; . ./.env; set +a
.venv/bin/python -m uvicorn app.main:app --port 8123
```

`set -a` exports every variable the file defines, so a plain `. ./.env` is
not enough on its own - without it the variables stay shell-local and never
reach the server process.

To avoid typing the source line every time, wrap it in a small launcher:

```bash
# server/run.sh
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
set -a; . ./.env; set +a
exec .venv/bin/python -m uvicorn app.main:app --port 8123
```

```bash
chmod +x run.sh
./run.sh
```

### 3. Check it took effect

The plan response carries a `source` field saying which engine produced it:

```bash
curl -X POST http://localhost:8123/cases/{case_id}/datasets/{dataset_id}/plan
# -> {"source": "llm", ...}            the LLM path is live
# -> {"source": "deterministic", ...}   no key reached the server
```

`GET /cases/{id}/datasets/{id}/plans` lists the history with each plan's
source, so you can tell after the fact which engine ran.

## Alternative: set the variables inline

For a one-off run, skip the file and set the variables on the command line:

```bash
DAH_LLM_API_KEY="your-provider-key" \
DAH_LLM_BASE_URL="https://your-provider.example.com/v1" \
DAH_LLM_MODEL="their-model-name" \
.venv/bin/python -m uvicorn app.main:app --port 8123
```

These do not persist once the terminal closes - that is what the `.env` file
is for.

## Notes

- **Safe by design.** If the key is missing or the LLM errors, `create_plan`
  falls back to the deterministic planner, so a plan is always returned. Bad LLM
  output is schema-validated and rejected on the way in - never persisted.
- **The key stays out of analysis runs.** The hard sandbox (P3-SEC-001) scrubs
  the environment of the Python child process, so user-supplied analysis code
  cannot read the key.
- **Never commit a key.** `.env` is gitignored precisely for this. Do not put a
  key value in any tracked file, and do not add `.env` to git with `-f`.
