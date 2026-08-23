#!/usr/bin/env python3
"""Add Xiaomi to LiteLLM's Admin UI provider list with API key + URL fields.

Upstream ships xiaomi_mimo routing but omits it from provider_create_fields.json,
so the credential form has nothing to render. Run at image build time.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ENTRY = {
    "provider": "Xiaomi",
    "provider_display_name": "Xiaomi",
    "litellm_provider": "xiaomi_mimo",
    "credential_fields": [
        {
            "key": "api_key",
            "label": "Xiaomi API Key",
            "placeholder": None,
            "tooltip": "Token Plan (tp-…) or pay-as-you-go key from platform.xiaomimimo.com",
            "required": True,
            "field_type": "password",
            "options": None,
            "default_value": None,
        },
        {
            "key": "api_base",
            "label": "API Base",
            "placeholder": "https://token-plan-sgp.xiaomimimo.com/v1",
            "tooltip": "Token Plan: https://token-plan-sgp.xiaomimimo.com/v1  Pay-as-you-go: https://api.xiaomimimo.com/v1",
            "required": True,
            "field_type": "text",
            "options": None,
            "default_value": "https://token-plan-sgp.xiaomimimo.com/v1",
        },
    ],
    "default_model_placeholder": "mimo-v2.5-pro",
}


def locate() -> Path:
    candidates: list[Path] = []
    try:
        import litellm.proxy.public_endpoints as pkg

        candidates.append(Path(pkg.__file__).resolve().parent / "provider_create_fields.json")
    except Exception:
        pass
    try:
        import litellm

        root = Path(litellm.__file__).resolve().parent
        candidates.append(root / "proxy" / "public_endpoints" / "provider_create_fields.json")
    except Exception:
        pass
    for path in candidates:
        if path.is_file():
            return path
    raise SystemExit("provider_create_fields.json not found: " + ", ".join(str(p) for p in candidates))


def main() -> int:
    path = locate()
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise SystemExit(f"unexpected schema in {path}")
    for i, row in enumerate(data):
        if row.get("litellm_provider") == "xiaomi_mimo" or row.get("provider_display_name") == "Xiaomi":
            data[i] = ENTRY
            path.write_text(json.dumps(data, indent=2) + "\n")
            print(f"updated Xiaomi in {path}")
            return 0
    data.append(ENTRY)
    data.sort(key=lambda r: str(r.get("provider_display_name") or r.get("provider") or "").lower())
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"inserted Xiaomi into {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
