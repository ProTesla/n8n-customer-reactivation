# Data model

One Google workbook per client with five tabs. Workflows match tabs and columns **by name**: never rename them, and add new columns only at the far right. Headers for every tab are in [`sheet-template/`](../sheet-template/).

**Formats:** dates `YYYY-MM-DD`; timestamps ISO 8601 with offset (for example `2026-09-28T12:00:00+01:00`). Format all date and timestamp columns as **Plain text**.

## Customers

The owner edits this tab. The automation updates the status columns.

| Column | Meaning |
|--------|---------|
| `customer_id` | Unique ID (`CUS-0001`). Required. Never rely on names. Email is the secondary identifier |
| `first_name`, `last_name`, `email`, `phone` | Contact details. A valid email is required to be contacted |
| `last_service_date` | `YYYY-MM-DD`. Eligibility is based on this, not on `customer_status` |
| `last_service` | Service name used in the email. Falls back to Settings `default_service` |
| `total_spend` | Informational |
| `customer_status` | `NEW`, `ACTIVE` or `INACTIVE`. Informational; WF1 sets `INACTIVE` when marking eligible |
| `consent_status` | `OPTED_IN`, `UNKNOWN`, `UNSUBSCRIBED`, `DO_NOT_CONTACT`. Only `OPTED_IN` is emailed |
| `campaign_status` | Where the customer is in the outreach (see [state-machine.md](state-machine.md)) |
| `booking_status` | `NOT_BOOKED`, `BOOKED`, `CANCELLED` |
| `payment_status` | Stays `NOT_REQUIRED` in V1 |
| `last_contacted_at` | Timestamp of the last email sent |
| `follow_up_count` | Follow-ups already sent. `0` after the initial email |
| `last_email_event` | Reserved for email-event tracking (empty with Gmail SMTP) |
| `booking_date`, `booking_id` | From the latest Cal.com booking |
| `amount` | Empty in V1 |
| `notes` | Free text for the owner |
| `created_at`, `updated_at` | Timestamps |
| `unsubscribe_token` | Long random string created by WF1; goes in the unsubscribe link |
| `stop_reason` | `BOOKED`, `UNSUBSCRIBED`, `COMPLAINED`, `BOUNCED`, `INVALID_EMAIL`, `NOT_INTERESTED`, `OWNER_STOPPED` |

## Settings

Two columns: `key`, `value`. Keys are `snake_case` and must not be renamed. WF0 refuses to enable the campaign if a required key is missing.

| Key | Required | Example | Notes |
|-----|:--------:|---------|-------|
| `business_name` | yes | Demo Home Services | Used in emails |
| `sender_name` | yes | Demo Home Services | From name |
| `sender_email` | yes | your.gmail@gmail.com | The Gmail address behind the SMTP credential |
| `booking_link` | yes | https://cal.com/you/event | Must start with `https://`. Never hard-coded in workflows |
| `reactivation_days` | yes | 180 | Eligible when service is **more than** this many days ago |
| `max_followups` | yes | 2 | Follow-ups **after** the initial: 1 initial + 2 = 3 emails max |
| `days_between_followups` | yes | 7 | Minimum gap between emails |
| `max_emails_per_run` | yes | 5 | Safety cap per run. Keep small while testing |
| `campaign_id` | yes | REACTIVATION-Q4-2026 | Fixed for the life of a campaign (see below) |
| `campaign_enabled` | yes | OFF | Exactly `ON` enables; anything else is `OFF` (fail-safe) |
| `owner_email` | yes | owner@example.com | Receives the weekly report |
| `operator_email` | yes | you@example.com | Receives error alerts. Never shown to the owner |
| `public_base_url` | yes | https://YOUR-NGROK-DOMAIN | Base of the unsubscribe link |
| `business_email` | no | hello@example.com | Reply-to address. Falls back to `sender_email` |
| `default_service` | no | Home Cleaning | Used when a customer has no `last_service` |
| `current_offer` | no | (empty) | The AI may mention an offer only if this is filled in |
| `email_tone` | no | friendly and professional | Passed to the AI |
| `report_sheet_url` | no | link to the Results tab | Linked in the weekly report |
| `openai_model` | no | gpt-4o-mini | Default `gpt-4o-mini` |
| `timezone` | no | Africa/Lagos | Stored but **not yet used** by the Code nodes; see [known-limitations.md](known-limitations.md) |

**`campaign_id` identifies a campaign, not a run.** Runs happen daily and the campaign continues. Starting a new campaign (so customers can get a fresh initial email) means deliberately changing this value and, if wanted, resetting specific customers to `NOT_STARTED`.

## Campaign_Log

Append-only audit trail. Never edit or delete rows by hand.

Columns: `event_id`, `customer_id`, `email`, `event_type`, `campaign_id`, `email_sequence` (`INITIAL`, `FOLLOWUP-1`, ...), `message_id`, `booking_id`, `timestamp`, `status`, `error`, `metadata`.

`event_id` is unique: internal events use `EVT-<time>-<random>` IDs, Cal.com events use `CAL-<uid>-<trigger>`.

| Event types written by the current workflows |
|-----|
| `ELIGIBLE_MARKED`, `SKIPPED` (reason in `metadata`), `CAMPAIGN_OFF_SKIP` |
| `EMAIL_SEND_STARTED`, `EMAIL_SENT`, `EMAIL_FAILED`, `AI_INVALID_OUTPUT` |
| `BOOKING_CREATED`, `BOOKING_CANCELLED`, `BOOKING_RESCHEDULED`, `BOOKING_UNMATCHED` |
| `WEBHOOK_REJECTED`, `UNKNOWN_EVENT`, `UNSUBSCRIBED`, `REPORT_SENT` |

The weekly report also counts `EMAIL_DELIVERED`, `EMAIL_CLICKED`, `EMAIL_BOUNCED` and `EMAIL_COMPLAINED`, but nothing writes them until email-event tracking is added ([roadmap](roadmap.md)).

## Results

One snapshot row per weekly report, **counted from `Campaign_Log`** (never live counters).

Columns: `campaign_id`, `date`, `eligible`, `contacted`, `followups_sent`, `delivered`, `clicked`, `booked`, `cancelled`, `unsubscribed`, `complained`, `bounced`, `failed`, `revenue`. Counts are unique customers, except `followups_sent`, which counts emails. `revenue` is `0` in V1.

## Errors

Columns: `error_id`, `workflow`, `customer_id`, `node`, `error_type`, `message`, `timestamp`, `retry_count`, `resolved`, `execution_id`.

Error types in use: `API_ERROR`, `AI_INVALID_OUTPUT`, `DATA_QUALITY`, `UNMATCHED_BOOKING`, `UNKNOWN`. Set `resolved` to `TRUE` once handled; resolved data-quality rows can be logged again if the problem returns.
