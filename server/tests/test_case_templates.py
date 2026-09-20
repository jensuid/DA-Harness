"""Case template tests for P3-CASE-007.

A template is the skeleton a new case starts from - question and dataset label -
and it outlives the case it came from, because templates are not case children.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"


def _temp_db(tmp_path):
    db_path = tmp_path / "test.db"

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    return db_path


def _promote(client, case_id, name=None):
    payload = {} if name is None else {"name": name}
    response = client.post(f"/cases/{case_id}/template", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_promote_defaults_name_to_question(tmp_path) -> None:
    db_path = _temp_db(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why did revenue decline?",
                            "dataset": "sales.csv"}
        ).json()["id"]
        template = _promote(client, case_id)

    assert template["name"] == "Why did revenue decline?"
    assert template["question"] == "Why did revenue decline?"
    assert template["dataset"] == "sales.csv"
    assert template["id"]

    app.dependency_overrides.clear()


def test_promote_keeps_explicit_name(tmp_path) -> None:
    db_path = _temp_db(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "sales.csv"}
        ).json()["id"]
        template = _promote(client, case_id, name="Q3 revenue review")

    assert template["name"] == "Q3 revenue review"
    assert template["question"] == "Why?"

    app.dependency_overrides.clear()


def test_promote_empty_name_is_a_400(tmp_path) -> None:
    db_path = _temp_db(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "sales.csv"}
        ).json()["id"]
        response = client.post(f"/cases/{case_id}/template", json={"name": "  "})

    assert response.status_code == 400

    app.dependency_overrides.clear()


def test_promote_unknown_case_is_404(tmp_path) -> None:
    db_path = _temp_db(tmp_path)
    with TestClient(app) as client:
        response = client.post("/cases/nope/template", json={})

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_list_templates_newest_first(tmp_path) -> None:
    db_path = _temp_db(tmp_path)
    with TestClient(app) as client:
        first = client.post(
            "/cases", json={"question": "first", "dataset": "a.csv"}
        ).json()["id"]
        second = client.post(
            "/cases", json={"question": "second", "dataset": "b.csv"}
        ).json()["id"]
        _promote(client, first, name="oldest")
        _promote(client, second, name="newest")
        templates = client.get("/templates").json()

    assert [t["name"] for t in templates] == ["newest", "oldest"]

    app.dependency_overrides.clear()


def test_case_from_template_keeps_skeleton(tmp_path) -> None:
    """A templated case starts clean: question and label only, no data."""
    db_path = _temp_db(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "sales.csv"}
        ).json()["id"]
        # Give the source case artifacts; none of them should be copied.
        client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        )
        template = _promote(client, case_id, name="skeleton")
        created = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        )

    assert created.status_code == 201, created.text
    new_case = created.json()
    assert new_case["question"] == "Why?"
    assert new_case["dataset"] == "sales.csv"
    assert new_case["id"] not in (case_id, template["id"])

    datasets = client.get(f"/cases/{new_case['id']}/datasets").json()
    assert datasets == []

    app.dependency_overrides.clear()


def test_case_from_template_allows_overrides(tmp_path) -> None:
    db_path = _temp_db(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "sales.csv"}
        ).json()["id"]
        template = _promote(client, case_id)
        created = client.post(
            "/cases/from-template",
            json={
                "template_id": template["id"],
                "question": "Why did churn spike?",
                "dataset": "users.csv",
            },
        )

    assert created.status_code == 201, created.text
    assert created.json()["question"] == "Why did churn spike?"
    assert created.json()["dataset"] == "users.csv"

    app.dependency_overrides.clear()


def test_case_from_unknown_template_is_404(tmp_path) -> None:
    db_path = _temp_db(tmp_path)
    with TestClient(app) as client:
        response = client.post(
            "/cases/from-template", json={"template_id": "no-such-template"}
        )

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_template_survives_its_source_case(tmp_path) -> None:
    """Deleting a promoted case leaves the template usable."""
    db_path = _temp_db(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "sales.csv"}
        ).json()["id"]
        template = _promote(client, case_id, name="survivor")
        client.delete(f"/cases/{case_id}")

        listed = client.get("/templates").json()
        assert [t["name"] for t in listed] == ["survivor"]
        created = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        )

    assert created.status_code == 201, created.text

    app.dependency_overrides.clear()


def test_delete_template_leaves_its_cases_alone(tmp_path) -> None:
    db_path = _temp_db(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "sales.csv"}
        ).json()["id"]
        template = _promote(client, case_id)
        child = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        ).json()

        gone = client.delete(f"/templates/{template['id']}")
        again = client.delete(f"/templates/{template['id']}")
        templates = client.get("/templates").json()
        case = client.get(f"/cases/{child['id']}")

    assert gone.status_code == 204
    assert again.status_code == 404
    assert templates == []
    # The case the template seeded is untouched.
    assert case.status_code == 200
    assert case.json()["question"] == "Why?"

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# P6-TEMPLATE-003: a template carries the shape of the case it came from.
# ---------------------------------------------------------------------------

import app.db as db_module
from app.db import get_connection

CSV_SHAPE = (
    b"order_id,revenue,region\n"
    b"1,125.0,north\n2,80.5,south\n3,200.0,north\n4,60.0,east\n"
)
PLAN_SQL = (
    "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
    "GROUP BY region ORDER BY region"
)


def _env(tmp_path, monkeypatch):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    monkeypatch.delenv("DAH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return db_path


def _finished_case(client) -> str:
    """A case with a plan, a run and a validated finding - a shape to carry."""
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "s.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("s.csv", CSV_SHAPE, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")
    run_id = client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": PLAN_SQL}
    ).json()["id"]
    finding = client.post(
        f"/cases/{case_id}/findings",
        json={"run_id": run_id, "statement": "North leads revenue."},
    )
    client.post(
        f"/cases/{case_id}/findings/{finding.json()['id']}/validate"
    )
    return case_id


def _finished_template(client) -> dict:
    """A promoted template from a case with a plan, a run and a finding."""
    return _promote(client, _finished_case(client), name="revenue review")


def test_promote_captures_the_plan_proposals_and_findings(tmp_path, monkeypatch) -> None:
    db_path = _env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        template = _finished_template(client)

    shape = template["shape"]
    assert shape is not None
    assert shape["plan"] is not None
    assert shape["plan_source"] == "deterministic"
    # The query the case ran is what the next case is offered.
    assert any(p["code"] == PLAN_SQL for p in shape["proposals"])
    # The finding and its verdict travel with it.
    assert [(f["statement"], f["validation_status"]) for f in shape["findings"]] == [
        ("North leads revenue.", "supported")
    ]


def test_promoting_an_empty_case_yields_no_shape(tmp_path, monkeypatch) -> None:
    """A case with nothing to carry promotes the skeleton it always did."""
    db_path = _env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        template = _promote(client, case_id)

    assert template["shape"] is None


def test_a_templated_case_starts_clean_but_records_its_lineage(
    tmp_path, monkeypatch,
) -> None:
    """No artifacts are inherited; the template id is."""
    db_path = _env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _finished_case(client)
        template = _promote(client, case_id)
        created = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        ).json()

    assert created["template_id"] == template["id"]
    assert client.get(f"/cases/{created['id']}/datasets").json() == []
    assert client.get(f"/cases/{created['id']}/progress").json()["stage"] == "data"


def test_the_plan_step_offers_the_template_plan(tmp_path, monkeypatch) -> None:
    """A templated case's first plan is the template's, not a derivation."""
    db_path = _env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        template = _finished_template(client)
        new_case = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        ).json()
        dataset_id = client.post(
            f"/cases/{new_case['id']}/datasets",
            files={"file": ("s.csv", CSV_SHAPE, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{new_case['id']}/datasets/{dataset_id}/profile")

        plan = client.post(
            f"/cases/{new_case['id']}/datasets/{dataset_id}/plan"
        ).json()

    assert plan["source"] == "template"
    assert plan["plan"] == template["shape"]["plan"]


def test_the_plan_step_falls_back_when_the_template_is_gone(
    tmp_path, monkeypatch,
) -> None:
    """A deleted template degrades to the derivation, never an error."""
    db_path = _env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        template = _finished_template(client)
        new_case = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        ).json()
        client.delete(f"/templates/{template['id']}")
        dataset_id = client.post(
            f"/cases/{new_case['id']}/datasets",
            files={"file": ("s.csv", CSV_SHAPE, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{new_case['id']}/datasets/{dataset_id}/profile")

        plan = client.post(
            f"/cases/{new_case['id']}/datasets/{dataset_id}/plan"
        ).json()

    assert plan["source"] == "deterministic"


def test_the_plan_step_derives_once_the_case_has_planned(tmp_path, monkeypatch) -> None:
    """The template's plan seeds the first plan; the second is the case's own."""
    db_path = _env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        template = _finished_template(client)
        new_case = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        ).json()
        dataset_id = client.post(
            f"/cases/{new_case['id']}/datasets",
            files={"file": ("s.csv", CSV_SHAPE, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{new_case['id']}/datasets/{dataset_id}/profile")
        client.post(f"/cases/{new_case['id']}/datasets/{dataset_id}/plan")

        second = client.post(
            f"/cases/{new_case['id']}/datasets/{dataset_id}/plan"
        ).json()

    assert second["source"] == "deterministic"


def test_generate_code_offers_the_template_query(tmp_path, monkeypatch) -> None:
    db_path = _env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        template = _finished_template(client)
        new_case = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        ).json()
        dataset_id = client.post(
            f"/cases/{new_case['id']}/datasets",
            files={"file": ("s.csv", CSV_SHAPE, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{new_case['id']}/datasets/{dataset_id}/profile")

        proposal = client.post(
            f"/cases/{new_case['id']}/datasets/{dataset_id}/generate-code",
            json={"question": "Why did revenue decline?", "kind": "sql"},
        ).json()

    assert proposal["source"] == "template"
    assert proposal["code"] == PLAN_SQL


def test_generate_code_refuses_a_query_for_columns_the_dataset_lacks(
    tmp_path, monkeypatch,
) -> None:
    """A template query written against other columns is not offered."""
    db_path = _env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        template = _finished_template(client)
        new_case = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        ).json()
        # Same shape but no `revenue` column: the template's query cannot run.
        thin = b"order_id,region\n1,north\n2,south\n"
        dataset_id = client.post(
            f"/cases/{new_case['id']}/datasets",
            files={"file": ("s.csv", thin, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{new_case['id']}/datasets/{dataset_id}/profile")

        proposal = client.post(
            f"/cases/{new_case['id']}/datasets/{dataset_id}/generate-code",
            json={"question": "Why did revenue decline?", "kind": "sql"},
        ).json()

    assert proposal["source"] == "deterministic"
    assert "revenue" not in proposal["columns_used"]


def test_a_shapeless_template_still_instantiates_and_plans(
    tmp_path, monkeypatch,
) -> None:
    """An older template, or one from an empty case, behaves as it always did."""
    db_path = _env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        template = _promote(client, case_id, name="skeleton")
        new_case = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        ).json()
        dataset_id = client.post(
            f"/cases/{new_case['id']}/datasets",
            files={"file": ("s.csv", CSV_SHAPE, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{new_case['id']}/datasets/{dataset_id}/profile")

        plan = client.post(
            f"/cases/{new_case['id']}/datasets/{dataset_id}/plan"
        ).json()

    assert plan["source"] == "deterministic"


def test_the_lineage_survives_the_export_round_trip(tmp_path, monkeypatch) -> None:
    db_path = _env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        template = _finished_template(client)
        new_case = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        ).json()
        package = client.get(f"/cases/{new_case['id']}/export").json()
        restored = client.post("/cases/import", json=package).json()

    assert restored["template_id"] == new_case["template_id"]


def test_a_duplicate_keeps_the_lineage(tmp_path, monkeypatch) -> None:
    db_path = _env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        template = _finished_template(client)
        new_case = client.post(
            "/cases/from-template", json={"template_id": template["id"]}
        ).json()
        copy = client.post(f"/cases/{new_case['id']}/duplicate").json()

    assert copy["template_id"] == template["id"]
