"""The six LLM adapters, exercised without a network (AT-38's biggest gap).

Every assistant has two engines behind one interface: a deterministic one that
always answers, and an OpenAI-compatible one that is dormant without
`DAH_LLM_API_KEY`. The suite covers the deterministic engines thoroughly and
the adapters barely at all - the existing LLM tests replace the whole adapter
with a fake, which proves the fallback contract but never runs the adapter's
own code: the prompt it builds, the request it posts, the body it parses, the
errors it turns into a fallback. That was most of the coverage the PRD's AT-38
target was measuring, and none of it was reached.

These tests do not replace the adapter. They patch `httpx.post` - the one call
each adapter makes - and let the adapter's own code run against a canned
response, so the request's shape, the response's parsing and the gate's
rejection are all the real code paths. No packet leaves the process and no key
is real; `DAH_LLM_API_KEY` is set to a test value so `_configured_llm` returns
an adapter instead of None, and the endpoint it would have called is the one
the fake answers.

What this proves that a fake adapter cannot: the adapter builds a request to
the URL it was configured with, raises on a status error, parses the chat
completion's content field, and hands the parsed object to the same validator
the deterministic engine passes - so an invented column or a rewritten question
is refused by the gate the adapter feeds, and the fallback is the deterministic
answer rather than nothing.
"""

import json
import importlib
from contextlib import contextmanager

import httpx
import pytest

from app import assistant as assistant_module
from app import drafter as drafter_module
from app import generator as generator_module
from app import interpreter as interpreter_module
from app import planner as planner_module
from app import refine as refine_module
from app import timeouts as timeouts_module
from app.timeouts import DEFAULT_LLM_TIMEOUT_SECONDS


PROFILE = {
    "rows": 3,
    "columns": ["region", "revenue"],
    "stats": {
        "region": {"type": "other", "null_count": 0, "null_percentage": 0},
        "revenue": {"type": "numeric", "null_count": 0, "null_percentage": 0,
                    "min": 10, "max": 90, "avg": 50},
    },
    "duplicate_rows": 0,
    "quality": [],
}

COLUMNS = ["region", "revenue"]
ROWS = [["north", 90], ["south", 10]]


class FakeResponse:
    """The slice of httpx.Response the adapters use."""

    last_url: str | None = None
    last_body: object | None = None
    last_timeout: float | None = None

    def __init__(self, payload: object, status: int = 200) -> None:
        self._payload = payload
        self.status_code = status
        self.text = json.dumps(payload) if not isinstance(payload, str) else payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "the endpoint refused", request=None, response=self
            )

    def json(self) -> object:
        if isinstance(self._payload, str):
            raise json.JSONDecodeError("no json here", self._payload, 0)
        return self._payload


@contextmanager
def chat(payload: object, status: int = 200):
    """Patch httpx.post to answer one canned chat completion.

    A context manager of its own so the patch is undone however the block
    leaves - a raised fallback included - and the next test's adapter sees the
    real httpx.post until it installs its own.
    """
    patcher = pytest.MonkeyPatch()

    def posted(url: str, **kwargs):
        FakeResponse.last_url = url
        FakeResponse.last_body = kwargs.get("json")
        FakeResponse.last_timeout = kwargs.get("timeout")
        return FakeResponse(payload, status)

    patcher.setattr(httpx, "post", posted)
    try:
        yield
    finally:
        patcher.undo()


QUESTION = "Why did revenue decline?"


def _chat_content(payload: object) -> object:
    """The shape the adapters parse: a chat completion's content field."""
    if isinstance(payload, str):
        return payload
    return {"choices": [{"message": {"content": json.dumps(payload)}}]}


def _plan_payload(**overrides) -> dict:
    payload = {
        "objective": "Compare revenue between regions.",
        "primary_question": QUESTION,
        "sub_questions": ["Which region is lower?"],
        "hypotheses": [
            {"statement": "The south is lower.", "rationale": "its total is smallest",
             "check": "sum revenue by region"}
        ],
        "data_requirements": [{"requirement": "revenue", "detail": "numeric"}],
        "analysis_steps": [{"action": "aggregate", "detail": "SUM(revenue) by region"}],
    }
    payload.update(overrides)
    return payload


def _code_payload(**overrides) -> dict:
    payload = {
        "kind": "sql",
        "code": "SELECT region, SUM(revenue) FROM read_csv_auto(?) GROUP BY region",
        "explanation": "Revenue totalled per region.",
        "columns_used": ["region", "revenue"],
    }
    payload.update(overrides)
    return payload


def _interpret_payload(**overrides) -> dict:
    payload = {
        "summary": "The north's revenue is nine times the south's.",
        "observations": ["north totals 90", "south totals 10"],
        "caveats": ["two regions only"],
    }
    payload.update(overrides)
    return payload


def _draft_payload(**overrides) -> dict:
    payload = {
        "statement": "North revenue (90) is higher than south (10).",
        "interpretation": "The gap is consistent across the rows shown.",
        "caveat": "Two rows only.",
        "grounds": ["run:r1"],
    }
    payload.update(overrides)
    return payload


def _answer_payload(**overrides) -> dict:
    payload = {
        "answer": "The north region leads revenue.",
        "grounds": ["dataset:sales.csv"],
    }
    payload.update(overrides)
    return payload


def _refine_payload(**overrides) -> dict:
    payload = {
        "original": QUESTION,
        "refined": "Why did revenue decline in the south region?",
        "rationale": "The profile measures revenue and region.",
        "grounds": [{"kind": "column", "name": "region", "detail": "4 values"}],
    }
    payload.update(overrides)
    return payload


def _facts() -> dict:
    """The shape create_answer describes to the adapter: label, profile, counts.

    A dataset cites by id or by its label, a run by id; the fields the prompt
    reads are the ones the fixture supplies, so the adapter's description of
    the case is covered rather than abbreviated.
    """
    return {
        "case_id": "c1",
        "question": QUESTION,
        "datasets": [
            {
                "id": "d1",
                "label": "sales.csv",
                "profile": {"rows": 3, "columns": COLUMNS},
            }
        ],
        "runs": [{"id": "r1", "kind": "sql", "row_count": 2, "columns": COLUMNS}],
        "findings": [],
        "memory": [],
        "progress": {"stage": "analyze", "next_action": "Run an analysis"},
    }


@pytest.fixture(autouse=True)
def no_real_key(monkeypatch) -> None:
    """A key the adapters accept, pointed at a host the fake answers."""
    monkeypatch.setenv("DAH_LLM_API_KEY", "test-key")
    monkeypatch.setenv("DAH_LLM_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("DAH_LLM_MODEL", "test-model")


def test_no_key_means_the_deterministic_engine_answers(monkeypatch) -> None:
    """An unconfigured build never calls the endpoint at all."""
    monkeypatch.delenv("DAH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with chat(_plan_payload()):
        plan, source = planner_module.create_plan(QUESTION, PROFILE)
    assert source == planner_module.SOURCE_DETERMINISTIC
    assert FakeResponse.last_body is None


def test_the_planner_adapter_posts_and_parses() -> None:
    with chat(_chat_content(_plan_payload())):
        plan, source = planner_module.create_plan(QUESTION, PROFILE)
    assert source == planner_module.SOURCE_LLM
    assert plan["objective"] == "Compare revenue between regions."
    # The request went where the configuration pointed, as a chat completion.
    assert FakeResponse.last_url == "https://example.invalid/v1/chat/completions"
    assert FakeResponse.last_body["model"] == "test-model"
    assert FakeResponse.last_body["response_format"] == {"type": "json_object"}


def test_the_planner_carries_the_stated_intent() -> None:
    with chat(_chat_content(_plan_payload())):
        plan, _ = planner_module.create_plan(
            QUESTION, PROFILE, {"purpose": "Decide where to spend."}
        )
    # An engine that did not name its basis inherits the intent the caller
    # supplied, so a reader knows what the plan was built from either way.
    assert plan["context_basis"] == ["purpose"]


def test_the_generator_adapter_reads_only_real_columns() -> None:
    with chat(_chat_content(_code_payload())):
        proposal, source = generator_module.create_code(QUESTION, PROFILE, "sql")
    assert source == generator_module.SOURCE_LLM
    assert proposal["kind"] == "sql"
    assert set(proposal["columns_used"]) <= {"region", "revenue"}


def test_the_generator_retry_prompt_names_the_earlier_attempts() -> None:
    with chat(_chat_content(_code_payload())):
        generator_module.create_code(QUESTION, PROFILE, "sql", variant=2)
    prompt = FakeResponse.last_body["messages"][1]["content"]
    assert "2 earlier attempt(s)" in prompt


def test_the_interpreter_adapter_parses_the_read() -> None:
    with chat(_chat_content(_interpret_payload())):
        read, source = interpreter_module.create_interpretation(
            QUESTION, "sql", "SELECT region, SUM(revenue)", COLUMNS, ROWS, PROFILE
        )
    assert source == interpreter_module.SOURCE_LLM
    assert read["observations"] == ["north totals 90", "south totals 10"]


def test_the_drafter_adapter_quotes_only_values_the_result_has() -> None:
    with chat(_chat_content(_draft_payload())):
        draft, source = drafter_module.create_draft(
            QUESTION, "sql", "SELECT region, SUM(revenue)", COLUMNS, ROWS, PROFILE
        )
    assert source == drafter_module.SOURCE_LLM
    assert draft["statement"] == _draft_payload()["statement"]


def test_the_assistant_adapter_cites_only_artifacts_the_case_has() -> None:
    with chat(_chat_content(_answer_payload())):
        answer, source = assistant_module.create_answer("Which region leads?", [], _facts())
    assert source == assistant_module.SOURCE_LLM
    assert answer["grounds"] == ["dataset:sales.csv"]


def test_the_refiner_adapter_echoes_the_original_verbatim() -> None:
    with chat(_chat_content(_refine_payload())):
        proposal, source = refine_module.create_refinement(QUESTION, PROFILE)
    assert source == refine_module.SOURCE_LLM
    assert proposal["original"] == QUESTION


@pytest.mark.parametrize(
    "module, call, payload",
    [
        (
            planner_module,
            lambda: planner_module.create_plan(QUESTION, PROFILE),
            _plan_payload(objective=""),
        ),
        (
            generator_module,
            lambda: generator_module.create_code(QUESTION, PROFILE, "sql"),
            _code_payload(code="SELECT invented_column FROM read_csv_auto(?)"),
        ),
        (
            interpreter_module,
            lambda: interpreter_module.create_interpretation(
                QUESTION, "sql", "SELECT 1", COLUMNS, ROWS, PROFILE
            ),
            _interpret_payload(summary=""),
        ),
        (
            drafter_module,
            lambda: drafter_module.create_draft(
                QUESTION, "sql", "SELECT 1", COLUMNS, ROWS, PROFILE
            ),
            _draft_payload(statement="North revenue (999) leads."),
        ),
        (
            assistant_module,
            lambda: assistant_module.create_answer("q", [], _facts()),
            _answer_payload(grounds=["dataset:nope.csv"]),
        ),
        (
            refine_module,
            lambda: refine_module.create_refinement(QUESTION, PROFILE),
            _refine_payload(original="a different question"),
        ),
    ],
)
def test_a_gate_rejection_falls_back(module, call, payload) -> None:
    """An output the validator refuses never reaches the analyst.

    Each module's invented failure is its own vocabulary: an empty objective, a
    column the profile does not have, a missing summary, a magnitude the result
    does not contain, a citation to an artifact that is not there, and an
    original the proposal did not echo. All six degrade to the deterministic
    answer, and the source says so - and says it *as a fallback*, so the panel
    announces the substitution rather than labelling it a choice (FIX-TIMEOUT-006).
    """
    with chat(_chat_content(payload)):
        _produced, source = call()
    assert source == module.SOURCE_DETERMINISTIC_FALLBACK


@pytest.mark.parametrize(
    "call",
    [
        lambda: planner_module.create_plan(QUESTION, PROFILE),
        lambda: generator_module.create_code(QUESTION, PROFILE, "sql"),
        lambda: interpreter_module.create_interpretation(
            QUESTION, "sql", "SELECT 1", COLUMNS, ROWS, PROFILE
        ),
        lambda: drafter_module.create_draft(
            QUESTION, "sql", "SELECT 1", COLUMNS, ROWS, PROFILE
        ),
        lambda: assistant_module.create_answer("q", [], _facts()),
        lambda: refine_module.create_refinement(QUESTION, PROFILE),
    ],
)
@pytest.mark.parametrize("failure", ["status", "malformed", "garbage"])
def test_every_adapter_degrades_on_an_endpoint_failure(call, failure) -> None:
    """An unavailable or incoherent endpoint answers deterministically.

    A 500, a body that is not JSON, and a completion whose content is not the
    object the schema asked for are the three ways a real endpoint fails; each
    must leave the analyst with an answer rather than an error, and the
    fallback is logged rather than silent (P4-RELIABILITY-002).
    """
    if failure == "status":
        payload, status = "internal error", 500
    elif failure == "malformed":
        payload, status = "not json at all", 200
    else:
        payload, status = {"choices": [{"message": {"content": {"not": "a string"}}}]}, 200
    with chat(payload, status):
        _produced, source = call()
    assert source == "deterministic fallback"


def test_a_python_proposal_is_gated_the_same_way() -> None:
    """The Python kind is not a second, weaker contract."""
    with chat(_chat_content(_code_payload(code="df['invented'].sum()", kind="python"))):
        proposal, source = generator_module.create_code(QUESTION, PROFILE, "python")
    assert source == generator_module.SOURCE_DETERMINISTIC_FALLBACK


def test_the_adapter_classes_can_be_called_directly() -> None:
    """The adapter's own parsing, outside the create_* wrapper's fallback."""
    with chat(_chat_content(_interpret_payload())):
        read = interpreter_module.LLMInterpreter("k", "https://x/v1", "m").interpret(
            QUESTION, "sql", None, COLUMNS, ROWS, PROFILE
        )
    assert read["summary"] == "The north's revenue is nine times the south's."


def test_the_refiner_appends_the_original_when_the_endpoint_omits_it() -> None:
    """An endpoint that forgot the field does not get to lose the question."""
    payload = _refine_payload()
    del payload["original"]
    with chat(_chat_content(payload)):
        proposal, source = refine_module.create_refinement(QUESTION, PROFILE)
    assert source == refine_module.SOURCE_LLM
    assert proposal["original"] == QUESTION


# --- one configured timeout (FIX-TIMEOUT-006, W-014) ----------------------


@pytest.mark.parametrize(
    "module",
    [planner_module, generator_module, interpreter_module, drafter_module,
     assistant_module, refine_module],
)
def test_every_adapter_sends_the_one_configured_timeout(module) -> None:
    """No call site waits its own hardcoded number any more.

    Six sites carried three different values - 30, 30, 30, 30, 60, 60 - and
    none was configurable, so the interpret and draft endpoints timed out
    while the planner at twice the budget finished. Now every adapter posts
    the single configured value, which the environment can raise.
    """
    with chat(_chat_content(_plan_payload())):
        # The payload is the planner's, so four of the six adapters reject it
        # and degrade - which is also fine, because the request is still sent
        # and the budget it was sent with is what is under test.
        _call(module)
    assert FakeResponse.last_timeout == DEFAULT_LLM_TIMEOUT_SECONDS


def _call(module):
    if module is planner_module:
        return module.create_plan(QUESTION, PROFILE)
    if module is generator_module:
        return module.create_code(QUESTION, PROFILE, "sql")
    if module is interpreter_module:
        return module.create_interpretation(
            QUESTION, "sql", "SELECT 1", COLUMNS, ROWS, PROFILE
        )
    if module is drafter_module:
        return module.create_draft(QUESTION, "sql", "SELECT 1", COLUMNS, ROWS, PROFILE)
    if module is assistant_module:
        return module.create_answer("q", [], _facts())
    return module.create_refinement(QUESTION, PROFILE)


def test_the_timeout_reads_the_environment(monkeypatch) -> None:
    """A deployment with a slow endpoint raises the one value it needs to.

    Reloading the module is what reads the environment again, because the
    value is a property of the deployment rather than of the request.
    """
    monkeypatch.setenv("DAH_LLM_TIMEOUT_SECONDS", "240")
    reloaded = importlib.reload(timeouts_module)
    try:
        assert reloaded.LLM_TIMEOUT_SECONDS == 240.0
    finally:
        monkeypatch.delenv("DAH_LLM_TIMEOUT_SECONDS", raising=False)
        importlib.reload(timeouts_module)
    # The restored module is what the next request reads.
    assert timeouts_module.LLM_TIMEOUT_SECONDS == DEFAULT_LLM_TIMEOUT_SECONDS


def test_an_unparsable_timeout_keeps_the_default(monkeypatch) -> None:
    """A typo (`12O`, a letter where a digit belongs) shortens nothing."""
    monkeypatch.setenv("DAH_LLM_TIMEOUT_SECONDS", "12O")
    reloaded = importlib.reload(timeouts_module)
    try:
        assert reloaded.LLM_TIMEOUT_SECONDS == DEFAULT_LLM_TIMEOUT_SECONDS
    finally:
        monkeypatch.delenv("DAH_LLM_TIMEOUT_SECONDS", raising=False)
        importlib.reload(timeouts_module)


@pytest.mark.parametrize("value", ["0", "-5", " "])
def test_a_non_positive_timeout_is_ignored(monkeypatch, value) -> None:
    """A misconfiguration must not turn into an immediate failure of every slice."""
    monkeypatch.setenv("DAH_LLM_TIMEOUT_SECONDS", value)
    reloaded = importlib.reload(timeouts_module)
    try:
        assert reloaded.LLM_TIMEOUT_SECONDS == DEFAULT_LLM_TIMEOUT_SECONDS
    finally:
        monkeypatch.delenv("DAH_LLM_TIMEOUT_SECONDS", raising=False)
        importlib.reload(timeouts_module)


def test_a_slow_endpoint_is_answered_not_timed_out() -> None:
    """An endpoint that would have timed out at the old default answers now.

    The failure was a wait: the harness gave up at 30s while the endpoint
    answered at just past it. The fake records the budget it was given, so the
    assertion is that the configured budget is above the old hardcoded one -
    and the response is read as the LLM's rather than degraded.
    """
    with chat(_chat_content(_interpret_payload())):
        read, source = interpreter_module.create_interpretation(
            QUESTION, "sql", "SELECT 1", COLUMNS, ROWS, PROFILE
        )
    assert source == interpreter_module.SOURCE_LLM
    assert FakeResponse.last_timeout > 30.0


# --- a fallback is announced, not merely labelled -------------------------


@pytest.mark.parametrize(
    "module, sentence",
    [
        (planner_module, "the LLM was unavailable, so a deterministic plan answered in its place"),
        (generator_module, "the LLM was unavailable, so a deterministic proposal answered in its place"),
        (interpreter_module, "the LLM was unavailable, so a deterministic reading answered in its place"),
        (drafter_module, "the LLM was unavailable, so a deterministic draft answered in its place"),
        (assistant_module, "the LLM was unavailable, so a deterministic answer answered in its place"),
        (refine_module, "the LLM was unavailable, so a deterministic proposal answered in its place"),
    ],
)
def test_a_fallback_source_renders_as_a_sentence(module, sentence) -> None:
    """`by deterministic` never says the engine asked for was not the one that answered.

    A fallback is a substitution of the trust model, so the label the panel
    shows is a sentence that names it - and every module's sentence is its own,
    because the artifact kind differs.
    """
    assert module.source_sentence(module.SOURCE_DETERMINISTIC_FALLBACK) == sentence


@pytest.mark.parametrize(
    "module",
    [planner_module, generator_module, interpreter_module, drafter_module,
     assistant_module, refine_module],
)
def test_a_chosen_engine_still_renders_as_by_source(module) -> None:
    """The announcement is only for the substitution; a chosen engine is named."""
    assert module.source_sentence("llm") == "by llm"
    assert module.source_sentence("deterministic") == "by deterministic"
