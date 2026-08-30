# Security

## Keys

| Kind | Where it lives | Who sees it |
|---|---|---|
| DeepSeek / DashScope / MiMo / OpenRouter | Railway variables / local `.env` / `secret/openrouter.txt` | Admins only |
| `LITELLM_MASTER_KEY` / `LITELLM_SALT_KEY` | same | Admins only |
| Virtual keys `MED001-CHAT` / `MED001-AGENT` | LiteLLM DB (hashed) + employee | That employee + admin |

Never commit `.env`. Never put provider keys in Open WebUI.

`LITELLM_SALT_KEY` encrypts provider keys stored in the database. Set it once. Changing it makes stored keys unreadable.

## TLS

- Railway: HTTPS is provided on the public domain
- Self-host / China: Caddy in `docker-compose.selfhost.yml` with Let’s Encrypt

Do not publish ports 3000, 4000, or 5432.

## Firewall (self-host)

Allow:

- 22 from admin IP / VPN only
- 443 public
- 80 only for ACME redirect

Database listens on the Docker internal network only.

## Admin UI

LiteLLM `/ui` is not for employees. Protect it with:

- Strong `UI_USERNAME` / `UI_PASSWORD`
- Optional Caddy basic auth (`proxy/Caddyfile`)
- Later: Cloudflare Access or Tailscale

Open WebUI: `ENABLE_SIGNUP=false`. Admins create users.

## Logging

Default: employee ID, timestamp, model, provider, tokens, cost, status, latency.

Prompt and response bodies are turned **off** (`turn_off_message_logging`, `store_prompts_in_spend_logs: false`). Open WebUI still stores chat history for the employee in its own database — that is per-user product state, not a central prompt archive for training. Retention: disable unused accounts; backups follow `docs/BACKUP_RESTORE.md`.

## Data classes

1. **Public** — allowed
2. **Internal company** — allowed on this gateway
3. **Sensitive (PHI, identifiable participants, secrets, unapproved legal)** — do not upload. This stack is **not** a HIPAA/PHI platform.

## Postgres

Not public. Local access is an SSH tunnel (`scripts/db-tunnel.sh`), not a Railway TCP proxy.
