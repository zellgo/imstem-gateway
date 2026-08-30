#!/usr/bin/env python3
"""Allow existing AGENT virtual keys to use coding-agent model aliases."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
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
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    load_env(root)
    gateway = (
        os.environ.get("PUBLIC_GATEWAY_URL")
        or "https://llm.imstem.org"
    ).rstrip("/")
    master = os.environ.get("LITELLM_MASTER_KEY")
    if not master:
        sys.stderr.write("LITELLM_MASTER_KEY missing\n")
        return 1
    models = json.loads((root / "config" / "agent-models.json").read_text())["agent_models"]
    listed = api(gateway, master, "GET", "/key/list?return_full_object=true")
    keys = listed.get("keys") or listed.get("data") or []
    if isinstance(keys, dict):
        keys = keys.get("keys") or []
    updated = 0
    for k in keys:
        if not isinstance(k, dict):
            continue
        alias = str(k.get("key_alias") or "")
        if not alias.endswith("-AGENT"):
            continue
        token = k.get("token") or k.get("key")
        if not token:
            print("skip", alias, "no token in list response")
            continue
        result = api(
            gateway,
            master,
            "POST",
            "/key/update",
            {"key": token, "models": models},
        )
        err = result.get("error") or result.get("detail")
        print(alias, "ok" if not err else err)
        if not err:
            updated += 1
    print(f"updated {updated} AGENT keys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
