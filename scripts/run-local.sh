#!/usr/bin/env bash
# Run LiteLLM locally against Railway Postgres (SSH tunnel required).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
export DATABASE_URL="${LITELLM_DATABASE_URL:?LITELLM_DATABASE_URL missing}"
if ! ss -ltn | grep -q ":${PG_TUNNEL_PORT:-15432} "; then
  echo "Start the DB tunnel first:  ./scripts/db-tunnel.sh"
  exit 1
fi
if [[ -x .venv/bin/litellm ]]; then
  exec .venv/bin/litellm --config litellm/config.yaml --port "${LITELLM_PORT:-4000}"
fi
exec litellm --config litellm/config.yaml --port "${LITELLM_PORT:-4000}"
