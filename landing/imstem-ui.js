/* Relabel LiteLLM admin spend as CNY (yen). Official Aliyun Beijing / MiMo / OpenRouter rates. */
(function () {
  var BANNER_ID = "imstem-cny-banner";
  var YEN = "\u00a5";

  function ensureBanner() {
    if (document.getElementById(BANNER_ID) || !document.body) return;
    var bar = document.createElement("div");
    bar.id = BANNER_ID;
    bar.setAttribute("role", "status");
    bar.style.cssText =
      "position:sticky;top:0;z-index:9999;background:#0f6b57;color:#f4fbf7;" +
      "font:500 13px/1.4 'IBM Plex Sans',system-ui,sans-serif;padding:8px 16px;" +
      "border-bottom:1px solid #0b5243;";
    bar.innerHTML =
      "用量与模型单价为人民币 <strong>&#165;</strong>（阿里云百炼华北2北京 / 小米国内按量 / OpenRouter×6.72）。界面里的 $ 表示同一笔人民币数字，不是美元。";
    document.body.insertBefore(bar, document.body.firstChild);
  }

  function rewrite(t) {
    if (!t) return t;
    if (/https?:\/\//.test(t) || t.indexOf("${") !== -1) return t;
    if (t.trim() === "$") return YEN;
    return t
      .replace(/\$\s*\/\s*1M/gi, YEN + " / 百万")
      .replace(/\$\s*\/\s*1k/gi, YEN + " / 千")
      .replace(/\$\s*\/\s*(?=token)/gi, YEN + " / ")
      .replace(/\(\s*\$\s*\)/g, "(" + YEN + ")")
      .replace(/US\$/g, YEN)
      .replace(/\$\s*(?=\d)/g, YEN)
      .replace(/\bUSD\b/g, "CNY")
      .replace(/\bSpend \(\$\)/g, "用量 (" + YEN + ")")
      .replace(/\bCost \(\$\)/g, "单价 (" + YEN + ")");
  }

  function relabel(node) {
    if (!node || node.nodeType !== 3) return;
    var t = node.nodeValue;
    if (!t) return;
    if (t.indexOf("$") === -1 && t.indexOf("USD") === -1) return;
    var next = rewrite(t);
    if (next !== t) node.nodeValue = next;
  }

  function walk(root) {
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    var n;
    while ((n = w.nextNode())) relabel(n);
  }

  function boot() {
    ensureBanner();
    walk(document.body);
    var obs = new MutationObserver(function (muts) {
      ensureBanner();
      muts.forEach(function (m) {
        if (m.type === "characterData") relabel(m.target);
        m.addedNodes.forEach(function (n) {
          if (n.nodeType === 3) relabel(n);
          else if (n.nodeType === 1) walk(n);
        });
      });
    });
    obs.observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
