# Moving from local to a VPS

Do this only after the whole flow works locally. A VPS solves the two local weaknesses: schedules stop when your computer sleeps, and the ngrok URL is temporary.

## Checklist

1. Get a small VPS (1 to 2 vCPU, 2 GB RAM is plenty). Don't over-provision. Check the **full-term** price and the **renewal** price at checkout; introductory prices usually rise.
2. Get a domain and point an `A` record at the server (for example `automation.example.com`).
3. Install Docker and Docker Compose.
4. Run n8n behind a reverse proxy with HTTPS (Caddy below handles certificates automatically).
5. Update `WEBHOOK_URL` and the Settings `public_base_url` to the real domain.
6. Re-import the workflows (with `scripts/configure.py`), reselect credentials, set the environment variables, and re-point the Cal.com webhook to `https://automation.example.com/webhook/cal-booking`.
7. Run the whole test plan again ([testing.md](testing.md)).
8. Set up backups and alerts (below).

## Starting-point configuration

`docker-compose.yml` (adjust names and domain; keep secrets in a `.env` file next to it):

```yaml
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    restart: unless-stopped
    environment:
      - N8N_HOST=automation.example.com
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://automation.example.com/
      - GENERIC_TIMEZONE=Africa/Lagos
      - TZ=Africa/Lagos
      - NODE_FUNCTION_ALLOW_BUILTIN=crypto
      - N8N_BLOCK_ENV_ACCESS_IN_NODE=false
      - CAL_WEBHOOK_SECRET=${CAL_WEBHOOK_SECRET}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    volumes:
      - n8n_data:/home/node/.n8n
  caddy:
    image: caddy:2
    restart: unless-stopped
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
volumes:
  n8n_data:
  caddy_data:
```

`Caddyfile`:

```
automation.example.com {
    reverse_proxy n8n:5678
}
```

n8n's own internal database (SQLite by default, or PostgreSQL if you choose) holds workflows and credentials only. **Customer data stays in Google Sheets.**

## Backups

Back up: the n8n data volume; exported workflow JSON (regularly); a periodic copy of the Google workbook. Store `N8N_ENCRYPTION_KEY` **separately and safely**; without it a restored backup cannot decrypt credentials. Don't rely on the VPS as the only copy.

## Monitoring (keep it simple)

WF7 failure alerts, the `Errors` sheet, `EMAIL_FAILED` tracking in `Campaign_Log`, and the weekly report. The operator should know when something important breaks. Don't add Kubernetes, Redis, load balancers or a monitoring stack until the workload demands it.
