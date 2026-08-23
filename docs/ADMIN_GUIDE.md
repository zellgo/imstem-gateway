# Admin guide

## URLs

| Who | URL |
|---|---|
| **Employees (chat homepage)** | https://open-webui-production-f828.up.railway.app |
| Agents (Codex / Claude Code) | https://imstem-gateway-production.up.railway.app/v1 |
| LiteLLM admin (keys, spend) | https://imstem-gateway-production.up.railway.app/ui |

The LiteLLM host is an **admin/API** site. Do not send it to employees as the homepage. First Open WebUI login on an empty database becomes the admin user; after that, create employees in Open WebUI Admin → Users (`ENABLE_SIGNUP` is off).

Log into LiteLLM UI with `UI_USERNAME` / `UI_PASSWORD`, then paste `LITELLM_MASTER_KEY` when asked.

Login can show a yellow **No Redis configured** banner. That is a warning, not a failed login. This stack runs **one LiteLLM worker** on purpose (small team, no Redis). Budgets still apply. `LITELLM_DISABLE_NO_REDIS_WARNING=true` hides the banner. Add a Railway Redis service only if you scale to more than one worker or replica.

## Company model names

Employees never type DeepSeek / Qwen / MiMo. They pick a company name. Default mapping (change anytime in the UI):

| Employees call | Default backend | Provider prefix | Credential |
|---|---|---|---|
| `company-fast` | DeepSeek Chat (extra: Qwen Turbo) | `deepseek/` / `dashscope/` | `deepseek` / `dashscope` |
| `company-standard` | Qwen Plus (extra: MiMo V2.5) | `dashscope/` / `xiaomi_mimo/` | `dashscope` / `mimo` |
| `company-pro` | **MiMo V2.5 Pro** (extra: Qwen Max) | `xiaomi_mimo/` / `dashscope/` | `mimo` / `dashscope` |
| `mimo-pro` | MiMo V2.5 Pro | `xiaomi_mimo/` | `mimo` |
| `company-agent` | DeepSeek Chat (extra: Qwen Plus) | `deepseek/` / `dashscope/` | `deepseek` / `dashscope` |

In **Add Model** / **LLM Credentials**:

- Qwen → **Dashscope**
- Xiaomi MiMo keys → credential `mimo`, provider **Custom Openai** (LiteLLM has no Xiaomi credential form, so the API key box would be blank/locked). Models still use the `xiaomi_mimo/` prefix and show as Xiaomi MiMo on the model list.
- DeepSeek → **Deepseek**

Two rows with the same public name are one group (primary + extra). Codex/Claude default names (`gpt-4o`, `claude-sonnet-4-5`, …) are aliases of `company-agent`.

## Change which LLM a company model uses, or its price

These rows are stored in Postgres (`LiteLLM_ProxyModelTable`) and have a **database** badge. They are editable.

1. LiteLLM UI → **Models + Endpoints** → **All Models**
2. Open the **database** row (not a **config** row)
3. **Edit Settings**
   - `litellm` model: e.g. `xiaomi_mimo/mimo-v2.5-pro` → `dashscope/qwen-max` or `deepseek/deepseek-chat`
   - Existing credential: `mimo` / `dashscope` / `deepseek`
   - Input / output cost per token (or per 1M, depending on the form)
4. Save. New requests pick it up; no git push.

If you still see grey **config** copies, the old `config.yaml` is still deployed. Push the yaml that no longer lists those models.

Reset to the git defaults:

```bash
python3 scripts/sync-company-models.py
```

## Rotate DeepSeek / Qwen / MiMo keys

LiteLLM UI → **Models + Endpoints** → **LLM Credentials** → `deepseek` / `dashscope` / `mimo`

Change `api_key` and `api_base`. Encrypted in `LiteLLM_CredentialsTable` (database **`litellm`**). First-time seed:

```bash
python3 scripts/bootstrap-credentials.py
```

Pass `--update` only if you want to overwrite UI-edited keys from `.env` / Railway variables.

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
- CHAT key (browser only)
- **AGENT key** — private to that employee — plus the Codex / Claude Code snippets printed by the script

The AGENT key is what Codex and Claude Code use. Spend for that key is always `user_id = MED00X` and `key_alias = MED00X-AGENT`. See [CODING_AGENTS.md](CODING_AGENTS.md).

Default create-user talks to production:

```bash
PUBLIC_GATEWAY_URL=https://imstem-gateway-production.up.railway.app \
  ./scripts/create-user.sh MED004 Medical
```

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

Edit `litellm/config.yaml` aliases, or restrict models on the key (`models` list). Employees never see `deepseek-chat` / `qwen-plus` / `mimo-v2.5-pro`. Open WebUI should list `company-fast`, `company-standard`, `company-pro`, and `mimo-pro` (`mimo-pro` is MiMo V2.5 Pro, same backend as `company-pro`).

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
