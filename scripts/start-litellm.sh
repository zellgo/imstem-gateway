#!/bin/sh
set -eu
PORT="${PORT:-4000}"
export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"
# One worker: budgets and rate limits are exact without Redis.
# Set LITELLM_NUM_WORKERS>1 only after adding Redis.
exec litellm --config /app/config.yaml --port "$PORT" --num_workers "${LITELLM_NUM_WORKERS:-1}"
