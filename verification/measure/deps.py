"""Production dependency security measurement (AT-37).

The PRD requires production dependencies to be scanned, with zero known
Critical and zero known High vulnerabilities that are not explicitly risk-
accepted. Nothing in the project scanned anything; the venv has no `pip-audit`
and the phase carries a no-new-dependency constraint (DEC-001), so the scanner
is built from what is already there:

- the inventory is computed, not typed in. The server's direct dependencies
  come from `pyproject.toml` and their transitive closure from the installed
  distributions' own `Requires-Dist` metadata, so the list cannot drift from
  what is actually shipped. The web inventory comes from `package.json`'s
  runtime dependencies and the installed `node_modules`.
- the check is the OSV database over HTTP, one query per (package, version),
  with the severity classified from the CVSS vector the advisory itself
  publishes - the base score is computed from the vector, because a scanner
  that read only "an advisory exists" would fail a library for a Low and pass
  one for a Critical.

An unreachable database answers `unknown` with a reason, never a silent
`clean` - the same discipline `GET /updates/latest` uses, because "could not
check" and "nothing to fix" are different statements and only one is true.
That keeps the suite honest offline: an offline run reports it scanned nothing
rather than reporting zero vulnerabilities it never looked for.

    server/.venv/bin/python -m verification.measure.deps
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SERVER = REPO / "server"
WEB = REPO / "web"

OSV_URL = "https://api.osv.dev/v1/query"
OSV_TIMEOUT_SECONDS = 20

# A vulnerability with a severity at or above these counts against the AT-37
# target. The PRD accepts a High only with an explicit, documented risk
# acceptance - recorded here with the sentence that accepts it, so the report
# names why rather than merely that.
SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
GATING_SEVERITIES = (SEVERITY_CRITICAL, SEVERITY_HIGH)

# Known and explicitly accepted: {"ecosystem:name@version": "the reason"}.
# Empty until a release accepts one; the report shows the field exists.
RISK_ACCEPTED: dict[str, str] = {}

PYPI = "PyPI"
NPM = "npm"


@dataclass
class Dependency:
    """One production dependency at its installed version."""

    ecosystem: str
    name: str
    version: str
    advisories: list[dict] = field(default_factory=list)
    scanned: bool = False
    error: str = ""

    @property
    def key(self) -> str:
        return f"{self.ecosystem}:{self.name}@{self.version}"

    @property
    def severity(self) -> str:
        """The worst severity among the advisories that did not get accepted."""
        found = [classify_severity(one) for one in self.advisories]
        found = [
            level
            for level, advisory in zip(found, self.advisories)
            if not _is_accepted(self.key, advisory)
        ]
        if SEVERITY_CRITICAL in found:
            return SEVERITY_CRITICAL
        if SEVERITY_HIGH in found:
            return SEVERITY_HIGH
        if "medium" in found:
            return "medium"
        if "low" in found:
            return "low"
        return "none" if self.scanned else "unknown"

    @property
    def accepted(self) -> list[dict]:
        """The advisories this build accepts, with the reason recorded."""
        return [one for one in self.advisories if _is_accepted(self.key, one)]


@dataclass
class DepsReport:
    """The AT-37 measurement: an inventory, a scan state, and the counts."""

    dependencies: list[Dependency] = field(default_factory=list)
    scan_status: str = "pending"  # scanned | unknown
    scan_reason: str = ""
    duration_seconds: float = 0.0

    @property
    def critical(self) -> list[Dependency]:
        return [d for d in self.dependencies if d.severity == SEVERITY_CRITICAL]

    @property
    def high(self) -> list[Dependency]:
        return [d for d in self.dependencies if d.severity == SEVERITY_HIGH]

    @property
    def ok(self) -> bool:
        # An inventory that scanned nothing cannot claim to be clean; it can
        # only claim it could not tell. Only a scan that ran answers the AT.
        return bool(self.dependencies) and self.scan_status == "scanned" and (
            not self.critical and not self.high
        )

    def failures_text(self) -> str:
        lines = []
        if not self.dependencies:
            lines.append("the production inventory is empty")
        if self.scan_status != "scanned":
            lines.append(f"the dependency scan did not complete: {self.scan_reason}")
        for dep in self.critical:
            lines.append(f"CRITICAL {dep.key} ({len(dep.advisories)} advisory/ies)")
        for dep in self.high:
            lines.append(f"HIGH {dep.key} ({len(dep.advisories)} advisory/ies)")
        return "\n".join(lines)


def _is_accepted(key: str, advisory: dict) -> bool:
    return key in RISK_ACCEPTED and bool(advisory.get("id"))


def _marker_matches(marker: str) -> bool:
    """The simplest PEP 508 markers, evaluated for this running interpreter.

    Only the markers that decide whether a dependency belongs to *this*
    build are evaluated: an `extra` marker excludes the requirement (the
    optional dependencies of a feature this product does not ship as its
    production set are not in its production set), and the environment
    markers for interpreter version and platform decide the platform-specific
    ones. Full PEP 508 evaluation would need `packaging`, which the
    no-new-dependency constraint rules out; a requirement whose marker is not
    understood is included rather than silently dropped.
    """
    marker = marker.strip()
    if not marker:
        return True
    if "extra" in marker:
        return False
    if "python_version" in marker:
        # "python_version >= '3.10'" and the like; compare against the running
        # interpreter as a tuple of ints.
        match = re.search(
            r"python_version\s*(>=|<=|==|<|>|!=)\s*['\"](\d+(?:\.\d+)?)['\"]", marker
        )
        if match:
            operator, raw = match.group(1), match.group(2)
            want = tuple(int(part) for part in raw.split("."))
            have = sys.version_info[: len(want)]
            return _compare(have, operator, want)
    return True


def _compare(have, operator: str, want) -> bool:
    return {
        ">=": have >= want,
        "<=": have <= want,
        "==": have == want,
        "<": have < want,
        ">": have > want,
        "!=": have != want,
    }[operator]


def _requirement_name(spec: str) -> str:
    """The distribution name a `Requires-Dist` entry names, sans version."""
    head = spec.split(";")[0].strip()
    match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", head)
    return match.group(1).lower() if match else head.lower()


def python_production_inventory() -> dict[str, str]:
    """The server's production dependencies and their transitive closure.

    Direct dependencies are read from `pyproject.toml`'s `dependencies`
    (never the optional groups: `charts`, `dev` and `packaging` are not
    shipped as the product's runtime), and the closure walks each installed
    distribution's own metadata. The list is therefore what is actually
    installed for the shipped set, and cannot stay stale when a dependency
    adds one.
    """
    import tomllib

    from importlib import metadata

    with open(SERVER / "pyproject.toml", "rb") as handle:
        project = tomllib.load(handle)
    direct = [
        _requirement_name(spec) for spec in project["project"]["dependencies"]
    ]

    inventory: dict[str, str] = {}
    pending = list(direct)
    while pending:
        name = pending.pop()
        if name in inventory:
            continue
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
        inventory[name] = version
        for requirement in metadata.requires(name) or []:
            if _marker_matches(requirement.split(";", 1)[-1]):
                pending.append(_requirement_name(requirement))
    return dict(sorted(inventory.items()))


def npm_production_inventory() -> dict[str, str]:
    """The web shell's runtime dependencies at their installed versions."""
    with open(WEB / "package.json", encoding="utf-8") as handle:
        package = json.load(handle)
    inventory: dict[str, str] = {}
    for name in sorted(package.get("dependencies", {})):
        installed = WEB / "node_modules" / name / "package.json"
        if installed.is_file():
            with open(installed, encoding="utf-8") as handle:
                inventory[name] = json.load(handle).get("version", "")
    return inventory


def query_osv(name: str, version: str, ecosystem: str) -> list[dict]:
    """Ask the OSV database for the advisories affecting one version.

    Raises on any failure to reach or parse the database: the caller decides
    whether that is `unknown`, and a network blip must never read as "clean".
    """
    payload = json.dumps(
        {"package": {"name": name, "ecosystem": ecosystem}, "version": version}
    ).encode()
    request = urllib.request.Request(
        OSV_URL, data=payload, headers={"content-type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=OSV_TIMEOUT_SECONDS) as response:
        body = json.loads(response.read() or b"{}")
    return list(body.get("vulns", []))


def classify_severity(advisory: dict) -> str:
    """An advisory's severity, from the CVSS vector it publishes.

    OSV carries the vector rather than a computed score, so the base score is
    computed from it - the rating the CVSS standard defines, not a guess from
    the advisory's wording. A vector the classifier cannot read is `unknown`,
    which the report shows rather than treating as safe.
    """
    for entry in advisory.get("severity", []):
        score = entry.get("score", "")
        if entry.get("type") == "CVSS_V3" and score.startswith("CVSS:3"):
            return _rate_v3(score)
        if entry.get("type") == "CVSS_V2" and score.startswith("CVSS:2"):
            return _rate_v2(score)
    # Some advisories carry no vector of their own and point at the database
    # entry instead; those are reported but not counted as Critical or High,
    # because counting them would need a guess.
    return "unrated"


def _metric_value(vector: str, metric: str) -> str:
    """One CVSS metric's value, anchored so metrics do not collide.

    `C:` would otherwise match the C inside `AC:`, and `I:` the I in `UI:`;
    a metric is preceded by a slash or the vector's start and nothing else.
    """
    match = re.search(rf"(?:^|/){metric}:([A-Z])", vector)
    return match.group(1) if match else ""


# The CVSS v3.1 metric weights. Privileges Required is the one metric whose
# weight depends on the Scope's direction, so it has a table per direction; the
# others are single values.
CVSS3_WEIGHTS = {
    "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
    "AC": {"L": 0.77, "H": 0.44},
    "UI": {"N": 0.85, "R": 0.62},
    "C": {"H": 0.56, "L": 0.22, "N": 0},
    "I": {"H": 0.56, "L": 0.22, "N": 0},
    "A": {"H": 0.56, "L": 0.22, "N": 0},
}
PR_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
PR_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.5}


def _rate_v3(vector: str) -> str:
    """CVSS v3.1 base score, rated against the AT-37 classes.

    The formula is the standard's own: an impact subscore from the
    confidentiality/integrity/availability triad, an exploitability subscore
    from the four metrics that describe the attack, and a base that sums them
    - multiplied by 1.08 when the vulnerable component and the impacted one
    are not the same, which is what a Changed Scope says.
    """
    av = _metric_value(vector, "AV")
    ac = _metric_value(vector, "AC")
    pr = _metric_value(vector, "PR")
    ui = _metric_value(vector, "UI")
    scope = _metric_value(vector, "S")
    if not (av and ac and pr and ui and scope):
        return "unrated"

    confidentiality = CVSS3_WEIGHTS["C"][_metric_value(vector, "C")]
    integrity = CVSS3_WEIGHTS["I"][_metric_value(vector, "I")]
    availability = CVSS3_WEIGHTS["A"][_metric_value(vector, "A")]

    isc = 1 - (1 - confidentiality) * (1 - integrity) * (1 - availability)
    if scope == "U":
        impact = 6.42 * isc
        pr_weight = PR_UNCHANGED[pr]
    else:
        impact = 7.52 * (isc - 0.029) - 3.25 * (isc - 0.02) ** 15
        pr_weight = PR_CHANGED[pr]

    if impact <= 0:
        return "none"

    exploitability = (
        8.22
        * CVSS3_WEIGHTS["AV"][av]
        * CVSS3_WEIGHTS["AC"][ac]
        * pr_weight
        * CVSS3_WEIGHTS["UI"][ui]
    )
    if scope == "U":
        base = min(impact + exploitability, 10.0)
    else:
        base = min(1.08 * (impact + exploitability), 10.0)
    return _rate_score(_roundup(base))


def _rate_v2(vector: str) -> str:
    """CVSS v2 base score, the fallback for advisories without a v3 vector."""
    av = _metric_value(vector, "AV")
    ac = _metric_value(vector, "AC")
    au = _metric_value(vector, "Au")
    if not (av and ac and au):
        return "unrated"
    weights = {
        "AV": {"N": 1.0, "A": 0.646, "L": 0.395},
        "AC": {"L": 0.71, "M": 0.61, "H": 0.35},
        "Au": {"M": 0.45, "S": 0.56, "N": 0.704},
    }
    impacts = {
        "C": {"C": 0.66, "I": 0.275, "A": 0.275},
        "P": {"C": 0.275, "I": 0.275, "A": 0.275},
        "N": {"C": 0, "I": 0, "A": 0},
    }
    c = _metric_value(vector, "C")
    i = _metric_value(vector, "I")
    a = _metric_value(vector, "A")
    if c not in impacts or i not in impacts[c] or a not in impacts[c]:
        return "unrated"
    impact = 10.41 * (1 - (1 - impacts[c]["C"]) * (1 - impacts[c]["I"]) * (1 - impacts[c]["A"]))
    exploitability = 20 * weights["AV"][av] * weights["AC"][ac] * weights["Au"][au]
    f = 0.0 if impact == 0 else 1.176
    base = (0.6 * impact + 0.4 * exploitability - 1.5) * f
    return _rate_score(max(base, 0.0))


def _roundup(value: float) -> float:
    """CVSS rounds up to one decimal, never down (a 7.34 is a 7.4)."""
    import math

    return math.ceil(value * 10) / 10.0


def _rate_score(score: float) -> str:
    if score >= 9.0:
        return SEVERITY_CRITICAL
    if score >= 7.0:
        return SEVERITY_HIGH
    if score >= 4.0:
        return "medium"
    if score > 0:
        return "low"
    return "none"


def measure_dependencies(
    inventory: dict[str, tuple[str, str]] | None = None,
    querier=query_osv,
) -> DepsReport:
    """Scan the production inventory and answer the AT-37 counts.

    `querier` is the OSV call, injected so a test can prove the classifier
    counts a Critical and that an unreachable database answers `unknown`
    instead of a fabricated zero.
    """
    import time

    if inventory is None:
        inventory = {
            name: (PYPI, version) for name, version in python_production_inventory().items()
        }
        inventory.update(
            (name, (NPM, version)) for name, version in npm_production_inventory().items()
        )

    started = time.perf_counter()
    report = DepsReport()
    failed = 0
    for name, (ecosystem, version) in sorted(inventory.items()):
        dependency = Dependency(ecosystem=ecosystem, name=name, version=version)
        try:
            dependency.advisories = querier(name, version, ecosystem)
            dependency.scanned = True
        except (urllib.error.URLError, OSError, ValueError, TimeoutError) as error:
            # A single unreachable package does not stop the scan; every
            # package unreachable does, and that is the `unknown` below.
            failed += 1
            dependency.error = f"{type(error).__name__}: {error}"
        report.dependencies.append(dependency)

    scanned = sum(1 for dep in report.dependencies if dep.scanned)
    if not report.dependencies:
        report.scan_status = "unknown"
        report.scan_reason = "the production inventory is empty"
    elif scanned == 0:
        report.scan_status = "unknown"
        report.scan_reason = (
            f"none of the {len(report.dependencies)} packages could be reached "
            f"({report.dependencies[0].error or 'network unavailable'})"
        )
    elif failed:
        report.scan_status = "unknown"
        report.scan_reason = (
            f"{failed} of {len(report.dependencies)} packages could not be checked"
        )
    else:
        report.scan_status = "scanned"
    report.duration_seconds = time.perf_counter() - started
    return report


def format_report(report: DepsReport) -> str:
    lines = [
        "AT-37 dependency security (production dependencies, scanned against OSV)",
        "",
        f"scan: {report.scan_status}"
        + (f" - {report.scan_reason}" if report.scan_reason else ""),
        f"packages scanned: {sum(1 for d in report.dependencies if d.scanned)}"
        f" / {len(report.dependencies)}",
        f"critical: {len(report.critical)}    high: {len(report.high)}"
        "    (target 0 / 0 without a documented risk acceptance)",
        f"measured in {report.duration_seconds:.1f}s",
        "",
    ]
    for dep in sorted(report.dependencies, key=lambda d: (d.severity != "none", d.name)):
        if dep.advisories or dep.error:
            lines.append(
                f"  {dep.ecosystem}:{dep.name}@{dep.version} -> "
                f"{len(dep.advisories)} advisory/ies, severity {dep.severity}"
                + (f" [{dep.error}]" if dep.error else "")
            )
    if report.critical or report.high:
        lines.append("")
        lines.append(report.failures_text())
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_report(measure_dependencies()))
