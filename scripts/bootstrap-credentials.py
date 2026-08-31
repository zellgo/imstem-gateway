#!/usr/bin/env python3
"""Create (or skip existing) named LiteLLM credentials for DeepSeek, DashScope, MiMo, OpenRouter.

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


def _secret_key(root: Path, filename: str) -> str:
    path = root / "secret" / filename
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return ""


TOKENPLAN_API_BASE_DEFAULT = (
    "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
)


def _secret_ali_tokenplan(root: Path) -> tuple[str, str]:
    """Parse secret/ali-tokenplan.txt: first line is key, then openai <url>."""
    path = root / "secret" / "ali-tokenplan.txt"
    if not path.is_file():
        return "", TOKENPLAN_API_BASE_DEFAULT
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]
    key = ""
    openai_base = ""
    i = 0
    while i < len(lines):
        if lines[i] and not lines[i].startswith("#"):
            key = lines[i]
            i += 1
            break
        i += 1
    while i < len(lines):
        if lines[i].lower() == "openai" and i + 1 < len(lines):
            openai_base = lines[i + 1]
            break
        i += 1
    return key, openai_base or TOKENPLAN_API_BASE_DEFAULT


def wanted_credentials(root: Path) -> list[dict]:
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "") or _secret_key(root, "openrouter.txt")
    tokenplan_key, tokenplan_base = _secret_ali_tokenplan(root)
    tokenplan_key = os.environ.get("DASHSCOPE_TOKENPLAN_API_KEY", "") or tokenplan_key
    tokenplan_base = os.environ.get("DASHSCOPE_TOKENPLAN_API_BASE", "") or tokenplan_base
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
                "description": "Aliyun Model Studio workspace (Kimi / DeepSeek)",
            },
        },
        {
            "credential_name": "dashscope-tokenplan",
            "credential_values": {
                "api_key": tokenplan_key,
                "api_base": tokenplan_base or TOKENPLAN_API_BASE_DEFAULT,
            },
            "credential_info": {
                "custom_llm_provider": "openai",
                "description": "Aliyun token plan (qwen3.8-flash / qwen3.8-27b / qwen3.8-max)",
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
        {
            "credential_name": "openrouter",
            "credential_values": {
                "api_key": openrouter_key,
                "api_base": os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"),
            },
            "credential_info": {
                "custom_llm_provider": "openrouter",
                "description": "OpenRouter (GLM-5.3 Flash)",
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
    for cred in wanted_credentials(root):
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
