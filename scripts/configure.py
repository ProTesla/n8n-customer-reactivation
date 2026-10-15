#!/usr/bin/env python3
"""Create ready-to-import copies of the workflows with YOUR settings filled in.

Your real Google Sheet ID never has to be written into the files that get committed:
this script writes to build/ (which is git-ignored) and leaves workflows/ untouched.

Usage:
  python scripts/configure.py --sheet-id <GOOGLE_SHEET_ID>
  python scripts/configure.py --sheet-id <ID> --timezone Europe/Berlin --offset +01:00

--timezone/--offset change the time zone used by the Code nodes. The offset is a FIXED
offset, so only use a zone without daylight saving time (e.g. Africa/Lagos +01:00,
Asia/Dubai +04:00, Asia/Kolkata +05:30). See docs/known-limitations.md.
"""
import argparse, pathlib, re, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "workflows", ROOT / "build"


def offset_ms(off):
    m = re.fullmatch(r"([+-])(\d{2}):(\d{2})", off)
    if not m:
        sys.exit("--offset must look like +01:00 or -05:00")
    ms = (int(m.group(2)) * 60 + int(m.group(3))) * 60000
    return -ms if m.group(1) == "-" else ms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-id", required=True)
    ap.add_argument("--timezone", default="Africa/Lagos")
    ap.add_argument("--offset", default="+01:00")
    a = ap.parse_args()
    ms = offset_ms(a.offset)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for f in sorted(SRC.glob("*.json")):
        t = f.read_text(encoding="utf-8")
        t = t.replace("YOUR_GOOGLE_SHEET_ID", a.sheet_id)
        t = t.replace("Africa/Lagos", a.timezone)
        t = t.replace("'+01:00'", f"'{a.offset}'")
        t = t.replace("Date.now() + 3600000", f"Date.now() + ({ms})")
        (OUT / f.name).write_text(t, encoding="utf-8")
        print("wrote build/" + f.name)
    print("\nImport the files in build/ into n8n (order: see docs/setup.md). Do NOT commit build/.")


if __name__ == "__main__":
    main()
