#!/usr/bin/env bash
# Revoke CHAT and AGENT keys for an employee. Takes < 5 minutes.
# Usage: ./scripts/offboard-user.sh MED003
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -f "${ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT}/.env"
  set +a
fi

EMPLOYEE_ID="${1:?employee id required}"
GATEWAY="${PUBLIC_GATEWAY_URL:-http://127.0.0.1:${LITELLM_PORT:-4000}}"
AUTH="Authorization: Bearer ${LITELLM_MASTER_KEY:?LITELLM_MASTER_KEY missing}"

echo "Listing keys for ${EMPLOYEE_ID}..."
curl -fsS -H "$AUTH" "${GATEWAY}/key/list?user_id=${EMPLOYEE_ID}" | python3 -c '
import json,sys,os
emp=os.environ.get("EMPLOYEE_ID","")
data=json.load(sys.stdin)
keys=data.get("keys") or data.get("data") or data
if isinstance(keys, dict):
    keys=keys.get("keys") or [keys]
for k in keys:
    if not isinstance(k, dict):
        continue
    token=k.get("token") or k.get("key")
    alias=k.get("key_alias") or k.get("alias") or ""
    print(f"{alias}\t{token}")
'

echo "Revoking ${EMPLOYEE_ID}-CHAT and ${EMPLOYEE_ID}-AGENT by alias..."
python3 - << PY
import json, os, urllib.request
gateway=os.environ.get("GATEWAY") or "${GATEWAY}"
master="${LITELLM_MASTER_KEY}"
emp="${EMPLOYEE_ID}"
req=urllib.request.Request(
    f"{gateway}/key/list?user_id={emp}",
    headers={"Authorization": f"Bearer {master}"},
)
with urllib.request.urlopen(req) as resp:
    data=json.loads(resp.read().decode())
keys=data.get("keys") or data.get("data") or []
if isinstance(keys, dict):
    keys=keys.get("keys") or []
for k in keys:
    if not isinstance(k, dict):
        continue
    token=k.get("token") or k.get("key")
    alias=str(k.get("key_alias") or "")
    if not token:
        continue
    body=json.dumps({"keys":[token]}).encode()
    r=urllib.request.Request(
        f"{gateway}/key/delete",
        data=body,
        headers={"Authorization": f"Bearer {master}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(r)
        print("revoked", alias or token[:8])
    except Exception as e:
        print("failed", alias, e)
print("Also disable the Open WebUI user", emp, "in Admin → Users.")
print("Record offboarding date in config/employees.yaml.")
PY
