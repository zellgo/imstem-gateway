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

## Coding agents (Codex, Claude Code, OpenCode)

Ask admin for **your** AGENT key. It looks like `MED001-AGENT`. Nobody else should have it. All of your agent usage is billed and reported under that key.

### Codex / OpenCode

```bash
export OPENAI_BASE_URL=https://imstem-gateway-production.up.railway.app/v1
export OPENAI_API_KEY=sk-…your AGENT key…
```

Prefer model `company-agent`. If the tool still sends `gpt-4o` or `gpt-5`, the gateway maps that to `company-agent` and still counts it as **you**.

### Claude Code

```bash
export ANTHROPIC_BASE_URL=https://imstem-gateway-production.up.railway.app
export ANTHROPIC_API_KEY=sk-…your AGENT key…
export ANTHROPIC_MODEL=company-agent
```

Do not add `/v1` on `ANTHROPIC_BASE_URL`. Full copy-paste examples: [CODING_AGENTS.md](CODING_AGENTS.md).

Never put a DeepSeek / Qwen / MiMo key in an agent tool. Those stay on the server.

## What you must not upload

| Class | Examples | Rule |
|---|---|---|
| Public | papers, public regs | OK |
| Internal | drafts, non-public decks | OK on this system |
| Sensitive | PHI, identifiable patients, passwords, API keys, unapproved legal files | **Do not upload** unless a separate approved environment exists |

De-identify clinical content before any AI use.

## Problems

Contact the gateway admin (ADMIN001). If a key stops working it was probably rotated or your monthly budget was hit.
