# Coding agents (Codex, Claude Code, OpenCode)

Every employee gets a **private LiteLLM virtual key**. That key is not the DeepSeek / Qwen / MiMo secret. It belongs to one person, has its own budget, and every request is logged against that employee.

Typical pair:

| Key alias | Use |
|---|---|
| `MED001-CHAT` | Open WebUI in the browser |
| `MED001-AGENT` | Codex, Claude Code, OpenCode, other CLI agents |

Admin creates them with:

```bash
./scripts/create-user.sh MED001 Medical
```

The AGENT key is printed **once**. Put it in the employee’s local env or agent config. Do not commit it.

Gateway:

```text
https://llm.imstem.org
```

## Codex / OpenAI-compatible tools

```bash
export OPENAI_BASE_URL=https://llm.imstem.org/v1
export OPENAI_API_KEY=sk-…your-MED001-AGENT-key…
```

Optional Codex `~/.codex/config.toml`:

```toml
model = "kimi-k3"
model_provider = "imstem"

[model_providers.imstem]
name = "ImStem"
base_url = "https://llm.imstem.org/v1"
env_key = "OPENAI_API_KEY"
wire_api = "chat"
```

Set `model` to a gateway id (`kimi-k3`, `qwen3.8-flash`, …). If Codex still sends `gpt-4o` / `gpt-5`, the request fails — the gateway does not remap or fall back.

## Claude Code

Claude Code talks Anthropic’s `/v1/messages` API. LiteLLM accepts that path. **Do not** put `/v1` on `ANTHROPIC_BASE_URL` — Claude Code appends it.

```bash
export ANTHROPIC_BASE_URL=https://llm.imstem.org
export ANTHROPIC_API_KEY=sk-…your-MED001-AGENT-key…
export ANTHROPIC_MODEL=kimi-k3
```

Or in `~/.claude/settings.json`:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://llm.imstem.org",
    "ANTHROPIC_API_KEY": "sk-…your-MED001-AGENT-key…",
    "ANTHROPIC_MODEL": "kimi-k3"
  }
}
```

If Claude Code still sends `claude-sonnet-4-…`, the gateway remaps it to `kimi-k3`. Spend still lands on `MED001-AGENT`.

## OpenCode / other OpenAI SDKs

Same as Codex: `OPENAI_BASE_URL=…/v1` and `OPENAI_API_KEY=<AGENT key>`.

## How tracking works

```
Employee MED001
  └── MED001-AGENT virtual key
        └── LiteLLM_SpendLogs.user_id = MED001
        └── LiteLLM_SpendLogs.metadata.kind = agent
        └── LiteLLM_SpendLogs.key_alias = MED001-AGENT
```

Monthly:

```bash
python3 scripts/monthly-report.py --month 2026-08
```

The CSV has one row group per employee, key kind (chat vs agent), model, and cost. Two employees never share a key.

## Rules

- Never give an employee `DEEPSEEK_API_KEY` / `DASHSCOPE_API_KEY` / `MIMO_API_KEY` / `OPENROUTER_API_KEY`.
- Never share `MED001-AGENT` with MED002.
- Revoke with `./scripts/offboard-user.sh MED001` — the key stops immediately.
- Agent loops that burn budget only hit **that** employee’s AGENT cap, not the whole company.
