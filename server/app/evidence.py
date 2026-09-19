"""Case-wide evidence graph and claim-to-source tracing (P3-EVIDENCE-006).

The single-finding chain (`GET .../findings/{id}/evidence`) answers "what backs
*this* claim". This module answers the case-level question a reviewer actually
asks: which claims exist, what each one rests on, and whether every finding in
the case traces back to stored data.

The graph is built from the persisted rows, never stored - it is a pure
projection of the case, so it cannot drift from what is on disk. Nodes are the
case's artifacts; edges say how one was derived from another:

    finding --anchored_on-->  run
    run    --queries-->      dataset   (one edge per dataset a run touches)
    chart  --rendered_from--> run
    plan   --planned_from-->  dataset

A finding that reaches no dataset is a claim with no source; `orphan_findings`
lists those, which is what makes the graph a review tool rather than a diagram.
"""

import json
from typing import Any

NODE_KINDS = ("dataset", "run", "chart", "plan", "finding")

EDGE_ANCHORED_ON = "anchored_on"
EDGE_QUERIES = "queries"
EDGE_RENDERED_FROM = "rendered_from"
EDGE_PLANNED_FROM = "planned_from"


def _dataset_ids_of(run_row) -> list[str]:
    """Every dataset a run bound, from its recorded list (P3-DATA-003)."""
    raw = run_row["dataset_ids_json"] if "dataset_ids_json" in run_row.keys() else None
    if raw:
        try:
            listed = json.loads(raw)
            if listed:
                return [str(item) for item in listed]
        except json.JSONDecodeError:
            pass
    return [run_row["dataset_id"]] if run_row["dataset_id"] else []


def build_evidence_graph(db, case_id: str) -> dict[str, Any]:
    """Project a case into its evidence graph.

    Raises ValueError when the case has no artifacts to graph, so the caller
    can answer 400 rather than returning an empty diagram.
    """
    datasets = db.execute(
        "SELECT id, filename, format, stored_path, created_at FROM datasets "
        "WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall()
    dataset_names = {row["id"]: row["filename"] for row in datasets}

    runs = db.execute(
        "SELECT id, dataset_id, dataset_ids_json, kind, sql, code, executed_at "
        "FROM runs WHERE case_id = ? ORDER BY executed_at",
        (case_id,),
    ).fetchall()

    charts = db.execute(
        "SELECT id, run_id, kind, title, created_at FROM charts "
        "WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall()

    plans = db.execute(
        "SELECT id, dataset_id, question, source, created_at FROM plans "
        "WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall()

    findings = db.execute(
        "SELECT id, run_id, statement, validation_status, created_at "
        "FROM findings WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall()

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []

    for row in datasets:
        nodes.append(
            {
                "id": row["id"],
                "kind": "dataset",
                "label": row["filename"],
                "detail": f"{row['format']} file",
                "created_at": row["created_at"],
            }
        )
    for row in runs:
        source = row["sql"] if row["kind"] == "sql" else row["code"]
        nodes.append(
            {
                "id": row["id"],
                "kind": "run",
                "label": f"{row['kind']} run",
                "detail": (source or "")[:160],
                "created_at": row["executed_at"],
            }
        )
        for dataset_id in _dataset_ids_of(row):
            edges.append(
                {
                    "source": row["id"],
                    "target": dataset_id,
                    "relation": EDGE_QUERIES,
                }
            )
    for row in charts:
        nodes.append(
            {
                "id": row["id"],
                "kind": "chart",
                "label": row["title"] or f"{row['kind']} chart",
                "detail": f"{row['kind']} over the run's stored result",
                "created_at": row["created_at"],
            }
        )
        if row["run_id"]:
            edges.append(
                {
                    "source": row["id"],
                    "target": row["run_id"],
                    "relation": EDGE_RENDERED_FROM,
                }
            )
    for row in plans:
        nodes.append(
            {
                "id": row["id"],
                "kind": "plan",
                "label": row["question"],
                "detail": f"source: {row['source']}",
                "created_at": row["created_at"],
            }
        )
        if row["dataset_id"]:
            edges.append(
                {
                    "source": row["id"],
                    "target": row["dataset_id"],
                    "relation": EDGE_PLANNED_FROM,
                }
            )
    for row in findings:
        nodes.append(
            {
                "id": row["id"],
                "kind": "finding",
                "label": row["statement"],
                "detail": f"validation: {row['validation_status']}",
                "created_at": row["created_at"],
            }
        )
        if row["run_id"]:
            edges.append(
                {
                    "source": row["id"],
                    "target": row["run_id"],
                    "relation": EDGE_ANCHORED_ON,
                }
            )

    # Claim-to-source: walk each finding out to the data it stands on.
    run_by_id = {row["id"]: row for row in runs}
    traces: list[dict[str, Any]] = []
    orphan_findings: list[str] = []
    for row in findings:
        run = run_by_id.get(row["run_id"])
        if run is None:
            orphan_findings.append(row["id"])
            traces.append(
                {
                    "finding_id": row["id"],
                    "statement": row["statement"],
                    "validation_status": row["validation_status"],
                    "hops": [
                        {
                            "id": row["id"],
                            "kind": "finding",
                            "label": row["statement"],
                        }
                    ],
                    "reaches_source": False,
                }
            )
            continue
        dataset_ids = _dataset_ids_of(run)
        hops = [
            {"id": row["id"], "kind": "finding", "label": row["statement"]},
            {
                "id": run["id"],
                "kind": "run",
                "label": f"{run['kind']} run",
                "detail": (run["sql"] or run["code"] or "")[:160],
            },
        ]
        for dataset_id in dataset_ids:
            hops.append(
                {
                    "id": dataset_id,
                    "kind": "dataset",
                    "label": dataset_names.get(dataset_id, dataset_id),
                }
            )
        traces.append(
            {
                "finding_id": row["id"],
                "statement": row["statement"],
                "validation_status": row["validation_status"],
                "hops": hops,
                "reaches_source": True,
            }
        )

    if not nodes:
        raise ValueError(
            "this case has no artifacts yet - attach data, run an analysis, or "
            "record a finding to build an evidence graph"
        )

    return {
        "case_id": case_id,
        "nodes": nodes,
        "edges": edges,
        "traces": traces,
        "orphan_findings": orphan_findings,
        "counts": {
            "datasets": len(datasets),
            "runs": len(runs),
            "charts": len(charts),
            "plans": len(plans),
            "findings": len(findings),
            "edges": len(edges),
        },
    }
