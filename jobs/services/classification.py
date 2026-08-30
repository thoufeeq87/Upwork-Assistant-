"""
Low-confidence single-vs-multiple-freelancer triage, run against the short
Gmail alert snippet only. Upwork's job page has an explicit "number of
freelancers to hire" field visible in screenshots — proposals.services
re-derives/confirms freelancer_type from there once screenshots exist.
This heuristic exists purely to give the dashboard a first-pass filter
before that.
"""

import re

from jobs.models import FreelancerTypeCorrection, Job, LearnedKeyword

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


# --- Learning from manual corrections ---
#
# When the user corrects a job's freelancer_type and explains why, that
# reason is mined for keywords/short phrases, stored as LearnedKeyword rows,
# and checked by classify_with_learned_keywords() as a fallback whenever the
# static regex heuristic above can't decide. Deliberately mines only the
# user's own reason text (not the job snippet) — the reason is a short,
# deliberate explanation ("mentions team of 3 testers"), so it's a much
# cleaner learning signal than mining noisy, generic snippet text.

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "to", "of", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "this", "that", "it", "its",
    "job", "jobs", "freelancer", "freelancers", "project", "projects",
    "need", "needs", "needed", "looking", "hire", "hiring", "hires",
    "please", "our", "we", "you", "your", "will", "can", "work", "working",
    "says", "say", "said", "mentions", "mention", "mentioned", "post", "posting",
}


def _extract_candidate_phrases(text: str) -> set[str]:
    """Unigrams and bigrams from `text`, lowercased, with filler words
    dropped. Bigrams tend to carry more signal ("team of", "single point")
    than isolated common words."""
    words = [w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS and len(w) > 2]
    bigrams = {f"{a} {b}" for a, b in zip(words, words[1:])}
    return set(words) | bigrams


def record_correction(job: Job, corrected_type: str, reason: str = "") -> FreelancerTypeCorrection:
    """Records a manual freelancer_type correction on `job`, updates the
    job itself, and — if a reason was given — reinforces LearnedKeyword
    rows from it so future jobs with similar wording classify correctly
    without another manual correction."""
    correction = FreelancerTypeCorrection.objects.create(
        job=job,
        previous_type=job.freelancer_type,
        corrected_type=corrected_type,
        reason=reason,
    )

    job.freelancer_type = corrected_type
    job.save(update_fields=["freelancer_type", "updated_at"])

    if reason and corrected_type in (Job.FreelancerType.SINGLE, Job.FreelancerType.MULTIPLE):
        for phrase in _extract_candidate_phrases(reason):
            keyword, created = LearnedKeyword.objects.get_or_create(
                phrase=phrase, freelancer_type=corrected_type, defaults={"weight": 1}
            )
            if not created:
                keyword.weight += 1
                keyword.save(update_fields=["weight", "updated_at"])

    return correction


def classify_with_learned_keywords(text: str) -> tuple[str, dict]:
    """classify() plus a fallback pass over LearnedKeyword when the static
    heuristic can't decide. Static patterns stay authoritative — learned
    keywords only kick in on an otherwise-unknown result, so a single
    correction can't override well-established rules."""
    freelancer_type, meta = classify(text)
    if freelancer_type != Job.FreelancerType.UNKNOWN:
        return freelancer_type, meta

    lowered = (text or "").lower()
    learned_multiple = [
        k.phrase for k in LearnedKeyword.objects.filter(freelancer_type=Job.FreelancerType.MULTIPLE) if k.phrase in lowered
    ]
    learned_single = [
        k.phrase for k in LearnedKeyword.objects.filter(freelancer_type=Job.FreelancerType.SINGLE) if k.phrase in lowered
    ]
    meta = {**meta, "learned_multiple_hits": learned_multiple, "learned_single_hits": learned_single}

    if learned_multiple and not learned_single:
        return Job.FreelancerType.MULTIPLE, meta
    if learned_single and not learned_multiple:
        return Job.FreelancerType.SINGLE, meta
    return Job.FreelancerType.UNKNOWN, meta
