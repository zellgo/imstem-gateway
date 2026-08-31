#!/usr/bin/env python3
"""Update model allowlists on every LiteLLM virtual key without rotating keys.

Usage:
  python3 scripts/grant-models.py glm-5.3-flash          # append
  python3 scripts/grant-models.py --replace               # set exact company list
"""
from __future__ import annotations

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
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:800]}


def list_keys(gateway: str, master: str) -> list[dict]:
    found: list[dict] = []
    page = 1
    while page <= 30:
        result = api(
            gateway,
            master,
            "GET",
            f"/key/list?return_full_object=true&page={page}&size=100",
        )
        keys = result.get("keys") or result.get("data") or []
        if isinstance(keys, dict):
            keys = keys.get("keys") or []
        if not keys:
            break
        found.extend([k for k in keys if isinstance(k, dict)])
        if page >= int(result.get("total_pages") or 1):
            break
        page += 1
    return found


ALLOWED = [
    "qwen3.8-flash",
    "qwen3.8-27b",
    "qwen3.8-max",
    "kimi-k3",
    "deepseek-v4-flash-0731",
    "deepseek-v4-pro-0813",
    "mimo-v2.5",
    "mimo-v2.5-pro",
    "glm-5.3-flash",
    "glm-4.7",
]


def main() -> int:
    replace = "--replace" in sys.argv
    extra = [a for a in sys.argv[1:] if not a.startswith("-")]
    root = Path(__file__).resolve().parents[1]
    load_env(root)
    gateway = (os.environ.get("PUBLIC_GATEWAY_URL") or "https://llm.imstem.org").rstrip("/")
    master = os.environ.get("LITELLM_MASTER_KEY")
    if not master:
        sys.stderr.write("LITELLM_MASTER_KEY missing\n")
        return 1

    keys = list_keys(gateway, master)
    updated = skipped = failed = 0
    for item in keys:
        alias = item.get("key_alias") or item.get("token") or "?"
        token = item.get("token") or item.get("key")
        models = list(item.get("models") or [])
        if not token:
            print(f"{alias}: skip (no token)")
            skipped += 1
            continue
        if replace:
            wanted = list(ALLOWED)
            extra_now = [m for m in models if m not in wanted]
            if models == wanted:
                print(f"{alias}: already {len(wanted)}")
                skipped += 1
                continue
            result = api(
                gateway,
                master,
                "POST",
                "/key/update",
                {"key": token, "models": wanted},
            )
            if result.get("error"):
                print(f"{alias}: error {result}")
                failed += 1
            else:
                print(f"{alias}: set {len(wanted)} (removed {extra_now})")
                updated += 1
            continue
        if not extra:
            extra = ["glm-5.3-flash"]
        if models in ([],) or any(m in {"*", "all"} for m in models):
            print(f"{alias}: skip (unrestricted)")
            skipped += 1
            continue
        missing = [m for m in extra if m not in models]
        if not missing:
            print(f"{alias}: already has {extra}")
            skipped += 1
            continue
        result = api(
            gateway,
            master,
            "POST",
            "/key/update",
            {"key": token, "models": models + missing},
        )
        if result.get("error"):
            print(f"{alias}: error {result}")
            failed += 1
        else:
            print(f"{alias}: added {missing}")
            updated += 1
    print(f"updated {updated}, skipped {skipped}, failed {failed}, keys {len(keys)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
