# Cost management

Budgets exist to catch runaway agents and understand real usage, not to starve legitimate work.

## Layer 1 — LiteLLM (employee accounting)

Every request is stored as spend against a virtual key:

| Key | Who |
|---|---|
| `MED001-CHAT` | Browser / Open WebUI |
| `MED001-AGENT` | Codex / OpenCode / other tools |

Defaults (override per employee):

- Normal: CHAT $20–30 / month, AGENT $30–50 / month
- High-use Medical: CHAT $50, AGENT $50–100
- Admin/technical: up to $100 combined

Export:

```bash
python3 scripts/monthly-report.py --month 2026-08
```

CSV lands in `reports/YYYY-MM-usage.csv`.

## Layer 2 — Provider invoices

Once a month, compare:

```
sum(LiteLLM spend)
≈ DeepSeek invoice + DashScope invoice + MiMo invoice
```

Differences are normal at small scale (rounding, cached tokens, failed retries). Investigate if LiteLLM is **much higher** (double logging) or **much lower** (missing keys, untracked traffic).

How to investigate abnormal usage:

1. Sort the monthly CSV by `cost_usd`
2. Check `key_kind=agent` for loops
3. Revoke the AGENT key immediately if it is a runaway process
4. Inspect LiteLLM request counts by model — a flood of `company-pro` is the usual expensive pattern

## OpenAI / Anthropic APIs

They are **not** the default. ChatGPT / Claude subscriptions are usually cheaper for interactive work. Enable those APIs only as an explicit premium fallback in `litellm/config.yaml`.
