#!/bin/sh
set -eu
PORT="${PORT:-4000}"
export PYTHONPATH="/app:/app/scripts${PYTHONPATH:+:$PYTHONPATH}"
# Re-apply Xiaomi + CNY label patches on the live image (Docker layer cache can skip the build RUN).
python /app/patch-xiaomi-provider.py
python - <<'PY'
from pathlib import Path
n = 0
for base in (Path("/app"),):
    for p in base.rglob("*.js"):
        try:
            t = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "Input: $" not in t:
            continue
        yen = chr(165)
        p.write_text(t.replace("Input: $", "Input: " + yen).replace("Output: $", "Output: " + yen), encoding="utf-8")
        n += 1
        print("cny-label", p)
print("cny-label files", n)
PY
# Refresh Aliyun/MiMo official CNY prices into LiteLLM once a week.
IMSTEM_APPLY_LOCAL=1 python /app/official_prices.py --loop-days 7 &
# One worker: budgets and rate limits are exact without Redis.
# Set LITELLM_NUM_WORKERS>1 only after adding Redis.
exec litellm --config /app/config.yaml --port "$PORT" --num_workers "${LITELLM_NUM_WORKERS:-1}"
