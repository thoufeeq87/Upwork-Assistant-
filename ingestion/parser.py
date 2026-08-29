"""
Parses Upwork job-alert emails. Upwork alert emails only ever contain a
short snippet per job — never the full description — so this module never
attempts to reconstruct anything beyond title/snippet/link.

Built and validated against a real Upwork "New job alert" email (single
job per email, fetched 2026-08-29). Each job block in the email carries
three anchors around the same job URL, distinguished by the `link` query
parameter Upwork itself tags them with:
  - `link=title` — the job title anchor (its text is the title)
  - `link=more`  — trailing "more" link at the end of the snippet
    paragraph; its parent element's full text (minus the "more" label) is
    the snippet
  - no `link` param (just tracking `frkscc`) — the "View job details" CTA
    button; the cleanest canonical URL for the job

This dict-by-uid approach also handles the (currently unobserved, but
plausible) case of a digest email containing more than one job block.
"""

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from jobs.utils import JOB_UID_RE, extract_job_uid


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
    entries: dict[str, dict] = {}
    order: list[str] = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if not JOB_UID_RE.search(href) or "/jobs/" not in href:
            continue

        job_uid = extract_job_uid(href)
        if job_uid not in entries:
            entries[job_uid] = {"title": "", "url": "", "snippet": ""}
            order.append(job_uid)
        entry = entries[job_uid]

        link_param = parse_qs(urlparse(href).query).get("link", [None])[0]

        if link_param == "title":
            entry["title"] = link.get_text(strip=True)
        elif link_param == "more":
            entry["snippet"] = _snippet_from_more_link(link)
        elif link_param is None and not entry["url"]:
            entry["url"] = href

    jobs = []
    for job_uid in order:
        entry = entries[job_uid]
        if not entry["title"]:
            continue
        jobs.append(
            ParsedJob(
                title=entry["title"],
                snippet=entry["snippet"],
                url=entry["url"] or f"https://www.upwork.com/jobs/{job_uid}",
                job_uid=job_uid,
            )
        )
    return jobs


def _snippet_from_more_link(more_link) -> str:
    """The snippet paragraph and its trailing 'more' anchor live in the same
    parent element — take that element's full text and strip the anchor's
    own label off the end."""
    container = more_link.parent or more_link
    full_text = container.get_text(" ", strip=True)
    more_label = more_link.get_text(strip=True)

    idx = full_text.rfind(more_label)
    if idx != -1:
        return full_text[:idx].strip()
    return full_text.strip()
