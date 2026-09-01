# Session handoff — ImStem gateway (2026-08-22)

Resume with: open this repo and read this file plus `docs/ADMIN_GUIDE.md`.

## What this session did

1. Explained LiteLLM Admin UI login: `UI_USERNAME` / `UI_PASSWORD`, then `LITELLM_MASTER_KEY`.
2. Config.yaml models are **read-only** in the UI. Employee models now live in Postgres (`LiteLLM_ProxyModelTable`) so backend + price can be edited.
3. Provider keys live in `LiteLLM_CredentialsTable` as named credentials: `deepseek`, `dashscope`, `mimo`.
4. Qwen uses `dashscope/` prefix. MiMo uses `xiaomi_mimo/` prefix. DeepSeek uses `deepseek/`.
5. LiteLLM’s UI omits Xiaomi and DeepSeek URL fields. This image patches `provider_create_fields.json` **and** the compiled dashboard JS so **Xiaomi** appears in the credential dropdown with API Key + API Base, and **Deepseek** also has API Base.
6. Single LiteLLM worker (`LITELLM_NUM_WORKERS=1`) + `LITELLM_DISABLE_NO_REDIS_WARNING=true`. The Redis banner is a warning, not a login failure.
7. Railway Data tab has **no database dropdown**. It only shows primary DB `railway` (empty). LiteLLM tables are in database **`litellm`**.

## Latest git (pushed to `main`)

Railway deploys `zellgo/imstem-gateway` from `main`.

- `f3d190a` Xiaomi in credential dropdown + DeepSeek API Base field (JS + JSON patch)
- `4a28c21` Xiaomi provider_create_fields patch
- `361d120` DeepSeek credential Custom OpenAI workaround (superseded for Deepseek form)
- `9901139` MiMo Custom OpenAI workaround (superseded; credential now `Xiaomi`)
- `9344dc4` Single worker, hide Redis banner
- `6741edb` Company models moved to Postgres

Scripts: `scripts/bootstrap-credentials.py`, `scripts/sync-company-models.py`, `scripts/patch-xiaomi-provider.py` (runs in Docker build).

## How to edit in the UI (after hard refresh)

https://llm.imstem.org/ui  
Login `admin` + UI password, then master key.

| Task | Where |
|---|---|
| Qwen key + URL | LLM Credentials → `dashscope` → provider **Dashscope** |
| Xiaomi key + URL | LLM Credentials → `mimo` → provider **Xiaomi** |
| DeepSeek key + URL | LLM Credentials → `deepseek` → provider **Deepseek** |
| Retarget company-pro / prices | All Models → **database** badge row → Edit Settings |

Do not pick native Xiaomi/Deepseek forms from an **old** cached JS bundle; Ctrl+Shift+R.

Employee-facing models: `qwen3.8-flash` / `qwen3.8-27b` / `qwen3.8-max` / `kimi-k3` / `deepseek-v4-flash-0731` / `deepseek-v4-pro-0813` / `mimo-v2.5` / `mimo-v2.5-pro` / `glm-5.3-flash` / `glm-5.3` / `glm-4.7-flash`. No `model_group_alias` and no router fallbacks. Clients must send an exact gateway model id. `glm-5.3-flash` uses the OpenRouter credential.

## Railway

- Project `ImStem-Gateway` `b69b4122-7af2-4bd6-bcb2-3703c8d947cd`
- Service `imstem-gateway` `b3c41bb3-4df9-4d49-aef7-2b9054020d7c`
- Postgres `8a2af395-a760-464d-9b04-477080c57858`
- DBs on that instance: `railway` (empty UI default), **`litellm`**, `openwebui`, `postgres`

Inspect LiteLLM tables via SSH/`psql -d litellm`, not the Data tab.

## Not done / watch

- DeepSeek/DashScope Railway vars may still be `replace-me`; paste real keys in LLM Credentials.
- Spend was $0 on old logs; new requests use baked-in prices on DB models.
- Do not rotate `LITELLM_SALT_KEY`.
- If LiteLLM image tag `main-stable` changes, re-test `scripts/patch-xiaomi-provider.py` (JS string replace).
