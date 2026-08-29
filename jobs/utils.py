import re

# Upwork job page URLs carry a "~<token>" job identifier, e.g.
# https://www.upwork.com/jobs/Some-Job-Title_~021847182634219876543/
# This is a best-effort pattern pending confirmation against a live Upwork
# job URL (see plan open item: "current Upwork job-page URL format").
JOB_UID_RE = re.compile(r"~[0-9a-zA-Z]+")


def extract_job_uid(url: str) -> str | None:
    match = JOB_UID_RE.search(url or "")
    return match.group(0) if match else None
