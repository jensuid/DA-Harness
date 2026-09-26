#!/usr/bin/env python3
"""Split web/src/CaseWorkspace.tsx into web/src/panels/*.tsx (P9-F1-001).

Each panel component moves verbatim into its own file with the imports its
body actually references. The composition root (state, load(), the three-zone
layout) stays in CaseWorkspace.tsx and imports the panels back.

Idempotent: re-running overwrites the panel files it owns.
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / 'web/src/CaseWorkspace.tsx'
PANELS = ROOT / 'web/src/panels'
WEB = ROOT / 'web'

# (file stem, [(start, end) line spans, 1-indexed inclusive]) of the defs that
# move into that file. A component is grouped with the helpers only it uses, so
# a panel is self-contained and the 600-line ceiling holds.
#
# `shared` holds the one type two panels both need (`RunSummary`), because
# RunsPanel renders ChartPanel and ChartPanel reads RunSummary - importing it
# from RunsPanel would be a cycle, and a cycle over a type is the kind a
# bundler tolerates and a reader trips over.
GROUPS: list[tuple[str, list[tuple[int, int]]]] = [
    ('LearnPanel', [(381, 484)]),
    ('WorkflowRail', [(485, 563)]),
    ('CaseOverview', [(564, 639)]),
    # DataPanel does not render CaseOverview; the span that looked like a
    # dependency was the CaseOverview block itself, duplicated by mistake.
    ('DataPanel', [(640, 771), (1059, 1086)]),
    # GenerateKind is the type GENERATE_KINDS is declared with, so it travels
    # with the const.
    ('GeneratePanel', [(83, 95), (772, 889)]),
    ('PlanPanel', [(890, 1058)]),
    ('RunsPanel', [(1087, 1525), (2069, 2088)]),
    ('DraftPanel', [(1526, 1578)]),
    ('FindingsPanel', [(1579, 1684), (2280, 2297)]),
    ('Chat', [(1685, 1803), (2317, 2360)]),
    ('EdaPanel', [(1804, 2068)]),
    ('EvaluatePanel', [(2089, 2279), (2298, 2316)]),
    ('EvidencePanel', [(2361, 2510)]),
    ('HistoryPanel', [(2511, 2613)]),
    ('AgentPanel', [(2614, 2890)]),
]

API_EXPORTS = set(re.findall(r'^export (?:async )?(?:function|const|type|interface|class) (\w+)',
                             (ROOT / 'web/src/api.ts').read_text(), re.M))

TYPE_NAMES = set(re.findall(r'^export type (\w+)', (ROOT / 'web/src/api.ts').read_text(), re.M))
INTERFACE_NAMES = set(re.findall(r'^export interface (\w+)', (ROOT / 'web/src/api.ts').read_text(), re.M))
TYPE_ONLY = TYPE_NAMES | INTERFACE_NAMES

# Types the workspace itself defined. Empty: the workspace's only type is
# GenerateKind, which travels with the const that uses it, and every peer
# symbol the panels share is a value (a component or a helper like
# formatValue). A peer import therefore never takes `type` - a function
# component imported as a type is a JSX element tsc cannot place.
WORKSPACE_TYPES: set[str] = set()

JSX_HINT = re.compile(r'<[A-Z]|<svg|<pre|<table|<ul|<li|<p\b|<div|<span|<button|'
                      r'<input|<textarea|<select|<label|<details|<summary|<strong|'
                      r'<em|<code|<h1|<h2|<h3|<h4|<ol|<dl|<dt|<dd|<th|<tr|<td|<thead|'
                      r'<tbody|<caption|<form|<fieldset|<legend|<img|<a\b|<br|<hr|'
                      r'<small|<mark|<abbr|<section|<nav|<article|<aside|<footer|'
                      r'<header|<main|<figure|<figcaption|<time|<address|'
                      r'<blockquote|<q|<cite|<kbd|<samp|<var|<sub|<sup|<u\b')

# The state the composition root keeps: every panel is pure over its props, so
# a panel import of a hook is a local one.
WORKSPACE_HOOKS = {'useEffect', 'useState'}


def block_for(lines: list[str], spans: list[tuple[int, int]]) -> str:
    """The source of one panel: its spans joined, with the workspace's own
    component excluded (it is never inside these spans)."""
    parts = []
    for start, end in spans:
        if end >= start:
            parts.append('\n'.join(lines[start - 1:end]))
    return '\n\n'.join(parts)


def symbol_map(lines: list[str]) -> dict[str, str]:
    """symbol -> the file stem that provides it."""
    out: dict[str, str] = {}
    for stem, spans in GROUPS:
        text = block_for(lines, spans)
        for name in re.findall(r'^(?:export )?function (\w+)', text, re.M):
            out[name] = stem
        for name in re.findall(r'^const (\w+)', text, re.M):
            out[name] = stem
    return out




def code_only(body: str) -> str:
    """Source minus comments and single-quoted string literals.

    Two ways a name appears in a block without being a reference to it: a
    comment that names a type, and a single-quoted literal's prose. Template
    literals are NOT stripped: they hold real runtime code (`` `Profile
    ${str('filename')}` `` is how AgentPanel reaches the type the span table
    needs to import), and stripping them is what made the heuristic miss it.
    """
    out = []
    for line in body.split('\n'):
        stripped = line.split('//')[0]
        stripped = re.sub(r"'[^']*'", "''", stripped)
        out.append(stripped)
    return '\n'.join(out)


def used_in_code(body: str, name: str) -> bool:
    """Referenced in code, not just mentioned in prose.

    Template literals count: `` `Profile ${str('filename')}` `` is a real
    reference to the Profile type, because `str` takes the step's fields and
    the template is where the panel reaches them. Only a comment or a
    single-quoted literal is prose.
    """
    code = code_only(body)
    return re.search(r'(?<![\w$.])' + re.escape(name) + r'\b', code) is not None


def used_names(body: str, candidates: set[str]) -> set[str]:
    return {n for n in candidates
            if re.search(r'(?<![\w$.])' + re.escape(n) + r'\b', body)}


# The two ways the generated import list can be wrong, and the only two worth
# fixing automatically: an import the body never reads (TS6133) and a name the
# body uses but no import carries (TS2304). Anything else - a wrong type
# parameter, a broken JSX element - is a bug in the span table, not an import
# arithmetic problem, and the loop stops and shows it.
TS_ERROR = re.compile(
    r'^(?P<file>src/panels/\w+\.tsx|src/CaseWorkspace\.tsx)'
    r'\((?P<line>\d+),(?P<col>\d+)\): error (?P<code>TS\d+): (?P<msg>.*)$')


def parse_tsc(log: str) -> tuple[list[tuple[str, str]], list[tuple[str, str, int, int]]]:
    """(file, name) pairs to drop, and (file, name, line, col) to add."""
    drop: list[tuple[str, str]] = []
    add: list[tuple[str, str, int, int]] = []
    for line in log.splitlines():
        m = TS_ERROR.match(line.strip())
        if not m:
            continue
        code = m.group('code')
        file = m.group('file')
        if code == 'TS6133':
            # "'Profile' is declared but its value is never read."
            name = re.match(r"'(\w+)'", m.group('msg'))
            if name:
                drop.append((file, name.group(1)))
        elif code == 'TS2304':
            # "Cannot find name 'formatValue'."
            name = re.match(r"Cannot find name '(\w+)'", m.group('msg'))
            if name:
                add.append((file, name.group(1), int(m.group('line')),
                            int(m.group('col'))))
    return drop, add


def name_source(name: str, sym2stem: dict[str, str], all_provides: dict[str, str],
                api_exports: set[str]) -> str | None:
    """The module `name` lives in: a peer panel, an api export, or nothing.

    The ordering matters: a peer panel's own helper is looked up before the
    api, because the workspace defined `formatValue` and the api did not.
    """
    if name in sym2stem:
        return f"src/panels/{sym2stem[name]}.tsx"
    if name in all_provides:
        return all_provides[name]
    if name in api_exports:
        return 'src/api.ts'
    return None


# Both shapes the generator writes: one line (`import { A, B } from './x'`),
# and the wrapped block it uses when the joined names are too wide
# (`import {\n  A,\n  B,\n} from './x'`). The loop has to find the name in
# either, or a wide import's unused entry is the round that changes nothing.
IMPORT_NAME = re.compile(r'^(?:type )?(\w+),?$')
# The generator writes single quotes for peer and react imports and double
# quotes for the wide api block (`} from "../api"`), so the source matcher
# accepts either - a quote-shape check is how a wide import's unused entry
# becomes the round that changes nothing.
_FROM_RE = re.compile(r"from ['\"](?P<path>[^'\"]+)['\"]")


def _entry_name(entry: str) -> str:
    """The bare name of an import entry, minus its comma and `type`."""
    return entry.strip().rstrip(',').removeprefix('type ').strip()


def _matches_from(head: str, tail: str, from_path: str) -> bool:
    """Whether the import at (head, tail) is the one from `from_path`."""
    m = _FROM_RE.search(head + ' ' + tail)
    return m is not None and m.group('path') == from_path.strip().strip('\'"')


def _import_block(lines: list[str], i: int) -> tuple[list[str], list[str], int] | None:
    """The names and the source line of the import at `i`, in either shape.

    Returns (edges, names, end): `edges` are the two surrounding fragments
    (`import {` and `} from '...'`) so the block can be re-rendered in the
    same shape it was found; `end` is the index past the import's last line.
    None when `i` is not the start of an import the loop can edit.
    """
    line = lines[i]
    if 'import' not in line or '{' not in line:
        return None
    if '}' in line:
        # The one-line shape: `import { A, B } from './x'`. The spec can be
        # typed (`import { type CaseProgress, type QualityIssue } from`), and
        # re-rendering has to preserve that shape rather than invent one.
        m = re.match(r'^(?P<head>import (?:type )?\{ ?)(?P<spec>[^}]*)(?P<tail> ?\} from .*)$', line)
        if not m:
            return None
        names = [n for n in (p.strip() for p in m.group('spec').split(',')) if n]
        return [m.group('head').rstrip(), m.group('tail').lstrip()], \
            _clean_entries(names), i + 1
    # The wrapped shape: `import {` ... `} from './x'` on its own lines.
    head = line.rstrip()
    names: list[str] = []
    j = i + 1
    while j < len(lines):
        if 'from' in lines[j]:
            tail = lines[j].strip()
            return [head, tail], _clean_entries(names), j + 1
        names.append(lines[j].strip())
        j += 1
    return None


def _spec_pairs(spec: str) -> list[tuple[str, bool]]:
    """The names in an import spec, each with its `type` flag."""
    out = []
    for part in spec.split(','):
        part = part.strip()
        if not part:
            continue
        is_type = part.startswith('type ')
        out.append((part[len('type '):] if is_type else part, is_type))
    return out


def apply_fixups(files: dict[str, str], drop: list[tuple[str, str]],
                 add: list[tuple[str, str, int, int]],
                 sym2stem: dict[str, str], all_provides: dict[str, str],
                 api_exports: set[str]) -> bool:
    """The round's fixups against `files`. Kept for callers that want the
    single-pass shape; the feedback loop inlines the same two calls so its
    state survives the round."""
    changed = False
    for file, name in drop:
        if file not in files:
            continue
        did, text = remove_import_name(files[file], name)
        if did:
            files[file] = text
            changed = True
    for file, name, _line, _col in add:
        if file not in files:
            continue
        source = name_source(name, sym2stem, all_provides, api_exports)
        if source is None:
            continue
        did, text = add_import_name(files[file], name, source, sym2stem,
                                    api_exports)
        if did:
            files[file] = text
            changed = True
    return changed


def _render_import(head: str, tail: str, names: list[str]) -> list[str]:
    """The import's lines, in whichever shape the original used.

    `head` is `import { ` in the one-line shape and `tail` starts with
    `} from`; in the wrapped shape `head` is `import {` and `tail` is the
    `} from '...'` line on its own. Two names or fewer stay on one line,
    because a two-name block spread over four lines is noise the reader has
    to re-fold.
    """
    if head.rstrip().endswith('{'):
        if len(names) <= 2:
            inner = ', '.join(names)
            return [head.rstrip() + ' ' + inner + ' ' + tail]
        return [head] + [f'  {n.rstrip(",")},' for n in names] + [tail]
    return [head.rstrip() + ' ' + ', '.join(n.rstrip(',') for n in names)
            + ' ' + tail.lstrip()]


def _clean_entries(names: list[str]) -> list[str]:
    """`type X` becomes `X` where the whole spec is already typed.

    The generator writes one `type` per name in the multi-line shape
    (`type A,\n type B,`), so a spec that is entirely types has the modifier
    once, not once per entry: `import { type A, type B }` is not a line this
    codebase writes, and it is not one a reader wants.
    """
    bare = [n.strip() for n in names if n.strip()]
    if bare and all(n.startswith('type ') for n in bare):
        return [_entry_name(n) for n in names]
    return names


def remove_import_name(text: str, name: str) -> tuple[bool, str]:
    """Drop `name` from whichever import statement of `text` carries it.

    Removing the last name of an import drops the whole statement, because an
    empty import is a syntax error a later round would have to explain.
    """
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        block = _import_block(lines, i)
        if block is None:
            i += 1
            continue
        (head, tail), names, end = block
        if not any(_entry_name(n) == name for n in names):
            i = end
            continue
        kept = [n for n in names if _entry_name(n) != name]
        if not kept:
            del lines[i:end]
        else:
            lines[i:end] = _render_import(head, tail, kept)
        return True, '\n'.join(lines)
    return False, text


def add_import_name(text: str, name: str, source: str,
                    sym2stem: dict[str, str], api_exports: set[str]) -> tuple[bool, str]:
    """Add `name` to the import from `source`, in TS2304's own terms: an api
    type gets `type`, an api value does not, and a peer name never does
    (every peer symbol is a component or a helper).

    Inserts a new import line when the file does not yet import from that
    module, keeping the project's style (peer imports are relative single
    quotes, the api import is the existing block).
    """
    if re.search(r'(?<![\w$.])' + re.escape(name) + r'\b', text):
        # Already present: a `type X` next to a used `X` is not the fix.
        return False, text
    lines = text.split('\n')
    is_type = name in TYPE_ONLY and name in api_exports
    entry = ('type ' if is_type else '') + name
    from_path = f"'./{Path(source).stem}'" if '/panels/' in source else "'../api'"
    i = 0
    last_import = -1
    while i < len(lines):
        block = _import_block(lines, i)
        if block is None:
            i += 1
            continue
        (head, tail), names, end = block
        last_import = end - 1
        if not _matches_from(head, tail, from_path):
            i = end
            continue
        names.append(entry)
        names.sort(key=lambda n: _entry_name(n).lower())
        lines[i:end] = _render_import(head, tail, _clean_entries(names))
        return True, '\n'.join(lines)
    # No existing import from that module: insert one after the last import,
    # or at the top of the file's import block.
    lines.insert(last_import + 1, f'import {{ {entry} }} from {from_path}')
    return True, '\n'.join(lines)


def tsc_feedback(files: dict[str, str], sym2stem: dict[str, str],
                 all_provides: dict[str, str], api_exports: set[str],
                 max_rounds: int = 8) -> bool:
    """Generate, compile, parse, fix. Deterministic and exact: the import list
    per file is what tsc says it has to be, not a guess at what it might be.

    Returns whether the loop converged. A round that changes nothing is
    convergence; a round that leaves errors it cannot name is a span-table
    bug the caller has to read, not an import to fix.
    """
    import subprocess
    # The generator's own heuristic list is only the first guess. The loop has
    # to carry its own corrections, because re-generating from `files` is what
    # undoes them: round N's write is round N-1's fixup, so the errors round
    # N reads are the current state, not the heuristic's.
    state = dict(files)
    for round_no in range(1, max_rounds + 1):
        for rel, text in state.items():
            (WEB / rel).write_text(text)
        proc = subprocess.run(['npx', 'tsc', '-b'], cwd=WEB,
                              capture_output=True, text=True)
        log = proc.stdout + proc.stderr
        if not log.strip():
            print(f'tsc round {round_no}: clean')
            return True
        drop, add = parse_tsc(log)
        print(f'tsc round {round_no}: {len(drop)} to drop, {len(add)} to add')
        if not drop and not add:
            # Errors the loop cannot read: a broken span, a wrong type.
            print(log, end='')
            return False
        changed = False
        for file, name in drop:
            did, text = remove_import_name(state[file], name)
            if did:
                state[file] = text
                changed = True
        for file, name, _line, _col in add:
            source = name_source(name, sym2stem, all_provides, api_exports)
            if source is None:
                print(f'  no known source for {name} in {file}')
                continue
            did, text = add_import_name(state[file], name, source, sym2stem,
                                       api_exports)
            if did:
                state[file] = text
                changed = True
        if not changed:
            print(log, end='')
            return False
    print(f'tsc feedback: did not converge in {max_rounds} rounds')
    for file in sorted(state):
        log_path = WEB / file
        if log_path.exists():
            log_path.write_text(state[file])
    return False


def original_lines() -> list[str]:
    """The pre-split CaseWorkspace.tsx, from the commit the split started at.

    Reading from git rather than from the file makes the script idempotent: it
    can be re-run any number of times, because its input is not also its
    output.
    """
    import subprocess
    text = subprocess.check_output(
        ['git', 'show', 'HEAD:web/src/CaseWorkspace.tsx'],
        cwd=ROOT, text=True)
    return text.split('\n')


def main() -> None:
    lines = original_lines()
    PANELS.mkdir(parents=True, exist_ok=True)
    sym2stem = symbol_map(lines)
    # Every name a panel provides, and the file it lives in - the lookup for a
    # TS2304 the span table did not predict (a shared helper like formatValue,
    # which two panels use but neither group owns).
    all_provides: dict[str, str] = {}
    for stem, spans in GROUPS:
        text = block_for(lines, spans)
        for name in re.findall(r'^(?:export )?function (\w+)', text, re.M):
            all_provides[name] = f'src/panels/{stem}.tsx'
    generated: dict[str, str] = {}
    report = []
    for stem, spans in GROUPS:
        body = block_for(lines, spans)
        provides = set(re.findall(r'^(?:export )?function (\w+)', body, re.M)) | \
                    set(re.findall(r'^const (\w+)', body, re.M))
        # The api names this file references but does not define itself.
        code = code_only(body)
        api_needs = sorted(
            n for n in API_EXPORTS
            if n not in provides and used_in_code(code, n))
        # A name the block defines locally is not an import: the regex above
        # sees the definition as a reference too.
        # A type the block defines or only mentions is not an import.
        code = code_only(body)
        api_needs = [n for n in api_needs
                     if used_in_code(code, n) and n not in provides]
        # The peer symbols it references but does not define itself.
        peer_needs = sorted(
            n for n in sym2stem
            if n not in provides and n in sym2stem
            and sym2stem[n] != stem and used_in_code(code, n))
        # Build the import block in the project's own style.
        imports: list[str] = []
        hooks = sorted(h for h in WORKSPACE_HOOKS if h in body)
        if hooks:
            imports.append("import { " + ", ".join(hooks) + " } from 'react'")
        if api_needs:
            entries = [f'type {n}' if n in TYPE_ONLY else n for n in api_needs]
            joined = ", ".join(entries)
            if len(joined) > 60:
                imports.append('import {\n' + ',\n'.join(f'  {e}' for e in entries) +
                               ',\n} from "../api"')
            else:
                imports.append(f"import {{ {joined} }} from '../api'")
        if 'ApiError' in body and 'ApiError' not in api_needs:
            imports.append("import { type ApiError } from '../api'")
        if 'sourceLabel' in body:
            imports.append("import { sourceLabel } from '../sourceLabel'")
        if 'messageOf' in body:
            imports.append("import { messageOf } from '../CaseList'")
        # Peer imports, one line per file.
        by_file: dict[str, list[str]] = {}
        for p in peer_needs:
            by_file.setdefault(sym2stem[p], []).append(p)
        for other, names in sorted(by_file.items()):
            # A peer symbol that is a type (an interface or a type alias the
            # workspace defined) needs `type` too, or TS6133 reads it as an
            # unused value import. The workspace's own names are the check,
            # because api's were handled above.
            entries = [f'type {n}' if n in WORKSPACE_TYPES else n
                       for n in sorted(names)]
            joined = ', '.join(entries)
            imports.append(f"import {{ {joined} }} from './{other}'")
        header = (
            '/**\n'
            ' * P9-F1-001: this panel moved out of CaseWorkspace.tsx verbatim.\n'
            ' * The workspace holds the state; the panel is pure over its props.\n'
            ' */\n\n'
        )
        # Every top-level def is exported: the composition root and the peer
        # panels import them by name, and an unexported panel is a link error.
        exported = re.sub(r'^(export )?(function|const) (\w+)',
                          r'export \2 \3', body, flags=re.M)
        out = header + '\n'.join(imports) + '\n\n' + exported.rstrip() + '\n'
        generated[f'src/panels/{stem}.tsx'] = out
        (PANELS / f'{stem}.tsx').write_text(out)
        report.append((stem, len(out.split('\n')), provides, imports, api_needs,
                       peer_needs))
    build_root(lines, sym2stem)
    generated['src/CaseWorkspace.tsx'] = SRC.read_text()
    # The import lists above are heuristics; tsc is the authority. The loop
    # compiles what was written, parses its own two import errors, and
    # adjusts the lists until the compiler is quiet - deterministic and
    # exact, with no second-guessing a regex.
    if not tsc_feedback(generated, sym2stem, all_provides, API_EXPORTS):
        raise SystemExit('the tsc feedback loop did not converge; the errors '
                         'above are a span-table problem, not an import one')
    for stem, n, provides, imports, api_needs, peer_needs in report:
        print(f'--- {stem}.tsx ({n} lines) exports={sorted(provides)}')
        for line in imports:
            print('    ' + line)
        if peer_needs:
            print(f'    peers: {peer_needs}')
        print()


# ----------------------------------------------------------------- the root

# What the composition root keeps: its own state, the loader, the layout, and
# the panels it renders once each. Everything else moved.
ROOT_USES = {
    'useEffect', 'useState', 'ApiError', 'messageOf', 'getCase', 'getProgress',
    'listDatasets', 'listRuns', 'listFindings', 'listChat', 'getContext',
    'getProfile', 'listEvaluations', 'getEvidenceGraph', 'getCaseHistory',
    'getLearnWalk', 'getAgentState', 'getRoleAgentState',
}
# The panels the root renders, in the order the layout renders them.
ROOT_PANELS = [
    'WorkflowRail', 'CaseOverview', 'RefinePanel', 'LearnPanel',
    'HistoryPanel', 'DataPanel', 'PlanPanel', 'EdaPanel',
    'RunsPanel', 'FindingsPanel', 'EvaluatePanel', 'EvidencePanel',
    'DecisionPanel', 'ContextPanel', 'AgentPanel', 'Chat',
]
ROOT_STATE_TYPES = [
    'Case', 'CaseContext', 'CaseProgress', 'CaseHistory', 'ConversationTurn',
    'Dataset', 'Evaluation', 'EvidenceGraph', 'Finding', 'LearnWalk',
    'Profile', 'RunSummary', 'AgentState',
]


def build_root(lines: list[str], sym2stem: dict[str, str]) -> None:
    """Rewrite CaseWorkspace.tsx as the composition root alone.

    The root's own source (state declarations, load(), the layout JSX) is
    copied verbatim from the lines the panels did not take, so the split is a
    move rather than a rewrite.
    """
    root_lines = lines[95:372]  # the root function, verbatim, closing brace included
    # The panel names the root renders come from panels/, the rest stay.
    panel_stems = sorted({sym2stem[p] for p in ROOT_PANELS if p in sym2stem})
    header = [
        '/**',
        ' * P9-F1-001: the workspace is a composition root. The state lives here;',
        ' * every surface it renders moved into `web/src/panels/` and is pure over',
        ' * its props. The three-zone layout (UX 8) is unchanged, as is every',
        ' * panel\'s contract - the split is structural, and the tests that assert',
        ' * the rendered output are the contract that it changed nothing.',
        ' */',
        "import { useEffect, useState } from 'react'",
    ]
    # Type imports.
    type_imports = [f'  type {t}' for t in ROOT_STATE_TYPES]
    header.append('import {\n' + ',\n'.join(type_imports) + ',\n} from \'./api\'')
    value_imports = sorted(n for n in ROOT_USES
                           if n not in TYPE_ONLY and n not in ('messageOf',)
                           and n not in ('useEffect', 'useState') and n != 'ApiError')
    header.append('import {\n' + ',\n'.join(f'  {n}' for n in value_imports) +
                  ',\n} from \'./api\'')
    header.append("import { ApiError } from './api'")
    header.append("import { messageOf } from './CaseList'")
    # Panels, one import per file, grouped the way the layout groups them.
    by_file: dict[str, list[str]] = {}
    for p in ROOT_PANELS:
        if p in sym2stem:
            by_file.setdefault(sym2stem[p], []).append(p)
    panel_import_lines = []
    for stem in sorted(by_file):
        names = ', '.join(sorted(set(by_file[stem])))
        panel_import_lines.append(f"import {{ {names} }} from './panels/{stem}'")
    # The panels the root renders that live in their own top-level files.
    for p in ROOT_PANELS:
        if p not in sym2stem:
            panel_import_lines.append(f"import {{ {p} }} from './{p}'")
    # The two the root renders that live in their own top-level files under
    # names that differ from the module's.
    panel_import_lines.append("import { PromoteTemplate } from './Templates'")
    out = '\n'.join(header) + '\n' + '\n'.join(sorted(panel_import_lines)) + \
        '\n\n' + ''.join('\n'.join(root_lines)) + '\n'
    SRC.write_text(out)
    print(f'--- CaseWorkspace.tsx rewritten as the composition root '
          f'({len(out.split(chr(10)))} lines)')
    for line in panel_import_lines:
        print('    ' + line)


if __name__ == '__main__':
    main()