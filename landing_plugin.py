"""Serve the employee landing, usage guides, and CNY price table on the LiteLLM proxy."""
from __future__ import annotations

import html
import sys
from pathlib import Path

try:
    from litellm.integrations.custom_logger import CustomLogger
except Exception:  # pragma: no cover
    class CustomLogger:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            pass

_INSTALLED = False
LANDING_DIR = Path("/app/landing")
if not LANDING_DIR.is_dir():
    LANDING_DIR = Path(__file__).resolve().parent / "landing"

DOCS_DIR = Path("/app/docs")
if not DOCS_DIR.is_dir():
    DOCS_DIR = Path(__file__).resolve().parent / "docs"

for extra in (Path("/app"), Path("/app/scripts"), Path(__file__).resolve().parent / "scripts", LANDING_DIR):
    s = str(extra)
    if extra.is_dir() and s not in sys.path:
        sys.path.insert(0, s)

GUIDES = (
    {
        "slug": "user",
        "file": "USER_GUIDE_ZH.md",
        "title": "员工使用指南",
        "kicker": "01 · 入职",
        "blurb": "登录、选模型、个人 API、CC Switch、安全与计费。",
    },
    {
        "slug": "openwebui",
        "file": "OPENWEBUI_GUIDE_ZH.md",
        "title": "网页对话与知识库",
        "kicker": "02 · Chat",
        "blurb": "Open WebUI 界面、文件夹、用 # 引用知识库。",
    },
    {
        "slug": "cost",
        "file": "MODEL_COST_ZH.md",
        "title": "模型单价与省钱",
        "kicker": "03 · 费用",
        "blurb": "各模型人民币官方价、岗位怎么选才省钱。",
    },
    {
        "slug": "local-openwebui",
        "file": "OPENWEBUI_LOCAL_ZH.md",
        "title": "本地 Open WebUI",
        "kicker": "04 · 本机",
        "blurb": "Desktop 与 Computer：文件留在电脑，知识库自建，模型走公司网关。",
    },
)


def _prices_payload() -> dict:
    try:
        from official_prices import load_prices

        return load_prices()
    except Exception:
        baked = LANDING_DIR / "model-prices.json"
        if baked.is_file():
            import json

            return json.loads(baked.read_text(encoding="utf-8"))
        return {"currency": "CNY", "symbol": "\u00a5", "models": {}, "errors": ["missing prices"]}


def _chrome(title: str, inner: str, current: str = "") -> str:
    css_fonts = (
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
        '&family=IBM+Plex+Sans:wght@400;500;600&family=Noto+Serif+SC:wght@600;700&display=swap" rel="stylesheet">'
        '<link rel="stylesheet" href="/site.css">'
    )
    nav = []
    for href, label, key in (
        ("/guides", "使用指南", "guides"),
        ("/costs", "官方单价", "costs"),
        ("/guide", "个人 API", "api"),
    ):
        cur = ' aria-current="page"' if current == key else ""
        nav.append(f'<a href="{href}"{cur}>{label}</a>')
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  {css_fonts}
</head>
<body>
  <div class="top">
    <a class="mark" href="/" style="text-decoration:none">ImStem Biotechnology</a>
    <nav aria-label="快捷">{"".join(nav)}</nav>
  </div>
  <main class="page">{inner}</main>
</body>
</html>"""


def _guides_index() -> str:
    cards = []
    for i, g in enumerate(GUIDES, 1):
        cards.append(
            f"""<li>
              <a href="/guides/{g['slug']}">
                <span class="idx">0{i}</span>
                <span><strong>{html.escape(g['title'])}</strong><small>{html.escape(g['blurb'])}</small></span>
                <span class="go">打开</span>
              </a>
            </li>"""
        )
    inner = f"""
    <a class="back" href="/">← 返回入口</a>
    <p class="kicker">ImStem LLM</p>
    <h1>使用指南</h1>
    <p class="lede">中文说明：先看员工总指南，再用网页对话和知识库；大文件用本地 Desktop / Computer，选模型时对照单价。</p>
    <section class="notebook">
      <h2>文档</h2>
      <ol class="ledger">{"".join(cards)}</ol>
    </section>
    <p class="lede" style="margin-top:2rem">个人 API 逐步命令仍在 <a href="/guide">/guide</a>。实时官方价在 <a href="/costs">/costs</a>。</p>
    """
    return _chrome("使用指南 · ImStem LLM", inner, "guides")


def _guide_page(slug: str) -> str | None:
    spec = next((g for g in GUIDES if g["slug"] == slug), None)
    if not spec:
        return None
    path = DOCS_DIR / spec["file"]
    if not path.is_file():
        path = Path(__file__).resolve().parent / "docs" / spec["file"]
    if not path.is_file():
        return None
    from render_md import md_to_html, toc_from_html

    body = md_to_html(path.read_text(encoding="utf-8"))
    toc = toc_from_html(body)
    inner = f"""
    <a class="back" href="/guides">← 全部指南</a>
    <p class="kicker">{html.escape(spec['kicker'])}</p>
    <div class="guide-layout">
      {toc}
      <article class="prose">{body}</article>
    </div>
    """
    return _chrome(f"{spec['title']} · ImStem LLM", inner, "guides")


def _install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    try:
        from fastapi.responses import HTMLResponse, JSONResponse, Response
        from litellm.proxy.proxy_server import app
        from starlette.routing import Route
    except Exception:
        return

    index = LANDING_DIR / "index.html"
    guide = LANDING_DIR / "api-guide.html"
    costs = LANDING_DIR / "costs.html"
    ui_js = LANDING_DIR / "imstem-ui.js"
    site_css = LANDING_DIR / "site.css"
    if not index.is_file():
        return

    index_html = index.read_text(encoding="utf-8")
    guide_html = guide.read_text(encoding="utf-8") if guide.is_file() else index_html
    costs_html = costs.read_text(encoding="utf-8") if costs.is_file() else index_html
    css_text = site_css.read_text(encoding="utf-8") if site_css.is_file() else ""
    ui_js_text = ui_js.read_text(encoding="utf-8") if ui_js.is_file() else "/* missing imstem-ui.js */"
    guides_index_html = _guides_index()

    async def home(_request=None):
        return HTMLResponse(index_html, media_type="text/html; charset=utf-8")

    async def api_guide(_request=None):
        return HTMLResponse(guide_html, media_type="text/html; charset=utf-8")

    async def cost_page(_request=None):
        return HTMLResponse(costs_html, media_type="text/html; charset=utf-8")

    async def prices(_request=None):
        return JSONResponse(_prices_payload())

    async def ui_script(_request=None):
        return Response(ui_js_text, media_type="application/javascript; charset=utf-8")

    async def css(_request=None):
        return Response(css_text, media_type="text/css; charset=utf-8")

    async def guides_home(_request=None):
        return HTMLResponse(guides_index_html, media_type="text/html; charset=utf-8")

    async def guide_one(request):
        slug = (request.path_params or {}).get("slug") or ""
        page = _guide_page(slug)
        if not page:
            return HTMLResponse("未找到该指南。", status_code=404, media_type="text/html; charset=utf-8")
        return HTMLResponse(page, media_type="text/html; charset=utf-8")

    skip = {
        ("/", "GET"),
        ("/guide", "GET"),
        ("/guides", "GET"),
        ("/costs", "GET"),
        ("/imstem/prices", "GET"),
        ("/imstem-ui.js", "GET"),
        ("/site.css", "GET"),
    }
    kept = []
    for route in app.router.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or set()
        drop = False
        for p, m in skip:
            if path == p and m in methods:
                drop = True
                break
        if not drop:
            kept.append(route)
    app.router.routes = kept
    app.router.routes.insert(0, Route("/guides/{slug}", guide_one, methods=["GET"]))
    app.router.routes.insert(0, Route("/guides", guides_home, methods=["GET"]))
    app.router.routes.insert(0, Route("/site.css", css, methods=["GET"]))
    app.router.routes.insert(0, Route("/imstem-ui.js", ui_script, methods=["GET"]))
    app.router.routes.insert(0, Route("/imstem/prices", prices, methods=["GET"]))
    app.router.routes.insert(0, Route("/costs", cost_page, methods=["GET"]))
    app.router.routes.insert(0, Route("/guide", api_guide, methods=["GET"]))
    app.router.routes.insert(0, Route("/", home, methods=["GET"]))
    _INSTALLED = True


class LandingPlugin(CustomLogger):
    def __init__(self) -> None:
        super().__init__()
        _install()

    def log_pre_api_call(self, model, messages, kwargs):  # noqa: ANN001
        _install()

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):  # noqa: ANN001
        _install()
        return data


landing_plugin = LandingPlugin()
