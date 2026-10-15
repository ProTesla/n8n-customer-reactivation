#!/usr/bin/env python3
"""Sanitize n8n workflow exports and check the repo for leaks.

Usage:
  python scripts/sanitize.py            # clean workflows/*.json in place
  python scripts/sanitize.py --check    # scan the whole repo, exit 1 if anything looks private

Run the first form every time you re-export a workflow from n8n, BEFORE you commit.
The second form is also run by GitHub Actions on every push.
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
WF_DIR = ROOT / "workflows"
SHEET_PLACEHOLDER = "YOUR_GOOGLE_SHEET_ID"
CRED_PLACEHOLDER = "REPLACE_ME"
# Top-level keys n8n adds on export that identify your instance.
STRIP_KEYS = ["id", "versionId", "meta", "shared", "staticData", "tags", "createdAt",
              "updatedAt", "triggerCount", "homeProject", "isArchived"]


def clean_node(node):
    changed = False
    p = node.get("parameters", {})
    doc = p.get("documentId")
    if isinstance(doc, dict) and doc.get("mode") == "id" and doc.get("value") != SHEET_PLACEHOLDER:
        doc["value"] = SHEET_PLACEHOLDER
        changed = True
    for cred in (node.get("credentials") or {}).values():
        if isinstance(cred, dict) and cred.get("id") != CRED_PLACEHOLDER:
            cred["id"] = CRED_PLACEHOLDER
            changed = True
    return changed


def sanitize():
    for path in sorted(WF_DIR.glob("*.json")):
        wf = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for node in wf.get("nodes", []):
            changed |= clean_node(node)
        for k in STRIP_KEYS:
            if k in wf:
                del wf[k]
                changed = True
        if wf.get("pinData"):
            wf["pinData"] = {}
            changed = True
        if changed:
            path.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(("cleaned  " if changed else "ok       ") + path.name)


# ---------------------------------------------------------------- leak check
ALLOWED_EMAIL = re.compile(
    r"@(example\.(com|org|net)|n8n\.io|users\.noreply\.github\.com)$|^your\.gmail@gmail\.com$", re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "Private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "Service-account email": re.compile(r"[A-Za-z0-9-]+@[A-Za-z0-9-]+\.iam\.gserviceaccount\.com"),
    "Real ngrok domain": re.compile(r"https://(?!your-|YOUR-)[a-z0-9-]+\.ngrok(-free)?\.(app|dev|io)"),
    "Bearer token": re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"),
}
SHEET_ID_LIKE = re.compile(r"\b1[A-Za-z0-9_-]{43}\b")
TEXT_EXT = {".json", ".md", ".txt", ".csv", ".py", ".yml", ".yaml", ".sh", ".example", ""}
SKIP_DIRS = {".git", "build", "node_modules"}


def check():
    problems = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXT:
            continue
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in EMAIL.finditer(text):
            if not ALLOWED_EMAIL.search(m.group(0)):
                problems.append(f"{rel}: email address {m.group(0)}")
        for label, rx in SECRET_PATTERNS.items():
            if rx.search(text):
                problems.append(f"{rel}: {label}")
        if SHEET_ID_LIKE.search(text) and path.name != "sanitize.py":
            problems.append(f"{rel}: string that looks like a Google Sheet ID")
        if path.suffix == ".json" and "workflows" in rel.parts:
            wf = json.loads(text)
            for node in wf.get("nodes", []):
                doc = (node.get("parameters", {}).get("documentId") or {})
                if isinstance(doc, dict) and doc.get("mode") == "id" and doc.get("value") != SHEET_PLACEHOLDER:
                    problems.append(f"{rel}: node '{node['name']}' has a real documentId")
                for cred in (node.get("credentials") or {}).values():
                    if isinstance(cred, dict) and cred.get("id") != CRED_PLACEHOLDER:
                        problems.append(f"{rel}: node '{node['name']}' has a real credential id")
            if wf.get("pinData"):
                problems.append(f"{rel}: pinData is not empty (may contain real data)")
            if "meta" in wf and wf["meta"].get("instanceId"):
                problems.append(f"{rel}: contains n8n instanceId")
    if problems:
        print("POSSIBLE PRIVATE DATA FOUND:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("Leak check passed: no private data patterns found.")


if __name__ == "__main__":
    check() if "--check" in sys.argv else sanitize()
