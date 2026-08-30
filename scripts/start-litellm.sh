#!/bin/sh
set -eu
PORT="${PORT:-4000}"
export PYTHONPATH="/app:/app/scripts${PYTHONPATH:+:$PYTHONPATH}"
# Re-apply Xiaomi + CNY label patches on the live image (Docker layer cache can skip the build RUN).
python /app/patch-xiaomi-provider.py
# Refresh Aliyun/MiMo official CNY prices into LiteLLM once a week.
IMSTEM_APPLY_LOCAL=1 python /app/official_prices.py --loop-days 7 &
# One worker: budgets and rate limits are exact without Redis.
# Set LITELLM_NUM_WORKERS>1 only after adding Redis.
exec litellm --config /app/config.yaml --port "$PORT" --num_workers "${LITELLM_NUM_WORKERS:-1}"
