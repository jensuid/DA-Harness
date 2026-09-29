"""Measure the LLM plan prompt's output cost against the configured provider.

Reproduces the W3X-003 measurement on the *current* prompt so a shrink is
shown to buy time rather than assumed to, and so the recorded rate (~13
completion tokens/s) can be re-checked against the provider in play.

Usage (from the repo root):
  server/.venv/bin/python walktest-w3/measure_plan_prompt.py

Environment wins over `server/.env` (the same precedence the core uses).
"""

import json
import os
import re
import sys
import time

sys.path.insert(0, "server")

PROFILE = {
    "rows": 2984,
    "columns": [
        "ticket_id", "created_date", "product", "tier", "agent",
        "first_response_hours", "resolution_hours", "satisfaction",
        "channel", "reopened",
    ],
    "duplicate_rows": 0,
    "quality": [],
    "stats": {
        "ticket_id": {"type": "other", "null_count": 0, "null_percentage": 0.0,
                      "distinct_count": 2984},
        "created_date": {"type": "temporal", "null_count": 0,
                         "null_percentage": 0.0},
        "product": {"type": "other", "null_count": 0, "null_percentage": 0.0,
                    "distinct_count": 6},
        "tier": {"type": "other", "null_count": 0, "null_percentage": 0.0,
                 "distinct_count": 4},
        "agent": {"type": "other", "null_count": 47, "null_percentage": 1.6,
                  "distinct_count": 18},
        "first_response_hours": {"type": "numeric", "null_count": 12,
                                 "null_percentage": 0.4, "min": 0.08,
                                 "max": 41.9, "avg": 3.7},
        "resolution_hours": {"type": "numeric", "null_count": 104,
                             "null_percentage": 3.5, "min": 0.3, "max": 962.5,
                             "avg": 18.4},
        "satisfaction": {"type": "numeric", "null_count": 216,
                         "null_percentage": 7.2, "min": 1, "max": 5,
                         "avg": 4.1},
        "channel": {"type": "other", "null_count": 0, "null_percentage": 0.0,
                    "distinct_count": 5},
        "reopened": {"type": "other", "null_count": 0, "null_percentage": 0.0,
                     "distinct_count": 2},
    },
}

QUESTION = ("Which product tiers have the slowest support, and does slow first "
            "response predict low satisfaction?")


def _configured() -> tuple[str, str, str]:
    """env wins; `server/.env` is the advisory fallback."""
    env: dict[str, str] = {}

    def read(key: str) -> str:
        return (env.get(key) or "").strip()

    if not (os.environ.get("DAH_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        for line in open("server/.env", encoding="utf-8").read().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            env[name.strip()] = value.strip().strip('"').strip("'")
    env.update({k: v for k, v in os.environ.items() if k in env or True})
    # os.environ wins over the file.
    env.update(dict(os.environ))

    key = read("DAH_LLM_API_KEY") or read("OPENAI_API_KEY")
    base = read("DAH_LLM_BASE_URL") or "https://api.openai.com/v1"
    model = read("DAH_LLM_MODEL") or "gpt-4o-mini"
    if not key:
        sys.exit("no LLM key configured (DAH_LLM_API_KEY or server/.env)")
    return key, base, model


def _tokens(text: str) -> int:
    """A completion-token estimate close enough for rate arithmetic."""
    return len(re.findall(r"\w+|[^\w\s]", text))


def _post(key: str, base: str, model: str, prompt: str, label: str) -> dict:
    import httpx

    started = time.monotonic()
    response = httpx.post(
        f"{base.rstrip('/')}/chat/completions",
        headers={
            "authorization": f"Bearer {key}",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "Return valid JSON only, no prose."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        },
        timeout=900.0,
    )
    elapsed = time.monotonic() - started
    response.raise_for_status()
    choice = response.json()["choices"][0]
    content = choice["message"]["content"]
    out = _tokens(content)

    parsed: object = None
    note = ""
    try:
        parsed = json.loads(content)
    except Exception as error:
        note = f" UNPARSED({error})"
    print(
        f"{label:32s} {out:5d} tokens out  {elapsed:6.1f}s  "
        f"finish={choice.get('finish_reason')}  "
        f"rate={out / elapsed:5.1f} tok/s{note}"
    )
    if isinstance(parsed, dict):
        for field in ("sub_questions", "hypotheses", "analysis_steps",
                      "data_requirements"):
            value = parsed.get(field)
            if isinstance(value, list):
                print(f"    {field:20s} {len(value)}")
    sys.stdout.flush()
    return {"tokens": out, "seconds": elapsed}


def main() -> None:
    from app.planner import LLMPlanner

    key, base, model = _configured()
    print(f"provider: {model} at {base}\n")

    prompt = LLMPlanner(key, base, model).prompt(QUESTION, PROFILE)
    _post(key, base, model, prompt, "shipped prompt")
    _post(key, base, model, prompt, "shipped prompt (repeat)")


if __name__ == "__main__":
    main()
