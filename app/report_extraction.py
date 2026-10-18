"""Pulls issue / action-taken / parts-used / time-spent out of a technician's free-text report.

Rule-based on purpose: there's no dataset of field-service reports to train an extractor on (the
Phase 3/4 mismatch problem again, one level worse — this time there's nothing to mine at all), and
a technician reviews and can correct every field before it's saved, so a wrong guess here costs a
moment's editing rather than silently corrupting a record. See app.routes.service_reports.

Known limitation: coordinated parts in one sentence ("replaced the belt and the bearing") only
pick up the first one, since there's no real parsing here, just keyword triggers. Good enough for
a first pass the technician corrects, not standalone enough to skip review.
"""

import re
from dataclasses import dataclass

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

_ISSUE_MARKERS = re.compile(r"\b(found|diagnosed|turned out|caused by|cause was|was due to|root cause)\b", re.IGNORECASE)

_ACTION_VERBS = re.compile(
    r"\b(replaced|repaired|fixed|cleaned|tightened|recalibrated|adjusted|reset|lubricated|"
    r"rewired|reseated|resoldered|realigned|serviced|tested|cleared|flushed)\b",
    re.IGNORECASE,
)

_PART_TRIGGER = re.compile(
    r"\b(?:replaced|installed|fitted|swapped(?: out)?|used|added|changed)\s+"
    r"(?:the\s+|an?\s+|new\s+)*([a-z0-9][a-z0-9\- ]*?)"
    r"(?=[.,;]| and\b| to\b| with\b| before\b| after\b|$)",
    re.IGNORECASE,
)

_DURATION = re.compile(r"(\d+(?:\.\d+)?)\s*(hours?|hrs?|hr|minutes?|mins?|min)\b", re.IGNORECASE)


@dataclass
class ExtractedFields:
    issue: str | None
    action_taken: str | None
    parts_used: str | None
    time_spent_minutes: int | None


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in _SENTENCE_SPLIT.split(text.strip()) if sentence.strip()]


def extract_fields(report_text: str) -> ExtractedFields:
    sentences = _sentences(report_text)

    issue = next((sentence for sentence in sentences if _ISSUE_MARKERS.search(sentence)), None)
    if issue is None and sentences:
        # No explicit diagnostic language found — a technician's report very often opens with
        # the problem anyway, so the first sentence is a reasonable fallback guess.
        issue = sentences[0]

    action_sentences = [sentence for sentence in sentences if _ACTION_VERBS.search(sentence)]
    action_taken = " ".join(action_sentences) if action_sentences else None

    parts: list[str] = []
    for match in _PART_TRIGGER.finditer(report_text):
        part = match.group(1).strip(" .,;")
        if part and part.lower() not in (seen.lower() for seen in parts):
            parts.append(part)
    parts_used = ", ".join(parts) if parts else None

    total_minutes = 0.0
    any_duration = False
    for value, unit in _DURATION.findall(report_text):
        any_duration = True
        amount = float(value)
        if unit.lower().startswith(("hour", "hr")):
            amount *= 60
        total_minutes += amount
    time_spent_minutes = round(total_minutes) if any_duration else None

    return ExtractedFields(issue=issue, action_taken=action_taken, parts_used=parts_used, time_spent_minutes=time_spent_minutes)
