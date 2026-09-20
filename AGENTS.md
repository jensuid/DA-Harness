## session resumption

Before starting any work in this repo, read `ai/HANDOFF.md` (entry point: what is
done, what is in flight, unresolved problems, next action) and `ai/TASKS.md`
(per-task contracts with acceptance criteria; it holds only the phase summary tables, the still-open carried follow-ups and the rolling window - the two most recent tasks - with everything older in `ai/TASKS-ARCHIVE.md`). `ai/CURRENT_STATE.md` holds phase,
test counts, and blockers. This is how a fresh session resumes in-flight work
without re-deriving it; if the user's request is clearly a continuation, do this
read first, then ask questions only if the handoff leaves the intent ambiguous.
After finishing a task, update these same files so the next session can resume
from them.

## task backlog hygiene

`ai/TASKS.md` is the working surface a session actually reads, so it stays
small. It holds, and only holds:

- the title and the phase summary tables (the `## Pn` tables, one row per task
  across every phase - those stay regardless of age, they are the index);
- `### Carried follow-ups (still open)` and any block with unchecked
  acceptance criteria;
- the rolling window: the most recently completed task block and the one
  immediately preceding it.

Everything else - every older `### <TASK-ID> contract` block and its
`TASK: ... STATUS: DONE` record - lives in `ai/TASKS-ARCHIVE.md`.

**Archival happens in the same commit that completes a task.** When a task's
acceptance criteria pass and its commit is being prepared, move the block that
the *newly completed* task pushes out of the window into
`ai/TASKS-ARCHIVE.md` as part of that same commit, so the push that lands the
task also lands the trimmed backlog. A task block is moved verbatim, never
edited or summarised - the archive is the record, and rewriting it on the way
in is how a lesson gets lost. Never delete a task block; it is either in
`TASKS.md` or in `TASKS-ARCHIVE.md`, always exactly one of the two.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## commit and push discipline

This repo commits and pushes continuously so any session can resume from the
remote. Follow these rules without being asked.

- **One commit per task.** When a task's acceptance criteria pass and its
  verification runs green, commit immediately: implementation + tests + the
  `ai/` state updates (`HANDOFF.md`, `TASKS.md`, `CURRENT_STATE.md`) in a
  single commit, then `git push origin master`. Do not accumulate finished
  tasks into one commit - per-task history is what makes a fresh session
  resumable.
- **One commit per phase close.** When a phase gate passes, commit the gate
  report plus the roadmap/state doc updates (`ai/ROADMAP.md` stage marker,
  phase table, next-phase checklist) as its own commit, then push.
- **Green state only.** Tests and the verification gate must pass before a
  commit exists. Never commit work in progress; leave it uncommitted and
  record it in `ai/HANDOFF.md` instead.
- **Every commit is atomic and self-consistent:** it builds and tests green on
  its own, and its `ai/` updates describe exactly what it changed.
- **Commit message conventions:**
  - task: `<TASK-ID>: <imperative summary>` (e.g. `P2-ANALYSIS-008: read-only Python execution`)
  - phase close: `docs: mark <Pn> <name> complete; refresh verification reports`
- **Never commit secrets.** `DAH_LLM_API_KEY` and friends are environment-only;
  `.env` is gitignored. Never add a key value to a file.
- **Never rewrite pushed history.** No force push, no rebase of commits already
  on `origin/master`. Fix forward with a new commit.
- **Confirm the push succeeded** and the working tree is clean before reporting
  a task as done; a task is not done until it is on the remote.
- After modifying code, run `graphify update .` before committing so the
  knowledge graph the graphify rules depend on stays current.
