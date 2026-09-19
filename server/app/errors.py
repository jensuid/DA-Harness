"""Which failures are the input's fault (P4-RELIABILITY-002).

Every engine the API exposes can fail two ways, and the HTTP status code is
what carries the difference:

- the analyst's input cannot be honoured - a non-read-only query, an unknown
  column, a script the sandbox rejects, SQL that cannot parse. These answer 400
  and the detail says what to change.
- the server itself failed - a database fault, an unreadable stored file, a bug
  in our own code. These answer 500 and get the traceback logged, and must
  never be flattened into a 400 that blames the analyst.

The engines raise `ValueError` for the first group wherever they validate, and
DuckDB raises its own hierarchy - `duckdb.Error`, which is *not* a `ValueError`
- for SQL that cannot run. Both are input errors. Catching only these two
families is what keeps a user's syntax error a 400 while letting a real bug
surface as a 500 instead of vanishing into one.
"""

import duckdb

INPUT_ERROR_TYPES: tuple[type[BaseException], ...] = (ValueError, duckdb.Error)
