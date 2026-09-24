"""The performance and envelope measurements (AT-28, AT-29, AT-46).

Three of the PRD's numbers that nothing in the project computed:

    AT-28 - 95% of case openings complete within 2 seconds, for benchmark
            cases inside the supported-size envelope.
    AT-29 - 95% of standard profiling operations complete within 5 seconds,
            on the MVP benchmark dataset.
    AT-46 - the application remains stable inside the Analysis Case envelope:
            100 runs, 500 results, 200 findings, 1 000 evidence
            relationships.

All three are measured against a real core over real HTTP, the pattern
verify_golden.py and verify_refine.py established: a fresh uvicorn on a free
port, an isolated data dir and the LLM env vars scrubbed so the deterministic
engines answer and the run needs no network. Nothing is mocked, and no number
is the engine's own claim about itself.

The envelope measurement is the interesting one. AT-46 does not ask that a
5 000 000-row CSV be committed to prove the envelope holds - it asks that the
*case* hold, so the runner builds a case at the boundary itself: ten datasets,
a hundred multi-dataset runs (each binding all ten, so the evidence graph
crosses a thousand edges), two hundred findings. Then it reads every surface a
reopened case offers the analyst - the case, its datasets, runs, findings, the
evidence graph, the decision view, the history, the export and the import round
trip - and requires each one to answer, in budget, at that scale. Stability is
a measured property of the reads at the boundary, not a promise about them.

The benchmark dataset for AT-29 is generated rather than committed: 50 000 rows
and ten columns is the scale the P4 performance task already pinned, with a
date column, a categorical split, a numeric measure, a duplicate and a null in
every tenth row - the shapes a profile has to work on, and small enough that
the measurement is about the profile's own cost rather than the upload's.

    server/.venv/bin/python -m verification.measure.perf

prints the report; `verify_measure.py` folds it into the AT-27..46 measurement
and asserts the thresholds.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SERVER = REPO / "server"
VENV_PYTHON = SERVER / ".venv" / "bin" / "python"
sys.path.insert(0, str(REPO))

from app import limits as limits_module  # noqa: E402  (the PRD's own numbers)

# The PRD's thresholds (sections 32, 33, 50).
CASE_LOADING_THRESHOLD_MS = 2000.0
PROFILING_THRESHOLD_MS = 5000.0

# AT-46's engineering envelope, read from the module that declares them so the
# measurement and the declaration cannot drift apart.
BOUNDARY_RUNS = limits_module.MAX_RUNS
BOUNDARY_FINDINGS = limits_module.MAX_FINDINGS
BOUNDARY_EDGES = limits_module.MAX_EVIDENCE_RELATIONSHIPS
BOUNDARY_DATASETS = 10  # 100 runs x 10 datasets = 1 000 evidence edges

# A read at the boundary that takes longer than this is not stable, it is
# stuck; generous, because the envelope's own reads are the ones a user waits
# on, and the PRD's AT-28 target already covers the common case.
STABILITY_BUDGET_SECONDS = 10.0

# The benchmark dataset's shape (AT-29); the scale P4-PERF-006 pinned.
BENCHMARK_ROWS = 50_000
BENCHMARK_COLUMNS = 10

# How many openings and profiles the percentiles are computed over. Twenty is
# what a p95 needs to be a percentile rather than a single observation.
CASE_LOADING_OPENINGS = 20
PROFILING_ATTEMPTS = 10

LLM_ENV_VARS = frozenset(
    {"DAH_LLM_API_KEY", "OPENAI_API_KEY", "DAH_LLM_BASE_URL", "DAH_LLM_MODEL"}
)


@dataclass
class Timed:
    """One percentile measurement against a PRD threshold."""

    label: str
    p95_ms: float
    threshold_ms: float
    samples: int

    @property
    def ok(self) -> bool:
        return self.samples > 0 and self.p95_ms <= self.threshold_ms


@dataclass
class BoundaryRead:
    """One surface read at the case envelope's boundary."""

    label: str
    status: int
    seconds: float
    expect: int = 200
    detail: str = ""

    @property
    def ok(self) -> bool:
        # Measured against the status this surface answers - the import's 201 is
        # a created case, not a failure, and a read that answered nothing at all
        # is recorded as -1 so it cannot pass by accident.
        return self.status == self.expect and self.seconds <= STABILITY_BUDGET_SECONDS


@dataclass
class BoundaryCase:
    """A case built at AT-46's boundary, and what reading it back cost."""

    case_id: str = ""
    runs: int = 0
    findings: int = 0
    edges: int = 0
    reads: list[BoundaryRead] = field(default_factory=list)

    @property
    def counts_ok(self) -> bool:
        """The case really did reach the envelope, not nearly reach it."""
        return (
            self.runs >= BOUNDARY_RUNS
            and self.findings >= BOUNDARY_FINDINGS
            and self.edges >= BOUNDARY_EDGES
        )

    @property
    def stable(self) -> bool:
        return all(read.ok for read in self.reads)

    @property
    def ok(self) -> bool:
        return self.counts_ok and self.stable

    def failures(self) -> list[str]:
        lines: list[str] = []
        if self.runs < BOUNDARY_RUNS:
            lines.append(
                f"runs: {self.runs} of the {BOUNDARY_RUNS} the envelope allows"
            )
        if self.findings < BOUNDARY_FINDINGS:
            lines.append(
                f"findings: {self.findings} of the {BOUNDARY_FINDINGS} "
                "the envelope allows"
            )
        if self.edges < BOUNDARY_EDGES:
            lines.append(
                f"evidence edges: {self.edges} of the {BOUNDARY_EDGES} "
                "the envelope allows"
            )
        for read in self.reads:
            if not read.ok:
                lines.append(
                    f"{read.label}: status {read.status} in {read.seconds:.2f}s"
                    + (f" - {read.detail}" if read.detail else "")
                )
        return lines


@dataclass
class PerfReport:
    """The AT-28, AT-29 and AT-46 measurements."""

    case_loading: Timed | None = None
    profiling: Timed | None = None
    boundary: BoundaryCase | None = None
    duration_seconds: float = 0.0
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            self.case_loading is not None
            and self.case_loading.ok
            and self.profiling is not None
            and self.profiling.ok
            and self.boundary is not None
            and self.boundary.ok
            and not self.failures
        )

    def failures_text(self) -> str:
        lines = list(self.failures)
        if self.case_loading and not self.case_loading.ok:
            lines.append(
                f"AT-28 case loading: p95 {self.case_loading.p95_ms:.0f}ms "
                f"over the {self.case_loading.threshold_ms:.0f}ms target"
            )
        if self.profiling and not self.profiling.ok:
            lines.append(
                f"AT-29 profiling: p95 {self.profiling.p95_ms:.0f}ms over the "
                f"{self.profiling.threshold_ms:.0f}ms target"
            )
        if self.boundary and not self.boundary.ok:
            lines.extend(f"AT-46 {line}" for line in self.boundary.failures())
        return "\n".join(lines)


def p95(samples: list[float]) -> float:
    """The 95th percentile, interpolated, in the units the samples are in.

    The same computation the web suite's own AT-27 helper makes, implemented
    here once so a server-side measurement and a browser-side one answer the
    same number from the same samples. An empty sample answers zero rather than
    dividing by nothing: a measurement that ran no samples says so.
    """
    if not samples:
        return 0.0
    ordered = sorted(samples)
    rank = 0.95 * (len(ordered) - 1)
    below = int(rank)
    above = min(below + 1, len(ordered) - 1)
    if below == above:
        return ordered[below]
    share = rank - below
    return ordered[below] + (ordered[above] - ordered[below]) * share


class Server:
    """A real core on a free port with an isolated data dir."""

    def __init__(self) -> None:
        self.log_lines: list[str] = []
        self.data_dir = Path(tempfile.mkdtemp(prefix="dah-measure-"))
        env = {
            **os.environ,
            # The deterministic engines answer, and the run needs no network.
            **{name: "" for name in LLM_ENV_VARS},
            "DAH_DATA_DIR": str(self.data_dir),
        }
        self.proc = subprocess.Popen(
            [str(VENV_PYTHON), "-m", "uvicorn", "app.main:app",
             "--port", "0", "--host", "127.0.0.1"],
            cwd=str(SERVER), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        self._pump = threading.Thread(target=self._pump_stdout, daemon=True)
        self._pump.start()
        self.port = self._wait_for_health()

    def _pump_stdout(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.log_lines.append(line)
            if len(self.log_lines) > 500:
                del self.log_lines[:200]

    def server_log_tail(self, lines: int = 20) -> str:
        return "".join(self.log_lines[-lines:])

    def _wait_for_health(self, timeout: float = 60.0) -> int:
        deadline = time.time() + timeout
        port: int | None = None
        while time.time() < deadline and port is None:
            if self.proc.poll() is not None:
                raise RuntimeError(f"server exited early:\n{self.server_log_tail(40)}")
            for line in list(self.log_lines):
                if "Uvicorn running on" in line:
                    port = int(line.rsplit(":", 1)[-1].split()[0])
                    break
            if port is None:
                time.sleep(0.1)
        if port is None:
            raise RuntimeError("server did not announce a port in time")
        while time.time() < deadline:
            if self._get(port, "/health").get("status") == "ok":
                return port
            time.sleep(0.25)
        raise RuntimeError("server never answered /health")

    def _url(self, path: str) -> str:
        # The core serves its routes at the root; the /api prefix is the web
        # dev server's proxy, not the core's own.
        return f"http://127.0.0.1:{self.port}{path}"

    def _get(self, port: int, path: str) -> dict:
        with urllib.request.urlopen(
            urllib.request.Request(f"http://127.0.0.1:{port}{path}"),
            timeout=120,
        ) as res:
            body = res.read()
            return json.loads(body) if body else {}

    def get(self, path: str) -> tuple[int, dict]:
        with urllib.request.urlopen(
            urllib.request.Request(self._url(path)), timeout=180
        ) as res:
            body = res.read()
            return res.status, (json.loads(body) if body else {})

    def post(self, path: str, payload: dict | None = None) -> tuple[int, dict]:
        data = json.dumps(payload).encode() if payload is not None else b""
        req = urllib.request.Request(
            self._url(path), data=data,
            headers={"content-type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as res:
                body = res.read()
                return res.status, (json.loads(body) if body else {})
        except urllib.error.HTTPError as err:
            body = err.read()
            try:
                return err.code, json.loads(body)
            except json.JSONDecodeError:
                return err.code, {"raw": body.decode(errors="replace")}

    def upload(self, path: str, filename: str, content: str) -> tuple[int, dict]:
        boundary = "dah-measure-boundary"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: text/csv\r\n\r\n{content}\r\n--{boundary}--\r\n"
        ).encode()
        req = urllib.request.Request(
            self._url(path), data=body,
            headers={"content-type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as res:
                return res.status, json.loads(res.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def stop(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


def _benchmark_csv(path: Path, rows: int = BENCHMARK_ROWS) -> None:
    """Write the AT-29 benchmark dataset: deterministic, and never committed.

    Fifty thousand rows of the shapes a profile has to work on: a key, a date,
    a categorical split, a numeric measure, plus one duplicate in twenty and a
    null in every tenth - so the profile's own detectors fire on real work
    rather than on clean numbers.
    """
    buf = []
    buf.append(",".join(_BENCHMARK_COLUMNS) + "\n")
    for index in range(rows):
        region = REGIONS[index % len(REGIONS)]
        revenue = round(100.0 + (index % 97) * 7.5, 2)
        units = 1 + (index % 50)
        opened = f"2024-{1 + (index % 12):02d}-{1 + (index % 28):02d}"
        # Every twentieth row repeats the one before it, so the duplicate
        # detector has something to count at scale.
        if index % 20 == 19:
            buf.append(buf[-1])
            continue
        # Every tenth row carries a null, so missingness is part of the
        # profile's workload rather than absent from it.
        revenue_text = "" if index % 10 == 9 else repr(revenue)
        buf.append(
            f"{index},{opened},{region},{revenue_text},{units},"
            f"{'yes' if index % 2 else 'no'},{index % 5},{1000 + index},"
            f"channel-{index % 4},{round(1.0 + (index % 9) * 0.5, 2)}\n"
        )
    path.write_text("".join(buf))


_BENCHMARK_COLUMNS = [
    "order_id", "opened", "region", "revenue", "units",
    "flagged", "bucket", "customer_id", "channel", "score",
]
REGIONS = ["north", "south", "east", "west", "central"]


def _envelope_datasets() -> list[str]:
    """Ten tiny CSVs sharing a key, so a hundred runs cross a thousand edges."""
    made = []
    for slot in range(BOUNDARY_DATASETS):
        region = REGIONS[slot % len(REGIONS)]
        made.append(
            "id,region,revenue\n"
            + f"1,{region},{100 * (slot + 1)}.0\n"
            + f"2,{region},{200 * (slot + 1)}.0\n"
            + f"3,{region},{300 * (slot + 1)}.0\n"
        )
    return made


def _boundary_sql(datasets: int) -> str:
    """A read-only query with one placeholder per dataset (P3-DATA-003).

    A count over the join of all of them: the work is real - the engine binds
    and reads every file - and the result stays one row, so a hundred of these
    cost seconds rather than materialising a hundred result sets.
    """
    refs = ", ".join(
        f"read_csv_auto(?) {chr(ord('a') + index)}" for index in range(datasets)
    )
    return f"SELECT COUNT(*) AS n FROM {refs}"


def measure_case_loading(server: Server, case_id: str) -> Timed:
    """AT-28: open a benchmark case repeatedly and take the 95th percentile.

    An opening is what the workspace actually does when a case is opened: the
    case itself, its datasets, its runs, its findings, the decision view and
    the history - one user-visible wait, measured as one. The p95 is over the
    composite, which is the number the analyst experiences.
    """
    surfaces = [
        "",
        "/datasets",
        "/runs",
        "/findings",
        "/decision",
        "/history",
    ]
    samples: list[float] = []
    for _ in range(CASE_LOADING_OPENINGS):
        started = time.perf_counter()
        for surface in surfaces:
            status, _body = server.get(f"/cases/{case_id}{surface}")
            if status != 200:
                raise RuntimeError(
                    f"GET /cases/{case_id}{surface} answered {status}"
                )
        samples.append((time.perf_counter() - started) * 1000.0)
    return Timed(
        label="case opening (six surfaces, 95th percentile)",
        p95_ms=p95(samples),
        threshold_ms=CASE_LOADING_THRESHOLD_MS,
        samples=len(samples),
    )


def measure_profiling(server: Server, rows: int = BENCHMARK_ROWS) -> Timed:
    """AT-29: profile the benchmark dataset and take the 95th percentile.

    The dataset is generated into a temp dir each run, so the measurement
    never depends on a committed fixture and always profiles the shape the
    threshold is about.
    """
    with tempfile.TemporaryDirectory(prefix="dah-benchmark-") as temp:
        csv_path = Path(temp) / "benchmark.csv"
        _benchmark_csv(csv_path, rows)
        case_id = server.post("/cases", {"question": "benchmark", "dataset": "benchmark.csv"})[1]["id"]
        status, attached = server.upload(
            f"/cases/{case_id}/datasets",
            "benchmark.csv",
            csv_path.read_text(),
        )
        if status != 201:
            raise RuntimeError(f"the benchmark dataset did not attach: {status} {attached}")
        dataset_id = attached["id"]
        samples: list[float] = []
        for _ in range(PROFILING_ATTEMPTS):
            started = time.perf_counter()
            status, _profile = server.post(
                f"/cases/{case_id}/datasets/{dataset_id}/profile"
            )
            if status != 201:
                raise RuntimeError(f"profiling answered {status}")
            samples.append((time.perf_counter() - started) * 1000.0)
        return Timed(
            label=f"profiling a {rows:,}-row dataset (95th percentile)",
            p95_ms=p95(samples),
            threshold_ms=PROFILING_THRESHOLD_MS,
            samples=len(samples),
        )


def build_boundary_case(server: Server) -> BoundaryCase:
    """Build a case at AT-46's boundary and read every surface back.

    The envelope's own numbers are the target: a hundred runs, two hundred
    findings and an evidence graph crossing a thousand edges. Reaching them is
    the first half of the measurement; the second is that the case a user would
    reopen at that scale still answers, in budget, on every surface.
    """
    case_id = server.post(
        "/cases",
        {"question": "the boundary case", "dataset": "envelope.csv"},
    )[1]["id"]

    dataset_ids: list[str] = []
    for slot, content in enumerate(_envelope_datasets()):
        status, attached = server.upload(
            f"/cases/{case_id}/datasets", f"envelope{slot}.csv", content
        )
        if status != 201:
            raise RuntimeError(f"dataset {slot} did not attach: {status} {attached}")
        dataset_ids.append(attached["id"])

    sql = _boundary_sql(len(dataset_ids))
    run_ids: list[str] = []
    for _ in range(BOUNDARY_RUNS):
        status, run = server.post(
            f"/cases/{case_id}/runs", {"dataset_ids": dataset_ids, "sql": sql}
        )
        if status != 201:
            raise RuntimeError(f"a boundary run answered {status} {run}")
        run_ids.append(run["id"])

    for index, run_id in enumerate(run_ids):
        # Two findings per run, so two hundred findings sit on a hundred runs.
        for which in range(2):
            status, _finding = server.post(
                f"/cases/{case_id}/findings",
                {
                    "run_id": run_id,
                    "statement": f"finding {index}.{which} over the boundary",
                    "interpretation": "measured, not assumed",
                    "caveat": "the envelope's own boundary",
                },
            )
            if status != 201:
                raise RuntimeError(f"a boundary finding answered {status}")

    boundary = BoundaryCase(
        case_id=case_id,
        runs=len(run_ids),
        findings=BOUNDARY_RUNS * 2,
        edges=0,
    )

    def read(label: str, path: str, expect: int = 200) -> dict | None:
        started = time.perf_counter()
        try:
            status, body = server.get(path)
        except urllib.error.HTTPError as err:
            boundary.reads.append(
                BoundaryRead(label, err.code, time.perf_counter() - started, str(err))
            )
            return None
        # A read's `ok` is measured against the status this surface answers,
        # not against 200 in the abstract: the import's 201 is a created case,
        # not a failure.
        boundary.reads.append(
            BoundaryRead(
                label, status, time.perf_counter() - started, expect=expect,
                detail="" if status == expect
                else f"answered {status}, expected {expect}",
            )
        )
        return body if status == expect else None

    case = read("GET /cases/{id}", f"/cases/{case_id}")
    datasets = read("GET /cases/{id}/datasets", f"/cases/{case_id}/datasets")
    runs = read("GET /cases/{id}/runs", f"/cases/{case_id}/runs")
    findings = read("GET /cases/{id}/findings", f"/cases/{case_id}/findings")
    graph = read("GET /cases/{id}/evidence-graph", f"/cases/{case_id}/evidence-graph")
    read("GET /cases/{id}/decision", f"/cases/{case_id}/decision")
    read("GET /cases/{id}/history", f"/cases/{case_id}/history")
    exported = read("GET /cases/{id}/export", f"/cases/{case_id}/export")

    # The counts are the envelope's own claim, checked against what the core
    # reports rather than against what the runner asked for.
    if runs is not None:
        boundary.runs = min(boundary.runs, len(runs))
    if findings is not None:
        boundary.findings = min(boundary.findings, len(findings))
    if graph is not None:
        boundary.edges = len(graph.get("edges", []))
        orphans = graph.get("orphan_findings", [])
        if orphans:
            boundary.reads.append(
                BoundaryRead(
                    "evidence graph orphans", 200, 0.0,
                    f"{len(orphans)} finding(s) trace to no dataset",
                )
            )
    if datasets is not None and len(datasets) != BOUNDARY_DATASETS:
        boundary.reads.append(
            BoundaryRead(
                "datasets", 200, 0.0,
                f"{len(datasets)} attached, {BOUNDARY_DATASETS} expected",
            )
        )
    if case is None:
        boundary.reads.append(BoundaryRead("case", 0, 0.0, "the case itself did not answer"))

    # The round trip is the envelope's portability test: a case this heavy
    # must still import, or the envelope is a dead end rather than a boundary.
    if exported is not None:
        started = time.perf_counter()
        status, _restored = server.post("/cases/import", exported)
        # 201: the import creates a case, and the round trip is the envelope's
        # portability test - a case this heavy must still restore, or the
        # boundary is a dead end rather than a limit.
        boundary.reads.append(
            BoundaryRead(
                "POST /cases/import", status, time.perf_counter() - started,
                expect=201,
                detail="" if status == 201
                else f"answered {status}, expected 201",
            )
        )
    return boundary


def measure_envelope_declaration() -> list[str]:
    """AT-45's declaration half: the limits the core publishes are the PRD's.

    In-process, because the declaration is a module of constants rather than a
    running computation. The comparison is against the PRD's literal numbers
    (sections 49 and 50), not against the module's own constants, so an
    envelope that drifts from the specification fails here before anyone
    measures against it.
    """
    failures: list[str] = []
    datasets = limits_module.dataset_limits()
    for name, rows in (("csv", 5_000_000), ("parquet", 5_000_000), ("xlsx", 500_000)):
        if datasets[name]["max_rows"] != rows:
            failures.append(
                f"{name}: {datasets[name]['max_rows']:,} rows is not the "
                f"PRD's {rows:,}"
            )
        if datasets[name]["max_columns"] != 100:
            failures.append(
                f"{name}: {datasets[name]['max_columns']} columns is not "
                "the PRD's 100"
            )
    cases = limits_module.case_limits()
    expected = {
        "max_runs": 100,
        "max_results": 500,
        "max_findings": 200,
        "max_evidence_relationships": 1_000,
    }
    for key, want in expected.items():
        if cases.get(key) != want:
            failures.append(
                f"{key}: {cases.get(key)} is not the PRD's envelope of {want}"
            )
    return failures


@dataclass
class EnvelopeRefusal:
    """AT-45's refusal half: beyond the envelope is a clear no, never a hang.

    A refusal at the column limit is exercised at the envelope's real default -
    101 columns is a file, not a fixture. The row limit is exercised at a
    tightened value, because the PRD's own five million rows would be the
    fixture the refusal exists to avoid loading; the comparison, the sentence
    and the cleanup are the same code at any value, which the suite tests at
    the real number and this measures at a runnable one.
    """

    too_wide: bool = False
    too_tall: bool = False
    sentence_wide: str = ""
    sentence_tall: str = ""

    @property
    def ok(self) -> bool:
        return self.too_wide and self.too_tall


def measure_envelope_refusal() -> EnvelopeRefusal:
    """Refuse a dataset past each of AT-45's limits, and keep the sentence.

    In-process: the refusal is `check_dataset_envelope`, the same function the
    attach endpoint calls the moment a file lands on disk, so a measurement
    here is the path a six-million-row upload takes rather than a claim about
    it.
    """
    import io

    result = EnvelopeRefusal()
    with tempfile.TemporaryDirectory(prefix="dah-envelope-") as temp:
        wide = Path(temp) / "wide.csv"
        wide.write_text(",".join(f"c{i}" for i in range(limits_module.MAX_COLUMNS + 1)) + "\n")
        try:
            limits_module.check_dataset_envelope(str(wide), "csv")
        except limits_module.EnvelopeExceeded as err:
            result.too_wide = True
            result.sentence_wide = str(err)

        # The row path at a tightened limit, restored whatever happens.
        tall = Path(temp) / "tall.csv"
        tall.write_text("a,b,c\n" + "1,2,3\n" * 4)
        saved = limits_module.MAX_ROWS
        limits_module.MAX_ROWS = 3
        try:
            limits_module.check_dataset_envelope(str(tall), "csv")
        except limits_module.EnvelopeExceeded as err:
            result.too_tall = True
            result.sentence_tall = str(err)
        finally:
            limits_module.MAX_ROWS = saved
    return result


def run_perf(server: Server | None = None) -> PerfReport:
    """Measure AT-28, AT-29 and AT-46 against a real core.

    Owns its server when none is given, so the module is runnable on its own;
    a caller that already has a server can pass it and this reads no second
    port.
    """
    started = time.perf_counter()
    owns = server is None
    if owns:
        server = Server()
    report = PerfReport()
    try:
        boundary = build_boundary_case(server)
        report.boundary = boundary
        # AT-28 is measured on the heaviest case in the envelope - the boundary
        # case - because a percentile over an empty case measures nothing.
        report.case_loading = measure_case_loading(server, boundary.case_id)
        report.profiling = measure_profiling(server)
    finally:
        if owns:
            server.stop()
    report.duration_seconds = time.perf_counter() - started
    return report


def format_report(report: PerfReport) -> str:
    """A plain-text report for the file and the log."""
    lines = [
        "AT-28 / AT-29 / AT-46 - performance and the case envelope",
        "(measured against a real core over HTTP, no LLM, no network)",
        "",
    ]

    def timed(one: Timed | None, at: str) -> None:
        if one is None:
            lines.append(f"{at}: not measured")
            return
        lines.append(
            f"{at}  {one.label}: {one.p95_ms:.0f}ms "
            f"(target <= {one.threshold_ms:.0f}ms over {one.samples} samples)  "
            f"{'PASS' if one.ok else 'FAIL'}"
        )

    timed(report.case_loading, "AT-28")
    timed(report.profiling, "AT-29")
    boundary = report.boundary
    if boundary is not None:
        lines.append(
            f"AT-46  case at the envelope: {boundary.runs} runs, "
            f"{boundary.findings} findings, {boundary.edges} evidence edges  "
            f"{'PASS' if boundary.ok else 'FAIL'}"
        )
        for read in boundary.reads:
            lines.append(
                f"        {'ok  ' if read.ok else 'FAIL'}  {read.label}  "
                f"{read.status} in {read.seconds:.2f}s"
                + (f" - {read.detail}" if read.detail else "")
            )
    failures = report.failures_text()
    if failures:
        lines.append("")
        lines.append("threshold failures:")
        for failure in failures.splitlines():
            lines.append(f"  - {failure}")
    lines.append(f"\nmeasured in {report.duration_seconds:.0f}s")
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_report(run_perf()))
