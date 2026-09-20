"""Cross-case recall: let an answer cite what a previous case found (P6-MEMORY-001).

A case already cites its own artifacts - runs, datasets, findings - through the
grounds budget in `assistant.py`. Nothing lets it cite a *previous* case, so
every investigation starts from scratch even when the same anomaly was found
and explained last month. This module is the input that closes that gap.

`summarize_memory` is a pure projection over rows that already exist: it reads
other cases and their findings, scores each by how much the current question
actually overlaps it, and hands back the ones worth citing. It writes nothing -
memory is derived, never stored, so it cannot drift from what is on disk any
more than the evidence graph or the case summary can.

Relevance is a shared-content-word count, not an embedding or a similarity
model. That is deliberate: it is deterministic, it needs no dependency and no
network call, and it makes the "no, nothing bears on this" answer honest
rather than a confident stretch. A case that shares one stopword-ish token is
not memory, it is noise; the threshold exists so a weakly-related case is left
out of the answer instead of being dragged into it.
"""

import re
from typing import Any

# Words too common to mean anything on their own. Kept small and hand-written
# rather than pulled from a library - the list has to be auditable, because it
# is the thing deciding whether a prior case gets cited or not.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "with", "by", "is", "are", "was", "were", "be", "been", "being", "as",
    "that", "this", "these", "those", "it", "its", "from", "into", "about",
    "what", "which", "who", "when", "where", "why", "how", "much", "many",
    "do", "does", "did", "have", "has", "had", "i", "you", "we", "they",
    "my", "your", "our", "their", "me", "us", "them", "if", "then", "than",
    "so", "such", "also", "not", "no", "any", "all", "both", "each", "more",
    "most", "other", "some", "there", "here", "over", "under", "again",
    "case", "cases", "data", "dataset", "datasets", "row", "rows", "value",
    "values", "column", "columns", "question", "finding", "findings",
}

_WORD_RE = re.compile(r"[A-Za-z0-9_]{2,}")

# A prior case must share at least this many content words to be cited. Below
# it, the answer says plainly that nothing bears on the question rather than
# reaching for a case that happens to mention the same common noun.
_MIN_SHARED_WORDS = 2

# How many prior cases one answer may cite. More than this and the answer
# becomes a list rather than a pointer.
_MAX_MEMORY_CASES = 3


def _content_words(text: str) -> set[str]:
    """The meaning-bearing lowercase tokens of a string, stopwords out."""
    return {word.lower() for word in _WORD_RE.findall(text or "") if word.lower() not in _STOPWORDS}


def _case_findings(db, case_id: str) -> list[dict[str, Any]]:
    """One case's findings, validated ones first so the strongest is cited."""
    rows = db.execute(
        "SELECT id, statement, validation_status FROM findings "
        "WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall()
    findings = [
        {"id": row["id"], "statement": row["statement"], "status": row["validation_status"]}
        for row in rows
    ]
    # A validated finding is the thing worth recalling; an unvalidated one is
    # still a real finding, but it comes second.
    findings.sort(key=lambda item: 0 if item["status"] == "supported" else 1)
    return findings


def summarize_memory(db, case_id: str, message: str, limit: int = _MAX_MEMORY_CASES) -> list[dict[str, Any]]:
    """Other cases whose findings bear on this question, best match first.

    Read-only over the cases and findings already on disk. Returns one entry
    per case, each carrying its strongest finding and the shared words that
    made it relevant - the caller cites the case by id, and the shared words
    are what make the citation legible to a reviewer.

    A case with no findings is skipped: there is nothing to recall from it,
    however similar its question sounds.
    """
    words = _content_words(message)
    if not words:
        return []

    candidates: list[dict[str, Any]] = []
    for row in db.execute(
        "SELECT id, question, dataset, created_at FROM cases "
        "WHERE id != ? ORDER BY created_at DESC",
        (case_id,),
    ).fetchall():
        findings = _case_findings(db, row["id"])
        if not findings:
            continue
        # The text a prior case is matched against: its question, its dataset
        # label, and every finding it closed on. A question alone can look
        # similar and have found nothing; the findings are the recall value.
        corpus = " ".join(
            [row["question"] or "", row["dataset"] or ""]
            + [finding["statement"] or "" for finding in findings]
        )
        shared = words & _content_words(corpus)
        if len(shared) < _MIN_SHARED_WORDS:
            continue
        candidates.append(
            {
                "case_id": row["id"],
                "question": row["question"],
                "dataset": row["dataset"],
                "shared": sorted(shared),
                "score": len(shared),
                "findings": findings,
            }
        )

    candidates.sort(key=lambda item: (-item["score"], item["case_id"]))
    return candidates[:limit]
