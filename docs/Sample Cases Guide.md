# Sample Cases — a detailed guide

The app opens with three worked cases already in the store, each stopped at a
different point on purpose. Together they show the whole ladder the product
walks: one closed loop, one mid-flight decision, one clean starting point.

If the case list is empty, the app is probably showing a stale window — press
**Cmd+R** to reload. If the store really is empty (a fresh install, or a wiped
data dir), the three cases can be recreated: create each case in the shell,
attach the CSV shown under its heading, and click **Profile**. Everything else
in each case is one button per step, in the order listed.

---

## The loop, in one breath

Every case in this product is the same shape, and the shell is the same panels
in the same order:

```
attach a dataset → profile → plan → run SQL → interpret → draft a finding
   → accept the finding → validate it → (the reviewer audits it)
```

The panels you will see, top to bottom:

| Panel | What it is |
|---|---|
| **Where this case stands** | The derived stage and the single next action |
| **Learn this case** | The same work as a Why → What → How → Validate walk |
| **Data** | Attached files and their profile (rows, columns, nulls, duplicates) |
| *Ask for the computation* | Type a question, get read-only SQL or Python proposed |
| **Runs** | What has executed; each run offers **Interpret** and **Draft a finding** |
| **Findings** | Accepted findings, each with a **Validate** button |
| **Agent** / **Reviewer** | A plan that proposes its own next step, one approved write at a time |
| **Ask this case** | Questions answered from the case's own artifacts, with citations |
| **Explore the data (EDA)** | Segment / correlate / distribution as read-only SQL |
| **Audit submitted work (EVALUATE)** | Judge code against a claim, nine axes |
| **Evidence graph** / **Case history** | What each artifact rests on, and everything that happened |

One rule holds throughout: **a proposal writes nothing.** Generating code,
interpreting a run and drafting a finding are all reads. Nothing becomes
evidence until you click the button that owns the write.

---

## Case 1 — "Why did western region revenue dip in Q3?"

**The finished one.** This is what a completed analysis looks like, so it is
the best place to simply *look around* before you try to drive.

```
sales_q3.csv
order_id,quarter,region,revenue
101,2024q2,north,4200.0
102,2024q2,south,3100.0
103,2024q2,west,5400.0
104,2024q3,north,3800.0
105,2024q3,south,2900.0
106,2024q3,west,          <- revenue is NULL: the honest explanation of the dip
107,2024q3,west,2700.0
103,2024q2,west,5400.0     <- an exact duplicate row
```

**What is already in the case:** a profile (8 rows, 4 columns, 1 duplicate, 1
null revenue), a plan, a `GROUP BY region, quarter` run, an interpretation, an
accepted finding, a bar chart, and a validation.

### What to do with it

1. **Read "Where this case stands" first.** It should say the loop closed. This
   is the panel to check on every case — it names the one action that matters
   now, rather than listing everything you could do.
2. **Open "Learn this case".** The four phases (Why, What, How, Validate) walk
   the same work this case already did, and each phase names the question a
   learner should be able to answer before moving on. It ends by saying the
   trust loop *ran* — not that the answer is right.
3. **Read the run before the finding.** The grouped result is the whole story:

   ```
   region  quarter  total    rows
   west    2024q2   10800.0  2     <- inflated: the duplicate row counts twice
   north   2024q2    4200.0  1
   north   2024q3    3800.0  1
   south   2024q2    3100.0  1
   south   2024q3    2900.0  1
   west    2024q3    2700.0  2     <- the null revenue counts as a row, not a value
   ```

   Both west groups carry `rows = 2` for opposite reasons: Q2's total is
   *inflated* by the duplicate, Q3's is *deflated* by the null. The finding
   says "west has the highest total at 10800.0" — which is arithmetically true
   and substantively misleading, because 5400 of it is the same order twice.
   That gap between a true number and a defensible claim is what the rest of
   the loop exists to close.
4. **Now read the finding and its status line: `partially_supported`.** Click
   **Validate** and read the per-check list. Reproducibility passes; the
   missing-data check fails, because order 106 has no revenue. This is the
   most important thing to understand about the product: a finding that does
   not survive contact with its own data says so, out loud, instead of
   presenting a clean number.
5. **Open the Evidence graph.** Follow the finding back to the run, and the run
   back to the dataset. The claim rests on named artifacts you can open, not on
   a paragraph of prose.
6. **Open Case history** for the full timeline of what happened, in order.
7. **Try the chart.** The seeded chart is a bar of `total` by `region`, and
   because the run grouped by quarter as well, each region gets a bar per
   quarter — the Q2/Q3 contrast *is* the dip. Try re-charting with `quarter`
   as the series to see the same numbers separated.

### Then try the agent

Scroll to the **Agent** panel and click **Propose the next step**. On a closed
case the honest answer is that *no further step is derivable from the case as
it stands* — which is the correct behaviour, not a dead end. If you then add a
second dataset or reject the finding, re-derive and watch it propose again.

The **Reviewer** panel beside it is a second agent whose entire method is
audit: it looks for the first finding with no evaluation and proposes auditing
the run that backs it. Approve it and read the nine-axis verdict.

---

## Case 2 — "Does marketing spend drive signups?"

**The decision point.** Everything up to the finding is done; the draft is
sitting in the panel waiting for a human. This is the case that teaches you
what a draft *is*.

```
spend.csv
month,spend,signups
2024-01,1200.0,310
2024-02,1400.0,365
2024-03,1100.0,290
2024-04,1800.0,480
2024-05,1900.0,505
2024-06,1600.0,420
```

### What to do with it

1. Open **Runs** and expand the run. It is a simple `SELECT month, spend,
   signups ... ORDER BY spend` — six rows, no aggregation.
2. Click **Interpret**. Read the summary, the observations, and the caveats.
   The caveats are the point: the engine says what it *cannot* conclude.
3. Click **Draft a finding**. Read the draft carefully — its statement, its
   interpretation, its caveat, and the grounds chips beneath it. Each chip is
   an artifact the claim rests on.
4. **Now the actual decision.** Notice what the draft does *not* say: it does
   not claim spend *causes* signups, because six rows cannot support that. You
   have three honest options:
   - **Accept as a finding** — the statement becomes real evidence, with
     status `not_evaluated` until you validate it.
   - **Edit and accept** — copy the statement, adjust it, and post it via the
     findings endpoint (or accept then refine). The draft is a proposal; the
     finding is yours.
   - **Leave it** — a draft that is never accepted writes nothing, and that is
     a valid outcome.
5. If you accept, click **Validate** on the finding and read the verdict. Then
   try the **Reviewer** panel: it will propose auditing exactly this finding,
   because it is now the case's first finding without an evaluation.

### The trap this case is here for

Two adjacent boxes look similar: **Ask for the computation** ("What would you
like to know?") and **Ask this case** ("How many datasets does this case
have?"). They do different things — the first proposes code, the second
answers a question from the case's own artifacts. It is easy to type a
question into the wrong one. Both are safe (neither writes), but the result
will look confused if you do.

---

## Case 3 — "Which support category is slowest to resolve?"

**The clean slate.** Nothing has run but the profile. Use this one to drive
the loop yourself, end to end, with the safety rail on.

```
tickets.csv
ticket_id,category,priority,minutes_to_resolve
1,billing,high,42
2,billing,low,190
3,access,high,35
4,billing,medium,88
5,access,low,240
6,access,medium,120
7,billing,high,51
```

The answer here is real and it is *not* the obvious one: `access` averages
131.7 minutes against `billing`'s 92.8, and the slowest single ticket (240)
is low-priority access. Priority and category cross-cut — a flat "billing vs
access" number hides that.

### Drive it, step by step

1. **Read the profile.** Seven rows, four columns, no nulls, no duplicates —
   the cleanest dataset of the three, so the honesty budget has nothing to
   trip on and the validation should come back fully supported.
2. **Ask for the computation.** Type something like
   `average minutes to resolve by category` and click **Generate code**.
   Read the proposal: the explanation, the columns it reads, and the code.
   Notice it is read-only — a write is rejected before it executes.
3. Click **Run this**. The result appears under **Runs**.
4. Click **Interpret**, then **Draft a finding**.
5. **Accept as a finding**, then **Validate**.
6. **Render a chart**: under the run, chart `avg_minutes` by `category`.
7. **Now the interesting move** — ask a question the first query cannot
   answer. Generate code for
   `average minutes by category and priority` and look at the cross-cut. Then
   try the EDA panel's *segment* operation with the same two columns.
8. **Ask this case**: `which category is slowest?` and read the cited answer.
   Every claim in the reply is a chip you can trace.
9. **Let the agent drive.** In the **Agent** panel click **Propose the next
   step**. It will propose profile → plan → analyze → interpret → accept →
   chart → validate, one step at a time. **Approve and run** each, or
   **Reject** with a reason (the reason is recorded with the step, not
   discarded). This is the loop from cases 1 and 2, but proposed by the
   product instead of by you — with the human approving every write.
10. **Promote a template** when you are done: the case's analytical shape
    (plan, proposals, how its findings validated) becomes a reusable starting
    point for the next case.

---

## What to expect from the deterministic engine

By default no LLM is configured, so the planner, interpreter and drafter are
**deterministic**: fast, offline, and deliberately blunt. Case 1's finding
reads "west has the highest total at 10800.0" — true, cited, and about as
insightful as a calculator. That is the honest floor: it cannot invent an
explanation it cannot ground.

The trade-off is worth knowing. To get richer drafts and plans, put an API key
in `server/.env` (`DAH_LLM_API_KEY`, `DAH_LLM_BASE_URL`, `DAH_LLM_MODEL`) and
restart the core. Every answer records its `source` — `deterministic` or `llm`
— so you always know which engine spoke, and the honesty budgets apply to
both: an LLM answer that cites a column that does not exist is rejected, not
rendered.

## If something looks wrong

- **Empty case list** — reload with Cmd+R. The core is on `127.0.0.1:8123`;
  `GET /cases` answers it directly.
- **A CSV "profiles as one column"** — a row with a stray trailing comma used
  to collapse the whole file; that is fixed, and the stray cell now becomes a
  null the profile reports. If you see one column where you expected several,
  check the raw file for a row wider than its header.
- **"not_evaluated" on a finding** — that is the state before validation, not
  an error. Click **Validate**.
- **A proposed step you disagree with** — **Reject** it with a reason. The
  rejection is recorded in the case's history and writes nothing else.
