# Admin guide

## URLs

- Chat: Open WebUI (`ai` hostname)
- Gateway API: LiteLLM `/v1` (`gateway` hostname)
- LiteLLM admin: `/ui` on the gateway host — **admins only**

Log into LiteLLM UI with `UI_USERNAME` / `UI_PASSWORD`, then paste `LITELLM_MASTER_KEY` when asked.

## Create an employee

```bash
./scripts/create-user.sh MED004 Medical "Display Name"
```

This creates:

1. LiteLLM user `MED004`
2. Virtual key `MED004-CHAT` (company-fast, company-standard, default $30 / 30d)
3. Virtual key `MED004-AGENT` (plus company-agent, default $50 / 30d)

Then in Open WebUI Admin → Users:

1. Add user `MED004` (signup is disabled)
2. Put the CHAT key in that user’s OpenAI API key field

Give the employee:

- Open WebUI login
- CHAT key (optional, already in the UI)
- AGENT key + `OPENAI_BASE_URL=https://<gateway>/v1` for Codex/OpenCode

Budgets are not hardcoded. Change them in LiteLLM UI or pass `CHAT_BUDGET` / `AGENT_BUDGET` when running the script.

High-use Medical example:

```bash
CHAT_BUDGET=50 AGENT_BUDGET=100 ./scripts/create-user.sh MED001 Medical
```

## Revoke an employee

```bash
./scripts/offboard-user.sh MED003
```

Then disable the Open WebUI user. Confirm in LiteLLM Virtual Keys that no `MED003-*` keys remain. Record the date in `config/employees.yaml`.

## Reset a budget

LiteLLM UI → Virtual Keys → select `MED001-CHAT` → set max budget / duration. Or delete and recreate the key (employee must update Codex if the AGENT key changes).

## Assign models

Edit `litellm/config.yaml` aliases, or restrict models on the key (`models` list). Employees never see `deepseek-chat` / `qwen-plus` / `mimo-v2.5-pro`.

## Read spend

- LiteLLM UI → Usage / Spend
- `python3 scripts/monthly-report.py --month 2026-08`

Questions this answers:

- How much did MED001 spend this month?
- Tokens for MED002
- Models MED003 called
- Top employee / agent spend
- Medical department total
- Calculated provider spend (reconcile with invoices — see COST_MANAGEMENT.md)

## Teams

```bash
python3 scripts/bootstrap-org.py
```

Creates Medical, CMC, Clinical, BD, Finance, Admin.
