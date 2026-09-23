"""The 50-case corpus AT-04 is measured over (P8-REFINE-007).

Each case is a question asked against a profiled dataset, plus the path the
suite drives it down (accept / edit / keep / leave pending). The corpus mixes
the shapes a real analyst's questions take:

- vague questions a profile can sharpen (the majority - these are where the
  relevance threshold is earned or lost),
- already-specific questions, where the honest engine looks and declines rather
  than rewording a question that is already answerable,
- thin questions with no topic at all, which must be declined because a
  refinement of "why?" is a new question rather than a sharpening,
- cases with no profiled data yet, where nothing can be grounded,
- a dataset with no numeric and no temporal columns, where there is genuinely
  nothing to sharpen with.

The expectations are stated as outcomes, not as strings: the suite measures
AT-04's four numbers from what the server actually answered, and the only
hard-coded expectations are which cases should produce a proposal and which
should decline. A question marked `expect="proposal"` that the engine declines
counts against the relevance rate; one marked `expect="decline"` that produces
a proposal counts against it too, because a rewording of an already-specific
question is not a refinement.
"""

from dataclasses import dataclass

# The paths the suite drives, so every one of AT-04's "accept / reject / edit"
# is exercised at volume rather than once.
PATH_ACCEPT = "accept"
PATH_EDIT = "edit"
PATH_KEEP = "keep"
PATH_PENDING = "pending"


@dataclass(frozen=True)
class RefineCase:
    question: str
    dataset: str
    expect: str          # "proposal" or "decline"
    path: str            # how the suite decides it
    edited: str = ""     # the analyst's own wording, on the edit path


# 50 cases. The questions are written the way people actually write them -
# lowercase, terse, sometimes one word - because a corpus of well-formed
# questions would measure nothing about the product its users have.
CASES: tuple[RefineCase, ...] = (
    # --- sales.csv: measure + dimension + time, the classic vague "why" ---
    RefineCase("Why are sales down?", "sales.csv", "proposal", PATH_ACCEPT),
    RefineCase("why is revenue declining?", "sales.csv", "proposal", PATH_EDIT,
               "What explains the change in revenue by region over order_date, "
               "comparing each period with the one before it?"),
    RefineCase("How are we doing?", "sales.csv", "proposal", PATH_KEEP),
    RefineCase("What's hurting sales?", "sales.csv", "proposal", PATH_ACCEPT),
    RefineCase("show me what changed in revenue", "sales.csv", "proposal", PATH_KEEP),
    RefineCase("Why did revenue drop in the west?", "sales.csv", "proposal", PATH_EDIT,
               "Why did revenue drop in the west, measured against the prior period?"),
    RefineCase("Which products are underperforming?", "sales.csv", "proposal", PATH_ACCEPT),
    RefineCase("What drives revenue?", "sales.csv", "proposal", PATH_PENDING),
    RefineCase("Explain the revenue trend", "sales.csv", "proposal", PATH_ACCEPT),
    # --- signups.csv: numeric but no temporal column; month is a string ---
    RefineCase("Are signups growing?", "signups.csv", "proposal", PATH_KEEP),
    RefineCase("Which channel works best?", "signups.csv", "proposal", PATH_ACCEPT),
    RefineCase("What is the relationship between spend and signups?", "signups.csv",
               "proposal", PATH_PENDING),
    RefineCase("How do paid and organic compare?", "signups.csv", "proposal", PATH_EDIT,
               "How do paid and organic signups compare by channel?"),
    RefineCase("Why did signups slow down?", "signups.csv", "proposal", PATH_KEEP),
    RefineCase("where should I spend more?", "signups.csv", "proposal", PATH_ACCEPT),
    RefineCase("What's the trend in signups by channel?", "signups.csv", "decline", PATH_KEEP),
    RefineCase("Is the paid channel worth it?", "signups.csv", "proposal", PATH_ACCEPT),
    RefineCase("Explain what happened in march", "signups.csv", "proposal", PATH_EDIT,
               "Explain what happened to signups and spend in march by channel"),
    # --- tickets.csv: numeric + temporal, with missingness to notice ---
    RefineCase("How are tickets doing?", "tickets.csv", "proposal", PATH_ACCEPT),
    RefineCase("Why is resolution time so high?", "tickets.csv", "proposal", PATH_KEEP),
    RefineCase("Are we closing tickets faster?", "tickets.csv", "proposal", PATH_EDIT,
               "Are resolution_hours falling over opened, by priority?"),
    RefineCase("priority breakdown of resolution time", "tickets.csv", "proposal", PATH_KEEP),
    RefineCase("What's the backlog cost?", "tickets.csv", "proposal", PATH_ACCEPT),
    RefineCase("How long do tickets take?", "tickets.csv", "proposal", PATH_KEEP),
    RefineCase("why are high priority tickets slow", "tickets.csv", "proposal", PATH_ACCEPT),
    RefineCase("Ticket trends over time", "tickets.csv", "proposal", PATH_PENDING),
    RefineCase("What explains the resolution hours?", "tickets.csv", "proposal", PATH_EDIT,
               "What explains resolution_hours by priority over opened?"),
    # --- inventory.csv: a high-cardinality sku the refiner must not split by ---
    RefineCase("What's our stock position?", "inventory.csv", "proposal", PATH_ACCEPT),
    RefineCase("Why is inventory low?", "inventory.csv", "proposal", PATH_KEEP),
    RefineCase("Which warehouses are short?", "inventory.csv", "proposal", PATH_EDIT,
               "Which warehouses have the lowest qty on last_count_date?"),
    RefineCase("How did stock levels change?", "inventory.csv", "proposal", PATH_ACCEPT),
    # --- people.csv: temporal but no numeric measure ---
    RefineCase("Who works here?", "people.csv", "proposal", PATH_KEEP),
    RefineCase("How has the team grown?", "people.csv", "proposal", PATH_ACCEPT),
    RefineCase("department headcount over time", "people.csv", "proposal", PATH_EDIT,
               "How does headcount per department change over hired_on?"),
    RefineCase("When did people join?", "people.csv", "proposal", PATH_KEEP),
    RefineCase("What does the org look like?", "people.csv", "proposal", PATH_PENDING),
    # --- already specific: a rewording here is noise, so these must decline ---
    RefineCase("What was revenue in Q2 by region?", "sales.csv", "decline", PATH_KEEP),
    RefineCase("How do signups differ between paid and organic channels?", "signups.csv",
               "decline", PATH_PENDING),
    RefineCase("What is the average resolution_hours per priority in january?",
               "tickets.csv", "decline", PATH_KEEP),
    RefineCase("Compare qty across warehouses for 2026", "inventory.csv", "decline",
               PATH_PENDING),
    RefineCase("How many people joined per department in 2024?", "people.csv", "decline",
               PATH_KEEP),
    RefineCase("total revenue by product over order_date", "sales.csv", "decline",
               PATH_PENDING),
    # --- thin or empty topics: nothing to preserve, so nothing to refine ---
    RefineCase("why?", "sales.csv", "decline", PATH_KEEP),
    RefineCase("help", "signups.csv", "decline", PATH_PENDING),
    RefineCase("data", "tickets.csv", "decline", PATH_KEEP),
    # --- no profile yet: the engine has nothing to read ---
    RefineCase("Why are sales down?", "sales.csv", "decline", PATH_KEEP),
    RefineCase("What drives signups?", "signups.csv", "decline", PATH_PENDING),
    RefineCase("How are tickets doing?", "tickets.csv", "decline", PATH_KEEP),
    # --- categories.csv: no numeric and no temporal column at all ---
    RefineCase("Which categories matter?", "categories.csv", "decline", PATH_KEEP),
    RefineCase("What's the status of our categories?", "categories.csv", "decline",
               PATH_PENDING),
)

DATASETS = (
    "sales.csv", "signups.csv", "tickets.csv", "inventory.csv",
    "people.csv", "categories.csv",
)

# The last three "no profile yet" cases are the ones with no attached dataset;
# they are identified positionally here so the runner can skip the attach step.
NO_PROFILE_COUNT = 3
