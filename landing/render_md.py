"""Tiny GitHub-flavored subset: headings, tables, lists, fences, links, emphasis."""
from __future__ import annotations

import html
import re

YEN = "&#165;"


def _inline(text: str) -> str:
    parts: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("`", i):
            j = text.find("`", i + 1)
            if j != -1:
                parts.append("<code>" + html.escape(text[i + 1 : j]) + "</code>")
                i = j + 1
                continue
        if text.startswith("**", i):
            j = text.find("**", i + 2)
            if j != -1:
                parts.append("<strong>" + _inline(text[i + 2 : j]) + "</strong>")
                i = j + 2
                continue
        if text.startswith("[", i):
            m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", text[i:])
            if m:
                label, href = m.group(1), m.group(2)
                href = _rewrite_href(href)
                inner = html.escape(label) if label.startswith("http") else _inline(label)
                parts.append(
                    f'<a href="{html.escape(href, quote=True)}">{inner}</a>'
                )
                i += m.end()
                continue
        if text.startswith("https://", i) or text.startswith("http://", i):
            j = i
            while j < n and text[j] not in " \t\n<>)\"'":
                j += 1
            url = text[i:j].rstrip(".,;:")
            parts.append(f'<a href="{html.escape(url, quote=True)}">{html.escape(url)}</a>')
            i += len(url)
            continue
        ch = text[i]
        if ch == "<" and text.startswith("<https://", i):
            j = text.find(">", i)
            if j != -1:
                url = text[i + 1 : j]
                parts.append(f'<a href="{html.escape(url, quote=True)}">{html.escape(url)}</a>')
                i = j + 1
                continue
        parts.append(html.escape(ch))
        i += 1
    out = "".join(parts)
    return out.replace("￥", YEN).replace("¥", YEN)


def _rewrite_href(href: str) -> str:
    mapping = {
        "USER_GUIDE_ZH.md": "/guides/user",
        "OPENWEBUI_GUIDE_ZH.md": "/guides/openwebui",
        "MODEL_COST_ZH.md": "/guides/cost",
        "EMAIL_ONBOARDING_ZH.md": "/guides",
    }
    name = href.split("/")[-1]
    if name in mapping:
        return mapping[name]
    if href.startswith("http") or href.startswith("/") or href.startswith("mailto:"):
        return href
    return href


def md_to_html(src: str) -> str:
    lines = src.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    def flush_para(buf: list[str]) -> None:
        text = " ".join(buf).strip()
        if text:
            out.append("<p>" + _inline(text) + "</p>")
        buf.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()
        if stripped == "":
            i += 1
            continue
        if stripped == "---":
            out.append("<hr>")
            i += 1
            continue
        if stripped.startswith("```"):
            lang = html.escape(stripped[3:].strip())
            body: list[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            if i < n:
                i += 1
            cls = f' class="lang-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>" + html.escape("\n".join(body)) + "</code></pre>")
            continue
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                raw = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(raw)
                i += 1
            if len(rows) >= 2:
                head, body = rows[0], rows[2:]
                thead = "<thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead>"
                tb = "<tbody>"
                for row in body:
                    while len(row) < len(head):
                        row.append("")
                    tb += "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row[: len(head)]) + "</tr>"
                tb += "</tbody>"
                out.append('<div class="table-wrap"><table>' + thead + tb + "</table></div>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title).strip("-").lower()
            tag = f"h{level}"
            out.append(f'<{tag} id="{html.escape(slug, quote=True)}">{_inline(title)}</{tag}>')
            i += 1
            continue
        if re.match(r"^[-*]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            ordered = bool(re.match(r"^\d+\.\s+", stripped))
            tag = "ol" if ordered else "ul"
            items: list[str] = []
            while i < n:
                s = lines[i].strip()
                if ordered:
                    mm = re.match(r"^\d+\.\s+(.*)$", s)
                else:
                    mm = re.match(r"^[-*]\s+(.*)$", s)
                if not mm:
                    break
                items.append("<li>" + _inline(mm.group(1)) + "</li>")
                i += 1
            out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue
        para: list[str] = [stripped]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if (
                nxt == ""
                or nxt == "---"
                or nxt.startswith("#")
                or nxt.startswith("|")
                or nxt.startswith("```")
                or re.match(r"^[-*]\s+", nxt)
                or re.match(r"^\d+\.\s+", nxt)
            ):
                break
            para.append(nxt)
            i += 1
        flush_para(para)
    return "\n".join(out)


def toc_from_html(body: str) -> str:
    # Headings already include 1 / 1.1 / 5.2. Do not use <ol> markers on top.
    items = re.findall(r'<h([23]) id="([^"]+)">(.*?)</h\1>', body, flags=re.S)
    if not items:
        return ""
    lis = []
    for level, i, t in items:
        cls = ' class="h3"' if level == "3" else ""
        lis.append(f'<li{cls}><a href="#{html.escape(i, quote=True)}">{t}</a></li>')
    return '<nav class="toc" aria-label="本页目录"><p>本页</p><ol>' + "".join(lis) + "</ol></nav>"
