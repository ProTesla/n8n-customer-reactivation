#!/usr/bin/env python3
"""Regenerate sheet-template/sample-data/Customers.csv with dates relative to today,
so the demo customers keep behaving the same way as time passes.

Usage: python scripts/make_sample_customers.py
Then replace the example.com addresses of CUS-0001 and CUS-0005 with an inbox you can read.
"""
import csv, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "sheet-template" / "sample-data" / "Customers.csv"
COLS = ["customer_id", "first_name", "last_name", "email", "phone", "last_service_date", "last_service",
        "total_spend", "customer_status", "consent_status", "campaign_status", "booking_status",
        "payment_status", "last_contacted_at", "follow_up_count", "last_email_event", "booking_date",
        "booking_id", "amount", "notes", "created_at", "updated_at", "unsubscribe_token", "stop_reason"]


def ago(days):
    return (datetime.date.today() - datetime.timedelta(days=days)).isoformat()


def row(**kw):
    base = {c: "" for c in COLS}
    base.update(customer_status="ACTIVE", consent_status="OPTED_IN", campaign_status="NOT_STARTED",
                booking_status="NOT_BOOKED", payment_status="NOT_REQUIRED", follow_up_count="0")
    base.update(kw)
    return base


rows = [
    row(customer_id="CUS-0001", first_name="Alex", last_name="Rivera", email="test+cus0001@example.com",
        last_service_date=ago(200), last_service="Deep Home Cleaning", notes="ELIGIBLE: old service, opted in"),
    row(customer_id="CUS-0002", first_name="Sam", last_name="Patel", email="test+cus0002@example.com",
        last_service_date=ago(30), last_service="Home Cleaning", notes="NOT ELIGIBLE: served recently"),
    row(customer_id="CUS-0003", first_name="Jordan", last_name="Lee", email="test+cus0003@example.com",
        last_service_date=ago(220), last_service="Window Cleaning", consent_status="UNSUBSCRIBED",
        campaign_status="STOPPED", stop_reason="UNSUBSCRIBED", notes="NOT ELIGIBLE: unsubscribed"),
    row(customer_id="CUS-0004", first_name="Casey", last_name="Brown", email="not-an-email",
        last_service_date=ago(210), last_service="Carpet Cleaning", notes="DATA_QUALITY: invalid email -> Errors sheet"),
    row(customer_id="CUS-0005", first_name="Morgan", last_name="Diaz", email="test+cus0005@example.com",
        last_service_date=ago(240), last_service="Home Cleaning", notes="ELIGIBLE: oldest, goes first"),
    row(customer_id="CUS-0006", first_name="Taylor", last_name="Kim", email="test+cus0006@example.com",
        last_service_date=ago(190), last_service="Deep Home Cleaning", booking_status="BOOKED",
        campaign_status="STOPPED", stop_reason="BOOKED", booking_id="cal_demo_uid", notes="NOT ELIGIBLE: already booked"),
]
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print("wrote", OUT.relative_to(ROOT))
