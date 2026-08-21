# Backup and restore

## What to back up

| Item | How |
|---|---|
| LiteLLM DB | `pg_dump -Fc` database `litellm` |
| Open WebUI DB | `pg_dump -Fc` database `openwebui` |
| Open WebUI volume | Docker volume `open-webui-data` on self-host; Railway volume if attached |
| Config | `docker-compose*.yml`, `litellm/config.yaml`, `proxy/Caddyfile`, `.env.example` |

Never back up real `.env` into git.

## Daily dump (Railway)

```bash
./scripts/backup.sh
```

Suggested retention: 7 daily, 4 weekly, 3 monthly.

## Restore

```bash
./scripts/restore.sh backups/20260821T120000Z
```

Then restart LiteLLM and Open WebUI. Virtual keys continue to work because they live in `LiteLLM_VerificationToken`.

## Recovery on a new server (China / VPS)

1. Install Docker
2. Clone this repo
3. Restore secrets into `.env`
4. Restore Postgres (`scripts/restore.sh` or `psql` / `pg_restore`)
5. Restore the Open WebUI volume
6. `docker compose -f docker-compose.selfhost.yml up -d`
7. Point DNS at the new host
8. `./scripts/healthcheck.sh`

A technically capable person who has the dumps and `.env` can do this without the original installer.
