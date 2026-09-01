#!/usr/bin/env bash
# Onboard an employee: LiteLLM user + CHAT key + AGENT key.
# Usage: ./scripts/create-user.sh MED004 Medical ["Display Name"]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -f "${ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT}/.env"
  set +a
fi

EMPLOYEE_ID="${1:?employee id required, e.g. MED004}"
DEPARTMENT="${2:?department required, e.g. Medical}"
DISPLAY_NAME="${3:-$EMPLOYEE_ID}"
GATEWAY="${PUBLIC_GATEWAY_URL:-https://llm.imstem.org}"
AUTH="Authorization: Bearer ${LITELLM_MASTER_KEY:?LITELLM_MASTER_KEY missing}"

CHAT_BUDGET="${CHAT_BUDGET:-30}"
AGENT_BUDGET="${AGENT_BUDGET:-50}"
DURATION="${BUDGET_DURATION:-30d}"
MODELS_FILE="${ROOT}/config/agent-models.json"
CHAT_MODELS="$(python3 -c "import json; print(json.dumps(json.load(open('${MODELS_FILE}'))['chat_models']))")"
AGENT_MODELS="$(python3 -c "import json; print(json.dumps(json.load(open('${MODELS_FILE}'))['agent_models']))")"

api() {
  local method="$1" path="$2" body="$3"
  curl -fsS -A "Mozilla/5.0 ImStemGateway/1.0" -X "$method" \
    -H "$AUTH" -H "Content-Type: application/json" \
    -d "$body" \
    "${GATEWAY}${path}"
}

echo "Ensuring team ${DEPARTMENT}..."
api POST /team/new "{\"team_alias\":\"${DEPARTMENT}\",\"models\":[\"qwen3.8-flash\",\"qwen3.8-27b\",\"qwen3.8-max\",\"kimi-k3\",\"deepseek-v4-flash-0731\",\"deepseek-v4-pro-0813\",\"mimo-v2.5\",\"mimo-v2.5-pro\"]}" >/tmp/imstem-team.json || true

echo "Creating user ${EMPLOYEE_ID}..."
api POST /user/new "$(cat <<JSON
{
  "user_id": "${EMPLOYEE_ID}",
  "user_alias": "${DISPLAY_NAME}",
  "user_email": "${EMPLOYEE_ID}@imstem.local",
  "max_budget": $(python3 -c "print(${CHAT_BUDGET}+${AGENT_BUDGET})"),
  "budget_duration": "${DURATION}",
  "metadata": {"department": "${DEPARTMENT}", "employee_id": "${EMPLOYEE_ID}"}
}
JSON
)" >/tmp/imstem-user.json

echo "Creating ${EMPLOYEE_ID}-CHAT..."
CHAT_JSON="$(api POST /key/generate "$(cat <<JSON
{
  "user_id": "${EMPLOYEE_ID}",
  "key_alias": "${EMPLOYEE_ID}-CHAT",
  "models": ${CHAT_MODELS},
  "max_budget": ${CHAT_BUDGET},
  "budget_duration": "${DURATION}",
  "metadata": {"kind": "chat", "employee_id": "${EMPLOYEE_ID}", "department": "${DEPARTMENT}"}
}
JSON
)")"
echo "$CHAT_JSON" > "/tmp/${EMPLOYEE_ID}-CHAT.json"

echo "Creating ${EMPLOYEE_ID}-AGENT..."
AGENT_JSON="$(api POST /key/generate "$(cat <<JSON
{
  "user_id": "${EMPLOYEE_ID}",
  "key_alias": "${EMPLOYEE_ID}-AGENT",
  "models": ${AGENT_MODELS},
  "max_budget": ${AGENT_BUDGET},
  "budget_duration": "${DURATION}",
  "metadata": {"kind": "agent", "employee_id": "${EMPLOYEE_ID}", "department": "${DEPARTMENT}"}
}
JSON
)")"
echo "$AGENT_JSON" > "/tmp/${EMPLOYEE_ID}-AGENT.json"

python3 - << PY
import json
from pathlib import Path
emp = "${EMPLOYEE_ID}"
gw = "${GATEWAY}".rstrip("/")
chat = json.load(open(f"/tmp/{emp}-CHAT.json"))
agent = json.load(open(f"/tmp/{emp}-AGENT.json"))
chat_key = chat.get("key") or ""
agent_key = agent.get("key") or ""
print("")
print(f"Employee {emp} provisioned. Give these keys to that person only, once.")
print("They are not stored in git. Usage is tracked per key in LiteLLM.")
print("")
print(f"Open WebUI username: {emp}")
print(f"CHAT key  ({emp}-CHAT):  {chat_key}")
print(f"AGENT key ({emp}-AGENT): {agent_key}")
print("")
print("--- Codex / OpenCode / OpenAI SDKs ---")
print(f"  export OPENAI_BASE_URL={gw}/v1")
print(f"  export OPENAI_API_KEY={agent_key}")
print("  model: kimi-k3   (must be a gateway id; gpt-4o / gpt-5 are not remapped)")
print("")
print("--- Claude Code ---")
print(f"  export ANTHROPIC_BASE_URL={gw}")
print(f"  export ANTHROPIC_API_KEY={agent_key}")
print("  export ANTHROPIC_MODEL=kimi-k3")
print("  (do not append /v1; Claude Code adds /v1/messages)")
print("")
print("Create the matching Open WebUI user in Admin → Users (signup is disabled).")
print(f"Set that user's OpenAI API key to the CHAT key so browser spend is {emp}-CHAT.")
print(f"See docs/CODING_AGENTS.md")
out = Path(f"/tmp/{emp}-credentials.txt")
out.write_text(
    f"employee={emp}\n"
    f"chat_key={chat_key}\n"
    f"agent_key={agent_key}\n"
    f"openai_base={gw}/v1\n"
    f"anthropic_base={gw}\n"
)
print(f"Copy of this printout: {out}")
PY
