#!/usr/bin/env python3
"""Upsert employee-facing models into LiteLLM Postgres so the Admin UI can edit them.

Config.yaml models are read-only in the UI. These rows live in LiteLLM_ProxyModelTable
(database badge) and can be retargeted / repriced without a git deploy.

Safe to re-run. Existing DB rows with the same model_info.id are updated.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

COST = {
    "deepseek": {
        "input_cost_per_token": 0.00000022,
        "output_cost_per_token": 0.00000066,
        "cache_read_input_token_cost": 0.000000007,
    },
    "qwen_turbo": {
        "input_cost_per_token": 0.00000004167,
        "output_cost_per_token": 0.00000008333,
        "cache_read_input_token_cost": 0.000000004167,
    },
    "qwen_plus": {
        "input_cost_per_token": 0.0000001111,
        "output_cost_per_token": 0.0000002778,
        "cache_read_input_token_cost": 0.00000001111,
    },
    "qwen_max": {
        "input_cost_per_token": 0.0000003333,
        "output_cost_per_token": 0.000001333,
        "cache_read_input_token_cost": 0.00000003333,
    },
    "mimo": {
        "input_cost_per_token": 0.00000014,
        "output_cost_per_token": 0.00000028,
        "cache_read_input_token_cost": 0.0000000028,
    },
    "mimo_pro": {
        "input_cost_per_token": 0.000000435,
        "output_cost_per_token": 0.00000087,
        "cache_read_input_token_cost": 0.0000000036,
    },
}


def deployment(
    public_name: str,
    model_id: str,
    backend: str,
    credential: str,
    cost_key: str,
    description: str,
) -> dict:
    cost = COST[cost_key]
    return {
        "model_name": public_name,
        "litellm_params": {
            "model": backend,
            "litellm_credential_name": credential,
            **cost,
        },
        "model_info": {
            "id": model_id,
            "mode": "chat",
            "description": description,
            **cost,
        },
    }


# Public name employees type → one or more backend deployments.
# Edit the PRIMARY row in the UI to change which LLM the alias uses.
# Extra rows with the same public name are load-balanced / failover targets.
MODELS = [
    deployment(
        "company-fast",
        "company-fast",
        "deepseek/deepseek-chat",
        "deepseek",
        "deepseek",
        "company-fast PRIMARY → DeepSeek Chat. Change litellm model + credential to retarget.",
    ),
    deployment(
        "company-fast",
        "company-fast-qwen",
        "dashscope/qwen-turbo",
        "dashscope",
        "qwen_turbo",
        "company-fast extra deployment → Qwen Turbo (load-balance / failover).",
    ),
    deployment(
        "company-standard",
        "company-standard",
        "dashscope/qwen-plus",
        "dashscope",
        "qwen_plus",
        "company-standard PRIMARY → Qwen Plus. Change litellm model + credential to retarget.",
    ),
    deployment(
        "company-standard",
        "company-standard-mimo",
        "xiaomi_mimo/mimo-v2.5",
        "mimo",
        "mimo",
        "company-standard extra deployment → MiMo V2.5.",
    ),
    deployment(
        "company-pro",
        "company-pro",
        "xiaomi_mimo/mimo-v2.5-pro",
        "mimo",
        "mimo_pro",
        "company-pro PRIMARY → MiMo V2.5 Pro. Change litellm model + credential to retarget.",
    ),
    deployment(
        "company-pro",
        "company-pro-qwen",
        "dashscope/qwen-max",
        "dashscope",
        "qwen_max",
        "company-pro extra deployment → Qwen Max.",
    ),
    deployment(
        "mimo-pro",
        "mimo-pro",
        "xiaomi_mimo/mimo-v2.5-pro",
        "mimo",
        "mimo_pro",
        "mimo-pro PRIMARY → MiMo V2.5 Pro (same backend as company-pro by default).",
    ),
    deployment(
        "company-agent",
        "company-agent",
        "deepseek/deepseek-chat",
        "deepseek",
        "deepseek",
        "company-agent PRIMARY → DeepSeek Chat. Codex/Claude aliases follow this via model_group_alias.",
    ),
    deployment(
        "company-agent",
        "company-agent-qwen",
        "dashscope/qwen-plus",
        "dashscope",
        "qwen_plus",
        "company-agent extra deployment → Qwen Plus.",
    ),
]


def load_env(root: Path) -> None:
    env = root / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v)


def api(gateway: str, master: str, method: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"{gateway}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {master}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        try:
            parsed = json.loads(err)
        except json.JSONDecodeError:
            parsed = {"raw": err}
        return {"error": e.code, "body": parsed}


def list_db_ids(gateway: str, master: str) -> dict[str, dict]:
    result = api(gateway, master, "GET", "/v2/model/info")
    rows = result.get("data") or result.get("models") or []
    found: dict[str, dict] = {}
    for row in rows:
        info = row.get("model_info") or {}
        if info.get("db_model") is False:
            continue
        mid = info.get("id")
        if mid:
            found[mid] = row
    return found


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    load_env(root)
    gateway = os.environ.get("PUBLIC_GATEWAY_URL") or f"http://127.0.0.1:{os.environ.get('LITELLM_PORT', '4000')}"
    master = os.environ.get("LITELLM_MASTER_KEY")
    if not master:
        sys.stderr.write("LITELLM_MASTER_KEY missing\n")
        return 1

    existing = list_db_ids(gateway, master)
    rc = 0
    for spec in MODELS:
        mid = spec["model_info"]["id"]
        if mid in existing:
            payload = {
                "id": mid,
                "model_name": spec["model_name"],
                "litellm_params": spec["litellm_params"],
                "model_info": spec["model_info"],
            }
            result = api(gateway, master, "POST", "/model/update", payload)
            action = "updated"
        else:
            result = api(gateway, master, "POST", "/model/new", spec)
            action = "created"
        if result.get("error"):
            print(f"{mid}: error {result.get('error')} {result.get('body')}")
            rc = 1
        else:
            db = None
            if isinstance(result, dict):
                db = (result.get("model_info") or {}).get("db_model")
                if db is None and isinstance(result.get("data"), dict):
                    db = (result["data"].get("model_info") or {}).get("db_model")
            print(f"{spec['model_name']:16} {mid:22} {action} db_model={db}")
    print("Done. In the UI, database-badge rows are editable. Config-badge rows stay locked until yaml is deployed without them.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
