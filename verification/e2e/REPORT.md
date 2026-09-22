# End-to-End Verification (real server)

Run: 2026-09-22T03:57:58.129717+00:00
Outcome: PASS (17.8s)

A fresh uvicorn server on a free port with an isolated data dir, driven
over real HTTP. No LLM key is passed to the server, so the deterministic
engines answer and the run is reproducible offline.

| Step | Verdict | Detail |
|------|---------|--------|
| Store opens at the build's schema | PASS | version 11 of 11, 0 migration(s) applied |
| Case created | PASS | question='Why did revenue change between the first two quarters?' |
| Dataset attached over multipart | PASS | sales.csv (csv) |
| Profile counts the null and the duplicate | PASS | rows=5, columns=['order_id', 'quarter', 'revenue', 'region'], revenue nulls=1, duplicates=1 |
| Plan derived | PASS | source=deterministic, keys=['analysis_steps', 'context_basis', 'data_requirements', 'hypotheses', 'objective', 'primary_question', 'sub_questions'] |
| Generated SQL runs | PASS | row_count=2, totals={'2024q2': 3, '2024q1': 2} |
| A write is refused | PASS | HTTP 400: only single read-only SELECT queries are supported |
| A drafted finding is accepted | PASS | statement=row_count spans 2 to 3 across 2 row(s)... |
| The finding validates, and the null is flagged | PASS | status=partially_supported, calculation=rerun matches stored result, data=flagged |
| EVALUATE answers all nine axes | PASS | 6 pass, 2 concern, 1 fail |
| The reviewer's GET proposes nothing | PASS | pending is null on a read |
| The reviewer proposes the finding's audit | PASS | kind=evaluate, claim is the finding's own statement |
| A cross-role approval is refused | PASS | HTTP 409, names the analyst's own pending step |
| The approved audit records its verdict | PASS | audited finding 73c48f70-944c-4f4e-bb4f-6b74de9bb303: 9 axes, 7 pass, 2 concern, 0 fail |
| An audited finding is not re-audited | PASS | the reviewer's next derivation has nothing pending |
| An unknown role is named, not guessed | PASS | HTTP 400 names the roles |
| The evidence graph traces the claim | PASS | counts={'datasets': 1, 'runs': 3, 'charts': 0, 'plans': 1, 'findings': 1, 'edges': 5} |
| The case history is the whole timeline | PASS | 8 events, kinds=['charts', 'datasets', 'findings', 'plans', 'profiles', 'runs'] |
| The LEARN walk is the spec's four phases | PASS | why, what, how, validate; work on now: how |
| The case answers with citations | PASS | source=deterministic, 2 ground(s) |
| The case round-trips through export | PASS | restored as b1512a7f with fresh ids |
| The analyst agent drives the loop to a stop | PASS | approved=7, rejected=0, steps=profile->plan->analyze->interpret->accept->chart->validate; stopped: no further step |
| Every agent step names its engine | PASS | sources=['deterministic'], 7 step(s) recorded |
| The agent-run case reaches a stated stage | PASS | stage=validated, loop_closed=True |
