# State machine and eligibility

Three columns, each owning one kind of state. No state appears in two places.

## campaign_status (where the customer is in the outreach)

| Value | Meaning | Set by |
|-------|---------|--------|
| `NOT_STARTED` | Default. Never processed | Owner / import |
| `ELIGIBLE` | Passed eligibility; about to receive the initial email | WF1 |
| `CONTACTED` | Initial email sent, no follow-up yet | WF2 |
| `FOLLOW_UP_PENDING` | At least one follow-up sent and more remain | WF2 |
| `COMPLETED` | All allowed emails sent, no booking | WF2 |
| `STOPPED` | Campaign ended for this customer; `stop_reason` says why | WF3, WF8, owner |

```
NOT_STARTED -> ELIGIBLE -> CONTACTED -> FOLLOW_UP_PENDING -> COMPLETED
                         (from any state) -> STOPPED
```

## booking_status

```
NOT_BOOKED -> BOOKED -> CANCELLED
```

A link click is not a booking; Cal.com sends no event when someone merely opens the page.

## consent_status

```
OPTED_IN | UNKNOWN | UNSUBSCRIBED | DO_NOT_CONTACT
```

Only `OPTED_IN` customers receive reactivation emails.

## Rules that always hold

- **BOOKED means stop.** No further email once `booking_status = BOOKED`.
- **UNSUBSCRIBED means no future marketing email**, permanently, unless the customer opts back in through a proper process.
- Re-including a `COMPLETED` or `STOPPED` customer needs a deliberate manual reset. The system never does it automatically.
- A cancelled booking sets `booking_status = CANCELLED` but leaves the campaign `STOPPED`. It shows in the owner report so the business can follow up personally.

## Initial-email eligibility (WF1)

All must be true:

```
campaign_enabled = ON
customer_id exists and is unique
email is valid
last_service_date is a valid date and (today - last_service_date) > reactivation_days
consent_status = OPTED_IN
booking_status != BOOKED
campaign_status is NOT_STARTED or ELIGIBLE (blank counts as NOT_STARTED)
no unresolved EMAIL_SEND_STARTED for customer_id + campaign_id + INITIAL (and fewer than 3 failures)
```

"Today" is the date in the configured time zone. "Older than 180 days" means strictly more than 180. Customers are processed oldest service first and capped at `max_emails_per_run`.

## Follow-up eligibility (WF5)

All must be true:

```
campaign_enabled = ON
campaign_status is CONTACTED or FOLLOW_UP_PENDING
booking_status != BOOKED
consent_status = OPTED_IN
follow_up_count < max_followups
days since last_contacted_at >= days_between_followups
email is valid
no EMAIL_SEND_STARTED row for customer_id + campaign_id + FOLLOWUP-(follow_up_count + 1)
```

`max_followups = 2` means at most **3 emails**: `INITIAL`, `FOLLOWUP-1`, `FOLLOWUP-2`.

**Never assume a customer is still eligible because they were last week.** WF5 checks, and WF2 checks again just before sending. A customer who books after the first email but before the follow-up gets no follow-up.

## Duplicate-email key

`customer_id + campaign_id + email_sequence`, for example `CUS-0001 + REACTIVATION-Q4-2026 + FOLLOWUP-1`.

1. If `Campaign_Log` has an `EMAIL_SEND_STARTED` row for the key with no later `EMAIL_FAILED`, do not send.
2. `EMAIL_SEND_STARTED` is written **before** the SMTP call. If n8n crashes in between, the next run sees the started row and will not double-send; the operator reviews it. This deliberately favours never emailing twice over guaranteed delivery.
3. After an `EMAIL_FAILED`, the key may be retried, up to 3 failures.
