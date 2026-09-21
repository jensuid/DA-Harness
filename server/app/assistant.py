"""Case-scoped conversational assistant (P3-AI-014, contextual AI slice 4).

The last piece of the assistant. Slices 1-3 propose - a question yields the
computation that would answer it (P3-AI-013), a result yields a reading of what
it shows (P3-AI-011) and a candidate finding with the grounds it stands on
(P3-AI-012). Each stops one step short of writing state. This slice answers
questions about the case as it stands, remembers the conversation, and cites the
artifact behind every claim.

`summarize_case` reads the case's rows and builds the facts an answer may draw
on - a pure projection, like the evidence graph and the history timeline, so it
cannot drift from what is on disk.

Two engines sit behind one interface, as in the planner, the interpreter, the
drafter and the generator:

- `answer_question` is deterministic and always available. It answers count
  questions, questions about a column or a dataset, and otherwise states where
  the case stands and the single action that advances it (reusing P3-FLOW-004's
  derived stage, so it cannot claim a step the data does not support).
- `LLMAssistant` calls an OpenAI-compatible endpoint when `DAH_LLM_API_KEY` is
  set and receives the recent turns as context - that is the memory.

Honesty is enforced rather than hoped for: every citation in `grounds` must be
an artifact the case actually has. An invented citation is a validation failure
and the answer falls back to the deterministic one, which only ever cites what
`summarize_case` read from the rows.

The LLM is an external engine the harness controls, not the other way round;
swapping provider means implementing `answer(message, history, facts)`.
"""

import json
import logging
import os
import re
from typing import Any

_MAX_HISTORY_TURNS = 10
_MAX_LLM_CHARS = 16_000

SOURCE_DETERMINISTIC = "deterministic"
SOURCE_LLM = "llm"

KIND_DATASET = "dataset"
KIND_RUN = "run"
KIND_FINDING = "finding"
KIND_PLAN = "plan"
KIND_CHART = "chart"
KIND_COLUMN = "column"
KIND_CASE = "case"  # a previous case, added by P6-MEMORY-001
KIND_CONTEXT = "context"  # the case's own stated intent, P8-CONTEXT-001

_GROUND_RE = re.compile(r"^(dataset|run|finding|plan|chart|column|case|context):(.+)$")
_WORD_RE = re.compile(r"[A-Za-z0-9_]+")


def _profile_of(db, dataset_id: str) -> dict | None:
    row = db.execute(
        "SELECT rows, columns_json, stats_json FROM profiles WHERE dataset_id = ?",
        (dataset_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "rows": row["rows"],
        "columns": json.loads(row["columns_json"]),
        "stats": json.loads(row["stats_json"]),
    }


def summarize_case(db, case_id: str, message: str = "") -> dict:
    """Everything an answer about this case may draw on.

    Read from the case's own rows, so the facts cannot drift from what is on
    disk. Runs carry their columns and row counts but not their result rows - a
    conversation points at evidence, it does not replay it.

    `message` is the question being answered, and it is what memory is built
    against (P6-MEMORY-001): which previous cases bear on *this* question is
    not a property of the case, it depends on what was asked. Optional because
    the facts are also read for purposes that have no question to match.
    """
    from app.workflow import case_progress

    case_row = db.execute(
        "SELECT question, dataset FROM cases WHERE id = ?", (case_id,)
    ).fetchone()
    facts: dict[str, Any] = {
        "case_id": case_id,
        "question": case_row["question"] if case_row else "",
    }

    datasets = []
    for row in db.execute(
        "SELECT id, filename FROM datasets WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        datasets.append(
            {
                "id": row["id"],
                "label": row["filename"],
                "profile": _profile_of(db, row["id"]),
            }
        )
    facts["datasets"] = datasets

    runs = []
    for row in db.execute(
        "SELECT id, kind, sql, code, row_count, columns_json FROM runs "
        "WHERE case_id = ? ORDER BY executed_at",
        (case_id,),
    ).fetchall():
        runs.append(
            {
                "id": row["id"],
                "kind": row["kind"],
                "row_count": row["row_count"],
                "columns": json.loads(row["columns_json"]),
                "source": (row["sql"] if row["kind"] == "sql" else row["code"]) or "",
            }
        )
    facts["runs"] = runs

    facts["findings"] = [
        {"id": row["id"], "statement": row["statement"], "status": row["validation_status"]}
        for row in db.execute(
            "SELECT id, statement, validation_status FROM findings "
            "WHERE case_id = ? ORDER BY created_at",
            (case_id,),
        ).fetchall()
    ]
    facts["plans"] = [
        {
            "id": row["id"],
            "objective": (json.loads(row["plan_json"]) or {}).get("objective", ""),
        }
        for row in db.execute(
            "SELECT id, plan_json FROM plans WHERE case_id = ? ORDER BY created_at",
            (case_id,),
        ).fetchall()
    ]
    facts["charts"] = [
        {"id": row["id"], "kind": row["kind"]}
        for row in db.execute(
            "SELECT id, kind FROM charts WHERE case_id = ? ORDER BY created_at",
            (case_id,),
        ).fetchall()
    ]
    # The analyst's stated intent (P8-CONTEXT-001): what the case is for, what
    # it would test. A question about purpose answers from here rather than from
    # the columns, which is what the UX architecture's Context section asks for.
    context_row = db.execute(
        "SELECT purpose, sub_questions_json, hypotheses_json, constraints_json "
        "FROM contexts WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    facts["context"] = (
        {
            "purpose": context_row["purpose"] or "",
            "sub_questions": json.loads(context_row["sub_questions_json"] or "[]"),
            "hypotheses": json.loads(context_row["hypotheses_json"] or "[]"),
            "constraints": json.loads(context_row["constraints_json"] or "[]"),
        }
        if context_row is not None
        else {"purpose": "", "sub_questions": [], "hypotheses": [], "constraints": []}
    )

    facts["progress"] = case_progress(db, case_id)

    # P6-MEMORY-001: what previous cases found. Derived per question, not
    # stored - the message decides which prior cases are relevant, so memory is
    # built alongside the answer rather than ahead of it.
    from app.memory import summarize_memory

    facts["memory"] = summarize_memory(db, case_id, message)
    return facts


def _references(facts: dict) -> dict[str, set[str]]:
    """The names a ground may cite, by kind.

    Columns are keyed by name across every dataset, since a question naming a
    column does not say which dataset it came from.
    """
    by_kind: dict[str, set[str]] = {
        KIND_DATASET: set(),
        KIND_RUN: set(),
        KIND_FINDING: set(),
        KIND_PLAN: set(),
        KIND_CHART: set(),
        KIND_COLUMN: set(),
        KIND_CASE: set(),
    }
    for dataset in facts.get("datasets") or []:
        by_kind[KIND_DATASET].add(dataset["id"])
        if dataset.get("label"):
            by_kind[KIND_DATASET].add(dataset["label"])
        profile = dataset.get("profile") or {}
        for name in profile.get("columns") or []:
            by_kind[KIND_COLUMN].add(name)
    for run in facts.get("runs") or []:
        by_kind[KIND_RUN].add(run["id"])
    for finding in facts.get("findings") or []:
        by_kind[KIND_FINDING].add(finding["id"])
    for plan in facts.get("plans") or []:
        by_kind[KIND_PLAN].add(plan["id"])
    for chart in facts.get("charts") or []:
        by_kind[KIND_CHART].add(chart["id"])
    # A previous case is citable by id and by its question, and its findings
    # are citable too - the recall is only useful if the citation resolves to
    # a real row in a real other case (P6-MEMORY-001).
    for memory in facts.get("memory") or []:
        by_kind[KIND_CASE].add(memory["case_id"])
        if memory.get("question"):
            by_kind[KIND_CASE].add(memory["question"])
        for finding in memory.get("findings") or []:
            by_kind[KIND_FINDING].add(finding["id"])
    return by_kind


def _has_artifacts(facts: dict) -> bool:
    return any(
        facts.get(key)
        for key in ("datasets", "runs", "findings", "plans", "charts")
    )


def _counts(facts: dict) -> dict[str, int]:
    return {
        "datasets": len(facts.get("datasets") or []),
        "runs": len(facts.get("runs") or []),
        "findings": len(facts.get("findings") or []),
        "plans": len(facts.get("plans") or []),
        "charts": len(facts.get("charts") or []),
    }


def _tidy(value: Any) -> Any:
    """Round a float for display, so an average does not print 16 digits."""
    if isinstance(value, float):
        return round(value, 4)
    return value


def _fmt_stat(name: str, stat: dict) -> str:
    parts = [f"type {stat.get('type', 'unknown')}"]
    if stat.get("distinct_count") is not None:
        parts.append(f"{stat['distinct_count']} distinct")
    if (stat.get("null_count") or 0) > 0:
        parts.append(f"{stat['null_percentage']}% null")
    for key in ("min", "max", "avg"):
        if stat.get(key) is not None:
            parts.append(f"{key} {_tidy(stat[key])}")
    return f"{name}: " + ", ".join(parts)


def _first_matching_column(message: str, facts: dict) -> tuple[str, str, dict] | None:
    """A column the message names, as (dataset_id, column_name, stat)."""
    words = {word.lower() for word in _WORD_RE.findall(message)}
    for dataset in facts.get("datasets") or []:
        profile = dataset.get("profile") or {}
        stats = profile.get("stats") or {}
        for name in profile.get("columns") or []:
            if name.lower() in words:
                return dataset["id"], name, stats.get(name) or {}
    return None


def answer_question(message: str, history: list[dict], facts: dict) -> dict:
    """Answer a question about the case, deterministically.

    Every fact the answer states is read from `facts`, which is read from the
    case's rows, so the answer cannot describe an artifact the case does not
    have. `history` is deliberately unused here - the deterministic engine has
    no use for it - but it is part of the interface the LLM engine fulfils.
    """
    message = (message or "").strip()
    lowered = message.lower()
    counts = _counts(facts)
    grounds: list[str] = []

    if re.search(r"\bhow (many|much)\b|\bcount\b|\bhow big\b", lowered):
        parts = [
            f"{counts['datasets']} dataset(s)",
            f"{counts['runs']} run(s)",
            f"{counts['findings']} finding(s)",
            f"{counts['charts']} chart(s)",
        ]
        grounds = _artifact_grounds(facts, kinds=(KIND_DATASET, KIND_RUN, KIND_FINDING, KIND_CHART))
        return {
            "answer": f"The case has {', '.join(parts)}.",
            "grounds": grounds,
        }

    # P6-MEMORY-001: what previous cases found. Two ways in, both deliberate:
    #  - the question is *about* prior work (before/previous/earlier/...). This
    #    is checked before the column and dataset branches on purpose: a
    #    question like "what did I find before about revenue?" names a column
    #    and would otherwise be answered with this case's column stats - a true
    #    answer to a question nobody asked.
    #  - this case has nothing of its own yet, so the alternative answer would
    #    be "attach a dataset" - true, but useless to someone who has already
    #    investigated this question and would rather know what they found.
    # A case with its own artifacts and no prior-work framing gets its own
    # stage and next action instead, because its own state is the more
    # actionable thing. Memory is threshold-filtered in summarize_memory, so
    # present means relevant.
    memory = facts.get("memory") or []
    asks_about_prior = re.search(
        r"\b(before|previous|prior|earlier|last time|already|"
        r"another case|other case|same)\b", lowered
    )
    if memory and (asks_about_prior or not _has_artifacts(facts)):
        first = memory[0]
        grounds = [f"{KIND_CASE}:{first['case_id']}"]
        for finding in (first.get("findings") or [])[:1]:
            grounds.append(f"{KIND_FINDING}:{finding['id']}")
        return {
            "answer": f"Before this case, {_memory_sentence(first)}. "
                      f"It shares {', '.join(first.get('shared') or [])} with your question.",
            "grounds": grounds,
        }

    # The case's own stated purpose and hypotheses (P8-CONTEXT-001). This sits
    # ahead of the column branch on purpose: "what is this case trying to do?"
    # names no column, and without it the assistant would fall past intent to
    # whichever statistic it could find.
    context = facts.get("context") or {}
    purpose = (context.get("purpose") or "").strip()
    hypotheses = [h for h in (context.get("hypotheses") or []) if str(h).strip()]
    if purpose or hypotheses:
        if re.search(r"\bpurpose|objective|goal|trying|hypothes|test|aim\b", lowered):
            parts = []
            grounds = []
            if purpose:
                parts.append(f"The case's stated purpose: {purpose}")
                grounds.append(f"{KIND_CONTEXT}:purpose")
            if hypotheses:
                parts.append(
                    f"Its stated hypotheses: {'; '.join(str(h) for h in hypotheses[:3])}"
                )
                grounds.append(f"{KIND_CONTEXT}:hypotheses")
            return {
                "answer": " ".join(parts) + ".",
                "grounds": grounds,
            }

    match = _first_matching_column(message, facts)
    if match is not None:
        dataset_id, name, stat = match
        dataset_label = next(
            (d["label"] for d in facts.get("datasets") or [] if d["id"] == dataset_id),
            dataset_id,
        )
        rows = ((facts.get("datasets") or [{}])[0].get("profile") or {}).get("rows")
        grounds = [f"{KIND_COLUMN}:{name}", f"{KIND_DATASET}:{dataset_label}"]
        return {
            "answer": (
                f"{_fmt_stat(name, stat)}"
                + (f" over {rows} row(s)" if isinstance(rows, int) else "")
                + f", in {dataset_label}."
            ),
            "grounds": grounds,
        }

    for dataset in facts.get("datasets") or []:
        if dataset.get("label") and dataset["label"].lower() in lowered:
            profile = dataset.get("profile") or {}
            columns = profile.get("columns") or []
            grounds = [f"{KIND_DATASET}:{dataset['label']}"]
            nulls = [
                name
                for name, stat in (profile.get("stats") or {}).items()
                if (stat.get("null_count") or 0) > 0
            ]
            null_note = f"; nulls in {', '.join(nulls[:3])}" if nulls else ""
            return {
                "answer": (
                    f"{dataset['label']} has {profile.get('rows', 0)} row(s) across "
                    f"{len(columns)} column(s) ({', '.join(columns[:6])}{', ...' if len(columns) > 6 else ''})"
                    f"{null_note}."
                ),
                "grounds": grounds,
            }

    findings = facts.get("findings") or []
    if findings and re.search(r"\bfinding|validat|support|evidence\b", lowered):
        latest = findings[-1]
        grounds = [f"{KIND_FINDING}:{latest['id']}"]
        return {
            "answer": (
                f"The latest finding is \"{latest['statement']}\" and its validation "
                f"status is {latest['status']}."
            ),
            "grounds": grounds,
        }

    # Nothing specific was asked: say where the case stands and the one action
    # that moves it, which is derived from the artifacts rather than asserted.
    progress = facts.get("progress") or {}
    stage = progress.get("stage", "unknown")
    next_action = progress.get("next_action")
    grounds = _artifact_grounds(facts, kinds=(KIND_DATASET, KIND_RUN, KIND_FINDING))
    if next_action:
        answer = (
            f"The case is at the {stage} stage. Next action: {next_action}"
            f" ({progress.get('next_hint') or ''})."
        )
    else:
        answer = (
            f"The case is at the {stage} stage; the loop is closed - every finding "
            "has been validated."
        )
    return {"answer": answer, "grounds": grounds}


def _artifact_grounds(facts: dict, kinds: tuple[str, ...]) -> list[str]:
    """Grounds for the artifacts of the given kinds, in facts order."""
    grounds: list[str] = []
    for kind in kinds:
        items = facts.get({"dataset": "datasets", "run": "runs", "finding": "findings",
                           "plan": "plans", "chart": "charts"}[kind]) or []
        for item in items[:3]:
            grounds.append(f"{kind}:{item.get('label') or item['id']}")
    return grounds[:8]


def parse_ground(ground: str) -> tuple[str, str] | None:
    match = _GROUND_RE.match((ground or "").strip())
    if match is None:
        return None
    return match.group(1), match.group(2)


def validate_answer(payload: Any, facts: dict) -> list[str]:
    """Problems with an LLM answer, as a list. Empty means acceptable.

    Beyond shape, every citation must be an artifact the case actually has. An
    invented citation is worse than no citation - it points a reviewer at
    evidence that does not exist, and the whole point of `grounds` is that a
    human can check the claim against the artifact.
    """
    problems: list[str] = []
    if not isinstance(payload, dict):
        return ["the answer must be a JSON object"]
    answer = payload.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        problems.append("'answer' must be a non-empty string")
    grounds = payload.get("grounds")
    if isinstance(grounds, str):
        problems.append("'grounds' must be a list of strings, not a string")
    elif not isinstance(grounds, list):
        problems.append("'grounds' must be a list of strings")
    elif not all(isinstance(item, str) and item.strip() for item in grounds):
        problems.append("every entry in 'grounds' must be a non-empty string")
    if problems:
        return problems

    references = _references(facts)
    for ground in grounds or []:
        parsed = parse_ground(ground)
        if parsed is None:
            problems.append(f"'{ground}' is not a citation of the form kind:name")
            continue
        kind, name = parsed
        if name not in references.get(kind, set()):
            problems.append(f"'{ground}' cites an artifact the case does not have")

    if not grounds and _has_artifacts(facts):
        problems.append("an answer about a case with artifacts must cite at least one")
    return problems

def _memory_sentence(memory: dict) -> str:
    """One prior case as a sentence, quoting its strongest finding."""
    findings = memory.get("findings") or []
    if not findings:
        return f"a previous case, \"{memory.get('question') or 'untitled'}\""
    strongest = findings[0]
    return (
        f"a previous case, \"{memory.get('question') or 'untitled'}\", which found "
        f"\"{strongest['statement']}\" (validation: {strongest['status']})"
    )


class LLMAssistant:
    """OpenAI-compatible assistant; dormant without configuration.

    Implemented on httpx so no SDK dependency is added. The response is expected
    to be the answer object itself; anything else is a validation failure and
    the caller falls back to the deterministic answer.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def answer(self, message: str, history: list[dict], facts: dict) -> dict:
        import httpx

        described = [
            {
                "id": dataset["id"],
                "label": dataset["label"],
                "rows": (dataset.get("profile") or {}).get("rows"),
                "columns": (dataset.get("profile") or {}).get("columns"),
            }
            for dataset in facts.get("datasets") or []
        ]
        runs = [
            {"id": run["id"], "kind": run["kind"], "rows": run["row_count"],
             "columns": run["columns"]}
            for run in facts.get("runs") or []
        ]
        findings = [
            {"id": finding["id"], "statement": finding["statement"],
             "status": finding["status"]}
            for finding in facts.get("findings") or []
        ]
        memory = [
            {
                "case_id": item["case_id"],
                "question": item["question"],
                "shared": item["shared"],
                "findings": [
                    {"id": finding["id"], "statement": finding["statement"],
                     "status": finding["status"]}
                    for finding in (item.get("findings") or [])
                ],
            }
            for item in facts.get("memory") or []
        ]
        progress = facts.get("progress") or {}
        turns = history[-_MAX_HISTORY_TURNS:]
        prompt = (
            "You are a data analyst's assistant answering questions about one "
            "analysis case. Answer from the case's artifacts only. Return ONLY "
            "a JSON object with this exact schema:\n"
            "{\n"
            '  "answer": string,\n'
            '  "grounds": [string]\n'
            "}\n"
            "Every entry in `grounds` is a citation of the form `kind:name` "
            "where kind is one of dataset, run, finding, plan, chart, column, "
            "case and name is an id, a column, or a case question from the "
            "artifacts below. Cite every claim. Quote no artifact that is not "
            "listed - a previous case is citable only when it appears under "
            "`memory`, and only for what its listed findings actually found. "
            "Do not add fields or commentary.\n\n"
            f"Case question: {facts.get('question') or '(none given)'}\n"
            f"Stage: {progress.get('stage')}; next action: "
            f"{progress.get('next_action') or 'none'}.\n\n"
            f"Datasets: {json.dumps(described, default=str)[:_MAX_LLM_CHARS // 2]}\n"
            f"Runs: {json.dumps(runs, default=str)[:_MAX_LLM_CHARS // 4]}\n"
            f"Findings: {json.dumps(findings, default=str)[:_MAX_LLM_CHARS // 4]}\n"
            f"Memory (previous cases that may bear on this question): "
            f"{json.dumps(memory, default=str)[:_MAX_LLM_CHARS // 4]}\n\n"
            f"Conversation so far: {json.dumps(turns, default=str)[:_MAX_LLM_CHARS // 4]}\n"
            f"Question: {message}\n"
        )
        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={
                "authorization": f"Bearer {self._api_key}",
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": "Return valid JSON only, no prose."},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)


def _configured_llm() -> "LLMAssistant | None":
    """The configured assistant, or None when no key is present."""
    api_key = os.environ.get("DAH_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return LLMAssistant(
        api_key=api_key,
        base_url=os.environ.get("DAH_LLM_BASE_URL", "https://api.openai.com/v1"),
        model=os.environ.get("DAH_LLM_MODEL", "gpt-4o-mini"),
    )


def create_answer(message: str, history: list[dict], facts: dict) -> tuple[dict, str]:
    """Produce a validated answer and the engine that gave it.

    Prefers the LLM when configured; falls back to the deterministic answer on
    any failure - an unavailable LLM, malformed output, a schema violation, or a
    citation the case cannot back - so an answer is always returned and the
    source says which engine spoke.
    """
    deterministic = answer_question(message, history, facts)
    llm = _configured_llm()
    if llm is None:
        return deterministic, SOURCE_DETERMINISTIC

    try:
        candidate = llm.answer(message, history, facts)
        problems = validate_answer(candidate, facts)
        if problems:
            raise ValueError(
                f"LLM answer failed validation: {'; '.join(problems[:3])}"
            )
        candidate.setdefault("grounds", [])
        return candidate, SOURCE_LLM
    except Exception as error:
        # An unavailable or misbehaving LLM degrades to the deterministic
        # answer rather than producing nothing. The breadth stays - the contract
        # is "any failure falls back" - but the reason is logged, so a fallback
        # caused by a bug in our own code surfaces instead of vanishing into
        # source=deterministic (P4-RELIABILITY-002).
        logging.getLogger(__name__).warning(
            "llm answer failed; falling back to deterministic: %s", error,
        )
        return deterministic, SOURCE_DETERMINISTIC
