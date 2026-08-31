# Admin guide

## URLs

| Who | URL |
|---|---|
| **Landing (3 links only)** | https://llm.imstem.org |
| **Employees (chat)** | https://chat.imstem.org |
| Agents (Codex / Claude Code) | https://llm.imstem.org/v1 |
| API guide | https://llm.imstem.org/guide |
| Official ￥ prices | https://llm.imstem.org/costs |
| LiteLLM admin (keys, spend in ￥) | https://llm.imstem.org/ui |

The LiteLLM host is an **admin/API** site. Do not send it to employees as the homepage. First Open WebUI login on an empty database becomes the admin user; after that, create employees in Open WebUI Admin → Users (`ENABLE_SIGNUP` is off).

Log into LiteLLM UI with `UI_USERNAME` / `UI_PASSWORD`, then paste `LITELLM_MASTER_KEY` when asked.

Login can show a yellow **No Redis configured** banner. That is a warning, not a failed login. This stack runs **one LiteLLM worker** on purpose (small team, no Redis). Budgets still apply. `LITELLM_DISABLE_NO_REDIS_WARNING=true` hides the banner. Add a Railway Redis service only if you scale to more than one worker or replica.

## Company model names

Employees pick the real model names. Backends are Aliyun Model Studio (workspace) and Xiaomi MiMo.

| Employees call | Backend | Credential |
|---|---|---|
| `qwen3.8-flash` | Aliyun `qwen3.8-flash` | `dashscope-tokenplan` |
| `qwen3.8-27b` | Aliyun `qwen3.8-27b` | `dashscope-tokenplan` |
| `qwen3.8-max` | Aliyun `qwen3.8-max` | `dashscope-tokenplan` |
| `kimi-k3` | Aliyun `kimi-k3` | `dashscope` |
| `deepseek-v4-flash-0731` | Aliyun `deepseek-v4-flash-0731` | `dashscope` |
| `deepseek-v4-pro-0813` | Aliyun `deepseek-v4-pro-0813` | `dashscope` |
| `mimo-v2.5` | `xiaomi_mimo/mimo-v2.5` | `mimo` |
| `mimo-v2.5-pro` | `xiaomi_mimo/mimo-v2.5-pro` | `mimo` |
| `glm-5.3-flash` | OpenRouter `z-ai/glm-5.3-flash` | `openrouter` |

Old `company-fast` / `company-agent` names still remap in the gateway so leftover Codex configs do not break, but they are not listed in Open WebUI. Employees only see the real model IDs above. `gpt-4o` / `claude-sonnet-4-5` remap to `kimi-k3`.

In **Add Model** / **LLM Credentials**:

- Qwen → **Dashscope** (API Key + API Base)
- Xiaomi → **Xiaomi** (API Key + API Base)
- DeepSeek → **Deepseek** (API Key + API Base on this image; upstream Deepseek form is key-only)

Codex/Claude default names (`gpt-4o`, `claude-sonnet-4-5`, …) are aliases of `kimi-k3`.

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

LiteLLM UI → **Models + Endpoints** → **LLM Credentials** → `deepseek` / `dashscope` / `dashscope-tokenplan` / `mimo` / `openrouter`

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
2. Virtual key `MED004-CHAT` (qwen3.8-* / kimi-k3 / deepseek-v4-* / mimo-v2.5*, default $30 / 30d)
3. Virtual key `MED004-AGENT` (same models plus Codex/Claude aliases, default $50 / 30d)

Then in Open WebUI Admin → Users:

1. Add user `MED004` (signup is disabled)
2. Attach that user’s `MED00X-CHAT` key with `python3 scripts/sync-openwebui-user-keys.py`

Chat spend is per employee in LiteLLM Usage (filter `MED001-CHAT`, …). Do not put a shared key back in Admin → Connections.

Give the employee:

- Open WebUI login
- CHAT key (browser only)
- **AGENT key** — private to that employee — plus the Codex / Claude Code snippets printed by the script

The AGENT key is what Codex and Claude Code use. Spend for that key is always `user_id = MED00X` and `key_alias = MED00X-AGENT`. See [CODING_AGENTS.md](CODING_AGENTS.md).

Default create-user talks to production:

```bash
PUBLIC_GATEWAY_URL=https://llm.imstem.org \
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

Restrict models on the virtual key. Open WebUI lists `qwen3.8-*`, `kimi-k3`, `deepseek-v4-*`, and `mimo-v2.5*`. Reset DB models with `python3 scripts/sync-company-models.py`. Onboard the spreadsheet with `python3 scripts/provision-employees.py` (writes `secret/outbox/`).

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
