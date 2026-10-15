# Security

## Secrets

- API keys and passwords live in **n8n credentials** only: OpenAI key, Gmail App Password, Google service account.
- The Cal.com webhook secret lives in an **environment variable** (`CAL_WEBHOOK_SECRET`), never in a node, never in a sheet.
- Never put keys in Google Sheets, and never give the business owner credentials or the n8n editor.
- Never put secrets in emails or reports.
- Keep `N8N_ENCRYPTION_KEY` safe and backed up separately from the n8n data.
- Use a Gmail **App Password**, not your account password. Gmail no longer accepts a plain password over SMTP.

## Webhook security

**Cal.com (WF3).** The webhook node has "Raw Body" enabled. The code computes HMAC-SHA256 of the raw request body with `CAL_WEBHOOK_SECRET`, accepts the signature header with or without a `sha256=` prefix, and compares in constant time. A wrong or missing signature gets HTTP 401 and a `WEBHOOK_REJECTED` log row. A missing secret also fails closed. After the signature, the event type, `uid`, start time and attendee email are validated, and duplicates are ignored via `event_id`.

If raw-body verification ever proves unreliable on your n8n version, a fallback is a long random token in the webhook path plus strict payload validation. Note it in your build log.

**Unsubscribe (WF8).** Public by design. It only accepts a valid, unguessable token and never reveals customer data on the page. GET never changes state, so link-scanning security software cannot unsubscribe anyone.

## Email safety

- Only `OPTED_IN` customers are emailed. Complaints and unsubscribes stop the campaign permanently.
- `max_emails_per_run` caps every run and sending is paced about 7 seconds apart, which also keeps Google Sheets calls well under quota.
- AI output is validated; it cannot add links, prices, discounts or guarantees.
- `campaign_enabled` is a kill switch: set to anything other than `ON` and nothing is sent.

## Consent and law

`OPTED_IN` must reflect genuine consent. Marking someone `OPTED_IN` who did not agree is the owner's responsibility (and a legal risk); the system cannot check it. Know the rules that apply to you and your customers (for example GDPR, CAN-SPAM, NDPA). This is not legal advice.

## Google Sheets access

- Use a **service account** (no expiry) and share the workbook only with that account and the people who need it.
- Protect `Campaign_Log`, `Results` and `Errors` so only the automation edits them. The owner edits `Customers` and `Settings` only.
- The report links to the workbook; keep link-sharing restricted and the protected tabs protected.

## Repository hygiene

- `python scripts/sanitize.py` strips your sheet ID, credential IDs and instance metadata from exports. `python scripts/sanitize.py --check` fails if anything private remains; CI runs it on every push.
- `.gitignore` excludes `.env`, key files, `build/` and spreadsheets.
- If you ever push a secret, rotate it first. Deleting it in a later commit does not remove it from history. See [SECURITY.md](../SECURITY.md).
