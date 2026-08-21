#!/usr/bin/env bash
# Dump Railway Postgres (litellm + openwebui) via SSH. Secrets stay off disk except the dump files.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${ROOT}/backups/${STAMP}"
mkdir -p "$DEST"

echo "Dumping litellm and openwebui on Railway Postgres..."
railway ssh --service Postgres -- bash -lc "pg_dump -U postgres -d litellm -Fc" > "${DEST}/litellm.dump"
railway ssh --service Postgres -- bash -lc "pg_dump -U postgres -d openwebui -Fc" > "${DEST}/openwebui.dump"
cp "${ROOT}/docker-compose.yml" "${ROOT}/litellm/config.yaml" "${ROOT}/.env.example" "${DEST}/"

echo "Wrote ${DEST}"
echo "Retention suggestion: 7 daily / 4 weekly / 3 monthly. Prune backups/ yourself."
