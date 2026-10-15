# Setup guide

Built for n8n 2.x (self-hosted, local), Google Sheets, Gmail SMTP, OpenAI `gpt-4o-mini` and Cal.com. Plan about an hour for a first setup.

## 1. Accounts you need

| Service | What to do | Notes |
|---------|-----------|-------|
| **n8n** | Run locally (`npx n8n` or Docker) | Community Edition is enough |
| **Google Cloud** | Create a project, enable the **Google Sheets API**, create a **service account**, download its JSON key | Share your workbook with the service account's email as **Editor**. A service account does not expire; OAuth apps in "Testing" status expire after 7 days |
| **OpenAI** | Create an API key, add a little prepaid credit, set a low monthly spend limit | A reactivation email costs a fraction of a cent |
| **Gmail** | Turn on 2-Step Verification, then create an **App Password** | Never use your normal password. SMTP: `smtp.gmail.com`, port 587 (STARTTLS) or 465 (SSL) |
| **Cal.com** | Free account, one event type with a booking question whose identifier is `customer_id` | Hide it from customers. If prefill of a hidden field fails, matching falls back to the attendee email |
| **ngrok** | Free account and one static domain | Only for local development; Cal.com and the unsubscribe link need a public HTTPS URL |

## 2. Environment variables

Copy the values from [`.env.example`](../.env.example), set them **before** starting n8n, then restart:

```
GENERIC_TIMEZONE=Africa/Lagos
TZ=Africa/Lagos
WEBHOOK_URL=https://YOUR-NGROK-DOMAIN
NODE_FUNCTION_ALLOW_BUILTIN=crypto
N8N_BLOCK_ENV_ACCESS_IN_NODE=false
CAL_WEBHOOK_SECRET=choose-a-long-random-secret
```

Start the tunnel in a second terminal: `ngrok http --url=YOUR-NGROK-DOMAIN 5678`

Why each one matters:

- `WEBHOOK_URL` makes n8n show your public address instead of `localhost`.
- `NODE_FUNCTION_ALLOW_BUILTIN=crypto` lets Code nodes verify signatures and generate random unsubscribe tokens.
- `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` lets WF3 read `CAL_WEBHOOK_SECRET`.
- Keep your `N8N_ENCRYPTION_KEY` backed up. Without it a restored n8n cannot decrypt its credentials.

## 3. Create the Google Sheet

1. Create a workbook with five tabs named **exactly**: `Customers`, `Settings`, `Campaign_Log`, `Results`, `Errors`.
2. Import the matching CSV from [`sheet-template/`](../sheet-template/) into each tab. When importing, **untick "Convert text to numbers, dates and formulas"**.
3. Format every date and timestamp column as **Plain text** (Format, Number, Plain text). Otherwise Sheets turns dates into numbers and the date maths breaks.
4. Freeze the header row. Never rename sheets or headers; workflows match by name. Add new columns only at the far right.
5. Optional but recommended: highlight duplicate `customer_id`, add dropdowns for `consent_status` and for `ON`/`OFF` in Settings, and protect `Campaign_Log`, `Results` and `Errors` so only the automation edits them.
6. Fill in the `Settings` tab (see [data-model.md](data-model.md)). Leave `campaign_enabled` at `OFF` until testing.
7. For a first run, import [`sheet-template/sample-data/Customers.csv`](../sheet-template/sample-data/Customers.csv) and replace the `example.com` addresses of CUS-0001 and CUS-0005 with an inbox you can read. (`python scripts/make_sample_customers.py` regenerates it with fresh dates.)

## 4. Fill in your IDs

The committed workflows contain the placeholder `YOUR_GOOGLE_SHEET_ID`. Generate import-ready copies:

```bash
python scripts/configure.py --sheet-id YOUR_REAL_SHEET_ID
```

Not in Lagos time? The Code nodes assume a fixed offset. For a zone **without daylight saving**:

```bash
python scripts/configure.py --sheet-id YOUR_REAL_SHEET_ID --timezone Asia/Dubai --offset +04:00
```

See [known-limitations.md](known-limitations.md). The output goes to `build/`, which is git-ignored. Never commit it.

## 5. Import the workflows

Import **one file at a time** (Workflows menu, Import from file) from `build/`, in this order, because later ones call earlier ones:

1. `WF0_Get_Settings.json`
2. `WF2_Send_Campaign_Email.json`
3. `WF1_Find_Eligible_Customers.json`
4. `WF3_CalCom_Booking_Webhook.json`
5. `WF8_Unsubscribe_Handler.json`
6. `WF5_Follow_up_Campaign.json`
7. `WF6_Weekly_Report.json`
8. `WF7_Error_Handler.json`

## 6. After each import

- Every **Google Sheets** node: pick your service-account credential.
- Every **Get Settings** node (Execute Workflow): choose `WF0 - Get Settings`.
- **Call WF2 - Send Email** (in WF1 and WF5): choose `WF2 - Send Campaign Email`.
- **OpenAI Generate Email** (WF2): pick your OpenAI credential.
- Every **Send Email** node (WF2, WF3, WF6, WF7): pick your Gmail SMTP credential.

Each workflow also has a yellow "Setup Notes" sticky note with its own checklist.

## 7. Activate

- Activate **WF3, WF8, WF7** first.
- Activate **WF1, WF5, WF6** only when you want scheduled runs (daily 09:00, daily 10:00, Monday 08:00).
- **Never activate WF0 or WF2.** They only run when called.
- In WF1, WF2, WF3, WF5, WF6 and WF8 open Settings (three dots), then **Error workflow**, and choose `WF7 - Error Handler`.

Scheduled workflows only run while n8n is running and the workflow is Active. If your computer sleeps, runs are missed; a VPS fixes this ([deployment-vps.md](deployment-vps.md)).

## 8. Connect Cal.com

After WF3 is Active:

- Webhook URL: `https://YOUR-NGROK-DOMAIN/webhook/cal-booking` (the **production** URL, not the test URL)
- Events: Booking Created, Cancelled, Rescheduled
- Secret: the same value as `CAL_WEBHOOK_SECRET`
- The event needs a booking question with identifier `customer_id`

## 9. Run the tests

Follow [testing.md](testing.md). Do not switch `campaign_enabled` to `ON` for real customers until the demo test and the failure tests pass.

## Optional

Add `openai_model` to the Settings tab to change the model (default `gpt-4o-mini`).
