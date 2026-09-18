## session resumption

Before starting any work in this repo, read `ai/HANDOFF.md` (entry point: what is
done, what is in flight, unresolved problems, next action) and `ai/TASKS.md`
(per-task contracts with acceptance criteria). `ai/CURRENT_STATE.md` holds phase,
test counts, and blockers. This is how a fresh session resumes in-flight work
without re-deriving it; if the user's request is clearly a continuation, do this
read first, then ask questions only if the handoff leaves the intent ambiguous.
After finishing a task, update these same files so the next session can resume
from them.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
