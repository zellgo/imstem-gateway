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
GATEWAY="${PUBLIC_GATEWAY_URL:-http://127.0.0.1:${LITELLM_PORT:-4000}}"
AUTH="Authorization: Bearer ${LITELLM_MASTER_KEY:?LITELLM_MASTER_KEY missing}"

CHAT_BUDGET="${CHAT_BUDGET:-30}"
AGENT_BUDGET="${AGENT_BUDGET:-50}"
DURATION="${BUDGET_DURATION:-30d}"
CHAT_MODELS='["company-fast","company-standard"]'
AGENT_MODELS='["company-fast","company-standard","company-agent"]'

api() {
  local method="$1" path="$2" body="$3"
  curl -fsS -X "$method" \
    -H "$AUTH" -H "Content-Type: application/json" \
    -d "$body" \
    "${GATEWAY}${path}"
}

echo "Ensuring team ${DEPARTMENT}..."
api POST /team/new "{\"team_alias\":\"${DEPARTMENT}\",\"models\":[\"company-fast\",\"company-standard\",\"company-pro\",\"company-agent\"]}" >/tmp/imstem-team.json || true

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
chat=json.load(open("/tmp/${EMPLOYEE_ID}-CHAT.json"))
agent=json.load(open("/tmp/${EMPLOYEE_ID}-AGENT.json"))
print("")
print("Employee ${EMPLOYEE_ID} provisioned.")
print("Give these keys to the employee once. They are not stored in git.")
print("")
print("Open WebUI username: ${EMPLOYEE_ID}")
print("CHAT key (${EMPLOYEE_ID}-CHAT):", chat.get("key") or chat)
print("AGENT key (${EMPLOYEE_ID}-AGENT):", agent.get("key") or agent)
print("")
print("Chat/API base:  ${GATEWAY}/v1")
print("Agent env:")
print("  OPENAI_BASE_URL=${GATEWAY}/v1")
print("  OPENAI_API_KEY=<AGENT key>")
print("")
print("Create the matching Open WebUI user in Admin → Users (signup is disabled).")
print("Set that user's OpenAI API key to the CHAT key so spend is attributed to ${EMPLOYEE_ID}-CHAT.")
PY
