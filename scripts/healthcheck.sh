#!/usr/bin/env bash
# Check LiteLLM (and optionally Open WebUI) health.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -f "${ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT}/.env"
  set +a
fi

GATEWAY="${PUBLIC_GATEWAY_URL:-http://127.0.0.1:${LITELLM_PORT:-4000}}"
CHAT="${PUBLIC_CHAT_URL:-http://127.0.0.1:${OPENWEBUI_PORT:-3000}}"
FAIL=0

check() {
  local name="$1" url="$2"
  if curl -fsS --max-time 10 "$url" >/dev/null; then
    echo "OK  $name  $url"
  else
    echo "FAIL $name  $url"
    FAIL=1
  fi
}

check "litellm-readiness" "${GATEWAY}/health/readiness"
check "litellm-live" "${GATEWAY}/health/liveliness" || true
if curl -fsS --max-time 5 "${CHAT}/health" >/dev/null 2>&1 || curl -fsS --max-time 5 "${CHAT}" >/dev/null 2>&1; then
  echo "OK  open-webui  ${CHAT}"
else
  echo "SKIP/FAIL open-webui  ${CHAT}  (not required for gateway-only local runs)"
fi

if [[ -n "${LITELLM_MASTER_KEY:-}" ]]; then
  models="$(curl -fsS --max-time 15 -H "Authorization: Bearer ${LITELLM_MASTER_KEY}" "${GATEWAY}/v1/models" || true)"
  if echo "$models" | grep -q "qwen3.8-flash" && echo "$models" | grep -q "mimo-v2.5-pro"; then
    echo "OK  models include qwen3.8-flash and mimo-v2.5-pro"
  else
    echo "FAIL models listing"
    FAIL=1
  fi
fi

exit "$FAIL"
