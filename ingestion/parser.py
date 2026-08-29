"""
Parses Upwork job-alert emails. Upwork alert emails only ever contain a
short snippet per job — never the full description — so this module never
attempts to reconstruct anything beyond title/snippet/link.

NOTE: built without a real sample alert email to validate against (open
plan item). The heuristics below assume a typical Upwork saved-search
digest: one or more job blocks, each anchored by a link to a job page
(`/jobs/...~<uid>...` or `/nx/...~<uid>...`) whose link text is the job
title, followed by a short paragraph of snippet text. Revisit once a real
sample is available.
"""

from dataclasses import dataclass

from bs4 import BeautifulSoup

from jobs.utils import extract_job_uid


@dataclass
class ParsedJob:
    title: str
    snippet: str
    url: str
    job_uid: str


def parse_alert_email(html: str) -> list[ParsedJob]:
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    seen_uids = set()
    jobs = []

    for link in soup.find_all("a", href=True):
        job_uid = extract_job_uid(link["href"])
        if not job_uid or job_uid in seen_uids:
            continue

        title = link.get_text(strip=True)
        if not title:
            continue

        snippet = _find_snippet_near(link)

        seen_uids.add(job_uid)
        jobs.append(ParsedJob(title=title, snippet=snippet, url=link["href"], job_uid=job_uid))

    return jobs


def _find_snippet_near(link_tag) -> str:
    """Walk forward through sibling/parent elements looking for the first
    substantial paragraph of text after the job title link — the snippet."""
    node = link_tag.find_parent(["td", "div", "table"]) or link_tag.parent
    if node is None:
        return ""

    for sibling in node.find_all_next(["p", "td", "div"], limit=10):
        text = sibling.get_text(" ", strip=True)
        if len(text) > 40:
            return text
    return ""
