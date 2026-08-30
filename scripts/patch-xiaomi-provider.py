#!/usr/bin/env python3
"""Make Xiaomi (and DeepSeek URL) editable in the LiteLLM Admin UI.

1. provider_create_fields.json — credential form schema served at
   GET /public/providers/fields
2. Compiled dashboard JS — the Add/Edit Credential dropdown is hardcoded
   from the Providers enum, which upstream omits Xiaomi.
"""
from __future__ import annotations

import json
from pathlib import Path

XIAOMI_ENTRY = {
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
            "tooltip": "Token Plan Singapore or PAYG https://api.xiaomimimo.com/v1",
            "required": True,
            "field_type": "text",
            "options": None,
            "default_value": "https://token-plan-sgp.xiaomimimo.com/v1",
        },
    ],
    "default_model_placeholder": "mimo-v2.5-pro",
}

DEEPSEEK_API_BASE = {
    "key": "api_base",
    "label": "API Base",
    "placeholder": "https://api.deepseek.com",
    "tooltip": "DeepSeek API endpoint. Default https://api.deepseek.com",
    "required": False,
    "field_type": "text",
    "options": None,
    "default_value": "https://api.deepseek.com",
}

JS_ENUM_OLD = 't.Deepseek="Deepseek",'
JS_ENUM_NEW = 't.Deepseek="Deepseek",t.Xiaomi="Xiaomi",'
JS_MAP_OLD = 'Deepseek:"deepseek",'
JS_MAP_NEW = 'Deepseek:"deepseek",Xiaomi:"xiaomi_mimo",'


def litellm_root() -> Path:
    import litellm

    return Path(litellm.__file__).resolve().parent


def fields_path() -> Path:
    candidates = [
        litellm_root() / "proxy" / "public_endpoints" / "provider_create_fields.json",
    ]
    try:
        import litellm.proxy.public_endpoints as pkg

        candidates.insert(0, Path(pkg.__file__).resolve().parent / "provider_create_fields.json")
    except Exception:
        pass
    for path in candidates:
        if path.is_file():
            return path
    raise SystemExit("provider_create_fields.json not found")


def patch_fields(path: Path) -> None:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise SystemExit(f"unexpected schema in {path}")
    saw_xiaomi = False
    for i, row in enumerate(data):
        slug = row.get("litellm_provider")
        if slug == "xiaomi_mimo" or row.get("provider_display_name") == "Xiaomi":
            data[i] = XIAOMI_ENTRY
            saw_xiaomi = True
        if slug == "deepseek":
            keys = {f.get("key") for f in row.get("credential_fields") or []}
            if "api_base" not in keys:
                row.setdefault("credential_fields", []).append(DEEPSEEK_API_BASE)
    if not saw_xiaomi:
        data.append(XIAOMI_ENTRY)
        data.sort(key=lambda r: str(r.get("provider_display_name") or r.get("provider") or "").lower())
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"patched fields {path}")


UI_SCRIPT = '<script src="/imstem-ui.js?v=5" defer></script>'


def patch_ui_html(root: Path) -> int:
    n = 0
    dirs = [
        root / "proxy" / "_experimental" / "out",
        root / "proxy" / "public",
        root / "proxy" / "ui",
        root / "proxy" / "_experimental" / "out" / "dashboard",
    ]
    seen: set[Path] = set()
    files: list[Path] = []
    for d in dirs:
        if d.is_dir():
            files.extend(d.rglob("*.html"))
    files.extend(root.rglob("index.html"))
    for html in files:
        html = html.resolve()
        if html in seen:
            continue
        seen.add(html)
        try:
            text = html.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if UI_SCRIPT in text:
            continue
        if "</body>" in text:
            html.write_text(text.replace("</body>", UI_SCRIPT + "</body>", 1), encoding="utf-8")
            n += 1
        elif "</html>" in text:
            html.write_text(text.replace("</html>", UI_SCRIPT + "</html>", 1), encoding="utf-8")
            n += 1
    if n:
        print(f"patched {n} LiteLLM UI html files with CNY script")
    return n


def patch_js(root: Path) -> int:
    n = 0
    for js in root.rglob("*.js"):
        try:
            text = js.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        orig = text
        if JS_ENUM_OLD in text and "t.Xiaomi=" not in text:
            text = text.replace(JS_ENUM_OLD, JS_ENUM_NEW)
        if JS_MAP_OLD in text and 'Xiaomi:"xiaomi_mimo"' not in text:
            text = text.replace(JS_MAP_OLD, JS_MAP_NEW)
        # Models page renders ["Input: $", cost, "/1M tokens"] — $ is its own text node.
        if "Input: $" in text:
            yen = chr(165)  # ASCII &#165;
            text = text.replace("Input: $", "Input: " + yen).replace("Output: $", "Output: " + yen)
        if "Max Budget (USD)" in text:
            text = text.replace("Max Budget (USD)", "Max Budget (CNY)")
        if "Current Cycle Spend (USD)" in text:
            text = text.replace("Current Cycle Spend (USD)", "Current Cycle Spend (CNY)")
        if "maximum budget in USD" in text:
            text = text.replace("maximum budget in USD", "maximum budget in CNY")
        if "Cost per PTU / Hour (USD)" in text:
            text = text.replace("Cost per PTU / Hour (USD)", "Cost per PTU / Hour (CNY)")
        if text != orig:
            js.write_text(text, encoding="utf-8")
            print(f"patched js {js}")
            n += 1
    return n


def main() -> int:
    patch_fields(fields_path())
    n = patch_js(litellm_root())
    print(f"js files patched: {n}")
    patch_ui_html(litellm_root())
    if n == 0:
        print("warning: no dashboard JS matched; Xiaomi may still be missing from the dropdown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
