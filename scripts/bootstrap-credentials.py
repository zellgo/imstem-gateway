#!/usr/bin/env python3
"""Create (or skip existing) named LiteLLM credentials for DeepSeek, DashScope, MiMo.

Safe to re-run. Existing credentials are left alone unless --update is passed.
Keys are stored encrypted in LiteLLM_CredentialsTable (Railway Postgres).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


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
        return {"error": e.code, "body": err}


def wanted_credentials() -> list[dict]:
    return [
        {
            "credential_name": "deepseek",
            "credential_values": {
                "api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
                "api_base": os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
            },
            "credential_info": {
                # LiteLLM Deepseek form is api_key only (no URL). custom_openai
                # exposes api_key + api_base. Models still use deepseek/ prefix.
                "custom_llm_provider": "custom_openai",
                "description": "DeepSeek official API",
            },
        },
        {
            "credential_name": "dashscope",
            "credential_values": {
                "api_key": os.environ.get("DASHSCOPE_API_KEY", ""),
                "api_base": os.environ.get(
                    "DASHSCOPE_API_BASE",
                    "https://ws-wl95ahuehne7eddv.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
                ),
            },
            "credential_info": {
                # Workspace is OpenAI-compatible, not the public DashScope host.
                "custom_llm_provider": "openai",
                "description": "Aliyun Model Studio workspace (Qwen / Kimi / DeepSeek)",
            },
        },
        {
            "credential_name": "mimo",
            "credential_values": {
                "api_key": os.environ.get("MIMO_API_KEY", ""),
                "api_base": os.environ.get(
                    "MIMO_API_BASE",
                    "https://token-plan-sgp.xiaomimimo.com/v1",
                ),
            },
            "credential_info": {
                # Enum key in the Admin UI dropdown (not the litellm slug).
                "custom_llm_provider": "Xiaomi",
                "description": "Xiaomi MiMo Token Plan / PAYG",
            },
        },
    ]


def existing_names(gateway: str, master: str) -> set[str]:
    result = api(gateway, master, "GET", "/credentials")
    if result.get("error"):
        sys.stderr.write(f"GET /credentials failed: {result}\n")
        return set()
    creds = result.get("credentials") or []
    names: set[str] = set()
    for item in creds:
        name = item.get("credential_name") if isinstance(item, dict) else None
        if name:
            names.add(name)
    return names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update",
        action="store_true",
        help="Overwrite existing credentials from env (default: create only)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    load_env(root)
    gateway = (
        os.environ.get("PUBLIC_GATEWAY_URL") or "https://llm.imstem.org"
    ).rstrip("/")
    master = os.environ.get("LITELLM_MASTER_KEY")
    if not master:
        sys.stderr.write("LITELLM_MASTER_KEY missing\n")
        return 1

    present = existing_names(gateway, master)
    rc = 0
    for cred in wanted_credentials():
        name = cred["credential_name"]
        key = cred["credential_values"].get("api_key") or ""
        if not key or key in {"replace-me", "changeme"}:
            print(f"{name}: warning — env key is empty/placeholder; creating so you can paste a real key in the UI")
        if name in present and not args.update:
            print(f"{name}: exists (UI-editable). Pass --update to overwrite from env.")
            continue
        if name in present and args.update:
            result = api(gateway, master, "PATCH", f"/credentials/{name}", cred)
            status = "updated" if not result.get("error") else f"error {result}"
        else:
            result = api(gateway, master, "POST", "/credentials", cred)
            status = "created" if not result.get("error") else f"error {result}"
            if result.get("error"):
                rc = 1
        print(f"{name}: {status}")
    print("Done. Edit keys in LiteLLM UI → Models + Endpoints → LLM Credentials.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
