#!/usr/bin/env bash
# Open an SSH tunnel from localhost:15432 to Railway Postgres:5432.
# Postgres stays private. Do not enable a public TCP proxy.
set -euo pipefail
PORT="${PG_TUNNEL_PORT:-15432}"
HOST_ALIAS="${RAILWAY_PG_SSH_HOST:-railway-postgres}"

if ss -ltn 2>/dev/null | grep -q ":${PORT} " || netstat -ltn 2>/dev/null | grep -q ":${PORT} "; then
  echo "Tunnel already listening on 127.0.0.1:${PORT}"
  exit 0
fi

if ! grep -q "Host ${HOST_ALIAS}" "${HOME}/.ssh/config" 2>/dev/null; then
  echo "Writing Railway SSH config for Postgres..."
  railway ssh config --service Postgres --alias "${HOST_ALIAS}"
fi

echo "Starting SSH tunnel 127.0.0.1:${PORT} -> ${HOST_ALIAS}:5432"
exec ssh -N -L "127.0.0.1:${PORT}:127.0.0.1:5432" \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  "${HOST_ALIAS}"
