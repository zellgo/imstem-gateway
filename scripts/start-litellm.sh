#!/bin/sh
set -eu
PORT="${PORT:-4000}"
exec litellm --config /app/config.yaml --port "$PORT" --num_workers "${LITELLM_NUM_WORKERS:-2}"
