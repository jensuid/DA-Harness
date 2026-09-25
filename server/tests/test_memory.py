"""Cross-case recall tests for P6-MEMORY-001.

A case could already cite its own artifacts. These cover the new capability:
an answer may cite a *previous* case's finding, an invented cross-case citation
is rejected exactly as an invented column is, a case with a similar question but
nothing to recall is not dragged in, and the read path writes nothing.

Every case is built through the API so the recall runs against real rows rather
than rows a test inserted by hand.
"""

from fastapi.testclient import TestClient

from app.main import app, get_db
from app.db import get_connection
import app.db as db_module
import app.assistant as assistant_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"
SQL = (
    "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
    "GROUP BY region ORDER BY region"
)


def _temp_env(tmp_path, monkeypatch):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:  # pragma: no cover
            yield connection

    app.dependency_overrides[get_db] = override
    monkeypatch.delenv("DAH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def _case_with_finding(
    client,
    question,
    filename="sales.csv",
    statement="Duplicate rows in sales.csv inflated revenue by 12 percent.",
):
    """A case that has walked far enough to carry a validated finding."""
    case_id = client.post(
        "/cases", json={"question": question, "dataset": filename}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": (filename, CSV, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    run_id = client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
    ).json()["id"]
    client.post(
        f"/cases/{case_id}/findings",
        json={
            "run_id": run_id,
            "statement": statement,
            "interpretation": "Each region's total counts some orders twice.",
            "caveat": "Only the north region is affected.",
            "grounds": ["run:1"],
        },
    )
    client.post(f"/cases/{case_id}/findings/{_finding_id(client, case_id)}/validate")
    return case_id


def _finding_id(client, case_id):
    rows = client.get(f"/cases/{case_id}/findings").json()
    return rows[-1]["id"]


def _empty_case(client, question, filename="newfile.csv"):
    return client.post(
        "/cases", json={"question": question, "dataset": filename}
    ).json()["id"]


class _RecallingAssistant:
    """An LLM stand-in that cites a previous case it was told about.

    Proves memory reaches the LLM and that a `case:` ground validates.
    """

    def __init__(self, seen):
        self._seen = seen

    def answer(self, message, history, facts):
        self._seen["memory"] = facts.get("memory") or []
        memory = facts.get("memory") or []
        if not memory:
            # No memory to cite: answer about the case itself.
            return {
                "answer": "Nothing to recall.",
                "grounds": [f"dataset:{facts['datasets'][0]['label']}"]
                if facts.get("datasets")
                else [],
            }
        first = memory[0]
        return {
            "answer": f"As found earlier, {first['findings'][0]['statement']}",
            "grounds": [f"case:{first['case_id']}", f"finding:{first['findings'][0]['id']}"],
        }


def test_an_empty_case_answers_from_a_previous_finding(tmp_path, monkeypatch):
    """The headline behaviour: a question a prior case answered is answered from it."""
    _temp_env(tmp_path, monkeypatch)
    client = TestClient(app)
    _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )
    later = _empty_case(client, "Why did revenue decline in the Q2 sales file?")

    turn = client.post(
        f"/cases/{later}/chat",
        json={"message": "Why did revenue decline in the Q2 sales file?"},
    ).json()

    assert turn["source"] == "deterministic"
    assert "Duplicate rows" in turn["answer"]
    assert any(g.startswith("case:") for g in turn["grounds"])
    assert any(g.startswith("finding:") for g in turn["grounds"])


def test_the_cited_case_and_finding_are_real_rows(tmp_path, monkeypatch):
    """A cross-case ground must resolve to a case and finding that exist."""
    _temp_env(tmp_path, monkeypatch)
    client = TestClient(app)
    earlier = _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )
    later = _empty_case(client, "Why did revenue decline in the Q2 sales file?")

    turn = client.post(
        f"/cases/{later}/chat",
        json={"message": "Why did revenue decline in the Q2 sales file?"},
    ).json()
    case_ground = next(g for g in turn["grounds"] if g.startswith("case:"))
    finding_ground = next(g for g in turn["grounds"] if g.startswith("finding:"))

    # The cited case is the earlier one, and the finding belongs to it.
    assert case_ground == f"case:{earlier}"
    db_path = db_module.DATA_DIR.parent / "test.db"
    with get_connection(db_path) as db:
        case = db.execute(
            "SELECT id FROM cases WHERE id = ?", (case_ground[len("case:"):],)
        ).fetchone()
        finding = db.execute(
            "SELECT id, case_id FROM findings WHERE id = ?",
            (finding_ground[len("finding:"):],),
        ).fetchone()
    assert case is not None
    assert finding is not None
    assert finding["case_id"] == earlier


def test_an_invented_cross_case_citation_is_rejected(tmp_path, monkeypatch):
    """`case:does-not-exist` fails validation, exactly as an invented column does."""
    _temp_env(tmp_path, monkeypatch)
    client = TestClient(app)
    _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )
    later = _empty_case(client, "Why did revenue decline in the Q2 sales file?")

    with get_connection(db_module.DATA_DIR.parent / "test.db") as db:
        facts = assistant_module.summarize_case(
            db, later, "Why did revenue decline in the Q2 sales file?"
        )

    problems = assistant_module.validate_answer(
        {"answer": "A prior case found the same thing.", "grounds": ["case:nope"]},
        facts,
    )
    assert any("does not have" in problem for problem in problems)


def test_an_invented_prior_finding_is_rejected(tmp_path, monkeypatch):
    """A finding id that does not exist cannot be cited as memory either."""
    _temp_env(tmp_path, monkeypatch)
    client = TestClient(app)
    _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )
    later = _empty_case(client, "Why did revenue decline in the Q2 sales file?")

    with get_connection(db_module.DATA_DIR.parent / "test.db") as db:
        facts = assistant_module.summarize_case(
            db, later, "Why did revenue decline in the Q2 sales file?"
        )

    problems = assistant_module.validate_answer(
        {"answer": "A prior case found the same thing.", "grounds": ["finding:nope"]},
        facts,
    )
    assert any("does not have" in problem for problem in problems)


def test_a_case_with_nothing_to_recall_says_so(tmp_path, monkeypatch):
    """A prior case with a similar question but no shared substance is not cited."""
    _temp_env(tmp_path, monkeypatch)
    client = TestClient(app)
    # A real finding, but about weather - its question, dataset label and
    # statement share no content word with the revenue question.
    _case_with_finding(
        client,
        question="Were weather patterns normal in Norway?",
        filename="climate.csv",
        statement="Rainfall in Bergen exceeded the seasonal average.",
    )
    later = _empty_case(client, "Why did revenue decline in the Q2 sales file?")

    turn = client.post(
        f"/cases/{later}/chat",
        json={"message": "Why did revenue decline in the Q2 sales file?"},
    ).json()

    # No memory matched, so the answer is about the case's own state, not a
    # stretched recollection.
    assert "stage" in turn["answer"]
    assert not any(g.startswith("case:") for g in turn["grounds"])


def test_a_case_with_its_own_artifacts_reports_their_state_first(tmp_path, monkeypatch):
    """A case with its own artifacts is not answered from memory without being asked.

    It answers from its own state - a column stat here, since the question names
    "revenue" - rather than reaching for a previous case.
    """
    _temp_env(tmp_path, monkeypatch)
    client = TestClient(app)
    _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )
    later = _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )

    turn = client.post(
        f"/cases/{later}/chat",
        json={"message": "Why did revenue decline in the Q2 sales file?"},
    ).json()

    # Own state: the question names "revenue", so its own column stat answers.
    assert "revenue" in turn["answer"]
    assert not any(g.startswith("case:") for g in turn["grounds"])


def test_asking_about_prior_work_recalls_even_with_artifacts(tmp_path, monkeypatch):
    """An explicit question about earlier work recalls regardless of own state."""
    _temp_env(tmp_path, monkeypatch)
    client = TestClient(app)
    _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )
    later = _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )

    turn = client.post(
        f"/cases/{later}/chat",
        json={"message": "What did I find before about the revenue decline?"},
    ).json()

    assert "Duplicate rows" in turn["answer"]
    assert any(g.startswith("case:") for g in turn["grounds"])


def test_the_llm_receives_memory_and_its_citation_validates(tmp_path, monkeypatch):
    """Memory reaches the LLM path and a `case:` ground is accepted."""
    _temp_env(tmp_path, monkeypatch)
    seen: dict = {}
    monkeypatch.setattr(
        assistant_module,
        "_configured_llm",
        lambda: _RecallingAssistant(seen),
    )
    client = TestClient(app)
    _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )
    later = _empty_case(client, "Why did revenue decline in the Q2 sales file?")

    turn = client.post(
        f"/cases/{later}/chat",
        json={"message": "Why did revenue decline in the Q2 sales file?"},
    ).json()

    assert turn["source"] == "llm"
    assert seen["memory"], "the LLM must be told about the prior case"
    assert any(g.startswith("case:") for g in turn["grounds"])


def test_a_malformed_llm_memory_answer_falls_back_to_deterministic(tmp_path, monkeypatch):
    """An LLM that invents a prior case degrades to the deterministic answer."""
    _temp_env(tmp_path, monkeypatch)

    class _Inventing:
        def answer(self, message, history, facts):
            return {
                "answer": "A prior case found the same anomaly.",
                "grounds": ["case:does-not-exist"],
            }

    monkeypatch.setattr(assistant_module, "_configured_llm", lambda: _Inventing())
    client = TestClient(app)
    _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )
    later = _empty_case(client, "Why did revenue decline in the Q2 sales file?")

    turn = client.post(
        f"/cases/{later}/chat",
        json={"message": "Why did revenue decline in the Q2 sales file?"},
    ).json()

    assert turn["source"] == "deterministic fallback"
    assert "Duplicate rows" in turn["answer"]


def test_recalling_writes_nothing(tmp_path, monkeypatch):
    """Memory is a projection; answering from it must not insert any row."""
    _temp_env(tmp_path, monkeypatch)
    client = TestClient(app)
    _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )
    later = _empty_case(client, "Why did revenue decline in the Q2 sales file?")

    db_path = db_module.DATA_DIR.parent / "test.db"
    with get_connection(db_path) as db:
        before_cases = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        before_findings = db.execute("SELECT COUNT(*) FROM findings").fetchone()[0]

    client.post(
        f"/cases/{later}/chat",
        json={"message": "Why did revenue decline in the Q2 sales file?"},
    )

    with get_connection(db_path) as db:
        after_cases = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        after_findings = db.execute("SELECT COUNT(*) FROM findings").fetchone()[0]

    assert (before_cases, before_findings) == (after_cases, after_findings)


def test_memory_excludes_the_case_itself(tmp_path, monkeypatch):
    """A case is never recalled as its own previous case."""
    _temp_env(tmp_path, monkeypatch)
    client = TestClient(app)
    case_id = _case_with_finding(
        client, "Why did revenue decline in the Q2 sales file?", "sales.csv"
    )

    with get_connection(db_module.DATA_DIR.parent / "test.db") as db:
        facts = assistant_module.summarize_case(
            db, case_id, "Why did revenue decline in the Q2 sales file?"
        )

    assert all(item["case_id"] != case_id for item in facts["memory"])
