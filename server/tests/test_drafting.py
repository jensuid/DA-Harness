"""Finding drafting tests for P3-AI-012.

A finding is the trust artifact - the evidence chain, validation and export all
stand on it - so drafting proposes and a human disposes. These cover the
deterministic draft, the honesty budget (every quoted number must be one the
result actually contains), the LLM path and its three failure modes, the
no-state property, the accept-then-validate round trip, the weaker draft a
non-numeric result yields, and the 404 contract.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module
import app.drafter as drafter_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"
# A result with a repeating region column, so the draft has both a measure and
# a dimension to compare: north 200.0, north 125.0, south 80.5.
SQL = "SELECT region, revenue FROM read_csv_auto(?) ORDER BY revenue DESC"
SQL_NO_NUMBERS = "SELECT region FROM read_csv_auto(?)"


def _temp_env(tmp_path, monkeypatch):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:  # pragma: no cover - generator
            yield connection

    app.dependency_overrides[get_db] = override
    # No key by default, so the deterministic engine speaks unless a test
    # installs a fake one - the suite never makes a live call.
    monkeypatch.delenv("DAH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def _case_with_run(client, sql=SQL):
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    run_id = client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": sql}
    ).json()["id"]
    return case_id, run_id


class _GoodDrafter:
    def draft(self, question, kind, source_text, columns, rows, profile):
        return {
            "statement": "north leads on revenue at 200.0 across 3 rows",
            "interpretation": "the north region carries the highest revenue",
            "caveat": "three rows is a small basis for a claim",
            "grounds": ["revenue = 200.0 for region = north", "3 rows in the result"],
        }


class _InventingDrafter:
    def draft(self, question, kind, source_text, columns, rows, profile):
        return {
            "statement": "north leads on revenue at 9999.0",
            "interpretation": "an invented magnitude",
            "caveat": "this number is not in the result",
            "grounds": ["revenue = 9999.0 for region = north"],
        }


class _FailingDrafter:
    def draft(self, *args, **kwargs):
        raise RuntimeError("LLM unavailable")


class _MalformedDrafter:
    def draft(self, *args, **kwargs):
        return {"statement": "", "interpretation": "no caveat", "grounds": "not a list"}


def test_deterministic_draft_names_the_runs_real_columns(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        response = client.post(f"/cases/{case_id}/runs/{run_id}/draft-finding")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == drafter_module.SOURCE_DETERMINISTIC
    assert body["run_id"] == run_id
    for field in ("statement", "interpretation", "caveat"):
        assert body[field].strip(), f"{field} must be non-empty"
    joined = " ".join([body["statement"], body["interpretation"], *body["grounds"]])
    # The draft speaks the result's own vocabulary: its measure and dimension.
    assert "revenue" in joined
    assert "region" in joined
    assert "north" in joined


def test_every_ground_is_a_value_the_result_contains(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        body = client.post(
            f"/cases/{case_id}/runs/{run_id}/draft-finding"
        ).json()
        run = client.get(f"/cases/{case_id}/runs/{run_id}").json()

    allowed = drafter_module._allowed_numbers(
        run["columns"], run["rows"], len(run["rows"])
    )
    quoted = set()
    for text in [body["statement"], *body["grounds"]]:
        quoted |= drafter_module._numbers_in(text)
    # Nothing the draft states as a magnitude may be unreachable from the result.
    assert quoted <= allowed, f"the draft quotes values absent from the result: {quoted - allowed}"


def test_an_llm_draft_quoting_real_values_is_accepted(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(drafter_module, "_configured_llm", lambda: _GoodDrafter())
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        response = client.post(f"/cases/{case_id}/runs/{run_id}/draft-finding")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == drafter_module.SOURCE_LLM
    assert body["statement"] == "north leads on revenue at 200.0 across 3 rows"
    assert body["grounds"] == [
        "revenue = 200.0 for region = north",
        "3 rows in the result",
    ]


def test_an_llm_draft_that_invents_a_magnitude_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(drafter_module, "_configured_llm", lambda: _InventingDrafter())
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        response = client.post(f"/cases/{case_id}/runs/{run_id}/draft-finding")

    assert response.status_code == 200
    body = response.json()
    # 9999 is nowhere in the result, so the LLM cannot be the basis of a finding.
    assert body["source"] == drafter_module.SOURCE_DETERMINISTIC_FALLBACK
    assert "9999" not in body["statement"]
    assert "9999" not in " ".join(body["grounds"])


def test_an_llm_failure_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(drafter_module, "_configured_llm", lambda: _FailingDrafter())
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        response = client.post(f"/cases/{case_id}/runs/{run_id}/draft-finding")

    assert response.status_code == 200
    assert response.json()["source"] == drafter_module.SOURCE_DETERMINISTIC_FALLBACK


def test_malformed_llm_output_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(drafter_module, "_configured_llm", lambda: _MalformedDrafter())
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        response = client.post(f"/cases/{case_id}/runs/{run_id}/draft-finding")

    assert response.status_code == 200
    assert response.json()["source"] == drafter_module.SOURCE_DETERMINISTIC_FALLBACK


def test_drafting_writes_nothing_to_the_findings_table(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        client.post(f"/cases/{case_id}/runs/{run_id}/draft-finding")
        # A draft is a proposal, not state: the case still has no findings.
        findings = client.get(f"/cases/{case_id}/findings")

    assert findings.status_code == 200
    assert findings.json() == []


def test_a_drafts_statement_can_be_accepted_and_validated(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        draft = client.post(
            f"/cases/{case_id}/runs/{run_id}/draft-finding"
        ).json()

        # Acceptance is the existing findings endpoint - the only path that
        # creates a finding, which is what keeps the human in charge of it.
        accepted = client.post(
            f"/cases/{case_id}/findings",
            json={
                "run_id": run_id,
                "statement": draft["statement"],
                "interpretation": draft["interpretation"],
                "caveat": draft["caveat"],
            },
        )
        finding = accepted.json()

        # The trust loop still closes on an accepted draft: the stored SQL is
        # rerun against the stored dataset and the numbers still match.
        verdict = client.post(
            f"/cases/{case_id}/findings/{finding['id']}/validate"
        )

    assert accepted.status_code == 201, accepted.text
    assert verdict.status_code == 200, verdict.text
    assert verdict.json()["status"] == "supported"


def test_a_draft_that_leads_with_an_outlier_names_it_as_one(
    tmp_path, monkeypatch
) -> None:
    """W2X-009: the deterministic draft does not promote a planted outlier.

    The walk planted 99000 where revenue was otherwise ~99; the profile's
    quality detector flagged it at 758x, and the draft crowned it anyway. The
    honest answer names the outlier and steps down to the largest remaining
    group, rather than announcing the extreme as the leader.
    """
    csv = (
        b"order_id,revenue,region\n"
        b"1,99000.0,north\n"
        b"2,99.0,east\n"
        b"3,130.0,south\n"
        b"4,99.5,east\n"
        b"5,120.0,south\n"
        b"6,88.0,north\n"
    )
    # The walk's shape: a raw row-level result whose region repeats, so the
    # draft has a grouping to compare and crowns the outlier's row.
    sql = "SELECT region, revenue FROM read_csv_auto(?) ORDER BY revenue DESC"
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "which region leads on revenue?", "dataset": "sales.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets", files={"file": ("sales.csv", csv, "text/csv")}
        ).json()["id"]
        profile = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile").json()
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": sql}
        ).json()["id"]
        body = client.post(f"/cases/{case_id}/runs/{run_id}/draft-finding").json()

    # The profile's quality layer is the thing the draft now reads.
    kinds = [issue["kind"] for issue in profile.get("quality") or []]
    assert drafter_module.CLASS_EXTREME_VALUES in kinds

    caveat = body["caveat"]
    # The outlier is named as an outlier, not as the answer. The detector's
    # multiple is computed over the dataset, so the assertion takes the
    # profile's own sentence rather than hard-coding the figure the walk saw.
    assert "is an outlier" in caveat
    extreme = next(
        issue for issue in (profile.get("quality") or [])
        if issue["kind"] == drafter_module.CLASS_EXTREME_VALUES
    )
    assert "the next-largest value" in extreme["observed"]
    # The ranking the analyst would act on is pointed at the largest group
    # that is not the outlier, not at the outlier itself.
    assert "largest revenue among the remaining groups" in caveat


def test_a_draft_without_a_quality_issue_does_not_mention_an_outlier(
    tmp_path, monkeypatch
) -> None:
    """The outlier caveat appears only when the profile recorded one.

    A draft on a dataset whose spread is ordinary - the suite's own fixture -
    must not gain the outlier sentence, so the caveat is a response to the
    profile rather than text the draft always carries.
    """
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        body = client.post(f"/cases/{case_id}/runs/{run_id}/draft-finding").json()

    assert "outlier" not in body["caveat"]


def test_a_result_without_a_numeric_column_yields_an_honest_weaker_draft(
    tmp_path, monkeypatch
) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client, sql=SQL_NO_NUMBERS)
        response = client.post(f"/cases/{case_id}/runs/{run_id}/draft-finding")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == drafter_module.SOURCE_DETERMINISTIC
    # It says plainly that no quantitative claim is possible rather than dressing
    # an observation up as a finding.
    assert "no numeric measure" in body["statement"]
    assert body["grounds"]


def test_404s_for_unknown_and_cross_case_runs(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        other_case = client.post(
            "/cases", json={"question": "Other?", "dataset": "o.csv"}
        ).json()["id"]

        assert (
            client.post(f"/cases/no-such-case/runs/{run_id}/draft-finding").status_code
            == 404
        )
        assert (
            client.post(f"/cases/{case_id}/runs/no-such-run/draft-finding").status_code
            == 404
        )
        # A run belonging to another case is not reachable through this path.
        assert (
            client.post(
                f"/cases/{other_case}/runs/{run_id}/draft-finding"
            ).status_code
            == 404
        )
