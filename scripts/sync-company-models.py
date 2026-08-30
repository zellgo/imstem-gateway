#!/usr/bin/env python3
"""Upsert employee-facing models into LiteLLM Postgres so the Admin UI can edit them.

Config.yaml models are read-only in the UI. These rows live in LiteLLM_ProxyModelTable
(database badge) and can be retargeted / repriced without a git deploy.

Safe to re-run. Existing DB rows with the same model_info.id are updated.
Old company-* deployment rows are removed so Open WebUI only lists real model names.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from official_prices import cost_fields, load_prices  # noqa: E402

RETIRE_IDS = [
    "company-fast",
    "company-fast-qwen",
    "company-standard",
    "company-standard-mimo",
    "company-pro",
    "company-pro-qwen",
    "mimo-pro",
    "company-agent",
    "company-agent-qwen",
]


def _prices() -> dict:
    return (load_prices().get("models") or {})


def deployment(
    public_name: str,
    model_id: str,
    backend: str,
    credential: str,
    fallback_description: str,
    extra_params: dict | None = None,
) -> dict:
    rec = _prices().get(public_name) or {}
    cost = cost_fields(rec) if rec else {}
    if rec:
        description = (
            f"{rec.get('purpose') or fallback_description}。"
            f"{rec.get('region') or '华北2（北京）'} 官方原价："
            f"输入 \u00a5{rec['input_cny_per_million']:g}/百万 · "
            f"输出 \u00a5{rec['output_cny_per_million']:g}/百万。"
        )
        cost = {**cost, "currency": "CNY"}
    else:
        description = fallback_description
    return {
        "model_name": public_name,
        "litellm_params": {
            "model": backend,
            "litellm_credential_name": credential,
            **{k: v for k, v in cost.items() if k != "currency"},
            **(extra_params or {}),
        },
        "model_info": {
            "id": model_id,
            "mode": "chat",
            "description": description,
            **cost,
        },
    }


# Public name employees type in Open WebUI / API.
def company_models() -> list[dict]:
    return [
        deployment(
            "qwen3.8-flash",
            "qwen3.8-flash",
            "openai/qwen3.8-flash",
            "dashscope",
            "Qwen3.8 Flash via Aliyun Model Studio workspace (OpenAI-compatible).",
        ),
        deployment(
            "qwen3.8-27b",
            "qwen3.8-27b",
            "openai/qwen3.8-27b",
            "dashscope",
            "Qwen3.8 27B via Aliyun Model Studio workspace.",
        ),
        deployment(
            "qwen3.8-max",
            "qwen3.8-max",
            "openai/qwen3.8-max",
            "dashscope",
            "Qwen3.8 Max via Aliyun Model Studio workspace.",
        ),
        deployment(
            "kimi-k3",
            "kimi-k3",
            "openai/kimi-k3",
            "dashscope",
            "Kimi K3 via Aliyun Model Studio workspace. Codex/Claude aliases map here.",
        ),
        deployment(
            "deepseek-v4-flash-0731",
            "deepseek-v4-flash-0731",
            "openai/deepseek-v4-flash-0731",
            "dashscope",
            "DeepSeek V4 Flash 0731 via Aliyun Model Studio workspace.",
        ),
        deployment(
            "deepseek-v4-pro-0813",
            "deepseek-v4-pro-0813",
            "openai/deepseek-v4-pro-0813",
            "dashscope",
            "DeepSeek V4 Pro 0813 via Aliyun Model Studio workspace.",
        ),
        deployment(
            "mimo-v2.5",
            "mimo-v2.5",
            "xiaomi_mimo/mimo-v2.5",
            "mimo",
            "Xiaomi MiMo V2.5.",
        ),
        deployment(
            "mimo-v2.5-pro",
            "mimo-v2.5-pro",
            "xiaomi_mimo/mimo-v2.5-pro",
            "mimo",
            "Xiaomi MiMo V2.5 Pro.",
        ),
        deployment(
            "glm-5.3-flash",
            "glm-5.3-flash",
            "openrouter/z-ai/glm-5.3-flash",
            "openrouter",
            "Z.ai GLM-5.3 Flash via OpenRouter.",
            extra_params={
                "headers": {
                    "HTTP-Referer": "https://llm.imstem.org",
                    "X-Title": "ImStem Gateway",
                }
            },
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
            "User-Agent": "Mozilla/5.0 ImStemGateway/1.0",
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
    gateway = (
        os.environ.get("PUBLIC_GATEWAY_URL") or "https://llm.imstem.org"
    ).rstrip("/")
    master = os.environ.get("LITELLM_MASTER_KEY")
    if not master:
        sys.stderr.write("LITELLM_MASTER_KEY missing\n")
        return 1

    existing = list_db_ids(gateway, master)
    rc = 0
    MODELS = company_models()
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
            print(f"{spec['model_name']:24} {mid:24} {action}")

    keep = {spec["model_info"]["id"] for spec in MODELS}
    for mid in RETIRE_IDS:
        if mid in keep or mid not in existing:
            continue
        result = api(gateway, master, "POST", "/model/delete", {"id": mid})
        if result.get("error"):
            print(f"retire {mid}: error {result.get('error')} {result.get('body')}")
        else:
            print(f"retired {mid}")
    print("Done. Employees pick qwen3.8-* / kimi-k3 / deepseek-v4-* / mimo-v2.5* / glm-5.3-flash.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
