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
