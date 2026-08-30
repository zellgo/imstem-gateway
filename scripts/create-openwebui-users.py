#!/usr/bin/env python3
"""Create Open WebUI users from secret/outbox/roster.csv.

Open WebUI signup is disabled. This script logs in as admin and calls /api/v1/auths/add.

  OPENWEBUI_URL=https://chat.imstem.org \\
  OPENWEBUI_ADMIN_EMAIL=... \\
  OPENWEBUI_ADMIN_PASSWORD=... \\
  python3 scripts/create-openwebui-users.py
"""
from __future__ import annotations

import csv
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


def request(url: str, method: str, body: dict | None = None, token: str | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 ImStemGateway/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    load_env(root)
    base = (os.environ.get("OPENWEBUI_URL") or os.environ.get("PUBLIC_CHAT_URL") or "https://chat.imstem.org").rstrip("/")
    email = os.environ.get("OPENWEBUI_ADMIN_EMAIL") or ""
    password = os.environ.get("OPENWEBUI_ADMIN_PASSWORD") or os.environ.get("WEBUI_ADMIN_PASSWORD") or ""
    if not email or not password:
        sys.stderr.write("Set OPENWEBUI_ADMIN_EMAIL and OPENWEBUI_ADMIN_PASSWORD\n")
        return 1
    roster_path = root / "secret" / "outbox" / "roster.csv"
    if not roster_path.exists():
        sys.stderr.write(f"missing {roster_path}; run provision-employees.py first\n")
        return 1

    auth = request(f"{base}/api/v1/auths/signin", "POST", {"email": email, "password": password})
    token = auth.get("token")
    if not token:
        sys.stderr.write(f"admin signin failed: {auth}\n")
        return 1

    with roster_path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    rc = 0
    for row in rows:
        payload = {
            "name": f"{row['name']} ({row['id']})",
            "email": row["openwebui_login"] or row["email"],
            "password": row["openwebui_password"],
            "role": "user",
        }
        if not payload["email"] or not payload["password"]:
            print(f"{row['id']}: skip, missing email/password")
            continue
        result = request(f"{base}/api/v1/auths/add", "POST", payload, token=token)
        if result.get("error"):
            print(f"{row['id']} {payload['email']}: error {result}")
            rc = 1
        else:
            print(f"{row['id']} {payload['email']}: created")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
