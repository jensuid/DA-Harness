"""The loop's exit, tested (P8-DECISION-008, UX 46).

What this suite pins:

- the view is the store's, not the moment's: reading it executes nothing and
  writes nothing, so the second read answers the verdict the first computed;
- uncertainty is the checks that did not pass, carried with their own sentences
  and never summarised as a score;
- the implications are the view's only write, and a malformed one is a 400
  naming the entry to fix;
- the decision travels - through the export round trip, through the duplicate -
  and is removed with the case, so a decision is not something a client that
  happened to be looking holds.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app import db as db_module
from app.decision import (
    IMPLICATION_MAX_LENGTH,
    MAX_IMPLICATIONS,
    clean_implications,
)
from app.db import LATEST_SCHEMA_VERSION, get_connection
from app.main import app, get_db

# Two columns, no defects. Every varying column is one the query reads, so the
# alternative-explanations check has nothing untested to name and the verdict is
# a clean `supported` - the case where the decision view's uncertainty is empty.
CSV_CLEAN = (
    "region,revenue\n"
    "north,125.0\n"
    "south,80.5\n"
    "north,200.0\n"
    "south,100.0\n"
)

# The same shape with one null revenue: the missing-data check flags it, the
# verdict is `partially_supported`, and the decision view has real residual
# uncertainty to carry.
CSV_NULL = CSV_CLEAN.replace("south,100.0", "south,")

SQL = "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region"


def _temp_env(tmp_path) -> None:
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _build(
    tmp_path,
    csv=CSV_CLEAN,
    question="Why did revenue change?",
    statement="north leads revenue",
):
    """Walk the loop as far as a validated finding, and hand back the pieces."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": question, "dataset": "sales.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", csv, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
        ).json()["id"]
        finding_id = client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": statement},
        ).json()["id"]
        # The evidence stage needs a chart as well as a finding, so the loop the
        # core declares closed is the loop this fixture walked.
        client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "bar", "x": "region", "y": "total"},
        )
    return client, case_id, finding_id


def _decision(client, case_id) -> dict:
    response = client.get(f"/cases/{case_id}/decision")
    assert response.status_code == 200, response.text
    return response.json()


# --------------------------------------------------------------------------
# The view: what it carries, and what it refuses to conclude
# --------------------------------------------------------------------------


def test_unknown_case_is_a_404(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        response = client.get("/cases/no-such-case/decision")
    assert response.status_code == 404, response.text


def test_a_case_with_no_findings_is_guidance_not_an_empty_decision(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        view = _decision(client, case_id)

    assert view["loop_closed"] is False
    assert view["findings"] == []
    assert view["open_items"] == []
    assert view["counts"]["key_findings"] == 0
    # The question the decision opens on is the case's own.
    assert view["question"] == "Why?"
    # No finding was ever scored, ranked or invented.
    assert view["counts"]["open_checks"] == 0


def test_a_supported_finding_is_a_key_finding_with_no_uncertainty(tmp_path) -> None:
    client, case_id, finding_id = _build(tmp_path)
    with TestClient(app) as client_:
        client_.post(f"/cases/{case_id}/findings/{finding_id}/validate")
        view = _decision(client_, case_id)

    assert view["loop_closed"] is True
    assert [item["id"] for item in view["findings"]] == [finding_id]
    key = view["findings"][0]
    assert key["statement"] == "north leads revenue"
    assert key["validation_status"] == "supported"
    assert key["uncertainty"] == []
    assert key["validated_at"]
    assert view["counts"] == {
        "findings": 1,
        "key_findings": 1,
        "supported": 1,
        "partially_supported": 0,
        "open_items": 0,
        "open_checks": 0,
        "implications": 0,
    }


def test_a_partially_supported_finding_carries_its_failing_checks(tmp_path) -> None:
    """The uncertainty is the checks that did not pass - a sentence each, never
    a score (UX 44's rule)."""
    client, case_id, finding_id = _build(tmp_path, csv=CSV_NULL)
    with TestClient(app) as client_:
        verdict = client_.post(
            f"/cases/{case_id}/findings/{finding_id}/validate"
        ).json()
        view = _decision(client_, case_id)

    assert verdict["status"] == "partially_supported", verdict
    key = view["findings"][0]
    assert key["validation_status"] == "partially_supported"
    failed = [
        check for check in verdict["checks"] if not check["passed"]
    ]
    assert failed, "the fixture is meant to leave a soft concern"
    # The view carries the failing checks verbatim - dimension, sentence and
    # whether it was hard, and nothing else.
    assert [
        (item["dimension"], item["detail"], item["hard"]) for item in key["uncertainty"]
    ] == [
        (check["dimension"], check["detail"], check["hard"]) for check in failed
    ]
    assert view["counts"]["open_checks"] == len(failed)
    # Every carried check is a failure; none is a pass or a skip.
    assert all(item["detail"] for item in key["uncertainty"])


def test_a_refused_finding_is_an_open_item_naming_what_failed(tmp_path) -> None:
    """A causal claim on a correlation-only basis fails a hard dimension, so the
    finding is refused - and the decision says why rather than burying it."""
    client, case_id, finding_id = _build(
        tmp_path, csv=CSV_CLEAN, statement="the region change caused revenue to rise"
    )
    with TestClient(app) as client_:
        verdict = client_.post(
            f"/cases/{case_id}/findings/{finding_id}/validate"
        ).json()
        view = _decision(client_, case_id)

    assert verdict["status"] == "insufficient_evidence", verdict
    assert view["findings"] == []
    assert len(view["open_items"]) == 1
    item = view["open_items"][0]
    assert item["id"] == finding_id
    assert item["validation_status"] == "insufficient_evidence"
    # The reasons are the hard dimensions that failed, as sentences.
    assert item["reasons"]
    assert all(isinstance(reason, str) and reason.strip() for reason in item["reasons"])
    assert view["counts"]["key_findings"] == 0
    assert view["counts"]["open_items"] == 1


def test_a_finding_never_validated_is_open_and_says_so(tmp_path) -> None:
    client, case_id, _ = _build(tmp_path)
    with TestClient(app) as client_:
        view = _decision(client_, case_id)

    assert view["loop_closed"] is False
    item = view["open_items"][0]
    assert item["validation_status"] == "not_evaluated"
    assert item["reasons"] == [
        "awaiting validation - the loop's last step has not run"
    ]


def test_the_purpose_the_analyst_stated_opens_the_decision(tmp_path) -> None:
    client, case_id, _ = _build(tmp_path)
    with TestClient(app) as client_:
        client_.put(
            f"/cases/{case_id}/context",
            json={"purpose": "Decide whether to chase the south region",
                  "sub_questions": [], "hypotheses": [], "constraints": []},
        )
        view = _decision(client_, case_id)

    assert view["purpose"] == "Decide whether to chase the south region"
    # A case that never stated intent still answers.
    client, case_id, _ = _build(
        tmp_path, csv=CSV_CLEAN, question="Why did revenue change again?"
    )
    with TestClient(app) as client_:
        view = _decision(client_, case_id)
    assert view["purpose"] == ""


def test_findings_read_oldest_first(tmp_path) -> None:
    """The decision reads as the analysis happened, not as a query returned
    them (the findings list endpoint is newest first; this is a decision)."""
    client, case_id, finding_a = _build(tmp_path)
    with TestClient(app) as client_:
        run_id = client_.get(f"/cases/{case_id}/runs").json()[0]["id"]
        finding_b = client_.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "south trails revenue"},
        ).json()["id"]
        for finding in (finding_a, finding_b):
            client_.post(f"/cases/{case_id}/findings/{finding}/validate")
        view = _decision(client_, case_id)

    assert [item["id"] for item in view["findings"]] == [finding_a, finding_b]


def test_loop_closed_agrees_with_the_workflow_it_sits_inside(tmp_path) -> None:
    """The view's meaning is the core's meaning, so the decision cannot say the
    loop is open while the shell's rail says it is closed (or the reverse)."""
    client, case_id, finding_id = _build(tmp_path)
    with TestClient(app) as client_:
        # The loop is open until a finding is validated - the core's own rule,
        # which the view reads rather than restating.
        assert client_.get(f"/cases/{case_id}/progress").json()["loop_closed"] is False
        assert _decision(client_, case_id)["loop_closed"] is False

        client_.post(f"/cases/{case_id}/findings/{finding_id}/validate")

        progress = client_.get(f"/cases/{case_id}/progress").json()
        view_after = _decision(client_, case_id)

    assert progress["loop_closed"] is True
    assert view_after["loop_closed"] is progress["loop_closed"]


# --------------------------------------------------------------------------
# The verdict is kept: reading is not recomputing
# --------------------------------------------------------------------------


def test_the_verdict_is_readable_without_revalidating(tmp_path) -> None:
    client, case_id, finding_id = _build(tmp_path)
    with TestClient(app) as client_:
        computed = client_.post(
            f"/cases/{case_id}/findings/{finding_id}/validate"
        ).json()
        response = client_.get(
            f"/cases/{case_id}/findings/{finding_id}/validation"
        )
        assert response.status_code == 200, response.text
        stored = response.json()

    assert stored["finding_id"] == finding_id
    assert stored["status"] == computed["status"]
    assert stored["checks"] == computed["checks"]
    assert stored["validated_at"] == computed["validated_at"]


def test_a_never_validated_finding_has_no_verdict_to_read(tmp_path) -> None:
    client, case_id, finding_id = _build(tmp_path)
    with TestClient(app) as client_:
        response = client_.get(
            f"/cases/{case_id}/findings/{finding_id}/validation"
        )
    assert response.status_code == 404, response.text
    assert "validate" in response.json()["detail"]


def test_a_verdict_is_not_readable_from_another_case(tmp_path) -> None:
    client, case_id, finding_id = _build(tmp_path)
    _, other_case, _ = _build(
        tmp_path, csv=CSV_CLEAN, question="An unrelated investigation?"
    )
    with TestClient(app) as client_:
        response = client_.get(f"/cases/{other_case}/findings/{finding_id}/validation")
    assert response.status_code == 404, response.text


def test_reading_the_decision_executes_and_writes_nothing(tmp_path) -> None:
    """The view is read-only by construction: the runs do not grow, the verdict
    does not move, and two reads are the same read."""
    client, case_id, finding_id = _build(tmp_path)
    with TestClient(app) as client_:
        client_.post(f"/cases/{case_id}/findings/{finding_id}/validate")
        runs_before = len(client_.get(f"/cases/{case_id}/runs").json())
        first = _decision(client_, case_id)
        for _ in range(3):
            again = _decision(client_, case_id)
            assert again == first
        runs_after = len(client_.get(f"/cases/{case_id}/runs").json())

    assert runs_before == runs_after == 1


def test_revalidating_replaces_the_verdict_it_keeps(tmp_path) -> None:
    """A second validation is a recompute, not an append: one row per finding,
    holding the latest verdict."""
    client, case_id, finding_id = _build(tmp_path, csv=CSV_NULL)
    with TestClient(app) as client_:
        first = client_.post(
            f"/cases/{case_id}/findings/{finding_id}/validate"
        ).json()
        second = client_.post(
            f"/cases/{case_id}/findings/{finding_id}/validate"
        ).json()
        rows = client_.get(
            f"/cases/{case_id}/findings/{finding_id}/validation"
        ).json()
        response = client_.get(
            f"/cases/{case_id}/history"
        ).json()

    assert first["status"] == second["status"] == "partially_supported"
    assert rows["checks"] == second["checks"]
    assert rows["validated_at"] == second["validated_at"]
    # One row per finding: the timeline is a projection of the store, so a
    # re-validation is a recompute it records once, not an append.
    assert response["counts"]["validations"] == 1
    package = client_.get(f"/cases/{case_id}/export").json()
    assert len(package["validations"]) == 1
    assert package["validations"][0]["finding_id"] == finding_id


def test_the_decision_of_a_deleted_case_leaves_no_trace(tmp_path) -> None:
    client, case_id, finding_id = _build(tmp_path)
    with TestClient(app) as client_:
        client_.post(f"/cases/{case_id}/findings/{finding_id}/validate")
        client_.put(
            f"/cases/{case_id}/decision", json={"implications": ["review pricing"]}
        )
        client_.delete(f"/cases/{case_id}")
        response = client_.get(f"/cases/{case_id}/decision")
    assert response.status_code == 404, response.text


def test_a_duplicated_case_keeps_its_decision_and_its_verdicts(tmp_path) -> None:
    client, case_id, finding_id = _build(tmp_path, csv=CSV_NULL)
    with TestClient(app) as client_:
        client_.post(f"/cases/{case_id}/findings/{finding_id}/validate")
        client_.put(
            f"/cases/{case_id}/decision",
            json={"implications": ["review pricing", "watch the south region"]},
        )
        copy_id = client_.post(f"/cases/{case_id}/duplicate").json()["id"]
        original = _decision(client_, case_id)
        copy = _decision(client_, copy_id)

    assert copy["implications"] == original["implications"]
    assert len(copy["findings"]) == 1
    assert copy["findings"][0]["uncertainty"] == original["findings"][0]["uncertainty"]
    assert copy["findings"][0]["id"] != original["findings"][0]["id"]
    assert copy["updated_at"] == original["updated_at"]


# --------------------------------------------------------------------------
# The implications: the view's only write
# --------------------------------------------------------------------------


def test_implications_round_trip_and_are_the_analysts_own(tmp_path) -> None:
    client, case_id, _ = _build(tmp_path)
    with TestClient(app) as client_:
        response = client_.put(
            f"/cases/{case_id}/decision",
            json={"implications": ["Review enterprise pricing", "Compare the baseline"]},
        )
        assert response.status_code == 200, response.text
        written = response.json()
        view = _decision(client_, case_id)

    assert written == view
    assert view["implications"] == ["Review enterprise pricing", "Compare the baseline"]
    assert view["counts"]["implications"] == 2
    assert view["updated_at"]


def test_implications_are_trimmed_and_blanks_are_refused(tmp_path) -> None:
    client, case_id, _ = _build(tmp_path)
    with TestClient(app) as client_:
        response = client_.put(
            f"/cases/{case_id}/decision", json={"implications": ["  spaced  "]}
        )
        view = _decision(client_, case_id)
        bad = client_.put(
            f"/cases/{case_id}/decision", json={"implications": ["   "]}
        )

    assert response.status_code == 200
    assert view["implications"] == ["spaced"]
    assert bad.status_code == 400, bad.text
    assert "implication 1 is empty" in bad.json()["detail"]


def test_a_bad_implication_is_a_400_naming_the_entry_to_fix(tmp_path) -> None:
    client, case_id, _ = _build(tmp_path)
    with TestClient(app) as client_:
        too_many = client_.put(
            f"/cases/{case_id}/decision",
            json={"implications": ["x"] * (MAX_IMPLICATIONS + 1)},
        )
        too_long = client_.put(
            f"/cases/{case_id}/decision",
            json={"implications": ["y" * (IMPLICATION_MAX_LENGTH + 1)]},
        )
        # Nothing was written by either refusal.
        view = _decision(client_, case_id)

    assert too_many.status_code == 400
    assert str(MAX_IMPLICATIONS) in too_many.json()["detail"]
    assert too_long.status_code == 400
    assert "implication 1 is longer than" in too_long.json()["detail"]
    assert view["implications"] == []


def test_an_empty_list_clears_the_implications(tmp_path) -> None:
    """Clearing them is a decision the analyst is allowed to make; the refusal
    is about shape, never about whether the analyst decided enough."""
    client, case_id, _ = _build(tmp_path)
    with TestClient(app) as client_:
        client_.put(f"/cases/{case_id}/decision", json={"implications": ["one"]})
        cleared = client_.put(f"/cases/{case_id}/decision", json={"implications": []})
        view = _decision(client_, case_id)

    assert cleared.status_code == 200
    assert view["implications"] == []
    assert view["updated_at"]


def test_clean_implications_rejects_a_non_list_outright() -> None:
    """The endpoint's schema answers a non-list body, but the store's rule is
    stated in one place and tested in one place."""
    for bad in ("a string", 3, {"not": "a list"}, None):
        try:
            clean_implications(bad)
        except ValueError as error:
            assert "list of strings" in str(error)
        else:  # pragma: no cover - the assertion above is the point
            raise AssertionError(f"accepted {bad!r}")
    for bad in ([3], ["ok", ""]):
        try:
            clean_implications(bad)
        except ValueError as error:
            assert "implication" in str(error)
        else:  # pragma: no cover
            raise AssertionError(f"accepted {bad!r}")


# --------------------------------------------------------------------------
# The timeline: the loop's exit is an auditable event
# --------------------------------------------------------------------------


def test_the_timeline_records_the_validation_and_the_decision(tmp_path) -> None:
    client, case_id, finding_id = _build(tmp_path)
    with TestClient(app) as client_:
        client_.post(f"/cases/{case_id}/findings/{finding_id}/validate")
        before = client_.get(f"/cases/{case_id}/history").json()
        client_.put(
            f"/cases/{case_id}/decision", json={"implications": ["act on it"]}
        )
        after = client_.get(f"/cases/{case_id}/history").json()

    kinds_before = [event["kind"] for event in before["events"]]
    assert kinds_before[-1] == "finding_validated"
    assert before["events"][-1]["artifact_id"] == finding_id
    assert before["events"][-1]["detail"] == "validation: supported"
    assert before["counts"]["validations"] == 1
    assert before["counts"]["decisions"] == 0

    kinds_after = [event["kind"] for event in after["events"]]
    assert kinds_after[-1] == "decision_written"
    assert after["events"][-1]["detail"] == "1 implication(s) written"
    assert after["counts"]["decisions"] == 1
    # Chronological: the decision follows the validation it decides on.
    timestamps = [event["timestamp"] for event in after["events"]]
    assert timestamps == sorted(timestamps)


def test_the_decision_event_reads_the_implications_count(tmp_path) -> None:
    client, case_id, _ = _build(tmp_path)
    with TestClient(app) as client_:
        client_.put(
            f"/cases/{case_id}/decision",
            json={"implications": ["one", "two", "three"]},
        )
        history = client_.get(f"/cases/{case_id}/history").json()
    event = next(e for e in history["events"] if e["kind"] == "decision_written")
    assert event["detail"] == "3 implication(s) written"


# --------------------------------------------------------------------------
# The export: AT-43's "validation states preserved" is a property of the
# package, not a claim about it
# --------------------------------------------------------------------------


def test_export_carries_the_verdicts_and_the_decision(tmp_path) -> None:
    client, case_id, finding_id = _build(tmp_path, csv=CSV_NULL)
    with TestClient(app) as client_:
        verdict = client_.post(
            f"/cases/{case_id}/findings/{finding_id}/validate"
        ).json()
        client_.put(
            f"/cases/{case_id}/decision", json={"implications": ["review pricing"]}
        )
        package = client_.get(f"/cases/{case_id}/export").json()

    assert len(package["validations"]) == 1
    carried = package["validations"][0]
    assert carried["finding_id"] == finding_id
    assert carried["status"] == verdict["status"]
    assert carried["checks"] == verdict["checks"]
    assert package["decision"]["implications"] == ["review pricing"]
    assert package["decision"]["updated_at"]


def test_a_case_with_no_decision_exports_none_rather_than_an_empty_one(tmp_path) -> None:
    client, case_id, _ = _build(tmp_path)
    with TestClient(app) as client_:
        package = client_.get(f"/cases/{case_id}/export").json()
    assert package["decision"] is None
    assert package["validations"] == []


def test_the_round_trip_restores_the_verdicts_and_the_decision(tmp_path) -> None:
    client, case_id, finding_id = _build(tmp_path, csv=CSV_NULL)
    with TestClient(app) as client_:
        client_.post(f"/cases/{case_id}/findings/{finding_id}/validate")
        client_.put(
            f"/cases/{case_id}/decision",
            json={"implications": ["review pricing", "watch the south region"]},
        )
        package = client_.get(f"/cases/{case_id}/export").json()
        imported = client_.post("/cases/import", json=package).json()

        original = _decision(client_, case_id)
        restored = _decision(client_, imported["id"])

    assert restored["implications"] == original["implications"]
    assert restored["findings"][0]["validation_status"] == "partially_supported"
    assert restored["findings"][0]["uncertainty"] == original["findings"][0]["uncertainty"]
    # The verdict survived with fresh ids, not the original ones.
    assert restored["findings"][0]["id"] != original["findings"][0]["id"]
    assert restored["loop_closed"] is True


def test_an_older_package_without_a_decision_still_imports(tmp_path) -> None:
    """A package written before the decision existed has no section for it;
    the round trip degrades, it does not fail."""
    client, case_id, finding_id = _build(tmp_path)
    with TestClient(app) as client_:
        client_.post(f"/cases/{case_id}/findings/{finding_id}/validate")
        package = client_.get(f"/cases/{case_id}/export").json()
        package.pop("decision")
        package.pop("validations")
        imported = client_.post("/cases/import", json=package).json()
        restored = _decision(client_, imported["id"])

    assert restored["implications"] == []
    # The finding's status travelled on the finding, as it always did.
    assert restored["open_items"] == []
    assert restored["findings"][0]["validation_status"] == "supported"
    # No verdict row was invented for it.
    assert restored["findings"][0]["uncertainty"] == []
    assert restored["findings"][0]["validated_at"] is None


def test_every_validated_finding_survives_the_round_trip(tmp_path) -> None:
    """AT-43 measured rather than asserted: every finding the loop validated is
    in the exported package, with the validation state it earned."""
    client, case_id, finding_a = _build(tmp_path, csv=CSV_NULL)
    with TestClient(app) as client_:
        run_id = client_.get(f"/cases/{case_id}/runs").json()[0]["id"]
        finding_b = client_.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "south trails revenue"},
        ).json()["id"]
        for finding in (finding_a, finding_b):
            client_.post(f"/cases/{case_id}/findings/{finding}/validate")
        package = client_.get(f"/cases/{case_id}/export").json()
        view = _decision(client_, case_id)

    exported = {item["id"]: item for item in package["findings"]}
    assert len(exported) == len(view["findings"]) == 2
    for key in view["findings"]:
        assert exported[key["id"]]["validation_status"] == key["validation_status"]
    assert {item["finding_id"] for item in package["validations"]} == set(exported)
    assert {item["status"] for item in package["validations"]} == {
        "partially_supported"
    }


# --------------------------------------------------------------------------
# The store: one migration, in place
# --------------------------------------------------------------------------


def _legacy_store(db_path: Path) -> None:
    """A store at v12 - the shape the previous task left behind."""
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE cases (id TEXT PRIMARY KEY, question TEXT NOT NULL,
                            dataset TEXT NOT NULL, template_id TEXT,
                            created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE findings (id TEXT PRIMARY KEY, case_id TEXT NOT NULL,
                               run_id TEXT NOT NULL, statement TEXT NOT NULL,
                               interpretation TEXT, caveat TEXT,
                               validation_status TEXT NOT NULL,
                               created_at TEXT NOT NULL);
        PRAGMA user_version = 12;
        """
    )
    conn.commit()
    conn.close()


def test_a_legacy_store_upgrades_to_v13_in_place(tmp_path) -> None:
    db_path = tmp_path / "legacy.db"
    _legacy_store(db_path)
    with get_connection(db_path) as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        applied = {
            row["version"]: row["name"]
            for row in conn.execute(
                "SELECT version, name FROM schema_migrations ORDER BY version"
            ).fetchall()
        }
        # The new tables exist and are empty, not absent.
        decisions = conn.execute("SELECT COUNT(*) AS n FROM decisions").fetchone()["n"]
        validations = conn.execute(
            "SELECT COUNT(*) AS n FROM validations"
        ).fetchone()["n"]

    assert version == LATEST_SCHEMA_VERSION == 13
    assert 13 in applied
    assert "decisions" in applied[13]
    assert decisions == 0
    assert validations == 0


def test_a_fresh_store_is_current_with_no_migrations_applied(tmp_path) -> None:
    """Born current: nothing was applied, so the audit trail is empty - the
    truth, not a row that flatters."""
    db_path = tmp_path / "fresh.db"
    with get_connection(db_path) as conn:
        applied = conn.execute(
            "SELECT COUNT(*) AS n FROM schema_migrations"
        ).fetchone()["n"]
    assert applied == 0
