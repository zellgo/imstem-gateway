#!/usr/bin/env python3
"""Fetch official China CNY token prices and map them onto LiteLLM models.

Sources (not estimates):
  Aliyun Model Studio 华北2（北京） model pages
  Xiaomi MiMo 国内按量价
  OpenRouter listed USD prices converted at CNY/USD 6.72

LiteLLM stores per-token numbers. Those numbers are CNY / token so Usage spend
matches Aliyun/MiMo invoices in yuan. The admin UI dollar sign is relabelled.

DeepSeek dated snapshots bill idle/busy. Accounting uses the official 忙时
(Beijing weekdays 09:00–12:00, 14:00–18:00) band; the public table shows both.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

UA = "Mozilla/5.0 ImStemGateway/1.0"
REGION = "华北2（北京）"
SYMBOL = "\u00a5"  # yen sign, ASCII source; HTML uses &#165;
WEEK_SECONDS = 7 * 24 * 3600

def _repo_root() -> Path:
    here = Path(__file__).resolve().parent
    for cand in (here, here.parent, Path("/app")):
        if (cand / "config" / "model-prices.json").is_file() or (cand / "landing").is_dir():
            return cand
    return here.parent


ROOT = _repo_root()
DEFAULT_JSON = ROOT / "config" / "model-prices.json"
RUNTIME_JSON = Path(os.environ.get("IMSTEM_PRICES_PATH") or "/tmp/imstem-model-prices.json")

ALIYUN = [
    {
        "id": "qwen3.8-flash",
        "url": "https://help.aliyun.com/zh/model-studio/qwen3-8-flash",
        "snapshot": None,
        "purpose": "快、便宜，草稿和翻译",
    },
    {
        "id": "qwen3.8-27b",
        "url": "https://help.aliyun.com/zh/model-studio/qwen3-8-27b",
        "snapshot": None,
        "purpose": "日常写作与修改",
    },
    {
        "id": "qwen3.8-max",
        "url": "https://help.aliyun.com/zh/model-studio/qwen3-8-max",
        "snapshot": None,
        "purpose": "难文、长上下文、复杂推理",
    },
    {
        "id": "kimi-k3",
        "url": "https://help.aliyun.com/zh/model-studio/kimi-k3",
        "snapshot": None,
        "purpose": "长程 Agent / 代码（最贵，勿作默认）",
    },
    {
        "id": "deepseek-v4-flash-0731",
        "url": "https://help.aliyun.com/zh/model-studio/deepseek-v4-flash",
        "snapshot": "deepseek-v4-flash-0731",
        "purpose": "低成本推理（快照忙/闲时）",
    },
    {
        "id": "deepseek-v4-pro-0813",
        "url": "https://help.aliyun.com/zh/model-studio/deepseek-v4-pro",
        "snapshot": "deepseek-v4-pro-0813",
        "purpose": "更强 DeepSeek V4（快照忙/闲时）",
    },
]

MIMO_URL = "https://platform.xiaomimimo.com/docs/zh-CN/price/pay-as-you-go"
MIMO = [
    {"id": "mimo-v2.5", "purpose": "小米 MiMo 2.5"},
    {"id": "mimo-v2.5-pro", "purpose": "小米 MiMo 2.5 Pro"},
]

OPENROUTER_FX_CNY_PER_USD = 6.72
OPENROUTER_GLM_FLASH_URL = "https://openrouter.ai/z-ai/glm-5.3-flash"

END_MARKERS = ("新加坡", "德国（法兰克福）", "美国（弗吉尼亚）", "日本（东京）", "中国香港", "限流")


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag in {"script", "style", "noscript"}:
            self.skip += 1
        if tag in {"p", "div", "tr", "h1", "h2", "h3", "h4", "h5", "li", "br", "table"}:
            self.parts.append("\n")
        if tag in {"td", "th"}:
            self.parts.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.skip:
            self.skip -= 1

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        t = data.strip()
        if t:
            self.parts.append(t)


def http_get(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9", "Accept": "text/html"},
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", "replace")


def html_to_text(html: str) -> str:
    p = _Text()
    p.feed(html)
    text = "\n".join("".join(p.parts).splitlines())
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text)


def beijing_price_block(text: str, snapshot: str | None) -> str:
    src = text
    if snapshot:
        i = src.find(snapshot)
        if i < 0:
            raise ValueError(f"snapshot {snapshot} not found")
        src = src[i:]
    i = src.find("模型价格")
    if i < 0:
        raise ValueError("模型价格 section missing")
    src = src[i:]
    i = src.find(REGION)
    if i < 0:
        raise ValueError(f"{REGION} missing after 模型价格")
    src = src[i + len(REGION) :]
    end = len(src)
    for mark in END_MARKERS:
        j = src.find(mark)
        if 0 <= j < end:
            end = j
    return src[:end]


ROW_RE = re.compile(
    r"(输入(?:（[^）]+）)?|输出(?:（[^）]+）)?|显式缓存创建|显式缓存命中)\s*\|\s*"
    r"([0-9]+(?:\.[0-9]+)?)\s*\|\s*每百万",
)


def parse_rows(block: str) -> dict[str, float]:
    rows: dict[str, float] = {}
    for label, num in ROW_RE.findall(block):
        if "Batch" in label:
            continue
        rows[label] = float(num)
    return rows


def from_aliyun_rows(model_id: str, url: str, purpose: str, rows: dict[str, float]) -> dict:
    peak = "输入（忙时）" in rows
    if peak:
        inp = rows["输入（忙时）"]
        out = rows["输出（忙时）"]
        cache = rows.get("输入（缓存命中，忙时）")
        idle_in = rows["输入（闲时）"]
        idle_out = rows["输出（闲时）"]
        idle_cache = rows.get("输入（缓存命中，闲时）")
        billing = "peak_offpeak"
        accounting = "busy"
    else:
        if "输入" not in rows or "输出" not in rows:
            raise ValueError(f"{model_id}: missing 输入/输出 in {rows}")
        inp = rows["输入"]
        out = rows["输出"]
        cache = rows.get("输入（缓存命中）") or rows.get("显式缓存命中")
        idle_in = idle_out = idle_cache = None
        billing = "flat"
        accounting = "list"
    return _record(
        model_id,
        source="aliyun",
        url=url,
        purpose=purpose,
        inp=inp,
        out=out,
        cache=cache,
        billing=billing,
        accounting=accounting,
        idle_in=idle_in,
        idle_out=idle_out,
        idle_cache=idle_cache,
        busy_in=rows.get("输入（忙时）"),
        busy_out=rows.get("输出（忙时）"),
        busy_cache=rows.get("输入（缓存命中，忙时）"),
    )


def _record(
    model_id: str,
    *,
    source: str,
    url: str,
    purpose: str,
    inp: float,
    out: float,
    cache: float | None,
    billing: str,
    accounting: str,
    idle_in: float | None = None,
    idle_out: float | None = None,
    idle_cache: float | None = None,
    busy_in: float | None = None,
    busy_out: float | None = None,
    busy_cache: float | None = None,
) -> dict:
    rec = {
        "id": model_id,
        "source": source,
        "source_url": url,
        "region": REGION if source == "aliyun" else ("OpenRouter" if source == "openrouter" else "中国内地按量"),
        "purpose": purpose,
        "billing": billing,
        "accounting_band": accounting,
        "currency": "CNY",
        "symbol": SYMBOL,
        "unit": "每百万tokens",
        "input_cny_per_million": inp,
        "output_cny_per_million": out,
        "cache_hit_cny_per_million": cache,
        "input_idle_cny_per_million": idle_in,
        "output_idle_cny_per_million": idle_out,
        "cache_hit_idle_cny_per_million": idle_cache,
        "input_busy_cny_per_million": busy_in,
        "output_busy_cny_per_million": busy_out,
        "cache_hit_busy_cny_per_million": busy_cache,
        "input_cost_per_token": round(inp / 1_000_000, 12),
        "output_cost_per_token": round(out / 1_000_000, 12),
        "cache_read_input_token_cost": round(cache / 1_000_000, 12) if cache is not None else None,
        "display_input": f"{SYMBOL}{inp:g}",
        "display_output": f"{SYMBOL}{out:g}",
    }
    return rec


def parse_mimo(text: str) -> dict[str, dict]:
    # 国内表：mimo-v2.5-pro | ¥0.025 | ¥3.00 | ¥6.00  → cache, uncached input, output
    found: dict[str, dict] = {}
    for spec in MIMO:
        mid = spec["id"]
        m = re.search(
            rf"{re.escape(mid)}\s*\|\s*¥\s*([0-9.]+)\s*\|\s*¥\s*([0-9.]+)\s*\|\s*¥\s*([0-9.]+)",
            text,
        )
        if not m:
            raise ValueError(f"{mid} not found on MiMo 国内定价")
        cache, inp, out = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
        found[mid] = _record(
            mid,
            source="xiaomi",
            url=MIMO_URL,
            purpose=spec["purpose"],
            inp=inp,
            out=out,
            cache=cache,
            billing="flat",
            accounting="list",
        )
    return found


def openrouter_glm_flash() -> dict:
    # OpenRouter model page In/Out Price (USD / million), not a single provider's list.
    usd_in, usd_out, usd_cache = 0.05, 0.1667, 0.01
    fx = OPENROUTER_FX_CNY_PER_USD
    rec = _record(
        "glm-5.3-flash",
        source="openrouter",
        url=OPENROUTER_GLM_FLASH_URL,
        purpose="GLM-5.3 Flash，与 Qwen Flash 同档、更便宜",
        inp=round(usd_in * fx, 4),
        out=round(usd_out * fx, 4),
        cache=round(usd_cache * fx, 4),
        billing="flat",
        accounting="list",
    )
    rec["usd_input_per_million"] = usd_in
    rec["usd_output_per_million"] = usd_out
    rec["usd_cache_hit_per_million"] = usd_cache
    rec["fx_cny_per_usd"] = fx
    return rec


def fetch_official_prices() -> dict:
    models: dict[str, dict] = {}
    errors: list[str] = []
    for spec in ALIYUN:
        try:
            html = http_get(spec["url"])
            text = html_to_text(html)
            block = beijing_price_block(text, spec["snapshot"])
            rows = parse_rows(block)
            models[spec["id"]] = from_aliyun_rows(spec["id"], spec["url"], spec["purpose"], rows)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{spec['id']}: {e}")
    try:
        mimo_text = html_to_text(http_get(MIMO_URL))
        models.update(parse_mimo(mimo_text))
    except Exception as e:  # noqa: BLE001
        errors.append(f"mimo: {e}")
    models["glm-5.3-flash"] = openrouter_glm_flash()
    if len(models) < 6:
        raise RuntimeError("too few official prices: " + "; ".join(errors))
    payload = {
        "currency": "CNY",
        "symbol": SYMBOL,
        "region": REGION,
        "unit": "每百万tokens",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "refresh_seconds": WEEK_SECONDS,
        "note": "阿里云为华北2（北京）官方原价；DeepSeek 快照记账用忙时官方价。小米为国内按量官方价。GLM-5.3 Flash 为 OpenRouter 标价（USD×6.72）。",
        "models": models,
        "errors": errors,
    }
    return payload


def write_prices(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_prices(path: Path | None = None) -> dict:
    candidates = []
    if path:
        candidates.append(path)
    candidates.extend(
        [
            RUNTIME_JSON,
            Path("/app/config/model-prices.json"),
            Path("/app/landing/model-prices.json"),
            DEFAULT_JSON,
            ROOT / "landing" / "model-prices.json",
        ]
    )
    for p in candidates:
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
    raise FileNotFoundError("model-prices.json not found")


def cost_fields(rec: dict) -> dict:
    out = {
        "input_cost_per_token": rec["input_cost_per_token"],
        "output_cost_per_token": rec["output_cost_per_token"],
    }
    if rec.get("cache_read_input_token_cost") is not None:
        out["cache_read_input_token_cost"] = rec["cache_read_input_token_cost"]
    return out


def _api(gateway: str, master: str, method: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        gateway.rstrip("/") + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {master}",
            "Content-Type": "application/json",
            "User-Agent": UA,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        try:
            parsed = json.loads(err)
        except json.JSONDecodeError:
            parsed = {"raw": err}
        return {"error": e.code, "body": parsed}


def push_costs_to_litellm(gateway: str, master: str, payload: dict) -> list[str]:
    listed = _api(gateway, master, "GET", "/v2/model/info")
    rows = listed.get("data") or listed.get("models") or []
    by_id: dict[str, dict] = {}
    for row in rows:
        info = row.get("model_info") or {}
        if info.get("db_model") is False:
            continue
        mid = info.get("id") or row.get("model_name")
        if mid:
            by_id[mid] = row
    logs = []
    for mid, rec in (payload.get("models") or {}).items():
        if mid not in by_id:
            logs.append(f"{mid}: not in LiteLLM DB yet")
            continue
        row = by_id[mid]
        params = dict(row.get("litellm_params") or {})
        info = dict(row.get("model_info") or {})
        costs = cost_fields(rec)
        params.update(costs)
        info.update(costs)
        info["currency"] = "CNY"
        extra = ""
        if rec.get("billing") == "peak_offpeak":
            extra = (
                f" 闲时输入{SYMBOL}{rec['input_idle_cny_per_million']:g}/输出{SYMBOL}{rec['output_idle_cny_per_million']:g}"
                f"；记账按忙时官方价。"
            )
        info["description"] = (
            f"{rec.get('purpose') or mid}。{rec.get('region')} 官方原价："
            f"输入 {SYMBOL}{rec['input_cny_per_million']:g}/百万 · "
            f"输出 {SYMBOL}{rec['output_cny_per_million']:g}/百万。{extra}"
        )
        result = _api(
            gateway,
            master,
            "POST",
            "/model/update",
            {
                "id": info.get("id") or mid,
                "model_name": row.get("model_name") or mid,
                "litellm_params": params,
                "model_info": info,
            },
        )
        if result.get("error"):
            logs.append(f"{mid}: update error {result.get('error')} {result.get('body')}")
        else:
            logs.append(
                f"{mid}: {SYMBOL}{rec['input_cny_per_million']:g} / {SYMBOL}{rec['output_cny_per_million']:g} per 1M"
            )
    return logs


def save_everywhere(payload: dict) -> list[Path]:
    written = []
    for path in (DEFAULT_JSON, RUNTIME_JSON):
        try:
            write_prices(payload, path)
            written.append(path)
        except OSError:
            continue
    landing = Path("/app/landing/model-prices.json")
    try:
        write_prices(payload, landing)
        written.append(landing)
    except OSError:
        pass
    local_landing = ROOT / "landing" / "model-prices.json"
    try:
        write_prices(payload, local_landing)
        written.append(local_landing)
    except OSError:
        pass
    return written


def run_once(apply: bool) -> int:
    payload = fetch_official_prices()
    save_everywhere(payload)
    print(json.dumps({k: payload[k] for k in ("fetched_at", "currency", "errors")}, ensure_ascii=False))
    for mid, rec in payload["models"].items():
        print(
            f"  {mid:28} in {SYMBOL}{rec['input_cny_per_million']:g}  "
            f"out {SYMBOL}{rec['output_cny_per_million']:g}  {rec['source_url']}"
        )
    if not apply:
        return 0 if not payload.get("errors") else 0
    gateway = (os.environ.get("PUBLIC_GATEWAY_URL") or os.environ.get("IMSTEM_GATEWAY") or "http://127.0.0.1:4000").rstrip(
        "/"
    )
    # Inside the container, always hit local proxy when applying on a loop.
    if os.environ.get("IMSTEM_APPLY_LOCAL") == "1":
        gateway = f"http://127.0.0.1:{os.environ.get('PORT') or '4000'}"
    master = os.environ.get("LITELLM_MASTER_KEY") or ""
    if not master:
        print("LITELLM_MASTER_KEY missing; skipped LiteLLM update", file=sys.stderr)
        return 1
    for line in push_costs_to_litellm(gateway, master, payload):
        print(line)
    return 0


def wait_proxy(timeout: int = 180) -> None:
    port = os.environ.get("PORT") or "4000"
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/health/readiness"
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2).read()
            return
        except Exception:
            time.sleep(2)
    print(f"proxy not ready at {url}, applying anyway", file=sys.stderr)


def loop(days: float) -> None:
    os.environ["IMSTEM_APPLY_LOCAL"] = "1"
    wait_proxy()
    while True:
        try:
            run_once(apply=True)
        except Exception as e:  # noqa: BLE001
            print(f"official price refresh failed: {e}", file=sys.stderr)
        time.sleep(max(60.0, days * 86400))


def load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v)


def main() -> int:
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="POST costs into LiteLLM /model/update")
    parser.add_argument("--loop-days", type=float, default=0, help="repeat forever every N days")
    args = parser.parse_args()
    if args.loop_days:
        loop(args.loop_days)
        return 0
    return run_once(apply=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
