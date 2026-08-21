# ImStem AI Gateway

Company LLM gateway for a small biotechnology team. Employees use internal model names (`company-fast`, `company-standard`, `company-pro`, `company-agent`). Upstream DeepSeek / Qwen / MiMo keys stay on the server.

**Chat:** Open WebUI  
**Agents (Codex, OpenCode, etc.):** OpenAI-compatible ` /v1 ` on LiteLLM  
**Accounting:** Railway PostgreSQL via LiteLLM virtual keys (`MED001-CHAT`, `MED001-AGENT`, …)

## Architecture

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

```
Open WebUI / Codex  →  LiteLLM virtual key  →  LiteLLM  →  DeepSeek | Qwen | MiMo
                                              └── Railway Postgres (keys, spend, sessions)
```

## Local development (cloud database)

Postgres is already on Railway. Do **not** run a local database.

```bash
cp .env.example .env   # already created on the build machine
./scripts/db-tunnel.sh                 # leave this running
# another terminal:
pip install 'litellm[proxy]' 'psycopg[binary]' pyyaml
set -a && source .env && set +a
litellm --config litellm/config.yaml --port 4000
./scripts/healthcheck.sh
```

Or, with Docker Desktop:

```bash
./scripts/db-tunnel.sh
docker compose up -d
```

Open:

- Gateway / Admin UI: http://127.0.0.1:4000/ui  (master key + UI password)
- Open WebUI: http://127.0.0.1:3000

## Railway

Project `ImStem-Gateway` is linked. Service `imstem-gateway` deploys from `zellgo/imstem-gateway` on `main`. Pushing to GitHub is the deploy.

Required service variables (set once, never commit):

| Variable | Value |
|---|---|
| `DATABASE_URL` | `postgresql://${{Postgres.PGUSER}}:${{Postgres.POSTGRES_PASSWORD}}@${{Postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/litellm` |
| `LITELLM_MASTER_KEY` | `sk-…` |
| `LITELLM_SALT_KEY` | `sk-…` (set once, never rotate after models are saved) |
| `UI_USERNAME` / `UI_PASSWORD` | admin UI |
| `DEEPSEEK_API_KEY` | provider |
| `DASHSCOPE_API_KEY` | Qwen |
| `MIMO_API_KEY` | Xiaomi MiMo |
| `STORE_MODEL_IN_DB` | `True` |

## Employee usage — private keys

Each employee gets two virtual keys. They never receive DeepSeek / Qwen / MiMo secrets.

| Key | Who uses it | Tracked as |
|---|---|---|
| `MED001-CHAT` | Open WebUI | that employee’s chat spend |
| `MED001-AGENT` | Codex, Claude Code, OpenCode | that employee’s agent spend |

```bash
# Codex / OpenCode
OPENAI_BASE_URL=https://imstem-gateway-production.up.railway.app/v1
OPENAI_API_KEY=<that employee's MED001-AGENT key>

# Claude Code  (no /v1 on the base URL)
ANTHROPIC_BASE_URL=https://imstem-gateway-production.up.railway.app
ANTHROPIC_API_KEY=<same MED001-AGENT key>
ANTHROPIC_MODEL=company-agent
```

Issue a new pair: `./scripts/create-user.sh MED004 Medical`  
Details: [docs/CODING_AGENTS.md](docs/CODING_AGENTS.md)

## Ops

| Task | Command |
|---|---|
| Create employee | `./scripts/create-user.sh MED004 Medical` |
| Offboard | `./scripts/offboard-user.sh MED003` |
| Health | `./scripts/healthcheck.sh` |
| Monthly CSV | `python3 scripts/monthly-report.py --month 2026-08` |
| Backup | `./scripts/backup.sh` |
| Restore | `./scripts/restore.sh backups/<stamp>` |

## Docs

- [Admin](docs/ADMIN_GUIDE.md)
- [Employee](docs/EMPLOYEE_GUIDE.md)
- [Cost](docs/COST_MANAGEMENT.md)
- [Security](docs/SECURITY.md)
- [Backup / restore](docs/BACKUP_RESTORE.md)
- [Migration to China](docs/MIGRATION_TO_CHINA.md)

## Shutdown / upgrade

Local: `docker compose down` or stop the `litellm` process. Railway: pause the service in the dashboard or revert the GitHub commit.

After a successful production deploy, pin image tags in `Dockerfile` and `docker-compose.yml` (replace `main-stable` / `v0.6.22` with the digest you tested).
