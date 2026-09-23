"""The question-refinement suite (P8-REFINE-007): AT-04, measured.

Four numbers the PRD asks for and nothing previously computed:

    AT-04  >= 95% of cases preserve the original question
           >= 90% produce a semantically relevant refinement
            0  silent overwrites
            0  fabricated data references

Measured against a real server over real HTTP, the pattern verify_golden.py
established: a fresh uvicorn on a free port, an isolated data dir, and the LLM
env vars scrubbed so the deterministic engine answers and the run needs no
network. Nothing is mocked.

Relevance is measured mechanically, not by taste, and the two halves of the
measurement are what makes it honest:

- the refined question keeps the original's subject terms (so it is the same
  question, sharpened rather than replaced), and
- it names at least one real column from the profile (so it is sharpened
  *by the data*, which is the only kind of refinement this product is allowed
  to offer).

A proposal that reworded a question into a neighbouring one would pass a
readability judgment and fail this one. A decline counts against the relevance
rate only when the corpus expected a proposal - an already-specific question
that the engine wisely left alone is not a failure, and is marked so in the
corpus.

The decisions are driven at volume: accept, edit and keep-original are each
exercised across the corpus, and the original question is checked after every
one of them, including the accept that replaced it on the case row.

    server/.venv/bin/python verification/refine/verify_refine.py

Exit 0 only when all four thresholds hold; the report is written to
verification/refine/REPORT.md either way, and the same four numbers are
asserted in server/tests/test_refine.py so a regression fails a test rather
than a report nobody reads.
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
DATASETS_DIR = Path(__file__).resolve().parent
REPORT_PATH = DATASETS_DIR / "REPORT.md"

sys.path.insert(0, str(REPO))

from verification.refine.cases import (  # noqa: E402
    CASES,
    NO_PROFILE_COUNT,
    PATH_ACCEPT,
    PATH_EDIT,
    PATH_KEEP,
    PATH_PENDING,
    RefineCase,
)

# AT-04's stated thresholds.
THRESHOLD_PRESERVE = 0.95
THRESHOLD_RELEVANT = 0.90
THRESHOLD_OVERWRITES = 0
THRESHOLD_FABRICATIONS = 0


@dataclass
class CaseResult:
    case: RefineCase
    proposed: bool = False
    refined: str = ""
    grounds: list[dict] = field(default_factory=list)
    preserved: bool = False
    relevant: bool = False
    overwritten: bool = False
    fabricated: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class Measurement:
    cases: int
    proposals: int
    declines: int
    preserved: int
    relevant: int
    silent_overwrites: int
    fabrications: int
    results: list[CaseResult] = field(default_factory=list)

    @property
    def preserve_rate(self) -> float:
        return self.preserved / self.cases if self.cases else 0.0

    @property
    def relevant_rate(self) -> float:
        # Relevant is measured over the cases that should have produced a
        # proposal. A decline the corpus expected is not a relevance failure,
        # and a proposal the corpus expected to decline is one.
        judged = [
            r for r in self.results
            if (r.case.expect == "proposal") or (r.proposed and r.case.expect == "decline")
        ]
        return self.relevant / len(judged) if judged else 0.0

    @property
    def passed(self) -> bool:
        return (
            self.preserve_rate >= THRESHOLD_PRESERVE
            and self.relevant_rate >= THRESHOLD_RELEVANT
            and self.silent_overwrites <= THRESHOLD_OVERWRITES
            and self.fabrications <= THRESHOLD_FABRICATIONS
        )


class Server:
    """A real core on a free port with an isolated data dir."""

    def __init__(self) -> None:
        self.log_lines: list[str] = []
        self.data_dir = Path(tempfile.mkdtemp(prefix="dah-refine-"))
        env = {
            **os.environ,
            # The deterministic engines answer, and the run needs no network.
            "DAH_LLM_API_KEY": "",
            "DAH_LLM_BASE_URL": "",
            "DAH_LLM_MODEL": "",
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

    def get(self, path: str) -> dict:
        return self._get(self.port, path)

    def post(self, path: str, payload: dict | None = None) -> tuple[int, dict]:
        data = json.dumps(payload).encode() if payload is not None else b""
        req = urllib.request.Request(
            self._url(path), data=data,
            headers={"content-type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as res:
                body = res.read()
                return res.status, (json.loads(body) if body else {})
        except urllib.error.HTTPError as err:
            body = err.read()
            try:
                return err.code, json.loads(body)
            except json.JSONDecodeError:
                return err.code, {"raw": body.decode(errors="replace")}

    def upload(self, path: str, filename: str, content: str) -> dict:
        boundary = "dah-refine-boundary"
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
        with urllib.request.urlopen(req, timeout=180) as res:
            return json.loads(res.read())

    def stop(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


def _subject_terms(question: str) -> list[str]:
    """The words carrying the question's topic; copied from the engine's own
    guard so the suite measures the same notion of relevance the gate enforces
    rather than a second, driftier one."""
    import re

    stopwords = {
        "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to",
        "for", "with", "by", "is", "are", "was", "were", "be", "been",
        "being", "do", "does", "did", "what", "which", "who", "whom", "whose",
        "why", "how", "when", "where", "there", "their", "they", "them",
        "this", "that", "these", "those", "from", "as", "into", "about",
        "have", "has", "had", "not", "no", "so", "if", "it", "its", "our",
        "we", "you", "your", "my", "me", "i", "can", "could", "would",
        "should", "will", "may", "might", "any", "all", "some", "more",
        "most", "less", "least", "than", "then", "over", "under", "between",
        "across", "per", "each", "one", "two", "three", "very", "much",
        "many", "such", "also", "just", "only", "even",
    }
    return [
        word
        for word in re.findall(r"[A-Za-z0-9]+", (question or "").lower())
        if len(word) > 2 and word not in stopwords
    ]


def _measure(server: Server) -> Measurement:
    results: list[CaseResult] = []

    for index, case in enumerate(CASES):
        result = CaseResult(case=case)
        status, body = server.post("/cases", {"question": case.question,
                                              "dataset": case.dataset})
        if status != 201:
            raise RuntimeError(f"could not create case for '{case.question}': {body}")
        case_id = body["id"]
        original = body["question"]

        # The last NO_PROFILE_COUNT cases are the ones with no data attached;
        # every other case attaches and profiles its own copy, so each case's
        # refinement reads a profile its own case owns.
        no_profile = index >= len(CASES) - NO_PROFILE_COUNT
        profile: dict = {}
        if not no_profile:
            content = (DATASETS_DIR / case.dataset).read_text()
            dataset = server.upload(
                f"/cases/{case_id}/datasets", case.dataset, content,
            )
            # Profiling is a separate call, so the profile the refiner reads is
            # one the profiler actually wrote.
            server.post(f"/cases/{case_id}/datasets/{dataset['id']}/profile", None)
            profile = server.get(
                f"/cases/{case_id}/datasets/{dataset['id']}/profile"
            )

        status, proposal = server.post(f"/cases/{case_id}/refine", None)
        if status not in (200, 201):
            raise RuntimeError(
                f"refine failed for '{case.question}' ({status}): {proposal}"
            )
        result.proposed = proposal["status"] == "pending"
        result.refined = proposal.get("refined_question") or ""
        result.grounds = proposal.get("grounds") or []

        # M1: the original is preserved on the proposal, verbatim.
        result.preserved = proposal["original_question"] == original

        columns = {
            (col or "").lower() for col in (profile.get("columns") or [])
        }
        stats = profile.get("stats") or {}

        if result.proposed:
            terms = _subject_terms(original)
            kept = all(term in result.refined.lower() for term in terms)
            # A refinement earns its name by grounding the question in data the
            # profile measured, so a real column name in the text is the
            # second half of the relevance measurement.
            names_column = any(
                (col or "").lower() in result.refined.lower()
                for col in (profile.get("columns") or [])
            )
            result.relevant = bool(kept and names_column)

            # M4: fabricated data references. A ground citing a column the
            # profile does not have, or a figure it did not measure.
            for ground in result.grounds:
                name = (ground.get("name") or "").strip().lower()
                if name and name not in columns:
                    result.fabricated.append(
                        f"ground cites '{ground.get('name')}', not a profiled column"
                    )
            import re as _re
            number_re = _re.compile(r"\d[\d,]*(?:\.\d+)?")

            def _spellings(value) -> set[str]:
                """Every way the engine may print a measured value.

                The formatter renders an integral float as an integer (52.0 ->
                "52"), rounds floats to their shortest form, and separates
                thousands. A figure the profile measured is allowed in any of
                those spellings; only a figure none of them spells is a
                fabrication.
                """
                text = str(value)
                out = {text, text.replace(",", "")}
                # A date or a range is allowed by its own digits too: the
                # refined question prints the pieces ("2026", "01", "04") as
                # well as the whole ("2026-01-04").
                for run in number_re.findall(text):
                    out.add(run.replace(",", ""))
                try:
                    number = float(value)
                except (TypeError, ValueError):
                    return out
                out.add(f"{number:g}")
                if number == int(number):
                    out.add(str(int(number)))
                    out.add(f"{int(number):,}")
                return out

            allowed = set()
            for run in number_re.findall(original):
                allowed |= _spellings(run)
            for stat in stats.values():
                for key in ("min", "max", "avg", "null_count", "null_percentage",
                            "distinct_count"):
                    if stat.get(key) is not None:
                        allowed |= _spellings(stat[key])
            for run in number_re.findall(result.refined):
                if run.replace(",", "") not in allowed:
                    result.fabricated.append(
                        f"quotes {run}, a figure the profile did not measure"
                    )
        elif case.expect == "proposal":
            # An expected proposal that did not come counts against relevance.
            result.relevant = False
            result.note = "declined; the corpus expected a proposal"
        else:
            # An expected decline is a pass on the relevance axis: leaving an
            # already-specific question alone is what relevance means here.
            result.relevant = True

        # The three paths, driven and then verified.
        if result.proposed and case.path != PATH_PENDING:
            path = case.path
            if path == PATH_ACCEPT:
                status, decided = server.post(
                    f"/cases/{case_id}/refine/{proposal['id']}/accept", None,
                )
                expected_question = result.refined
            elif path == PATH_EDIT:
                status, decided = server.post(
                    f"/cases/{case_id}/refine/{proposal['id']}/edit",
                    {"question": case.edited},
                )
                expected_question = case.edited
            else:
                status, decided = server.post(
                    f"/cases/{case_id}/refine/{proposal['id']}/reject", None,
                )
                expected_question = original
            if status != 200:
                raise RuntimeError(
                    f"{path} failed for '{case.question}' ({status}): {decided}"
                )
            # M3: a silent overwrite is a question that moved without a
            # decision, or a decision that moved it somewhere it was not told
            # to go. The case row is read back from the server the shell reads.
            reopened = server.get(f"/cases/{case_id}/refinements")[0]
            if path in (PATH_ACCEPT, PATH_EDIT):
                moved = server.get(f"/cases/{case_id}")
                if moved["question"] != expected_question:
                    result.overwritten = True
                    result.note = (
                        f"question moved to '{moved['question']}' on {path}"
                    )
            # The original survives every path, including the one that
            # replaced it - this is AT-04's recoverability threshold, checked
            # where it can actually fail.
            if reopened["original_question"] != original:
                result.preserved = False
                result.note = "the original question is not recoverable after " + path

        results.append(result)

    return Measurement(
        cases=len(results),
        proposals=sum(1 for r in results if r.proposed),
        declines=sum(1 for r in results if not r.proposed),
        preserved=sum(1 for r in results if r.preserved),
        relevant=sum(
            1 for r in results
            if r.relevant and (r.case.expect == "proposal" or r.proposed)
        ),
        silent_overwrites=sum(1 for r in results if r.overwritten),
        fabrications=sum(len(r.fabricated) for r in results),
        results=results,
    )


def _format_rate(value: float) -> str:
    return f"{value * 100:.1f}%"


def _write_report(measurement: Measurement) -> None:
    lines: list[str] = [
        "# AT-04 — AI Question Refinement, measured",
        "",
        f"Cases: **{measurement.cases}** over 6 datasets, each driven through "
        "one of accept / edit / keep-original / left pending. The deterministic "
        "engine answered (no LLM was configured), so every number below is "
        "reproducible offline.",
        "",
        "| Threshold | Required | Measured | |",
        "|---|---|---|---|",
        f"| Preserve the original question | >= 95% | "
        f"**{_format_rate(measurement.preserve_rate)}** "
        f"({measurement.preserved}/{measurement.cases}) | "
        f"{'PASS' if measurement.preserve_rate >= THRESHOLD_PRESERVE else 'FAIL'} |",
        f"| Semantically relevant refinement | >= 90% | "
        f"**{_format_rate(measurement.relevant_rate)}** "
        f"({measurement.relevant}/{measurement.cases}) | "
        f"{'PASS' if measurement.relevant_rate >= THRESHOLD_RELEVANT else 'FAIL'} |",
        f"| Silent overwrites | 0 | **{measurement.silent_overwrites}** | "
        f"{'PASS' if measurement.silent_overwrites <= THRESHOLD_OVERWRITES else 'FAIL'} |",
        f"| Fabricated data references | 0 | **{measurement.fabrications}** | "
        f"{'PASS' if measurement.fabrications <= THRESHOLD_FABRICATIONS else 'FAIL'} |",
        "",
        f"Proposals made: {measurement.proposals}; declines: "
        f"{measurement.declines} (the already-specific, the topicless, the "
        "unprofiled and the column-less).",
        "",
    ]

    failures = [r for r in measurement.results
                if r.note or r.fabricated or r.overwritten or not r.preserved
                or (r.proposed and not r.relevant)]
    if failures:
        lines += ["## Cases worth reading", "",
                  "| Question | Outcome | Note |", "|---|---|---|"]
        for r in failures:
            outcome = "proposed" if r.proposed else "declined"
            note = r.note or "; ".join(r.fabricated) or (
                "not relevant" if r.proposed else ""
            )
            lines.append(
                f"| {r.case.question!r} on {r.case.dataset} | {outcome} | {note} |"
            )
        lines.append("")

    lines += [
        "How relevance is measured, not judged: the refined question keeps "
        "every one of the original's subject terms (so it is the same question, "
        "sharpened) and names at least one real column from the profile (so it "
        "is sharpened by measured data). A decline the corpus expected counts "
        "as relevant, because leaving an already-answerable question alone is "
        "the correct behaviour; a decline it did not expect counts against it.",
        "",
        "How preservation is measured: the proposal carries the original "
        "verbatim, and after every decision - including the accept that "
        "replaced it on the case row - the original is still readable from the "
        "case's refinement history.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines))


def run_refine(write_report: bool = True) -> Measurement:
    """Measure AT-04 against a real server, and optionally write the report.

    The entry point the test suite uses, so the four numbers are asserted in
    the suite rather than only read from REPORT.md.
    """
    server = Server()
    try:
        measurement = _measure(server)
    except Exception as error:
        tail = server.server_log_tail(60)
        raise RuntimeError(f"{error}\nserver log tail:\n{tail}") from error
    finally:
        server.stop()
    if write_report:
        _write_report(measurement)
    return measurement


def main() -> int:
    measurement = run_refine()

    print(f"cases={measurement.cases} proposals={measurement.proposals} "
          f"declines={measurement.declines}")
    print(f"preserve={_format_rate(measurement.preserve_rate)} "
          f"({measurement.preserved}/{measurement.cases}) "
          f"[>= 95%]")
    print(f"relevant={_format_rate(measurement.relevant_rate)} "
          f"[>= 90%]")
    print(f"silent_overwrites={measurement.silent_overwrites} [0]")
    print(f"fabrications={measurement.fabrications} [0]")
    print(f"report: {REPORT_PATH}")
    if measurement.passed:
        print("AT-04: PASS")
        return 0
    print("AT-04: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
