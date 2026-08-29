"""
Low-confidence single-vs-multiple-freelancer triage, run against the short
Gmail alert snippet only. Upwork's job page has an explicit "number of
freelancers to hire" field visible in screenshots — proposals.services
re-derives/confirms freelancer_type from there once screenshots exist.
This heuristic exists purely to give the dashboard a first-pass filter
before that.
"""

import re

from jobs.models import Job

MULTIPLE_PATTERNS = [
    r"multiple freelancers",
    r"\bteam of\b",
    r"several freelancers",
    r"more than one freelancer",
    r"looking for freelancers\b",
    r"hiring \d+\+?\s*(freelancers|people|developers|writers)",
    r"\d+\s*(freelancers|people)\s*needed",
    r"\btesters\b",
    r"\bpeople\b",
    r"\bseveral\b",
]

SINGLE_PATTERNS = [
    r"\bone freelancer\b",
    r"\ba single freelancer\b",
    r"looking for a freelancer\b",
    r"hiring 1 freelancer",
    r"\bsomeone\b",
    r"\btester\b",
    r"\bfreelancer\b",
    # Singular "a/an <role>" for any position, e.g. "a developer", "an editor",
    # "a writer", "a designer", "an analyst" — a broad proxy for "hiring one
    # of a given role" rather than a fixed list of job titles. Deliberately
    # loose (this whole heuristic is best-effort triage, not ground truth)
    # so it will also catch some false positives like "a paper" or "a lawyer".
    r"\ban?\s+\w+(?:er|or|ist)\b",
]


def classify(text: str) -> tuple[str, dict]:
    text = (text or "").lower()

    multiple_hits = [p for p in MULTIPLE_PATTERNS if re.search(p, text)]
    single_hits = [p for p in SINGLE_PATTERNS if re.search(p, text)]

    meta = {"multiple_hits": multiple_hits, "single_hits": single_hits}

    if multiple_hits and not single_hits:
        return Job.FreelancerType.MULTIPLE, meta
    if single_hits and not multiple_hits:
        return Job.FreelancerType.SINGLE, meta
    return Job.FreelancerType.UNKNOWN, meta
