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
]

SINGLE_PATTERNS = [
    r"\bone freelancer\b",
    r"\ba single freelancer\b",
    r"looking for a freelancer\b",
    r"hiring 1 freelancer",
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
