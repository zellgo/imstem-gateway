#!/usr/bin/env bash
# Restore custom-format dumps into Railway Postgres.
# Usage: ./scripts/restore.sh backups/20260821T120000Z
set -euo pipefail
SRC="${1:?path to backup directory}"
test -f "${SRC}/litellm.dump"
test -f "${SRC}/openwebui.dump"

echo "This will overwrite litellm and openwebui on Railway Postgres."
echo "Source: ${SRC}"
read -r -p "Type RESTORE to continue: " confirm
[[ "$confirm" == "RESTORE" ]] || { echo "aborted"; exit 1; }

railway ssh --service Postgres -- bash -lc 'dropdb -U postgres --if-exists litellm; createdb -U postgres litellm'
railway ssh --service Postgres -- bash -lc 'dropdb -U postgres --if-exists openwebui; createdb -U postgres openwebui'

# Stream dumps through SSH stdin.
railway ssh --service Postgres -- bash -lc 'pg_restore -U postgres -d litellm --clean --if-exists' < "${SRC}/litellm.dump"
railway ssh --service Postgres -- bash -lc 'pg_restore -U postgres -d openwebui --clean --if-exists' < "${SRC}/openwebui.dump"

echo "Restore finished. Restart LiteLLM and Open WebUI."
