# Observability

DAH's core is a FastAPI process the desktop shell spawns as a child. In a
checkout that child runs in a terminal someone is reading. In the packaged app
it is a PyInstaller binary whose stderr goes nowhere, so a server fault used to
log a traceback into a void and a user hitting a problem had nothing to show
for it.

As of P5-OBSERVE-002 the core keeps its own log, in the same place it keeps
your cases.

## Where the log lives

```
<your data directory>/logs/dah-core.log
```

The data directory is the one the desktop shell points the core at - on macOS
that is `~/Library/Application Support/DAH-Harness` (or whatever `DAH_DATA_DIR`
was set to when the core started). An explicit `DAH_LOG_DIR` overrides it, the
same way `DAH_DB_PATH` overrides the database location. When neither is set the
log lands in `server/data/logs` of the checkout.

The file is capped at 2 MB with three rotating backups, so the whole log is
bounded at about 8 MB and cannot grow without end. Older backups are named
`dah-core.log.1` (newest) through `dah-core.log.3` (oldest).

`DAH_LOG_LEVEL` sets the level (default `INFO`).

## Reading it

```bash
# The last 200 lines, as JSON
curl http://127.0.0.1:8123/logs

# The last 1000 lines (the most the endpoint will return)
curl 'http://127.0.0.1:8123/logs?lines=1000'
```

`GET /logs` is read-only: it accepts no body, writes nothing, and returns

```json
{
  "enabled": true,
  "path": "/Users/you/Library/Application Support/DAH-Harness/logs/dah-core.log",
  "size_bytes": 9962,
  "rotated": ["dah-core.log.1", "dah-core.log.2"],
  "lines": ["...the last N lines, oldest first..."]
}
```

`lines` defaults to 200 and is clamped to 1000, because the useful part of a
log is its end. A negative or zero ask means "the last line". `enabled` is
`false` when file logging is off - an unwritable data directory, or a core
running under a test harness - which is a state to report rather than an error
to raise.

The desktop shell has a **Reveal DAH Logs** item in its app menu. It asks the
core for that path and opens the folder in Finder with the log selected - no
terminal needed. If the core reports file logging is off, or cannot be reached,
the shell says so in its own log rather than failing the click.

## What is in it

- one line per request: method, path, status and duration
- the core's own startup line: pid, data directory, log level
- the reason an LLM fell back to the deterministic engine, when it did
- the full traceback of a server fault (a 500)

To find the thing that just went wrong, read the end:

```bash
curl -s http://127.0.0.1:8123/logs | python3 -c "import json,sys; [print(l) for l in json.load(sys.stdin)['lines']]" | tail -40
```

## Finding the failure behind an error

When the core fails on a request it answers

```json
{"detail": "internal error", "request_id": "3f239488576c453cb61b9f38716d1bb7"}
```

That id is the key to the failure. Search the log for it and you land on the
traceback:

```bash
curl -s http://127.0.0.1:8123/logs | python3 -c "import json,sys; [print(l) for l in json.load(sys.stdin)['lines']]" | grep -A 20 3f239488
```

The id is also what the desktop shell shows alongside the error, so quoting it
is something a user can do without a terminal. The traceback stays in the log
and never goes back in the body: a fault can be holding user data - an unknown
column name, a filename, a value that failed to parse - so only the id and a
fixed message leave the process.

## What is not in it

The boundary is a property of what the code passes to a logger, not a
configuration:

- **Not logged:** request bodies and response payloads. Your question, the SQL
  or Python you wrote, the contents of any dataset you attached, and every value
  in your data. Nothing that holds them is ever passed to a logger.
- **Logged:** the *path* of a request (`POST /cases`, not what was in it), the
  names of files the core itself wrote, exception types and messages.

The one exception is a fault's traceback, which can quote what it was holding -
an unknown column name, a filename, a value that failed to parse. That is the
trade that makes a 500 debuggable rather than opaque, and it stays on your
machine: the log is written locally and nothing in DAH transmits it.

If you would rather DAH kept no log at all, point it somewhere it cannot write
or unset the data directory's write permission - the core falls back to stderr
and keeps running.
