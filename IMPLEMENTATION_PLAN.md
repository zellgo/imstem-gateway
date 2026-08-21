# Implementation plan — ImStem AI Gateway

Adapted from `公司统一 AI Gateway 部署与管理平台.md` for the actual hosting the company is using now.

## Goal

A 5–10 person biotechnology company gateway:

- Employees talk to `company-fast` / `company-standard` / `company-pro` / `company-agent`
- Real DeepSeek / Qwen / MiMo keys never leave the server
- Each employee has `EMP-CHAT` and `EMP-AGENT` virtual keys so chat vs agent spend is separate
- Management can answer “how much did MED001 spend this month?”

## What changed from the original US-VPS sketch

| Original spec | What we are actually doing |
|---|---|
| Docker Compose on a US Linux server | LiteLLM + Open WebUI on **Railway**, auto-deployed from `https://github.com/zellgo/imstem-gateway` |
| Compose Postgres volume | Existing **Railway Postgres** (`Postgres` service in project `ImStem-Gateway`) |
| Public 443 via Caddy on the VPS | Railway HTTPS on two services; Caddy kept for the later China self-host |
| Phase 1 = US server | Phase 1 = Railway + local development against that Postgres |

The self-host Compose file remains so China migration does not require a redesign.

## Architecture

```
Employees
  ├── browser  →  Open WebUI  →  MED00X-CHAT virtual key
  └── Codex / OpenCode / agents  →  MED00X-AGENT virtual key
           │
           ▼
     LiteLLM (/v1)
           │
     Railway Postgres
      ├── database litellm     users, keys, spend
      └── database openwebui   accounts, sessions, chats
           │
     ┌─────┼──────┐
     ▼     ▼      ▼
  DeepSeek Qwen  MiMo
```

PostgreSQL is **not** on the public internet. Railway services use the private hostname. Local development uses `scripts/db-tunnel.sh` (SSH local forward to `127.0.0.1:15432`).

Redis is omitted. One LiteLLM replica is enough for 5–10 people. Add Redis later only if a second replica is required.

## Identity

- Accounting ID = `MED001`, `CMC001`, … never a person’s name
- Departments: Medical, CMC, Clinical, BD, Finance, Admin (`config/employees.yaml`)
- Two LiteLLM keys per employee: `ID-CHAT` and `ID-AGENT`
- Open WebUI signup is disabled. Admin creates a user with the same employee ID and sets that user’s OpenAI key to `ID-CHAT`

That last point is the simplest way to keep per-employee attribution through the chat UI. A shared Open WebUI key would collapse spend into one bucket, which the spec forbids.

## Services (Railway project ImStem-Gateway)

| Service | Role |
|---|---|
| Postgres | Existing managed Postgres 18 with volume |
| imstem-gateway | LiteLLM, built from this GitHub repo |
| open-webui | Official Open WebUI image (added after first LiteLLM deploy) |

## Local workflow

1. `./scripts/db-tunnel.sh` — keep running
2. Put provider keys in `.env`
3. `docker compose up` **or** `litellm --config litellm/config.yaml --port 4000`
4. `./scripts/healthcheck.sh`
5. `./scripts/bootstrap-org.py` then `./scripts/create-user.sh MED001 Medical`

## Security defaults

- Provider keys only in Railway variables / local `.env` (gitignored)
- Prompt bodies not stored (`turn_off_message_logging`, `store_prompts_in_spend_logs: false`)
- LiteLLM admin UI: `UI_USERNAME` / `UI_PASSWORD` + master key. Do not give employees the gateway hostname except `/v1`
- Open WebUI: signup off
- No PHI / identifiable patient data (see `docs/SECURITY.md`)

## Done when

See the checklist in the original requirements. First milestone for this pass:

- [x] Repo structure
- [x] Railway Postgres `litellm` and `openwebui` databases
- [ ] Local LiteLLM talking to Railway Postgres
- [ ] GitHub push (Railway already points at `zellgo/imstem-gateway`)
- [ ] Railway LiteLLM health endpoint
- [ ] Open WebUI service
- [ ] Sample employees + CHAT/AGENT keys
- [ ] Provider smoke tests (need DeepSeek / DashScope / MiMo keys)
