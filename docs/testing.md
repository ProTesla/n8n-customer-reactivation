# Testing

Keep `campaign_enabled = OFF` until the checks below pass, keep `max_emails_per_run` at 5 or fewer, and use inboxes you can read. `john@example.com` never delivers anywhere.

## 1. Smoke tests

1. **WF0:** execute it manually. The output should show your settings and an empty `problems` list.
2. **Credentials:** run each Google Sheets, OpenAI and Send Email node once from the editor to confirm access.

## 2. Demo test with the sample customers

Import [`sheet-template/sample-data/Customers.csv`](../sheet-template/sample-data/Customers.csv) and set `campaign_enabled = ON`. Replace the `example.com` addresses of CUS-0001 and CUS-0005 with an inbox you can read.

| ID | Situation | Expected result of WF1 |
|----|-----------|------------------------|
| CUS-0001 | Old service, opted in | Emailed |
| CUS-0005 | Oldest service, opted in | Emailed (first, oldest goes first) |
| CUS-0002 | Served recently | Untouched |
| CUS-0003 | Unsubscribed | Untouched |
| CUS-0004 | Invalid email | Not emailed; `DATA_QUALITY` row in `Errors` |
| CUS-0006 | Already booked | Untouched |

Then walk the whole journey:

1. Run **WF1** with *Manual Run*. Check the two emails (and spam folder); the unsubscribe footer should be present and the personalised booking link should open Cal.com with name and email prefilled.
2. In the sheet, CUS-0001 should be `CONTACTED` with `last_contacted_at` set, and `Campaign_Log` should show `ELIGIBLE_MARKED`, `EMAIL_SEND_STARTED`, `EMAIL_SENT`.
3. Click the unsubscribe link in one email. The GET page only asks for confirmation; pressing the button unsubscribes (`consent_status = UNSUBSCRIBED`, `campaign_status = STOPPED`).
4. For the other customer, make a real free booking through the emailed link. Cal.com sends the webhook; the customer becomes `BOOKED` / `STOPPED` with `stop_reason = BOOKED`.
5. Set `days_between_followups` to `0`, then run **WF5** with *Manual Run*. Only contacted, unbooked, opted-in customers get `FOLLOWUP-1`. Here, none should be sent. Reset the value afterwards.
6. Run **WF6** with *Manual Run*. The report arrives at `owner_email` and a row lands in `Results`.
7. Set `campaign_enabled` to `OFF` and run WF1. Expect a `CAMPAIGN_OFF_SKIP` row and no emails.

**V1 is done when:** a customer in the sheet becomes eligible, gets a personalised email with a working unsubscribe link, books through Cal.com, is marked `BOOKED` with the campaign `STOPPED`, receives no follow-up, and appears in the report; and the system survives duplicate webhooks and single-customer failures without corrupting the rest.

## 3. Failure tests

| Test | Expected |
|------|----------|
| Same booking webhook sent twice | Only one booking counted; second ignored |
| Customer unsubscribes (open link, press button) | No future emails |
| Invalid email | No email; `DATA_QUALITY` error logged |
| OpenAI failure (temporarily use a wrong key) | Email not sent; error logged; other customers continue |
| Gmail failure (temporarily use a wrong App Password) | Retries, then `EMAIL_FAILED` and an `Errors` row |
| Customer books after first email, before follow-up | Follow-up NOT sent |
| Campaign switched `OFF` | No new campaign emails |
| Booking with a different email than the customer's | Matched via the `customer_id` answer if present (mismatch noted); otherwise `BOOKING_UNMATCHED`, `Errors` row, operator alert |
| Booking cancelled | `booking_status = CANCELLED`; campaign still `STOPPED`; counted in report |
| Booking rescheduled | Date and booking ID updated; not counted twice |
| Webhook with a wrong signature | HTTP 401; `WEBHOOK_REJECTED` logged |
| WF1 run twice at once | No duplicate email (duplicate send-key holds) |
| AI returns a link or a discount | Rejected by validation; nothing sent |
| Duplicate `customer_id` in the sheet | Both rows skipped; `DATA_QUALITY` error |
| A required Settings key is blank | `problems` lists it; campaign forced `OFF` |

## Tips

- n8n Webhook nodes have a **Test** URL (works only while you click "Listen for test event") and a **Production** URL (works only when the workflow is Active). Give Cal.com the Production URL.
- The ngrok browser interstitial does not affect webhooks, only people opening links in a browser (it shows once on the unsubscribe page in development).
- To retest a customer, reset their `campaign_status`, `follow_up_count`, `last_contacted_at`, `booking_*` and `stop_reason` columns **and** use a new `campaign_id`, because the send-key is stored in `Campaign_Log`.
