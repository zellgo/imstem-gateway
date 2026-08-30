"""Serve the employee landing page at / and /guide on the LiteLLM proxy."""
from __future__ import annotations

from pathlib import Path

try:
    from litellm.integrations.custom_logger import CustomLogger
except Exception:  # pragma: no cover - import only exists in the LiteLLM image
    class CustomLogger:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            pass

_INSTALLED = False
LANDING_DIR = Path("/app/landing")


def _install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    try:
        from fastapi.responses import HTMLResponse
        from litellm.proxy.proxy_server import app
        from starlette.routing import Route
    except Exception:
        return

    index = LANDING_DIR / "index.html"
    guide = LANDING_DIR / "api-guide.html"
    if not index.is_file():
        return

    index_html = index.read_text(encoding="utf-8")
    guide_html = guide.read_text(encoding="utf-8") if guide.is_file() else index_html

    async def home(_request=None):
        return HTMLResponse(index_html, media_type="text/html; charset=utf-8")

    async def api_guide(_request=None):
        return HTMLResponse(guide_html, media_type="text/html; charset=utf-8")

    kept = []
    for route in app.router.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or set()
        if path in {"/", "/guide"} and "GET" in methods:
            continue
        kept.append(route)
    app.router.routes = kept
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
