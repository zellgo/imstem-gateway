#!/usr/bin/env python3
"""Create LiteLLM teams from config/employees.yaml. Safe to re-run."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("Install pyyaml: pip install pyyaml\n")
    sys.exit(1)


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
    cfg = yaml.safe_load((root / "config" / "employees.yaml").read_text())
    models = list({*cfg.get("chat_models", []), *cfg.get("agent_models", [])})
    for name, dept in cfg["departments"].items():
        payload = {
            "team_alias": dept.get("team_alias") or name,
            "models": models,
            "max_budget": float(dept.get("default_chat_budget_usd", 0))
            + float(dept.get("default_agent_budget_usd", 0)) * 10,
            "budget_duration": cfg.get("budget_duration", "30d"),
            "metadata": {"department": name},
        }
        result = api(gateway, master, "POST", "/team/new", payload)
        status = "error" if result.get("error") else "ok"
        print(f"team {name}: {status}")
    print("Done. Create employees with scripts/create-user.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
