# Upwork Assistant

Automates the workflow between "an Upwork job alert lands in Gmail" and "a
proposal is ready to copy into Upwork." It never touches Upwork.com itself —
screenshots are captured by your own browser via a small Chrome extension,
and no proposal is ever auto-submitted.

See `/root/.claude/plans/root-claude-uploads-1c2dc38f-3ada-578b-shimmying-honey.md`
(or ask for a copy) for the full architecture/build plan this was built from.

## Status

Phases 0, 1, 3, 4, 5, 6, 7 are implemented and smoke-tested locally
(skeleton + Railway config, models/admin/auth, classification heuristic,
dashboard, Chrome extension + screenshot API, Claude hook/proposal
generation). Phase 2 (Gmail ingestion) is implemented but **not yet
runnable** — it needs:

1. A Google Cloud OAuth client (Gmail readonly scope) — client ID/secret in `.env`.
2. A Gmail filter that labels your Upwork saved-search alert emails (default
   expected label: `Upwork/Alerts`, configurable via `GMAIL_ALERT_LABEL`).
3. A real sample alert email to validate `ingestion/parser.py` against —
   it was written from a best-effort guess at Upwork's alert HTML structure
   and needs to be checked against the real thing.

Screenshot storage in production (Cloudflare R2 or similar S3-compatible
bucket) is also not yet configured — local dev falls back to the filesystem
under `media/`.

## Local development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in what you have; blanks are fine for local dev
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` and log in. Without Gmail/Anthropic
credentials configured, the dashboard works but is empty and hook/proposal
generation will show a friendly "not configured yet" message instead of
erroring.

## Chrome extension (local testing)

1. `chrome://extensions` → enable Developer mode → "Load unpacked" → select
   the `extension/` directory.
2. Click the extension icon → "Set API token" → enter your dev server URL
   (`http://127.0.0.1:8000`) and the `EXTENSION_API_TOKEN` from your `.env`.
3. Open a Job's Upwork URL in your own browser, click the extension icon,
   click "Capture Screenshot."

## Deployment (Railway)

`Procfile` / `railway.json` are set up for Railway's Nixpacks builder
(collectstatic + migrate + gunicorn on deploy). Add a Railway Postgres addon
(`DATABASE_URL` is picked up automatically) and set the remaining env vars
from `.env.example` as service variables. Gmail sync is meant to run via a
second Railway **Cron Job** service (`python manage.py sync_gmail`) — not
yet wired up, see Phase 8 in the plan.

## Environment variables

See `.env.example` for the full list, with comments on what's required
where.
