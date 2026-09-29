"""Request/response models for Analysis Cases, datasets, profiles, and runs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CaseCreate(BaseModel):
    question: str
    dataset: str


class WorkflowStage(BaseModel):
    """One stage of the analysis loop: what it asks for and where it stands."""
    name: str
    completed: bool


class CaseProgress(BaseModel):
    """Where a case sits in the guided workflow (P3-FLOW-004).

    The stage is derived from the artifacts the case actually has, so it can
    never claim a step the data does not support.
    """
    case_id: str
    stage: str
    completed: list[str]
    stages: list[WorkflowStage]
    next_action: str | None
    next_hint: str | None
    next_endpoint: str | None
    loop_closed: bool
    counts: dict[str, int]


class CaseContext(BaseModel):
    """The analyst's intent for a case (P8-CONTEXT-001).

    The primary question stays on the case row - it is already editable and
    persisted - so this is what a question alone cannot carry: why the analysis
    matters, what it would answer in pieces, what it would test, and what it is
    assuming. Read by the planner and the assistant; written only by the analyst.
    """
    case_id: str
    purpose: str = ""
    sub_questions: list[str] = []
    hypotheses: list[str] = []
    constraints: list[str] = []
    updated_at: datetime | None = None


class RefinementGround(BaseModel):
    """One thing a proposed refinement cites, and what the profile said about it.

    Every ground names a column the profile measured, so a proposal's basis is
    checkable rather than asserted (AT-04: 0 fabricated data references).
    """
    kind: str
    name: str
    detail: str


# The statuses that close a refinement proposal, plus `pending` for one the
# analyst has not decided on yet and `declined` for one where the engine looked
# and had nothing to add. One source of truth: the endpoint's decision guard and
# the importer's validation both ask "is this a status we store?" of this list.
REFINEMENT_STATUSES = (
    "pending", "declined", "accepted", "rejected", "edited",
)


class Refinement(BaseModel):
    """A proposed sharpening of the case's question and its decision (AT-04).

    The original is carried beside the proposal and never overwritten: `accept`
    moves the refined question onto the case row, but the row keeps what was
    there before, so the transformation stays recoverable and auditable. The
    three paths the analyst has - accept, edit, keep original - are the three
    statuses that close a proposal; a proposal with no decision is `pending`,
    and one where the engine looked and had nothing to add is `declined`.
    """
    id: str
    case_id: str
    original_question: str
    refined_question: str = ""
    rationale: str = ""
    grounds: list[RefinementGround] = []
    source: str
    status: str
    edited_question: str | None = None
    created_at: datetime
    decided_at: datetime | None = None


class RefinementEdit(BaseModel):
    """The analyst's own wording for the question, applied in place of the proposal.

    An edit is a third path, not a silent overwrite: it is recorded on the row
    with the wording the analyst chose, and the original the proposal replaced
    stays recoverable on the same row.
    """
    question: str


class ContextUpdate(BaseModel):
    """A whole-context replacement.

    Lists, not single strings, because the analyst adds and removes entries as
    the investigation moves; PUT semantics keep the stored object identical to
    what the form held, so a retry after a failed save cannot merge duplicates.
    """
    purpose: str = ""
    sub_questions: list[str] = []
    hypotheses: list[str] = []
    constraints: list[str] = []


class CaseUpdate(BaseModel):
    """Rename a case; either field may be omitted to leave it unchanged."""
    question: str | None = None
    dataset: str | None = None


class Case(BaseModel):
    id: str
    question: str
    dataset: str
    # Which template seeded this case, if any. Advisory: a template outlives
    # its source case and may be deleted before this one, so a missing template
    # degrades to the normal derivation rather than an error.
    template_id: str | None = None
    # Which case this one repeats, if its question and dataset match an
    # existing case exactly. Advisory in the same way and for the same reason:
    # a duplicate is a case in its own right, so the field is read to warn and
    # never to enforce (W2X-010). Whichever case it points at may be deleted
    # first, and a dangling pointer degrades to "no duplicate" rather than an
    # error.
    duplicate_of: str | None = None
    created_at: datetime
    updated_at: datetime


class Dataset(BaseModel):
    id: str
    case_id: str
    filename: str
    stored_path: str
    format: str
    created_at: datetime


class QualityIssue(BaseModel):
    """One detected data-quality defect and what it costs an analysis.

    `observed` is the measured fact; `impact` is the consequence (AT-09) - the
    second sentence is the one an analyst acts on, so it is never empty.
    `column` is None for a dataset-wide issue such as insufficient coverage.
    """

    kind: str
    column: str | None = None
    severity: str = "medium"
    observed: str
    impact: str


class Profile(BaseModel):
    dataset_id: str
    rows: int
    columns: list[str]
    stats: dict
    duplicate_rows: int
    quality: list[QualityIssue] = []
    profiled_at: datetime


class EdaCreate(BaseModel):
    """One exploratory operation over an attached dataset (P3-ANALYSIS-005).

    `op` picks the analysis; the rest are its inputs:

        segment       by, measure  - group stats per category
        correlate     x, y         - Pearson r between two numeric columns
        distribution  column       - numeric spread, or top values for a category
    """
    op: str
    by: str | None = None
    measure: str | None = None
    x: str | None = None
    y: str | None = None
    column: str | None = None


class EdaResult(BaseModel):
    op: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool


class MultiRunCreate(BaseModel):
    """A SQL run that touches several attached datasets (P3-DATA-003).

    Placeholders bind positionally to the datasets in the order listed, so a
    query can join files: one `?` per dataset.
    """
    sql: str
    dataset_ids: list[str]


class RunCreate(BaseModel):
    sql: str


class PythonRunCreate(BaseModel):
    code: str


# A run's source is the query or the script, never both; `kind` says which.
RUN_KINDS = ("sql", "python")


class Run(BaseModel):
    id: str
    case_id: str
    dataset_id: str
    kind: str = "sql"
    sql: str | None = None
    code: str | None = None
    # Every dataset the run touches. A single-dataset run has [dataset_id];
    # a join run lists them in placeholder order (P3-DATA-003). Absent on runs
    # created before that task, which are single-dataset by construction.
    dataset_ids: list[str] | None = None
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    executed_at: datetime


class RunSummary(BaseModel):
    id: str
    case_id: str
    dataset_id: str
    kind: str = "sql"
    sql: str | None = None
    code: str | None = None
    dataset_ids: list[str] | None = None
    row_count: int
    truncated: bool
    executed_at: datetime


# Per the Master Specification quality model: a finding's support is a property
# of the evidence, not of AI confidence.
VALIDATION_STATUSES = (
    "supported",
    "partially_supported",
    "insufficient_evidence",
    "contradicted",
    "not_evaluated",
)


class FindingCreate(BaseModel):
    run_id: str
    statement: str
    interpretation: str | None = None
    caveat: str | None = None


class Finding(BaseModel):
    id: str
    case_id: str
    run_id: str
    statement: str
    interpretation: str | None
    caveat: str | None
    validation_status: str
    created_at: datetime


class EvidenceNode(BaseModel):
    """One artifact in a case's evidence graph (P3-EVIDENCE-006)."""
    id: str
    kind: str
    label: str
    detail: str | None = None
    created_at: str | None = None


class EvidenceEdge(BaseModel):
    """How one artifact was derived from another."""
    source: str
    target: str
    relation: str


class ClaimTrace(BaseModel):
    """A single claim's path back to the data it stands on."""
    finding_id: str
    statement: str
    validation_status: str
    hops: list[EvidenceNode]
    reaches_source: bool


class EvidenceGraph(BaseModel):
    """Every claim in a case and what it rests on.

    Nodes are the case's artifacts; edges say how each was derived. A finding
    that reaches no dataset is a claim with no source, listed in
    `orphan_findings` - which is what makes this a review tool, not a diagram.
    """
    case_id: str
    nodes: list[EvidenceNode]
    edges: list[EvidenceEdge]
    traces: list[ClaimTrace]
    orphan_findings: list[str]
    counts: dict[str, int]


class EvidenceChain(BaseModel):
    """The trust chain a reviewer walks to verify a finding."""
    finding: Finding
    kind: str = "sql"
    sql: str | None = None
    code: str | None = None
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    dataset_filename: str


class ChartCreate(BaseModel):
    kind: str
    x: str
    y: str
    series: str | None = None
    title: str = ""
    format: str = "svg"


class Chart(BaseModel):
    id: str
    case_id: str
    run_id: str
    kind: str
    x: str
    y: str
    series: str | None
    title: str
    stored_path: str
    width: int
    height: int
    # The artifact's own format, sniffed from the bytes the core wrote. It is
    # what the shell reads to decide whether a chart is inline SVG or a
    # bitmap link, so a response without it reads as neither. The default is
    # SVG because that is what charts before P3-CHART-002 are, and the image
    # endpoint sniffs the same way.
    format: str = "svg"
    created_at: datetime


class ChartSummary(BaseModel):
    """Chart metadata without the image bytes."""
    id: str
    case_id: str
    run_id: str
    kind: str
    x: str
    y: str
    series: str | None
    title: str
    created_at: datetime


class Plan(BaseModel):
    """A structured analysis plan, persisted against a case and dataset."""
    id: str
    case_id: str
    dataset_id: str
    question: str
    plan: dict
    source: str
    created_at: datetime


class PlanSummary(BaseModel):
    """Plan metadata without the plan body."""
    id: str
    case_id: str
    dataset_id: str
    question: str
    source: str
    created_at: datetime


class ValidationCheck(BaseModel):
    """One dimension of a finding's validation (P8-VALID-003, AT-17).

    `name` is kept identical to `dimension` so a client reading the old three
    checks still finds them; the PRD's nine dimensions are carried by
    `dimension`. `hard` marks a dimension whose failure blocks `supported`
    rather than yielding `partially_supported`.
    """

    name: str
    dimension: str = ""
    passed: bool
    detail: str
    hard: bool = False

    def __init__(self, **data: Any) -> None:
        # A caller passing the legacy three fields (name/passed/detail) still
        # works, and a caller passing the new ones fills `name` from the
        # dimension so both shapes agree.
        dimension = data.get("dimension") or data.get("name") or ""
        data.setdefault("dimension", dimension)
        data["name"] = data.get("name") or dimension
        data.setdefault("hard", False)
        super().__init__(**data)


class ValidationResult(BaseModel):
    finding_id: str
    run_id: str
    status: str
    checks: list[ValidationCheck]
    validated_at: datetime


# The loop's exit (P8-DECISION-008, UX 46): the case's decision view. A
# validated finding used to be the end of the road - the verdict was computed,
# shown and discarded, and nothing closed over what the loop had established.
# This is what the analyst acts on: the findings validation stood behind, the
# uncertainty that survived them, the claims still open, and the implications
# the analyst wrote. DAH informs decisions and does not make them, so nothing
# here recommends anything and no number summarises a finding's trust.

class DecisionCheck(BaseModel):
    """One check a validated finding did not pass.

    The PRD's own rule (UX 44) is that uncertainty is communicated as
    structured signals with a sentence, not a confidence score; this is that
    signal, carried verbatim from the verdict validation computed.
    """
    dimension: str
    detail: str
    hard: bool = False


class DecisionFinding(BaseModel):
    """A finding the case can act on, with what validation left unresolved."""
    id: str
    statement: str
    validation_status: str
    interpretation: str | None
    caveat: str | None
    uncertainty: list[DecisionCheck]
    validated_at: datetime | None


class DecisionOpenItem(BaseModel):
    """A claim the loop has not closed over.

    Either validation has not run, or it ran and refused - in which case the
    reasons are the hard dimensions that failed, named rather than scored, so
    the analyst reads what to fix rather than how badly it scored.
    """
    id: str
    statement: str
    validation_status: str
    reasons: list[str]


class DecisionWrite(BaseModel):
    """The implications the analyst writes - the only write the view accepts."""
    implications: list[str]


class DecisionView(BaseModel):
    case_id: str
    question: str
    purpose: str
    loop_closed: bool
    findings: list[DecisionFinding]
    open_items: list[DecisionOpenItem]
    implications: list[str]
    updated_at: datetime | None
    counts: dict[str, int]


class TemplateProposal(BaseModel):
    """One code proposal captured from a finished case.

    The columns the proposal reads are carried so a later case can refuse it
    when *its* dataset does not have them - the proposal travels, the schema it
    was written against does not.
    """

    kind: str
    code: str
    explanation: str
    columns_used: list[str]


class TemplateFindingSummary(BaseModel):
    """What a finished case concluded, and whether it survived validation."""

    statement: str
    validation_status: str


class TemplateShape(BaseModel):
    """The analytical shape of a promoted case (P6-TEMPLATE-003).

    A pure projection over artifacts that already exist: the case's latest plan
    and which engine produced it, the proposals its agent run offered (or its
    runs, when the case was driven by hand), and its findings' statements with
    the verdicts validation gave them. Every field is optional or a list, so a
    case with nothing to carry promotes a shapeless template that behaves
    exactly as the question-only skeleton always did.
    """

    plan: dict | None = None
    plan_source: str | None = None
    proposals: list[TemplateProposal] = []
    findings: list[TemplateFindingSummary] = []


class TemplateCreate(BaseModel):
    """Promote a case into a reusable template (P3-CASE-007).

    `name` is optional - it defaults to the case's question - so the common
    "save this as a template" gesture needs no second prompt.
    """
    name: str | None = None


class Template(BaseModel):
    """A reusable case skeleton plus the shape of the case it came from.

    A template outlives the case it came from - promoting a case and then
    deleting it keeps the template - because templates are not case children.
    `shape` is nullable: a template promoted before P6-TEMPLATE-003, or one
    promoted from a case with nothing to carry, has none and seeds only the
    question and the label, exactly as it always did.
    """
    id: str
    name: str
    question: str
    dataset: str
    shape: TemplateShape | None = None
    created_at: datetime


class CaseFromTemplate(BaseModel):
    """Start a new case from a template, optionally overriding its fields."""
    template_id: str
    question: str | None = None
    dataset: str | None = None


class HistoryEvent(BaseModel):
    """One entry in a case's timeline (P3-CASE-007).

    The timestamp is the artifact's own `created_at`; nothing extra is stored.
    """
    timestamp: datetime
    kind: str
    artifact_id: str | None = None
    label: str
    detail: str | None = None


class CaseHistory(BaseModel):
    """Everything that happened in a case, in the order it happened.

    A read-side projection like the evidence graph: it is recomputed from the
    persisted rows, so the timeline cannot drift from what is on disk.
    """
    case_id: str
    question: str
    events: list[HistoryEvent]
    counts: dict[str, int]


class LearnStage(BaseModel):
    """One ANALYZE stage inside a LEARN phase (P7-LEARN-001)."""
    name: str
    completed: bool
    # What closes the stage, from workflow's own table - the ladder is the
    # workflow regrouped, so there is one source of truth for the actions.
    action: str
    hint: str


class LearnStep(BaseModel):
    """One phase of the LEARN ladder: why, what, how or validate.

    `purpose` is what the phase teaches - the thing the workflow's next action
    never says. `prompt` is the question a learner should be able to answer
    before leaving the phase, which is what makes it teaching rather than a
    checklist.
    """
    name: str
    purpose: str
    prompt: str
    stages: list[LearnStage]
    status: str  # complete | current | pending


class LearnWalk(BaseModel):
    """A case as the LEARN ladder (P7-LEARN-001).

    A read-side projection over the artifact counts, like the evidence graph
    and the case history: nothing is stored, so the walk cannot drift from the
    case. `done` says the trust loop closed - a finding was validated - which
    means the loop ran, not that the answer is right.
    """
    case_id: str
    question: str
    steps: list[LearnStep]
    current: str | None
    next_action: str | None
    next_hint: str | None
    next_endpoint: str | None
    done: bool


class Interpretation(BaseModel):
    """A plain-language read of a persisted run result (P3-AI-011).

    An artifact of the run, not of the case: it says what a result shows in the
    language of the case's question. `source` records which engine spoke, so a
    reviewer knows how much weight to give it - the deterministic read only
    ever cites values the result actually contains.
    """

    id: str
    run_id: str
    case_id: str
    summary: str
    observations: list[str]
    caveats: list[str]
    source: str
    created_at: datetime


class DraftFinding(BaseModel):
    """The candidate finding a result would support (P3-AI-012).

    A proposal, not an artifact: drafting writes nothing, so nothing has to be
    un-written when the analyst rejects it. Acceptance is a POST to the findings
    endpoint - the only path that creates a finding - which keeps "the LLM
    proposes, the human disposes" structural rather than a flag. `grounds` are
    the values from the result the statement stands on, so a human can check the
    claim against the numbers before it becomes evidence.
    """

    run_id: str
    case_id: str
    statement: str
    interpretation: str
    caveat: str
    grounds: list[str]
    source: str


class GenerateCodeRequest(BaseModel):
    """A natural-language request for the computation that would answer it."""

    question: str
    kind: str = "sql"


class GeneratedCode(BaseModel):
    """The read-only computation a question would need (P3-AI-013).

    A proposal, not an artifact: generation writes nothing, so nothing has to be
    un-written when the analyst rejects it. Running it is a POST to the runs
    endpoint - the only path that persists a run - which keeps "the human
    decides what executes" structural rather than a flag. `columns_used` are the
    dataset columns the proposal reads, so an analyst can see the proposal's
    reach before running it, and `source` records which engine wrote it.
    """

    dataset_id: str
    case_id: str
    kind: str
    code: str
    explanation: str
    columns_used: list[str]
    source: str


class ChatRequest(BaseModel):
    """A question put to the case's assistant."""

    message: str


class ConversationTurn(BaseModel):
    """One question and its answer, grounded in the case's artifacts
    (P3-AI-014).

    A conversation is the one assistant surface that persists, because memory is
    the point: a reopened case resumes mid-thought. `grounds` cites the artifact
    behind each claim as `kind:name`, so a reviewer can check the answer against
    the evidence rather than trusting it; `source` records which engine spoke.
    """

    id: str
    case_id: str
    message: str
    answer: str
    grounds: list[str]
    source: str
    created_at: datetime


class AgentStep(BaseModel):
    """One step of an agent run (P6-AGENT-002).

    The agent proposes; the human disposes. `payload` is exactly what the step
    will write or compute, decided when the step was proposed so the human
    approves something specific rather than a promise; `status` is pending until
    the human answers. `source` is the engine that produced the proposal, so a
    reviewer of an agent-run case can see which engine spoke at every step.
    """

    id: str
    case_id: str
    role: str
    kind: str
    payload: dict
    source: str
    status: str
    note: str
    created_at: datetime
    decided_at: datetime | None


class AgentState(BaseModel):
    """Where the agent stands on a case: the live proposal and the audit trail.

    `pending` is None when the loop has closed or the case has no further step
    - both are stated in `history` rather than signalled by silence, so a caller
    never has to guess whether the agent is idle or finished. `role` names which
    agent this state belongs to (P7-AGENT-001): a case can be worked by several,
    each with its own pending step and its own trail.
    """

    case_id: str
    role: str
    pending: AgentStep | None
    history: list[AgentStep]


class AgentApproval(BaseModel):
    """The human's decision on a pending step.

    `step_id` must be the case's current pending step, so an approval can never
    apply to a proposal the case has since moved past. `reason` on a rejection
    is recorded with the step - it is the analyst's note, not the agent's.
    """

    step_id: str
    reason: str | None = None


class LlmStatus(BaseModel):
    """Whether the core will answer an LLM-typed question with an LLM
    (W2X-012).

    A read-only answer to the walk-test's finding that the packaged app's LLM
    features degrade to deterministic engines and the analyst is told nothing:
    `configured` is what the shell branches on, `provider` names the env var
    to set (never its value), and the model and base URL are the public
    defaults a configured deployment overrode. Nothing here is a credential.
    """

    configured: bool
    provider: str | None
    model: str
    base_url: str


class LlmConfig(BaseModel):
    """The settings the shell writes so the packaged core reaches an LLM
    (W2X-012 phase B).

    The inverse of the problem `LlmStatus` answers: the status surface names a
    state, and this surface changes it. A packaged app cannot read a `.env`
    that was never bundled, so the credential arrives through a file in the
    data directory the shell already points the core at, and this model is the
    shape of that file.

    All three fields are optional and may be blank: an empty `api_key` is the
    analyst clearing the setting, and the two public values fall back to the
    defaults the adapters already hold when the core answers status. The
    response never carries the key back out - only whether one is set, so the
    surface can show a present key without echoing it into a webview that can
    read it or a log line that can capture it.
    """

    api_key: str = ""
    model: str = ""
    base_url: str = ""


class LogView(BaseModel):
    """The tail of the core's own log (P5-OBSERVE-002).

    Read-only: a support question is answered by the last thing that happened,
    so this hands back the path, its size, the rotated backups' names and the
    most recent lines. `enabled` is False when file logging is off (an
    unwritable data dir, or a core running under pytest) - that is a state to
    report, not an error to raise, so the shell can say "logging is off"
    instead of guessing why a log is missing.
    """

    enabled: bool
    path: str | None
    size_bytes: int
    rotated: list[str]
    lines: list[str]


class AxisFinding(BaseModel):
    """One axis of an EVALUATE audit: a verdict and a sentence."""

    axis: str
    verdict: str
    detail: str


class Evaluation(BaseModel):
    """An EVALUATE-mode audit of submitted analytical work (P7-EVAL-001).

    Nine axes, each a verdict and a sentence a reader can act on. The verdicts
    are pass / concern / fail rather than a score, because a single number would
    imply a precision nine heterogenous axes do not have. Every verdict is
    derived from the profile, the code or the run the code produced - never from
    the claim's own confidence.
    """

    id: str
    case_id: str
    dataset_id: str
    run_id: str | None
    artifact_kind: str
    code: str
    claim: str
    findings: list[AxisFinding]
    source: str
    created_at: str


class EvaluationCreate(BaseModel):
    """A submitted artifact and the claim it is offered as evidence for."""

    code: str
    claim: str
    kind: str = "sql"


class UpdateCheckResult(BaseModel):
    """Whether a newer published build exists (P6-UPDATE-005).

    Three answers, and they are not interchangeable: `current` is the claim
    that the feed was reached and nothing newer exists; `available` is the
    claim that it was reached and something newer does exist, carrying the
    tag, the release page and the published notes; `unknown` is the honest
    "could not tell", and its `reason` is the sentence to show a user. An
    unreachable feed, a private repository, a rate limit and a malformed body
    are all `unknown` - never a silent `current`, because "could not check"
    and "is up to date" are different statements and only one is true.
    """

    status: str
    current: str
    latest: str | None = None
    page_url: str | None = None
    notes: str | None = None
    reason: str | None = None


class SchemaMigrationRecord(BaseModel):
    """One migration that actually ran against this store."""

    version: int
    name: str
    applied_at: str


class SchemaVersion(BaseModel):
    """The shape of the local store, and whether this build understands it.

    The answer to "is my data safe with this build": `current` is True when the
    store's recorded schema is the one this core knows. A store above the
    target is not downgraded and not served - `GET /schema-version` still
    reports it, so the mismatch is visible rather than silent. `migrations` is
    the audit trail of what was applied and when; it is empty for a store
    created by this build, which was born current and had nothing applied.
    """

    version: int
    target: int
    current: bool
    migrations: list[SchemaMigrationRecord]


class EnvelopeFormat(BaseModel):
    """One file format's declared size limits (AT-45)."""

    max_rows: int
    max_columns: int


class DatasetEnvelope(BaseModel):
    """The dataset sizes this build supports, published rather than assumed.

    AT-45 requires the MVP to define its envelope explicitly instead of
    claiming unlimited scale. A file beyond it is refused at attach with a
    sentence naming the limit, so the analyst learns the boundary from the
    product instead of a hang.
    """

    formats: dict[str, EnvelopeFormat]


class CaseEnvelope(BaseModel):
    """The case sizes this build supports (AT-46).

    Engineering benchmark limits rather than conceptual ones: the measurement
    layer builds a case at the boundary and asserts it stays stable.
    """

    max_runs: int
    max_results: int
    max_findings: int
    max_evidence_relationships: int


class Envelope(BaseModel):
    """The whole supported envelope, as `GET /envelope` publishes it.

    Read-only by construction: a GET with no body and no path parameters can
    write nothing, and the limits it reports are the values this build was
    configured with.
    """

    datasets: DatasetEnvelope
    cases: CaseEnvelope
