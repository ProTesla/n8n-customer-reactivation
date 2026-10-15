# Roadmap and upgrade path

Not built yet. The V1 architecture is designed so these can be added without rewrites.

## Near term

- Read the time zone from Settings instead of hard-coding it ([known limitations](known-limitations.md)).
- Add `List-Unsubscribe` and `List-Unsubscribe-Post` headers to the send node.
- A static fallback template when the AI output fails validation twice.
- Setting for auto-restarting a campaign after a cancelled booking.

## Moving from Gmail SMTP to Resend (or similar)

Needed once volume goes beyond a handful of test emails, or when real delivery tracking matters.

- Verify a sending domain you control (DNS records).
- Replace the Send Email node with the provider's send API and log the returned `message_id`.
- Build **WF4: Email Events**:

```
Webhook (POST /resend-events, raw body)
  -> verify signature (Svix)
  -> idempotency check on the event ID in Campaign_Log
  -> identify customer (message_id in Campaign_Log, fallback recipient email)
  -> switch on event type -> update Customers row + log event
```

| Provider event | Action |
|----------------|--------|
| delivered | `last_email_event = delivered`; log `EMAIL_DELIVERED` |
| bounced (permanent) | `campaign_status = STOPPED`, `stop_reason = BOUNCED`; log |
| complained (spam report) | `consent_status = UNSUBSCRIBED`, `STOPPED`, `stop_reason = COMPLAINED`. Treat like an unsubscribe |
| clicked | `last_email_event = clicked`; log. A click does not change booking status |
| opened | Log only if enabled; unreliable, never used for decisions |

A late `delivered` must never overwrite a stronger state. Priority: complained, bounced, clicked, delivered, sent. WF6 already counts these event types, so the report fills in automatically.

- Respect the provider's daily limits in `max_emails_per_run` and watch the spam-complaint rate; this is why consent and unsubscribe handling are mandatory.

## Later ideas

- Database for customer data (Supabase / PostgreSQL) instead of Sheets.
- Payments (for example Flutterwave): booking, then payment, then webhook, then **verify the transaction with the provider** before updating status. Never trust a payment webhook blindly.
- SMS, WhatsApp or Telegram channels.
- Business dashboard and richer analytics.
- CRM integrations and other booking tools (Calendly, SimplyBook.me).
- Multi-tenant architecture. If you manage several clients on one n8n instance, check the n8n license terms first.

## Principles to keep

Simple, reliable, reusable, understandable, maintainable. Not: over-engineered, AI for everything, 100+ nodes, hard to debug, dependent on manual intervention. Don't add infrastructure without a concrete requirement.
