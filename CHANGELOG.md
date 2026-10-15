# Changelog

## v2.0.0 (spec revision 2026-09-28)

Test-scale build: **Gmail SMTP** instead of Resend. WF4 (email events) is intentionally not built.

Design changes since the first draft (v1):

| # | Change | Why |
|---|--------|-----|
| 1 | Eligibility split into initial-email and follow-up rules | v1 only excluded `STOPPED`, so contacted customers were re-picked every run |
| 2 | `campaign_id` is a fixed Settings value, not generated per run | A per-run ID makes the duplicate-email key useless |
| 3 | One state model: three columns, each owning one kind of state | v1 mixed states that existed in no column |
| 4 | Own unsubscribe mechanism (WF8) | Sending one-by-one via SMTP/API gives no built-in unsubscribe |
| 5 | Unmatched bookings handled explicitly | v1 had no path when the booking email differs from the customer email |
| 6 | Cancelled and rescheduled bookings handled | v1 only handled new bookings |
| 7 | Idempotency checks `Campaign_Log`, not the customer row | A customer row holds one booking ID and cannot detect duplicates |
| 8 | AI never writes URLs; n8n inserts links and the unsubscribe footer | Removes the risk of invented or altered links |
| 9 | Settings keys standardised to `snake_case` | v1 mixed several naming styles |
| 10 | Added WF0 (settings), WF7 (errors), WF8 (unsubscribe) | Needed for the Errors sheet, alerts and unsubscribe |
| 11 | `max_followups` = number of follow-ups after the initial email | v1 was ambiguous |
| 12 | Booking rate = bookings / customers contacted (delivered when known) | Matches the report numbers |
