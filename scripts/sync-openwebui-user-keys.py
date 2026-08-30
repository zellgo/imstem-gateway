#!/usr/bin/env python3
"""Attach each employee's MED00X-CHAT key to their Open WebUI account.

Open WebUI keeps a shared env key (OPENWEBUI-CHAT) unless we:
  1. Enable Direct Connections
  2. Store each user's LiteLLM CHAT key in user.settings.directConnections
  3. Clear the global OpenAI connection so chat cannot fall back to the shared key

Usage:
  python3 scripts/sync-openwebui-user-keys.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 ImStemGateway/1.0"
LITELLM_PUBLIC_V1 = "https://llm.imstem.org/v1"
CHAT_MODELS = [
    "qwen3.8-flash",
    "qwen3.8-27b",
    "qwen3.8-max",
    "kimi-k3",
    "deepseek-v4-flash-0731",
    "deepseek-v4-pro-0813",
    "mimo-v2.5",
    "mimo-v2.5-pro",
    "glm-5.3-flash",
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


def http(url: str, method: str = "GET", body: dict | None = None, token: str | None = None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json", "User-Agent": UA}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:800]


def ow(base: str, path: str, method: str = "GET", body: dict | None = None, token: str | None = None):
    return http(base.rstrip("/") + path, method, body, token)


def litellm_api(gw: str, master: str, method: str, path: str, body: dict | None = None) -> dict:
    code, data = http(
        gw.rstrip("/") + path,
        method,
        body,
        token=master,
    )
    if isinstance(data, dict) and data.get("error"):
        return data
    if code >= 400:
        return {"error": code, "body": data}
    return data if isinstance(data, dict) else {"data": data}


def ensure_admin_chat_key(gw: str, master: str) -> str:
    listed = litellm_api(gw, master, "GET", "/user/info?user_id=ADMIN001")
    keys = listed.get("keys") or listed.get("data") or []
    if isinstance(keys, dict):
        keys = keys.get("keys") or []
    for item in keys:
        if not isinstance(item, dict):
            continue
        if item.get("key_alias") != "ADMIN001-CHAT":
            continue
        token = item.get("token") or item.get("key")
        if token:
            litellm_api(gw, master, "POST", "/key/update", {"key": token, "models": list(CHAT_MODELS)})
            plaintext = item.get("key") or ""
            if plaintext.startswith("sk-"):
                return plaintext
        break
    created = litellm_api(
        gw,
        master,
        "POST",
        "/key/generate",
        {
            "user_id": "ADMIN001",
            "key_alias": "ADMIN001-CHAT",
            "models": list(CHAT_MODELS),
            "max_budget": 50,
            "budget_duration": "30d",
            "metadata": {"kind": "chat", "employee_id": "ADMIN001", "department": "Admin"},
        },
    )
    key = created.get("key") or ""
    if not key:
        raise SystemExit(f"could not issue ADMIN001-CHAT: {created}")
    return key


def connection_settings(api_key: str) -> dict:
    # Open WebUI login only hydrates settings.ui into the browser store.
    # Keys must live under ui.directConnections or the picker stays empty.
    blob = {
        "OPENAI_API_BASE_URLS": [LITELLM_PUBLIC_V1],
        "OPENAI_API_KEYS": [api_key],
        "OPENAI_API_CONFIGS": {
            "0": {
                "enable": True,
                "tags": [],
                "prefix_id": "",
                "model_ids": list(CHAT_MODELS),
                "connection_type": "external",
                "auth_type": "bearer",
            }
        },
    }
    return {"ui": {"directConnections": blob}, "directConnections": blob}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    load_env(root)
    chat = (os.environ.get("OPENWEBUI_URL") or os.environ.get("PUBLIC_CHAT_URL") or "https://chat.imstem.org").rstrip(
        "/"
    )
    gw = (os.environ.get("PUBLIC_GATEWAY_URL") or "https://llm.imstem.org").rstrip("/")
    master = os.environ.get("LITELLM_MASTER_KEY") or ""
    admin_email = os.environ.get("OPENWEBUI_ADMIN_EMAIL") or "admin@imstem.local"
    admin_password = (
        os.environ.get("OPENWEBUI_ADMIN_PASSWORD")
        or os.environ.get("WEBUI_ADMIN_PASSWORD")
        or ""
    )
    if not admin_password:
        admin_txt = root / "secret" / "admin.txt"
        if admin_txt.exists():
            admin_password = admin_txt.read_text().splitlines()[1].strip()
    if not master or not admin_password:
        sys.stderr.write("Need LITELLM_MASTER_KEY and Open WebUI admin password\n")
        return 1

    roster_path = root / "secret" / "outbox" / "roster.csv"
    if not roster_path.exists():
        sys.stderr.write(f"missing {roster_path}\n")
        return 1
    rows = list(csv.DictReader(roster_path.open(encoding="utf-8")))

    code, auth = ow(chat, "/api/v1/auths/signin", "POST", {"email": admin_email, "password": admin_password})
    token = auth.get("token") if isinstance(auth, dict) else None
    if not token:
        sys.stderr.write(f"admin signin failed: {code} {auth}\n")
        return 1

    code, conn = ow(
        chat,
        "/api/v1/configs/connections",
        "POST",
        {"ENABLE_DIRECT_CONNECTIONS": True, "ENABLE_BASE_MODELS_CACHE": False},
        token=token,
    )
    print("direct connections", code, conn)

    # Stop using the shared OPENWEBUI-CHAT env key for inference.
    code, openai_cfg = ow(
        chat,
        "/openai/config/update",
        "POST",
        {
            "ENABLE_OPENAI_API": True,
            "OPENAI_API_BASE_URLS": [],
            "OPENAI_API_KEYS": [],
            "OPENAI_API_CONFIGS": {},
        },
        token=token,
    )
    print("cleared global openai connection", code, openai_cfg if code != 200 else "ok")

    admin_chat_key = ensure_admin_chat_key(gw, master)
    accounts = [
        {"email": admin_email, "password": admin_password, "id": "ADMIN001", "chat_key": admin_chat_key}
    ]
    for row in rows:
        accounts.append(
            {
                "email": row["openwebui_login"],
                "password": row["openwebui_password"],
                "id": row["id"],
                "chat_key": row["chat_key"],
            }
        )

    rc = 0
    for acc in accounts:
        code, sess = ow(chat, "/api/v1/auths/signin", "POST", {"email": acc["email"], "password": acc["password"]})
        utoken = sess.get("token") if isinstance(sess, dict) else None
        if not utoken:
            print(f"{acc['id']} signin failed {code} {sess}")
            rc = 1
            continue
        code, saved = ow(
            chat,
            "/api/v1/users/user/settings/update",
            "POST",
            connection_settings(acc["chat_key"]),
            token=utoken,
        )
        dc = {}
        if isinstance(saved, dict):
            dc = (saved.get("ui") or {}).get("directConnections") or saved.get("directConnections") or {}
        keys = dc.get("OPENAI_API_KEYS") or []
        ok = code == 200 and any(k == acc["chat_key"] for k in keys)
        print(f"{acc['id']} {acc['email']} settings", "ok" if ok else f"{code} {saved}")
        if not ok:
            rc = 1
            continue
        code, models = ow(chat, "/api/models", token=utoken)
        ids = []
        if isinstance(models, dict):
            ids = [m.get("id") for m in models.get("data") or [] if isinstance(m, dict)]
        print(f"  models {code} n={len(ids)} sample={ids[:8]}")

    # Persist admin chat key next to the roster for the operator.
    admin_line = root / "secret" / "outbox" / "ADMIN001.md"
    admin_line.write_text(
        f"# ADMIN001 Open WebUI\n\nemail: {admin_email}\nCHAT key: {admin_chat_key}\n"
        f"LiteLLM base: {LITELLM_PUBLIC_V1}\n",
        encoding="utf-8",
    )
    print(f"wrote {admin_line}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
