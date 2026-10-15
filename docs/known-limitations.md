# Known limitations

Honest list of what this build does not do, so you know before relying on it.

## Time zone is fixed in the Code nodes

Every Code node has `const TZ = 'Africa/Lagos'` and builds timestamps with a fixed `+01:00` offset. This is correct in Lagos (no daylight saving) but wrong elsewhere. The Settings key `timezone` is stored but not yet used.

**Workaround:** `python scripts/configure.py --sheet-id <ID> --timezone <Zone> --offset <+HH:MM>`. This only works for zones **without daylight saving**, because the offset is fixed. Also set `GENERIC_TIMEZONE` and `TZ` and make sure your schedule hours still make sense.

**Proper fix (welcome as a PR):** read the zone from Settings and compute the offset with `Intl.DateTimeFormat`.

## No `List-Unsubscribe` header

Every email has a visible unsubscribe link in the footer, but the Send Email node is not configured to add the `List-Unsubscribe` / `List-Unsubscribe-Post` headers. Gmail and Yahoo therefore won't show their own one-click Unsubscribe button. WF8 is already built to accept the POST such a button would send.

## No delivery, bounce, click or complaint tracking

Gmail SMTP only confirms the message was accepted. The `Results` columns `delivered`, `clicked`, `bounced`, `complained` stay at 0, and the booking rate uses customers contacted as its denominator. For a bounce or an unreachable address, set `campaign_status = STOPPED` and `stop_reason = BOUNCED` in the sheet by hand; the workflows respect it. Real tracking means moving to a transactional provider ([roadmap](roadmap.md)).

## Gmail is for testing, not production

A free Gmail account allows about 500 recipients per day and shows your Gmail address as the sender. Sending many messages in a tight loop can trip spam systems, which is why sending is paced. Don't run real recurring campaigns on it.

## Google Sheets is the database

Fine for a few hundred to a few thousand customers. Limits and quirks: API quota (reads are paced and whole sheets are read once per run), no transactions (two simultaneous runs can race, the duplicate send-key is the safety net), and dates must be plain text. Move to PostgreSQL or Supabase when it outgrows this.

## Other

- **Unsubscribe link depends on your public URL.** With ngrok the link only works while the tunnel and n8n are running, and links already sent break if the domain changes.
- **Hidden `customer_id` prefill is not guaranteed.** If Cal.com does not pass it through, matching falls back to the attendee email, and a booking under a different email becomes `BOOKING_UNMATCHED` (the operator is alerted).
- **Cancelled bookings don't restart the campaign.** They show in the report for personal follow-up. Auto-restart is a possible future setting.
- **No payments.** `payment_status` is `NOT_REQUIRED` and `Results.revenue` is always `0`.
- **One workbook and one set of workflows per client.** There is no multi-tenant mode.
- **Consent is not verified**; see [security.md](security.md).
- **OpenAI model names and prices change often.** Check the current pricing page and set a spend limit.
- **No WF4.** The number is reserved for Resend event tracking.
