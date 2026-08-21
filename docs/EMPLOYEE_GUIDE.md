# Employee guide — ImStem AI

## Chat (browser)

1. Open the company AI site (admin will send the URL)
2. Sign in with your employee ID (`MED001`, `CMC001`, …)
3. Pick a model:
   - **company-fast** — quick drafts, translation
   - **company-standard** — everyday work
   - **company-pro** — harder writing / reasoning
   - **company-agent** — tool-heavy work (usually via Codex, not the chat box)

Do not paste provider keys. You do not have them.

## Agents (Codex, OpenCode, and similar)

Ask admin for your **AGENT** key (`MED001-AGENT`).

```text
OPENAI_BASE_URL=https://<gateway-host>/v1
OPENAI_API_KEY=sk-…your AGENT key…
```

Set the model to `company-agent` (or `company-fast` / `company-standard`).

Never put a DeepSeek / Qwen / MiMo key in an agent tool.

## What you must not upload

| Class | Examples | Rule |
|---|---|---|
| Public | papers, public regs | OK |
| Internal | drafts, non-public decks | OK on this system |
| Sensitive | PHI, identifiable patients, passwords, API keys, unapproved legal files | **Do not upload** unless a separate approved environment exists |

De-identify clinical content before any AI use.

## Problems

Contact the gateway admin (ADMIN001). If a key stops working it was probably rotated or your monthly budget was hit.
