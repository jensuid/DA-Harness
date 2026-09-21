# Data Analysis Harness

## UX/UI Architecture

**Artifact:** 06  
**Version:** 1.0  
**Status:** Master UX/UI Specification  
**Product:** Data Analysis Harness (DAH)  
**Design Direction:** Modern Analytical Workspace

---

# 1. UX/UI Design Thesis

DAH should **not look like an old-fashioned BI application**.

Avoid:

- dashboard-first interface
    
- dense enterprise panels
    
- endless configuration dialogs
    
- spreadsheet-like primary experience
    
- chatbot as the main interface
    
- excessive tabs
    
- decorative dashboards
    
- large collections of isolated charts
    
- command-heavy workflows
    
- information overload
    

Instead:

> **DAH is a modern analytical workspace where the user always knows what they are solving, what evidence they have, what they have discovered, and what still needs validation.**

The interface should feel closer to:

**Modern IDE + Notion-like workspace + analytical notebook + AI copilot**

rather than:

**Traditional BI dashboard + spreadsheet + chatbot.**

---

# 2. Core UX Mental Model

The primary UX model is:

```text
                ANALYSIS CASE
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
     CONTEXT       DATA        QUESTION
        │            │            │
        └────────────┼────────────┘
                     ↓
                  EXPLORE
                     ↓
                  ANALYZE
                     ↓
                  EVIDENCE
                     ↓
                 VALIDATE
                     ↓
                  FINDING
                     ↓
                 DECISION
```

The UI should visually reinforce this model.

The user should never feel:

> "Where am I?"

They should always understand:

> **Where am I in the analysis? What do I know? What should I do next?**

---

# 3. Primary UX Principle

## Progressive Disclosure

Do not show everything simultaneously.

Reveal complexity only when needed.

```text
Simple question
      ↓
Basic workspace
      ↓
Need more detail?
      ↓
Advanced analysis
      ↓
Need technical control?
      ↓
SQL / Python / diagnostics
```

Therefore:

> **Simple by default. Powerful when needed.**

---

# 4. Primary Navigation Model

Use a **Case-Centric Workspace** rather than application-centric navigation.

### Global Navigation

```text
┌──────────────────────────────────────────────┐
│ DAH                         Search   Profile │
├──────────────┬───────────────────────────────┤
│              │                               │
│ Cases        │                               │
│              │        WORKSPACE              │
│ Recent       │                               │
│ Templates    │                               │
│              │                               │
│ Knowledge    │                               │
│              │                               │
│ Settings     │                               │
│              │                               │
└──────────────┴───────────────────────────────┘
```

Keep global navigation small.

Recommended:

- **Cases**
    
- **Templates**
    
- **Knowledge**
    
- **Settings**
    

Everything else belongs inside an Analysis Case.

---

# 5. Analysis Case UX

The Analysis Case is the center of the application.

Opening a case should produce:

```text
┌────────────────────────────────────────────────────┐
│ ← Cases     Revenue Decline Investigation     ••• │
├────────────────────────────────────────────────────┤
│                                                    │
│ Purpose → Question → Data → Explore → Analyze     │
│          → Evidence → Validate → Findings         │
│                                                    │
├────────────────────────────────────────────────────┤
│                                                    │
│              CURRENT WORKSPACE                     │
│                                                    │
│                                                    │
│                                                    │
└────────────────────────────────────────────────────┘
```

The workflow indicator should remain visible.

This creates a persistent orientation mechanism.

---

# 6. Modern Workflow Navigation

Use a **horizontal analytical journey** rather than traditional nested menus.

```text
Purpose
   ↓
Question
   ↓
Context
   ↓
Data
   ↓
Quality
   ↓
Explore
   ↓
Analyze
   ↓
Evidence
   ↓
Validate
   ↓
Findings
   ↓
Decision
```

However, this should **not behave like a rigid wizard**.

Users must be able to move backward and revisit previous stages.

Therefore:

> **Guided workflow, not forced workflow.**

---

# 7. Stage Status

Every stage should communicate state.

Example:

```text
✓ Purpose
✓ Question
✓ Context
✓ Data
⚠ Quality
● Explore
○ Analyze
○ Evidence
○ Validate
○ Findings
```

Meaning:

- `✓` complete
    
- `⚠` requires attention
    
- `●` active
    
- `○` not started
    

This gives the user a continuous analytical status map.

---

# 8. Main Workspace Layout

The primary workspace should use a flexible **three-zone model**.

```text
┌─────────────────────────────────────────────────────────┐
│ Case / Stage / Actions                                  │
├──────────────┬──────────────────────────┬───────────────┤
│              │                          │               │
│ CASE         │      WORKSPACE           │   CONTEXT     │
│ NAVIGATION   │                          │   / AI        │
│              │                          │               │
│ stages       │ tables                   │ AI assistant  │
│ evidence     │ charts                   │ suggestions   │
│ findings     │ analysis                 │ validation    │
│ data         │ code                     │ evidence      │
│              │                          │               │
├──────────────┴──────────────────────────┴───────────────┤
│ Status / execution / notifications                      │
└─────────────────────────────────────────────────────────┘
```

### Left

**Orientation**

- case stages
    
- datasets
    
- findings
    
- evidence
    
- analysis history
    

### Center

**Work**

- tables
    
- charts
    
- analysis
    
- code
    
- results
    
- writing
    

### Right

**Intelligence**

- AI assistance
    
- context
    
- suggestions
    
- validation
    
- evidence
    
- warnings
    

The three zones represent:

> **Where am I? → What am I doing? → What can help me?**

---

# 9. Adaptive Workspace

The three-column structure should not always remain fixed.

For example:

### Exploration

Center becomes large.

```text
LEFT       CENTER                    RIGHT
Navigation │ Charts / Tables         │ AI
           │                         │
           │                         │
```

### Coding

```text
LEFT       CENTER                    RIGHT
Navigation │ Code                    │ AI
           │                         │ Diagnostics
           │                         │ Results
```

### Validation

```text
LEFT       CENTER                    RIGHT
Findings   │ Validation              │ Evidence
           │ checklist               │ sources
```

### Finding creation

```text
LEFT       CENTER                    RIGHT
Evidence   │ Finding editor          │ Supporting
           │                         │ evidence
```

The interface adapts to the user's current analytical activity.

---

# 10. Home / Case Dashboard

Do **not** make the home screen a traditional KPI dashboard.

Instead, make it a **work launcher**.

```text
Good morning

Continue analysis
────────────────────────────────────

Revenue Decline Investigation
Analyze • 68% complete

Customer Churn Analysis
Validate • 82% complete

Marketing Campaign Review
Explore • 41% complete


────────────────────────────────────

+ New Analysis Case

Start from:
• Blank case
• Template
• Existing case
• Dataset
```

The purpose of Home is:

> **Resume work or start an investigation.**

Not:

> Show 30 charts.

---

# 11. Create Analysis UX

Creating a case should feel lightweight.

Instead of a large configuration form:

```text
New Analysis

What are you trying to understand?

[ Why did monthly revenue decline?              ]

Optional context

[ Revenue dropped ~15% during Q2...             ]

Add data

[ Drop files here ]

              Create Analysis →
```

DAH can then generate:

```text
Potential objective
Primary question
Sub-questions
Initial hypotheses
Data requirements
Suggested analysis plan
```

The user reviews these rather than manually configuring everything.

---

# 12. Question Refinement UX

The system should help transform:

> "Why are sales down?"

into:

> "What factors explain the 15% decline in monthly revenue during Q2 compared with Q1?"

The UI should show the transformation explicitly.

```text
YOUR QUESTION

Why are sales down?

        ↓ AI suggestion

REFINED QUESTION

What factors explain the decline in
monthly revenue during Q2 vs Q1?

        ↓

[Accept] [Edit] [Keep original]
```

AI should propose rather than silently rewrite.

---

# 13. Context UX

Context should be treated as a first-class analytical object.

Example:

```text
Context

Business objective
────────────────────────
Understand the Q2 revenue decline.

Time period
────────────────────────
Jan – Jun 2026

Relevant business changes
────────────────────────
• Pricing changed in April
• Campaign ended in March

Known constraints
────────────────────────
• Customer-level data unavailable
```

Context becomes available to the AI and analytical workflow.

---

# 14. Data Workspace

The Data stage should provide an immediate understanding of the dataset.

```text
Customers.csv

1.2M rows
38 columns

Quality
──────────────────
✓ Schema detected
⚠ 4.2% missing values
⚠ 2.1% duplicate records
✓ Date range identified

Columns
──────────────────
customer_id
signup_date
country
plan
revenue
...
```

The UI should prioritize **meaningful diagnostics** over raw technical metadata.

---

# 15. Data Quality UX

Data quality should be visible before analysis.

Example:

```text
DATA QUALITY

Overall
────────────────
Needs attention

Missing values       ⚠
Duplicates            ⚠
Data types            ✓
Date coverage         ✓
Outliers              ⚠
Relationships         ?

Potential impact

Revenue contains 4.8% missing values.
This may affect revenue comparison.

[Inspect] [Continue anyway]
```

Never hide important analytical risks.

---

# 16. Exploration UX

EDA should feel visual and interactive.

```text
Explore

Suggested questions

┌──────────────────────────────────┐
│ How has revenue changed over    │
│ time?                            │
│                                  │
│ [Explore]                        │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ Which segments changed most?     │
│                                  │
│ [Explore]                        │
└──────────────────────────────────┘
```

AI can suggest explorations based on:

- question
    
- data
    
- context
    
- previous findings
    

But the user remains in control.

---

# 17. Analysis Workspace

The central analysis workspace should support multiple analytical objects.

```text
Analysis

┌──────────────────────────────────────┐
│ Result                               │
│                                      │
│ Revenue declined 15.2% in Q2        │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │             CHART                │ │
│ │                                  │ │
│ └──────────────────────────────────┘ │
│                                      │
│ SQL                                  │
│ [ View query ]                       │
│                                      │
│ Execution: 1.4 sec                   │
└──────────────────────────────────────┘
```

Every important result should have a relationship to:

**computation → evidence → finding**

---

# 18. Analysis Canvas

A powerful future UX concept is an **Analysis Canvas**.

Users can arrange:

```text
Question
   ↓
Dataset
   ↓
Analysis
   ↓
Result
   ↓
Finding
   ↓
Validation
```

Example:

```text
┌──────────────┐
│ Question     │
│ Revenue ↓ ?  │
└──────┬───────┘
       ↓
┌──────────────┐
│ Analysis     │
│ Revenue by   │
│ segment      │
└──────┬───────┘
       ↓
┌──────────────┐
│ Result       │
│ Enterprise   │
│ −24%         │
└──────┬───────┘
       ↓
┌──────────────┐
│ Finding      │
│ Enterprise   │
│ segment drove│
│ decline      │
└──────────────┘
```

This creates a visual reasoning graph.

This should be a later-stage feature rather than an MVP requirement.

---

# 19. Evidence UX

Evidence should be extremely visible.

When a user creates a finding:

```text
Finding

"Enterprise revenue declined 24% in Q2."

Evidence

✓ Result #12
✓ SQL query #12
✓ Dataset: sales.parquet
✓ Time period: Q1 → Q2

Validation

⚠ Segment mix changed during the period.

Confidence / limitations

The finding describes association.
It does not establish causation.
```

This directly reinforces DAH's trust model.

---

# 20. Finding UX

Findings should be treated as structured objects.

```text
Finding

Claim
────────────────────
Enterprise revenue declined 24% in Q2.

Evidence
────────────────────
Result #12

Method
────────────────────
Segment revenue comparison

Validation
────────────────────
✓ Calculation verified
✓ Comparison period verified
⚠ Potential confounding factor

Limitation
────────────────────
Does not establish causal explanation.
```

This is fundamentally different from simply writing a paragraph in a report.

---

# 21. Validation UX

Validation should be visual and actionable.

```text
Validate Finding

✓ Calculation
✓ Dataset
✓ Time period
✓ Comparison population

⚠ Missing data
⚠ Alternative explanation

✕ Causal claim unsupported
```

The user should immediately understand:

> **What has been verified and what remains uncertain?**

---

# 22. AI Assistant UX

The AI should **not dominate the application**.

Avoid:

```text
CHATBOT
"How can I help?"
```

Instead, AI should be contextual.

Example:

```text
AI

Current stage: Explore

Based on your question and dataset:

1. Compare revenue by segment
2. Check monthly trend
3. Examine customer count
4. Investigate pricing change

Why these?

They directly test the current hypotheses.

[Run] [Explain] [Dismiss]
```

This is:

> **Contextual Copilot**

rather than:

> **Generic Chatbot**

---

# 23. AI Interaction Model

Use three interaction levels.

### Level 1 — Suggestions

```text
AI suggests
↓
User accepts
```

### Level 2 — Assisted execution

```text
AI proposes analysis
↓
User reviews
↓
Harness executes
```

### Level 3 — Advanced agentic assistance

Future:

```text
Goal
 ↓
AI creates plan
 ↓
Harness executes controlled steps
 ↓
Results recorded
 ↓
AI interprets
 ↓
Validation
 ↓
Human approval
```

Never allow AI to bypass the Harness.

---

# 24. AI Actions

Every AI-generated action should communicate:

**What**  
**Why**  
**Evidence**  
**Impact**

Example:

```text
Suggested analysis

Compare Q2 vs Q1 revenue by customer segment.

Reason:
Tests whether the decline is concentrated
in a specific segment.

Data:
sales.parquet

Action:
Generate SQL + execute

[Review] [Run]
```

---

# 25. SQL / Python UX

Technical users should have access to the underlying computation.

But code should be **progressively disclosed**.

Default:

```text
Result
Revenue decreased 15.2%

[Show computation]
```

Expanded:

```text
SQL
────────────────────────
SELECT ...

[Run] [Edit] [Save]
```

Python can follow the same model.

This prevents technical complexity from overwhelming non-technical users.

---

# 26. Result Object UX

Every analytical result should expose:

```text
RESULT

What
────────────
Revenue declined 15.2%.

How
────────────
SQL comparison

Data
────────────
sales.parquet

When
────────────
Executed Sep 19, 2026

Computation
────────────
[View SQL]

Evidence
────────────
[Attach to finding]
```

This creates traceability.

---

# 27. Modern Interaction Patterns

Prefer:

- inline editing
    
- command palette
    
- keyboard shortcuts
    
- drag-and-drop files
    
- contextual actions
    
- smart suggestions
    
- expandable detail
    
- side sheets
    
- floating action controls
    
- non-blocking notifications
    
- autosave
    
- undo where appropriate
    
- progressive disclosure
    
- persistent state
    
- quick search
    

Avoid excessive:

- modal dialogs
    
- wizard chains
    
- nested menus
    
- confirmation dialogs
    
- full-page reloads
    
- configuration screens
    
- dense tables as the default UI
    

---

# 28. Command Palette

A command palette should eventually provide:

```text
⌘K

Search or run command

Create finding
Run analysis
Open dataset
Search evidence
Ask AI
Validate finding
Export case
Jump to Question
Jump to Data
Jump to Findings
```

This provides power-user acceleration without cluttering the UI.

---

# 29. Search

Search should operate across the **Analysis Case**, not only filenames.

Search:

```text
"revenue decline"
```

can return:

- questions
    
- findings
    
- datasets
    
- analysis runs
    
- SQL
    
- evidence
    
- validation notes
    
- decisions
    

This reinforces the concept that the case is a connected analytical knowledge object.

---

# 30. Visual Design Language

## Overall character

DAH should feel:

- modern
    
- calm
    
- analytical
    
- precise
    
- premium
    
- trustworthy
    
- spacious
    
- focused
    

Avoid:

- corporate dashboard aesthetic
    
- excessive gradients
    
- visual noise
    
- rainbow charts
    
- overly decorative UI
    
- overly dark "developer tool" aesthetic
    
- old enterprise software appearance
    

---

# 31. Layout Principles

Use:

### 1. Strong hierarchy

```text
Page
 ↓
Section
 ↓
Object
 ↓
Detail
```

### 2. Generous spacing

Avoid dense information packing.

### 3. Visual grouping

Related information should appear physically together.

### 4. Stable orientation

The user should always know:

```text
Case
Stage
Current task
Status
Next useful action
```

---

# 32. Color System

Color should communicate **meaning**, not decoration.

Recommended semantic roles:

```text
Neutral      → normal information
Primary      → active interaction
Success      → verified / complete
Warning      → attention required
Error        → failure / blocking issue
Info         → explanation
```

Do not use color as the only indication.

Always combine with:

- icon
    
- text
    
- position
    
- state
    

---

# 33. Typography

Use a modern system/UI typeface.

Priorities:

1. readability
    
2. hierarchy
    
3. compact analytical notation
    
4. clear numbers
    
5. accessible contrast
    

Typography hierarchy should clearly distinguish:

```text
Case title
Stage
Section
Object
Metric
Supporting text
Metadata
```

---

# 34. Charts

Charts should communicate analytical meaning rather than decoration.

Default philosophy:

> **Few charts, high information value.**

Charts should support:

- comparison
    
- trend
    
- distribution
    
- relationship
    
- composition
    
- anomaly
    
- segmentation
    

Every chart should provide:

- title
    
- meaningful axes
    
- units
    
- relevant timeframe
    
- source/context
    
- optional computation
    

Avoid unnecessary chart decoration.

---

# 35. Tables

Tables should support investigation.

Required capabilities over time:

- sorting
    
- filtering
    
- search
    
- column visibility
    
- type-aware formatting
    
- pagination/virtualization
    
- copy
    
- export
    
- row inspection
    

Avoid making the entire application look like a spreadsheet.

---

# 36. Notifications

Use lightweight notifications.

Example:

```text
✓ Analysis completed
```

or:

```text
⚠ 4.8% missing revenue values may affect this result
```

Avoid intrusive popups.

---

# 37. Loading and Long-Running Operations

Never leave the user staring at a spinner.

Use:

```text
Analyzing revenue by segment...

✓ Loading data
✓ Computing groups
● Running comparison
○ Preparing result
```

For long operations:

- show progress where measurable
    
- allow cancellation
    
- preserve current work
    
- provide meaningful status
    

---

# 38. Error UX

Errors should explain:

```text
What happened
Why it happened
What can be done
```

Example:

```text
Analysis could not run.

Revenue column contains mixed data types.

Possible actions:

[Inspect column]
[Clean data]
[Choose another column]
```

Never show raw stack traces as the primary user experience.

Technical details may be expandable.

---

# 39. Empty States

Empty states should teach the workflow.

Example:

```text
No findings yet.

A finding connects an analytical claim
to evidence and validation.

Start by exploring your data.

[Explore Data]
```

Empty states are part of onboarding.

---

# 40. Responsive Behavior

Although the initial product is desktop-first, design the system responsively.

Desktop:

```text
Navigation | Workspace | AI
```

Smaller window:

```text
Navigation
     ↓
Workspace
     ↓
Context / AI as drawer
```

Do not simply shrink the desktop UI.

---

# 41. Accessibility

Design for:

- keyboard navigation
    
- visible focus
    
- readable typography
    
- sufficient contrast
    
- semantic controls
    
- screen-reader compatibility where practical
    
- non-color-only status indicators
    
- predictable interaction
    
- reduced-motion support
    

Accessibility is part of architecture, not post-processing.

---

# 42. UX State Model

Every major object should have explicit states.

Example:

```text
Analysis

Draft
 ↓
Ready
 ↓
Running
 ↓
Completed
 ↓
Validated
 ↓
Attached to Finding
```

And:

```text
Finding

Draft
 ↓
Evidence Attached
 ↓
Validation Pending
 ↓
Validated
 ↓
Published
```

This should exist in the domain model as well as the UI.

---

# 43. Trust UX

DAH should constantly distinguish:

```text
FACT
What the data directly shows.

ANALYSIS
What was computed.

INTERPRETATION
What the result may mean.

HYPOTHESIS
What might explain it.

ASSUMPTION
What we are assuming.

UNCERTAINTY
What remains unknown.

DECISION
What someone may choose to do.
```

This distinction is one of DAH's strongest UX differentiators.

---

# 44. Analytical Confidence

Avoid simplistic "AI confidence scores."

Instead communicate evidence quality using structured signals:

```text
Evidence quality

✓ Directly computed
✓ Source identified
✓ Calculation verified
⚠ Missing data
⚠ Alternative explanation
```

The UI should explain **why** something is trustworthy or uncertain.

---

# 45. Case Overview

Every case should have a concise overview.

```text
Revenue Decline Investigation

OBJECTIVE
Understand the Q2 revenue decline.

QUESTION
What factors explain the decline?

STATUS
7 / 10 stages complete

KEY FINDINGS
3

OPEN ISSUES
2

DATA SOURCES
3

VALIDATION
2 findings validated
1 pending
```

This becomes the analytical control center.

---

# 46. Decision View

The final stage should transform analysis into decision support.

```text
Decision Support

Question
────────────
What explains the revenue decline?

Key findings
────────────
1. Enterprise revenue declined 24%.
2. Customer volume declined 8%.
3. Pricing changed in April.

Evidence
────────────
[3 validated findings]

Uncertainty
────────────
Pricing impact cannot be isolated
from seasonal effects.

Potential implications
────────────
• Review enterprise pricing
• Investigate customer loss
• Compare seasonal baseline

[Export Analysis Case]
```

DAH should **inform decisions**, not make decisions for the user.

---

# 47. Case Export UX

Export should preserve analytical structure.

Possible outputs:

```text
Analysis Case
├── Executive Summary
├── Question
├── Context
├── Data
├── Quality
├── Methods
├── Results
├── Findings
├── Evidence
├── Validation
├── Limitations
└── Reproducibility
```

Future exports:

- PDF
    
- Markdown
    
- HTML
    
- notebook
    
- structured case package
    

---

# 48. Modern UX Flow

The complete primary flow:

```text
                    HOME
                      │
                      ↓
              CREATE CASE
                      │
                      ↓
             DEFINE PURPOSE
                      │
                      ↓
              REFINE QUESTION
                      │
                      ↓
                 ADD CONTEXT
                      │
                      ↓
                  ADD DATA
                      │
                      ↓
               CHECK QUALITY
                      │
                      ↓
                 EXPLORE
                      │
                      ↓
                 ANALYZE
                      │
              ┌───────┴───────┐
              ↓               ↓
             SQL            Python
              │               │
              └───────┬───────┘
                      ↓
                   RESULT
                      │
                      ↓
                  EVIDENCE
                      │
                      ↓
                  FINDING
                      │
                      ↓
                 VALIDATION
                      │
                      ↓
               DECISION SUPPORT
                      │
                      ↓
                   EXPORT
```

This is the primary UX backbone.

---

# 49. AI-Enhanced Modern Flow

With AI:

```text
User Problem
     ↓
AI helps clarify
     ↓
Harness structures
     ↓
AI proposes plan
     ↓
User reviews
     ↓
Harness executes
     ↓
Evidence recorded
     ↓
AI interprets
     ↓
Harness validates
     ↓
User approves finding
     ↓
Decision-ready case
```

The key UX principle:

> **AI is embedded into the workflow, not placed beside it as a separate chatbot.**

---

# 50. MVP UX Scope

Do not implement the entire UX architecture initially.

### P0

Build:

- application shell
    
- case list
    
- case creation
    
- basic navigation
    
- workflow indicator
    
- basic workspace
    
- persistence
    

### P1

Build:

- Purpose
    
- Question
    
- Data
    
- Quality
    
- Explore
    
- Analysis
    
- Evidence
    
- Finding
    
- Validation
    
- case overview
    

### P2

Add:

- SQL workspace
    
- Python workspace
    
- charts
    
- execution history
    
- contextual AI
    
- export
    
- command palette
    
- richer evidence interface
    

### P3

Add:

- Analysis Canvas
    
- visual reasoning graph
    
- reusable analysis blocks
    
- advanced search
    
- richer contextual AI
    
- multiple datasets
    
- advanced validation
    

---

# 51. MVP Screen Architecture

Initial application should require only a small number of major screens.

```text
APP
│
├── Home
│
├── Cases
│   └── Case Overview
│
└── Analysis Workspace
    ├── Purpose
    ├── Question
    ├── Context
    ├── Data
    ├── Quality
    ├── Explore
    ├── Analyze
    ├── Evidence
    ├── Validate
    └── Findings
```

Do not create a separate page for every minor feature.

---

# 52. Component Architecture

Recommended conceptual component hierarchy:

```text
AppShell
│
├── GlobalNav
│
├── CaseShell
│   ├── CaseHeader
│   ├── WorkflowNavigator
│   ├── CaseSidebar
│   └── Workspace
│       ├── MainPanel
│       └── ContextPanel
│
├── DataComponents
│   ├── DatasetCard
│   ├── SchemaView
│   ├── QualityReport
│   └── DataPreview
│
├── AnalysisComponents
│   ├── AnalysisCard
│   ├── ResultView
│   ├── ChartView
│   ├── SQLView
│   └── PythonView
│
├── EvidenceComponents
│   ├── EvidenceCard
│   ├── EvidenceChain
│   └── SourceReference
│
├── ValidationComponents
│   ├── ValidationPanel
│   └── ValidationCheck
│
└── AIComponents
    ├── SuggestionCard
    ├── AIAction
    └── AIContextPanel
```

---

# 53. UX Information Architecture

The hierarchy should remain:

```text
Application
   ↓
Analysis Case
   ↓
Analytical Stage
   ↓
Analytical Object
   ↓
Evidence
   ↓
Computation
```

Example:

```text
DAH
 ↓
Revenue Investigation
 ↓
Analyze
 ↓
Revenue by Segment
 ↓
Finding #3
 ↓
Result #12
 ↓
SQL Run #12
 ↓
sales.parquet
```

This hierarchy should be reflected consistently across UI, domain model, and persistence.

---

# 54. Design System Principles

The design system should be built around:

### Surface

Cards and panels should be used selectively.

### Depth

Use subtle elevation and borders rather than heavy shadows.

### Density

Allow users to switch between:

- comfortable
    
- compact
    

### Motion

Use subtle motion for:

- transitions
    
- state changes
    
- progress
    
- expanding information
    

Never use motion merely for decoration.

### Consistency

The same object should look the same everywhere.

---

# 55. Anti-Patterns

DAH should explicitly avoid:

### Old BI Dashboard

```text
10 KPI cards
+
8 charts
+
filters everywhere
```

### Generic Chatbot

```text
User: Analyze my data
AI: ...
User: What about...
AI: ...
```

### Spreadsheet Clone

```text
Rows × Columns
as the primary mental model
```

### Notebook Clone

```text
Code
 ↓
Output
 ↓
Code
 ↓
Output
```

### Wizard

```text
Step 1 → Step 2 → Step 3 → Step 4
```

### AI Black Box

```text
Ask
 ↓
AI does everything
 ↓
Answer
```

DAH should instead be:

```text
Question
 ↓
Structured analytical state
 ↓
Evidence
 ↓
Reasoning
 ↓
Validation
 ↓
Decision support
```

---

# 56. North-Star UX Principle

The user should be able to answer these questions at any moment:

```text
1. What am I trying to understand?

2. What data am I using?

3. What have I discovered?

4. What evidence supports it?

5. What has been validated?

6. What remains uncertain?

7. What should I investigate next?
```

If the interface consistently answers these seven questions, the UX is aligned with the DAH product thesis.

---

# 57. Final UX Architecture

The complete UX architecture can be summarized as:

```text
                         DAH
                          │
                    ANALYSIS CASE
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
   ORIENTATION          WORK               INTELLIGENCE
       │                  │                  │
   Workflow          Workspace            AI Copilot
   Case status        Data                 Suggestions
   Findings           Analysis             Explanations
   Evidence           Results              Validation
   History            Code                 Next steps
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ↓
                   TRUSTED ANALYSIS
                          │
                Evidence + Validation
                          │
                          ↓
                  DECISION SUPPORT
```

---

# 58. UX/UI Design Contract

All future DAH UI implementation should follow these rules:

1. **Case-first, not dashboard-first.**
    
2. **Workflow-first, not tool-first.**
    
3. **Contextual AI, not generic chatbot-first.**
    
4. **Progressive disclosure, not information overload.**
    
5. **Evidence visible, not hidden.**
    
6. **Validation visible, not optional decoration.**
    
7. **Computation inspectable, not black-box.**
    
8. **Guided workflow, not rigid wizard.**
    
9. **Modern workspace, not old enterprise dashboard.**
    
10. **Human remains in control of analytical conclusions.**
    
11. **Every important claim should be traceable to evidence.**
    
12. **Every major action should preserve analytical state.**
    
13. **Complexity should appear only when useful.**
    
14. **The UI should communicate uncertainty honestly.**
    
15. **The interface should help users think, not merely operate software.**
    

---

# 59. One-Sentence UX Definition

> **DAH is a modern, case-centric analytical workspace that guides users from question to evidence-backed decision through an adaptive workflow, contextual AI, inspectable computation, and visible validation.**