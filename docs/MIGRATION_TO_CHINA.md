# Migration to China

The software does not change. Only the host, DNS, and possibly provider endpoints change.

## Why this is portable

- Everything is Compose + env vars + Postgres dumps
- Employees keep the same IDs and virtual keys
- Model aliases hide provider swaps (for example if MiMo is easier to reach from China than DeepSeek)

## Procedure

1. **Dump**
   - `./scripts/backup.sh` on the current environment
   - Copy `open-webui-data` volume if chats must move
2. **New server** in China: Docker, 2–4 vCPU, 8 GB RAM, 50 GB SSD is enough
3. **Clone** this repo. Fill `.env` with the same `LITELLM_MASTER_KEY` and `LITELLM_SALT_KEY` (required — salt cannot change)
4. **Postgres**
   - Use `docker-compose.selfhost.yml` (local Postgres) or a China-side managed Postgres
   - `./scripts/restore.sh backups/<stamp>` (adjust hosts if not Railway)
5. **Providers**
   - Confirm DeepSeek / DashScope / MiMo endpoints from the new network
   - Update `api_base` in `litellm/config.yaml` only if a China endpoint differs
6. **TLS**
   - Caddy issues Let’s Encrypt certs for `ai.<domain>` and `gateway.<domain>`
7. **DNS**
   - Lower TTL the day before
   - Switch A/AAAA records
8. **Test**
   - `./scripts/healthcheck.sh`
   - One CHAT request as MED001
   - One AGENT request as MED001-AGENT
   - Confirm spend still lands on those keys
9. **Rollback**
   - Point DNS back
   - Old Railway/US stack is still running until you decommission it

## Firewall reminder

22 from admin only, 443 public, 5432 internal.
