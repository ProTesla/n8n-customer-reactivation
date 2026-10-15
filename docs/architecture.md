# Architecture

## Principles

```
n8n           = boss      (all business rules and state)
OpenAI        = copywriter (wording only, validated)
Google Sheets = database  (V1)
Gmail SMTP    = delivery
Cal.com       = booking system
```

- Many small workflows instead of one giant one.
- AI never controls eligibility, consent, booking status, follow-up limits, customer identification, or any link.
- Business rules live in Code nodes that don't know about Sheets; Sheets reads and writes sit in clearly named nodes at the start and end of each workflow. That keeps a later move to a real database possible.
- Always **fail safe**: when in doubt, don't send, and log why.

## Workflow map

| | Workflow | Called by |
|---|----------|-----------|
| WF0 | Get Settings | every other workflow |
| WF1 | Find Eligible Customers | schedule (daily 09:00) or manual |
| WF2 | Send Campaign Email | WF1, WF5 |
| WF3 | Cal.com Booking Webhook | Cal.com |
| WF5 | Follow-up Campaign | schedule (daily 10:00) or manual |
| WF6 | Weekly Report | schedule (Monday 08:00) or manual |
| WF7 | Error Handler | n8n, when a workflow fails |
| WF8 | Unsubscribe Handler | customers (link in every email) |

## WF0: Get Settings

Reads the `Settings` tab, turns the rows into one object, validates required keys and numeric values, and returns `{ settings, problems }`. If any required key is missing or invalid, `campaign_enabled` is forced to `OFF`. Every workflow calls it first, so a setting is never interpreted two different ways.

## WF1: Find Eligible Customers

```
Schedule / Manual -> Get Settings -> campaign ON?
   no  -> log CAMPAIGN_OFF_SKIP, stop
   yes -> read Customers -> read Campaign_Log
            |-> Eligibility Filter (oldest service first, capped at max_emails_per_run)
            |      -> mark ELIGIBLE (+ create unsubscribe_token if empty) -> log ELIGIBLE_MARKED
            |      -> loop: call WF2 (INITIAL), pause ~7 s between customers
            '-> Data Quality Check -> append DATA_QUALITY rows to Errors
```

Data-quality rejects (missing or duplicate `customer_id`, invalid email, unparseable date) go to `Errors` without blocking the other customers. Already-logged problems are not logged twice.

## WF2: Send Campaign Email (sub-workflow)

Input: `customer_id`, `email_sequence` (`INITIAL`, `FOLLOWUP-1`, ...).

```
Start -> Get Settings, read Customers, read Campaign_Log
  -> Pre-send Checks (state, consent, booking, sequence, spacing, duplicate key, retry limit)
        fail -> log SKIPPED with reason -> result: Skipped
  -> OpenAI (2 candidate emails, JSON) -> Validate & Build Email
        fail -> log AI_INVALID_OUTPUT + Errors row -> result: AI Invalid
  -> log EMAIL_SEND_STARTED (before sending)
  -> Send via Gmail SMTP (3 tries, 5 s apart)
  -> log EMAIL_SENT or EMAIL_FAILED
        ok   -> update customer row -> result: Sent
        fail -> Errors row -> result: Failed
```

WF2 always returns a small result object so the calling loop continues with the next customer no matter what happened.

**Validation** (deterministic, in code). An AI candidate is rejected if it: isn't valid JSON with `subject` and `body`; has a subject over 120 characters or a body outside 20 to 1,500 characters; doesn't contain `{{BOOKING_LINK}}` exactly once; contains any URL; contains a currency symbol or `%`; uses "discount", "free", "guarantee" or "off" when those words weren't in the provided inputs; mentions AI or automation; or names a different customer. The first candidate that passes is used.

**Links are added by n8n.** The AI only writes the `{{BOOKING_LINK}}` placeholder. n8n replaces it with the Settings booking link plus URL-encoded `name`, `email` and `customer_id` prefill values, and appends the footer with the unsubscribe link.

## WF3: Cal.com Booking Webhook

```
Webhook (raw body) -> Verify & Parse (HMAC-SHA256 of raw body vs x-cal-signature-256)
  bad signature -> respond 401, log WEBHOOK_REJECTED
  -> respond 200 -> valid event?  no -> log UNKNOWN_EVENT
  -> read Settings, Campaign_Log, Customers -> Process Booking
       duplicate (event_id already in log) -> stop
       identify customer: rescheduleUid / booking_id -> customer_id answer -> attendee email
       no match -> BOOKING_UNMATCHED log + Errors row + email operator
       created     -> BOOKED, campaign STOPPED, stop_reason BOOKED
       cancelled   -> booking CANCELLED (campaign stays STOPPED)
       rescheduled -> update booking_id and date, not counted twice
```

## WF5: Follow-up Campaign

Daily: checks `campaign_enabled`, reads customers, filters those in `CONTACTED` or `FOLLOW_UP_PENDING` who are opted in, not booked, below `max_followups`, and at least `days_between_followups` since last contact. Calls WF2 with `FOLLOWUP-n`. WF2 re-checks everything immediately before sending, because state can change between the filter and the send.

## WF6: Weekly Report

Reads `Campaign_Log`, counts **unique customers** per event type for the current `campaign_id` (follow-ups are counted as emails), appends a snapshot row to `Results`, emails a plain-language report to `owner_email`, and logs `REPORT_SENT`. Booking rate is bookings divided by delivered customers; with Gmail SMTP there are no delivery events, so it falls back to customers contacted. Only bookings made **after** the customer's first campaign email count as campaign bookings.

## WF7: Error Handler

Error Trigger, then a row in `Errors`, then an email to `operator_email` with workflow, node, message and execution link. Per-customer failures inside loops are logged to `Errors` without an email, so one bad batch can't send dozens of alerts.

## WF8: Unsubscribe Handler

Public webhook at `/webhook/unsubscribe?t=<token>`. **GET** looks up the token and shows a confirm page with a button; it changes nothing, because email security scanners open links. **POST** (the button) sets `consent_status = UNSUBSCRIBED`, `campaign_status = STOPPED`, `stop_reason = UNSUBSCRIBED`, logs `UNSUBSCRIBED`, and returns a confirmation page. The token is long and random, so links can't be guessed from a customer ID.

## Failure behaviour

| Situation | Behaviour |
|-----------|-----------|
| OpenAI error or invalid output | Email not sent, error logged, other customers continue |
| SMTP failure | Retries, then `EMAIL_FAILED`; retried on a later run up to 3 times |
| Same webhook delivered twice | Second event ignored (`event_id` already in `Campaign_Log`) |
| Booking after first email, before follow-up | Follow-up not sent |
| Campaign switched `OFF` | No emails; `CAMPAIGN_OFF_SKIP` logged |
| Two runs at once | Duplicate send-key prevents a second email |
| n8n crashes between sending and logging | Started row blocks a resend; operator reviews (favours never emailing twice) |
