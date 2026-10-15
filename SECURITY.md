# Security policy

## Reporting a vulnerability

Please do **not** open a public issue for security problems. Use GitHub's
"Report a vulnerability" button (Security tab) on this repository, or contact the maintainer privately.

## Before you contribute workflow files

Workflow exports from n8n contain your Google Sheet ID and credential IDs.
Always run this before committing:

```bash
python scripts/sanitize.py          # cleans workflows/*.json in place
python scripts/sanitize.py --check  # fails if anything private is left
```

Never commit: API keys, service-account key files, App Passwords, `.env`, real customer data,
or your tunnel/domain name. GitHub Actions runs the check on every push and pull request.

## If you accidentally pushed a secret

1. Revoke/rotate it immediately (OpenAI key, Gmail App Password, Google service-account key, Cal.com secret).
2. Removing the file in a new commit is **not enough**; the secret stays in git history.
   Rewrite history (`git filter-repo`) or, for a young repo, delete and recreate it.
