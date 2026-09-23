"""Question refinement, tested (P8-REFINE-007, AT-04).

Two weights, like the golden suite beside it.

The fast tests cover the contract in-process: the deterministic engine
sharpens what a profile measured and declines when honesty requires it; the
gate that an LLM's output must pass before the analyst sees it; and the three
paths - accept, edit, keep original - that are the only ways a proposal can
move the case's question, with the original recoverable after each.

The slow test asserts the four numbers AT-04 names, measured by
verification/refine/verify_refine.py against a real server over HTTP over 50
cases. A report nobody reads guards nothing, so the numbers live here, where a
regression fails a test.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db as db_module
from app.main import app, get_db
from app.refine import (
    SOURCE_DETERMINISTIC,
    create_refinement,
    refine_question,
    validate_refinement,
)

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from verification.refine.cases import (  # noqa: E402
    CASES,
    PATH_ACCEPT,
    PATH_EDIT,
    PATH_KEEP,
)
from verification.refine.verify_refine import (  # noqa: E402
    THRESHOLD_FABRICATIONS,
    THRESHOLD_OVERWRITES,
    THRESHOLD_PRESERVE,
    THRESHOLD_RELEVANT,
    run_refine,
)

SALES_CSV = REPO / "verification" / "refine" / "sales.csv"

# A profile shaped like the profiler actually answers: real columns, measured
# min/max, measured cardinality. The engine reads only these keys, so a hand
# built profile is the same input the endpoint builds from the store.
SALES_PROFILE = {
    "rows": 12,
    "duplicate_rows": 0,
    "columns": ["order_id", "region", "product", "revenue", "units", "order_date"],
    "stats": {
        "order_id": {"type": "numeric", "null_count": 0, "null_percentage": 0.0,
                     "distinct_count": 12, "min": 101, "max": 112, "avg": 106.5},
        "region": {"type": "other", "null_count": 0, "null_percentage": 0.0,
                   "distinct_count": 4},
        "product": {"type": "other", "null_count": 0, "null_percentage": 0.0,
                    "distinct_count": 2},
        "revenue": {"type": "numeric", "null_count": 0, "null_percentage": 0.0,
                    "distinct_count": 11, "min": 2400, "max": 9600, "avg": 6003.3},
        "units": {"type": "numeric", "null_count": 0, "null_percentage": 0.0,
                  "distinct_count": 12, "min": 8, "max": 26, "avg": 17.3},
        "order_date": {"type": "temporal", "null_count": 0, "null_percentage": 0.0,
                       "distinct_count": 12, "min": "2026-01-04", "max": "2026-06-14"},
    },
}


def _temp_env(tmp_path) -> None:
    db_module.DATA_DIR = tmp_path / "data"
    # A store of this test's own. Without an override the client inherits
    # whatever `app.dependency_overrides` the previous test file left behind -
    # those are never cleared, so the fixtures would silently share one store
    # across files, and a store another test left fresh reports the current
    # version with no migration rows recorded (a fresh store is born current,
    # which is the truth, but it is not the upgrade path under test).
    db_path = tmp_path / "test.db"
    app.dependency_overrides[get_db] = _override_get_db(db_path)


def _override_get_db(db_path):
    """The dependency shape the app expects: a connection per request."""
    def override():
        with db_module.get_connection(db_path) as connection:
            yield connection

    return override


def _client_with_sales_case(tmp_path, question="Why are sales down?"):
    _temp_env(tmp_path)
    client = TestClient(app)
    case = client.post(
        "/cases", json={"question": question, "dataset": "sales.csv"}
    ).json()
    dataset = client.post(
        f"/cases/{case['id']}/datasets",
        files={"file": ("sales.csv", SALES_CSV.read_text(), "text/csv")},
    ).json()
    client.post(f"/cases/{case['id']}/datasets/{dataset['id']}/profile")
    return client, case["id"], dataset["id"]


# --------------------------------------------------------------------------
# The deterministic engine: what it adds, and when it declines
# --------------------------------------------------------------------------


def test_a_vague_question_is_sharpened_by_measured_data() -> None:
    """'Why are sales down?' gains the measure, the split, the window and the
    comparison it never named - each one a value the profile measured."""
    proposal = refine_question("Why are sales down?", SALES_PROFILE)
    assert proposal is not None
    # The original is the prefix of its own refinement, so the question asked
    # is the question answered (AT-04's preserve-and-relevant, by construction).
    assert proposal["original"] == "Why are sales down?"
    assert proposal["refined"].startswith("Why are sales down?")
    assert "revenue" in proposal["refined"]
    # The split is the lowest-cardinality dimension the profile has, because a
    # two-value split is the comparison the question can act on.
    assert "split by product" in proposal["refined"]
    assert "order_date" in proposal["refined"]
    assert "comparing each period with the one before it" in proposal["refined"]
    # Measured values, not estimates.
    assert "2,400" in proposal["refined"]
    assert "9,600" in proposal["refined"]
    assert "2026-01-04" in proposal["refined"]
    # Every claim has a ground naming a real column.
    assert {ground["name"] for ground in proposal["grounds"]} <= set(
        SALES_PROFILE["columns"]
    )
    assert proposal["rationale"].strip()


def test_the_engine_never_proposes_without_a_profile() -> None:
    """No measured data, no proposal - a guess is the fabrication AT-04 bans."""
    assert refine_question("Why are sales down?", None) is None


def test_a_column_less_dataset_declines() -> None:
    """A table with no numeric and no temporal column has nothing to sharpen
    with, so the engine says so rather than dressing the question up."""
    profile = {
        "rows": 6, "duplicate_rows": 0,
        "columns": ["category", "owner", "status"],
        "stats": {
            "category": {"type": "other", "distinct_count": 3, "null_count": 0,
                         "null_percentage": 0.0},
            "owner": {"type": "other", "distinct_count": 3, "null_count": 0,
                      "null_percentage": 0.0},
            "status": {"type": "other", "distinct_count": 2, "null_count": 0,
                       "null_percentage": 0.0},
        },
    }
    assert refine_question("Which categories matter?", profile) is None


def test_a_topicless_question_declines() -> None:
    """A question with no subject cannot be sharpened without inventing one,
    which is the silent overwrite AT-04 forbids even when an engine makes it."""
    for question in ("why?", "help", "data", "show me stuff"):
        assert refine_question(question, SALES_PROFILE) is None, question


def test_an_already_specific_question_is_left_alone() -> None:
    """A question naming its measure, its dimension and its window is already
    answerable; rewording it would be noise sold as help."""
    assert refine_question(
        "What was revenue in Q2 by region?", SALES_PROFILE
    ) is None
    assert refine_question(
        "total revenue by product over order_date", SALES_PROFILE
    ) is None


def test_a_question_that_names_its_measure_and_split_still_gets_the_window() -> None:
    """Partly specific is not fully specific: the missing pieces are still
    added, and only the missing ones."""
    proposal = refine_question("How does revenue differ by product?", SALES_PROFILE)
    assert proposal is not None
    assert "order_date" in proposal["refined"]
    # It does not re-add what the question already stated.
    assert proposal["refined"].count("measured as") == 0


def test_the_engine_is_deterministic() -> None:
    """The same inputs always yield the same proposal - no randomness, no
    hidden state, no dependency on the network."""
    first = refine_question("Why are sales down?", SALES_PROFILE)
    second = refine_question("Why are sales down?", SALES_PROFILE)
    assert first == second


def test_a_high_cardinality_column_is_not_offered_as_the_split() -> None:
    """An id-like column is not a usable dimension, so the engine does not
    propose splitting by it."""
    profile = json.loads(json.dumps(SALES_PROFILE))
    profile["stats"]["region"]["distinct_count"] = 500
    proposal = refine_question("Why are sales down?", profile)
    assert proposal is not None
    assert "region" not in proposal["refined"]
    assert "product" in proposal["refined"]


def test_the_engine_passes_its_own_gate() -> None:
    """What the deterministic engine proposes is valid by the same standard an
    LLM's output is held to - the gate is not weaker for the local engine."""
    proposal = refine_question("Why are sales down?", SALES_PROFILE)
    assert proposal is not None
    assert validate_refinement(proposal, "Why are sales down?", SALES_PROFILE) == []


def test_create_refinement_reports_the_engine_that_spoke() -> None:
    """Without a key, the deterministic engine answers and the source says so -
    the label the shell shows beside the proposal."""
    proposal, source = create_refinement("Why are sales down?", SALES_PROFILE)
    assert source == SOURCE_DETERMINISTIC
    assert proposal is not None


# --------------------------------------------------------------------------
# The gate: an LLM's proposal is checked, never trusted
# --------------------------------------------------------------------------


def _bad_proposal(**overrides) -> dict:
    base = {
        "original": "Why are sales down?",
        "refined": "Why are sales down? measured as revenue (2,400 to 9,600)",
        "rationale": "The measure was unnamed; revenue is profiled.",
        "grounds": [{"kind": "column", "name": "revenue",
                     "detail": "numeric column, 2,400 to 9,600"}],
    }
    base.update(overrides)
    return base


def test_a_proposal_must_echo_the_original_verbatim() -> None:
    """The engine does not get to restate the question it was handed."""
    problems = validate_refinement(
        _bad_proposal(original="Why is revenue down?"),
        "Why are sales down?", SALES_PROFILE,
    )
    assert any("verbatim" in problem for problem in problems)


def test_a_proposal_that_loses_the_topic_is_rejected() -> None:
    """Semantic relevance is checked, not assumed: a rewrite about a
    neighbouring subject fails the gate."""
    problems = validate_refinement(
        _bad_proposal(
            refined="What factors explain user churn across the platform?",
            grounds=[],
        ),
        "Why are sales down?", SALES_PROFILE,
    )
    assert any("subject terms" in problem for problem in problems)


def test_a_cited_column_the_data_does_not_have_is_a_fabrication() -> None:
    """A ground naming a column the profile never saw is the invented
    reference AT-04 scores at zero."""
    problems = validate_refinement(
        _bad_proposal(grounds=[{"kind": "column", "name": "profit",
                                "detail": "not a real column here"}]),
        "Why are sales down?", SALES_PROFILE,
    )
    assert any("profit" in problem for problem in problems)


def test_a_quoted_column_the_data_does_not_have_is_a_fabrication() -> None:
    """A backtick-quoted column is a schema citation, and it must resolve."""
    problems = validate_refinement(
        _bad_proposal(refined="Why are sales down? measured as `profit`",
                      grounds=[]),
        "Why are sales down?", SALES_PROFILE,
    )
    assert any("profit" in problem for problem in problems)


def test_an_unmeasured_figure_is_a_fabrication() -> None:
    """A number the profile did not measure and the question did not state."""
    problems = validate_refinement(
        _bad_proposal(refined="Why are sales down? the 15% decline in revenue"),
        "Why are sales down?", SALES_PROFILE,
    )
    assert any("did not measure" in problem for problem in problems)


def test_a_measured_figure_in_any_spelling_is_allowed() -> None:
    """52.0 and 52 are the same measurement; the gate is about provenance, not
    about formatting."""
    profile = json.loads(json.dumps(SALES_PROFILE))
    profile["stats"]["revenue"]["max"] = 9600.0
    assert validate_refinement(
        _bad_proposal(refined="Why are sales down? revenue up to 9,600"),
        "Why are sales down?", profile,
    ) == []


def test_a_bare_proposal_without_a_rationale_is_rejected() -> None:
    """A proposal is never bare: the analyst reads why before deciding."""
    problems = validate_refinement(
        _bad_proposal(rationale=""),
        "Why are sales down?", SALES_PROFILE,
    )
    assert any("rationale" in problem for problem in problems)


def test_a_proposal_identical_to_the_original_is_rejected() -> None:
    """A refinement that changes nothing is not one."""
    problems = validate_refinement(
        _bad_proposal(refined="Why are sales down?"),
        "Why are sales down?", SALES_PROFILE,
    )
    assert any("differ from the original" in problem for problem in problems)


def test_a_non_object_proposal_is_rejected() -> None:
    assert validate_refinement("nope", "Why are sales down?", SALES_PROFILE)


# --------------------------------------------------------------------------
# The endpoints: propose, then decide
# --------------------------------------------------------------------------


def _propose(client, case_id):
    response = client.post(f"/cases/{case_id}/refine")
    assert response.status_code == 200, response.text
    return response.json()


def test_proposing_writes_nothing_to_the_case(tmp_path) -> None:
    """A proposal is a proposal: the case's question is untouched until the
    analyst decides."""
    client, case_id, _ = _client_with_sales_case(tmp_path)
    question_before = client.get(f"/cases/{case_id}").json()["question"]
    proposal = _propose(client, case_id)
    assert proposal["status"] == "pending"
    assert proposal["original_question"] == question_before
    assert client.get(f"/cases/{case_id}").json()["question"] == question_before


def test_a_read_never_proposes(tmp_path) -> None:
    """Opening a case commits nothing, as with every other GET in the
    workspace."""
    client, case_id, _ = _client_with_sales_case(tmp_path)
    assert client.get(f"/cases/{case_id}/refine").json() is None
    assert client.get(f"/cases/{case_id}/refinements").json() == []
    _propose(client, case_id)
    # The read after a proposal hands back what was proposed, and adds nothing.
    assert client.get(f"/cases/{case_id}/refine").json()["status"] == "pending"
    assert client.get(f"/cases/{case_id}/refine").json()["status"] == "pending"


def test_proposing_is_idempotent_while_pending(tmp_path) -> None:
    """Two asks, one proposal: a refresh is not a re-roll."""
    client, case_id, _ = _client_with_sales_case(tmp_path)
    first = _propose(client, case_id)
    second = _propose(client, case_id)
    assert first["id"] == second["id"]


def test_a_question_the_engine_cannot_sharpen_answers_a_decline(tmp_path) -> None:
    """A decline is stored and served, not an error and not an empty proposal,
    so the analyst knows the engine looked."""
    client, case_id, _ = _client_with_sales_case(
        tmp_path, question="What was revenue in Q2 by region?"
    )
    proposal = _propose(client, case_id)
    assert proposal["status"] == "declined"
    assert not proposal["refined_question"]
    assert proposal["rationale"]
    # Nothing was written, and the decline is the case's latest state.
    assert client.get(f"/cases/{case_id}/refine").json()["status"] == "declined"


def test_accept_moves_the_question_and_keeps_the_original(tmp_path) -> None:
    """The accept path: the case carries the refined question, and the original
    is still readable from the case's refinement history."""
    client, case_id, _ = _client_with_sales_case(tmp_path)
    original = client.get(f"/cases/{case_id}").json()["question"]
    proposal = _propose(client, case_id)
    decision = client.post(
        f"/cases/{case_id}/refine/{proposal['id']}/accept"
    ).json()
    assert decision["status"] == "accepted"
    assert client.get(f"/cases/{case_id}").json()["question"] == proposal["refined_question"]
    history = client.get(f"/cases/{case_id}/refinements").json()
    assert history[0]["original_question"] == original
    assert history[0]["status"] == "accepted"


def test_keep_original_writes_nothing_and_is_remembered(tmp_path) -> None:
    """The reject path: the question is untouched, and the no is recorded."""
    client, case_id, _ = _client_with_sales_case(tmp_path)
    original = client.get(f"/cases/{case_id}").json()["question"]
    proposal = _propose(client, case_id)
    decision = client.post(
        f"/cases/{case_id}/refine/{proposal['id']}/reject"
    ).json()
    assert decision["status"] == "rejected"
    assert client.get(f"/cases/{case_id}").json()["question"] == original
    assert client.get(f"/cases/{case_id}/refine").json()["status"] == "rejected"


def test_edit_applies_the_analysts_own_wording(tmp_path) -> None:
    """The edit path: neither the original nor the proposal, but the analyst's
    wording - and the original is still recoverable."""
    client, case_id, _ = _client_with_sales_case(tmp_path)
    original = client.get(f"/cases/{case_id}").json()["question"]
    proposal = _propose(client, case_id)
    edited = "What explains the change in revenue by region, period over period?"
    decision = client.post(
        f"/cases/{case_id}/refine/{proposal['id']}/edit",
        json={"question": edited},
    ).json()
    assert decision["status"] == "edited"
    assert decision["edited_question"] == edited
    assert client.get(f"/cases/{case_id}").json()["question"] == edited
    row = client.get(f"/cases/{case_id}/refinements").json()[0]
    assert row["original_question"] == original
    assert row["edited_question"] == edited


def test_an_edit_that_restores_the_original_is_refused(tmp_path) -> None:
    """An edit back to the original is a keep-original; routing it through the
    write path would record a no-op as a change."""
    client, case_id, _ = _client_with_sales_case(tmp_path)
    original = client.get(f"/cases/{case_id}").json()["question"]
    proposal = _propose(client, case_id)
    response = client.post(
        f"/cases/{case_id}/refine/{proposal['id']}/edit",
        json={"question": original},
    )
    assert response.status_code == 400, response.text
    assert "keep original" in response.json()["detail"]


def test_an_edit_must_not_be_empty(tmp_path) -> None:
    client, case_id, _ = _client_with_sales_case(tmp_path)
    proposal = _propose(client, case_id)
    response = client.post(
        f"/cases/{case_id}/refine/{proposal['id']}/edit",
        json={"question": "   "},
    )
    assert response.status_code == 400, response.text


def test_a_decision_is_not_made_twice(tmp_path) -> None:
    """A decided proposal stays decided; the second decision is a 409."""
    client, case_id, _ = _client_with_sales_case(tmp_path)
    proposal = _propose(client, case_id)
    client.post(f"/cases/{case_id}/refine/{proposal['id']}/accept")
    response = client.post(f"/cases/{case_id}/refine/{proposal['id']}/accept")
    assert response.status_code == 409, response.text
    response = client.post(f"/cases/{case_id}/refine/{proposal['id']}/reject")
    assert response.status_code == 409, response.text


def test_deciding_a_proposal_from_another_case_is_a_404(tmp_path) -> None:
    client, case_id, _ = _client_with_sales_case(tmp_path)
    other = client.post(
        "/cases", json={"question": "other", "dataset": "o.csv"}
    ).json()
    proposal = _propose(client, case_id)
    response = client.post(f"/cases/{other['id']}/refine/{proposal['id']}/accept")
    assert response.status_code == 404, response.text


def test_deciding_a_missing_proposal_is_a_404(tmp_path) -> None:
    client, case_id, _ = _client_with_sales_case(tmp_path)
    response = client.post(
        f"/cases/{case_id}/refine/no-such-proposal/accept"
    )
    assert response.status_code == 404, response.text


def test_an_unknown_case_answers_404(tmp_path) -> None:
    _temp_env(tmp_path)
    client = TestClient(app)
    assert client.post("/cases/nope/refine").status_code == 404
    assert client.get("/cases/nope/refine").status_code == 404
    assert client.get("/cases/nope/refinements").status_code == 404


def test_the_history_records_the_transformation(tmp_path) -> None:
    """AT-04's 'show the transformation explicitly' is the case's own
    timeline: the proposal, then the decision."""
    client, case_id, _ = _client_with_sales_case(tmp_path)
    proposal = _propose(client, case_id)
    client.post(f"/cases/{case_id}/refine/{proposal['id']}/accept")
    history = client.get(f"/cases/{case_id}/history").json()
    kinds = [event["kind"] for event in history["events"]]
    assert kinds.count("question_refined") == 1
    assert kinds.count("refine_decision") == 1
    assert kinds.index("question_refined") < kinds.index("refine_decision")
    assert history["counts"]["refinements"] == 1
    decided = next(event for event in history["events"]
                   if event["kind"] == "refine_decision")
    assert "accepted" in decided["detail"]


def test_a_kept_original_is_in_the_history_too(tmp_path) -> None:
    client, case_id, _ = _client_with_sales_case(tmp_path)
    proposal = _propose(client, case_id)
    client.post(f"/cases/{case_id}/refine/{proposal['id']}/reject")
    history = client.get(f"/cases/{case_id}/history").json()
    decided = next(event for event in history["events"]
                   if event["kind"] == "refine_decision")
    assert "kept the original" in decided["detail"]


def test_the_proposal_travels_with_an_export(tmp_path) -> None:
    """An accepted refinement replaced the question on the case row; the
    export carries the original, so the round trip keeps it recoverable."""
    client, case_id, _ = _client_with_sales_case(tmp_path)
    original = client.get(f"/cases/{case_id}").json()["question"]
    proposal = _propose(client, case_id)
    client.post(f"/cases/{case_id}/refine/{proposal['id']}/accept")
    package = client.get(f"/cases/{case_id}/export").json()
    assert package["refinements"]
    assert package["refinements"][0]["original_question"] == original
    assert package["refinements"][0]["status"] == "accepted"

    imported = client.post("/cases/import", json=package).json()
    restored = client.get(f"/cases/{imported['id']}/refinements").json()
    assert restored[0]["original_question"] == original
    assert restored[0]["status"] == "accepted"
    assert restored[0]["refined_question"] == proposal["refined_question"]


def test_an_exported_decline_round_trips(tmp_path) -> None:
    client, case_id, _ = _client_with_sales_case(
        tmp_path, question="What was revenue in Q2 by region?"
    )
    _propose(client, case_id)
    package = client.get(f"/cases/{case_id}/export").json()
    imported = client.post("/cases/import", json=package).json()
    assert client.get(f"/cases/{imported['id']}/refine").json()["status"] == "declined"


def test_a_duplicated_case_keeps_its_refinement_history(tmp_path) -> None:
    client, case_id, _ = _client_with_sales_case(tmp_path)
    original = client.get(f"/cases/{case_id}").json()["question"]
    proposal = _propose(client, case_id)
    client.post(f"/cases/{case_id}/refine/{proposal['id']}/accept")
    duplicate = client.post(f"/cases/{case_id}/duplicate").json()
    restored = client.get(f"/cases/{duplicate['id']}/refinements").json()
    assert restored[0]["original_question"] == original
    assert restored[0]["status"] == "accepted"


def test_deleting_a_case_removes_its_proposals(tmp_path) -> None:
    """A deleted case leaves no orphaned state behind."""
    client, case_id, _ = _client_with_sales_case(tmp_path)
    proposal = _propose(client, case_id)
    client.delete(f"/cases/{case_id}")
    assert client.get(f"/cases/{case_id}/refinements").status_code == 404
    with db_module.get_connection(tmp_path / "test.db") as conn:
        rows = conn.execute(
            "SELECT 1 FROM refinements WHERE id = ?", (proposal["id"],)
        ).fetchall()
    assert rows == []


LEGACY_SCHEMA = """
CREATE TABLE cases (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    dataset TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE datasets (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def test_the_schema_records_the_new_table(tmp_path) -> None:
    """A store written before this feature upgrades into it, and the upgrade
    is what reports the refinements migration.

    A store born on this build is created at the current shape in one step, so
    it records no migrations at all - the honest answer for a store that was
    never anything else (test_migrations pins that). The refinements migration
    is only *run* by a store that predates it, so that is the store this test
    builds: the upgrade is the path a real user's data takes, and it is the
    path the acceptance criterion is about.
    """
    legacy = tmp_path / "legacy.db"
    connection = sqlite3.connect(legacy)
    connection.executescript(LEGACY_SCHEMA)
    connection.commit()
    connection.close()

    db_module.DATA_DIR = tmp_path / "data"
    app.dependency_overrides[get_db] = _override_get_db(legacy)
    with TestClient(app) as client:
        body = client.get("/schema-version").json()
    assert body["version"] == db_module.LATEST_SCHEMA_VERSION
    assert body["current"] is True
    assert any(
        "refinements" in migration["name"]
        for migration in body["migrations"]
    ), "the upgrade to the refinements table is recorded in the audit trail"


# --------------------------------------------------------------------------
# The measurement: AT-04's four numbers, over 50 cases
# --------------------------------------------------------------------------


def test_the_corpus_is_50_cases_covering_every_path() -> None:
    """AT-04 measures a rate over 50 evaluation cases, and the three paths it
    names are each exercised at volume rather than once."""
    assert len(CASES) == 50
    assert sum(1 for case in CASES if case.expect == "proposal") >= 25
    paths = {case.path for case in CASES}
    assert paths >= {PATH_ACCEPT, PATH_EDIT, PATH_KEEP}


@pytest.mark.slow
def test_at04s_four_thresholds_hold_over_a_real_server() -> None:
    """The four numbers the PRD names, measured - not claimed.

    The deterministic engine makes preservation and relevance structural (the
    refined question carries the original as its prefix, so it cannot drop the
    question it was asked), but structural is one renamed variable away from
    being a regression, so the suite measures them anyway.
    """
    measurement = run_refine(write_report=False)
    assert measurement.cases == 50
    assert measurement.preserve_rate >= THRESHOLD_PRESERVE, (
        f"preserved {measurement.preserved}/{measurement.cases}"
    )
    assert measurement.relevant_rate >= THRESHOLD_RELEVANT, (
        f"relevant {measurement.relevant_rate:.1%}"
    )
    assert measurement.silent_overwrites <= THRESHOLD_OVERWRITES
    assert measurement.fabrications <= THRESHOLD_FABRICATIONS
    # A failure the rates can hide is still a failure: if any single case broke,
    # the measurement carries it.
    broken = [
        result for result in measurement.results
        if result.note or result.fabricated or result.overwritten
    ]
    assert not broken, f"{broken[0].case.question}: {broken[0].note}"
    # The suite is offline by construction: the engine that answered is the
    # deterministic one, which is what makes the numbers reproducible.
    assert measurement.proposals > 0
    assert measurement.declines > 0
