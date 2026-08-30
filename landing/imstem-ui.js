/* Relabel LiteLLM admin spend as CNY (yen). Official Aliyun Beijing / MiMo rates. */
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
      "用量金额为人民币 <strong>&#165;</strong>（阿里云百炼华北2北京 / 小米国内按量官方原价，每周自动同步）。界面里的 $ 符号表示同一笔人民币数字。";
    document.body.insertBefore(bar, document.body.firstChild);
  }

  function relabel(node) {
    if (!node || node.nodeType !== 3) return;
    var t = node.nodeValue;
    if (!t || t.indexOf("$") === -1) return;
    if (/https?:\/\//.test(t) || t.indexOf("${") !== -1) return;
    node.nodeValue = t
      .replace(/\$\s*(?=\d)/g, YEN)
      .replace(/\(\$\)/g, "(" + YEN + ")")
      .replace(/\bUSD\b/g, "CNY")
      .replace(/\bSpend \(\$\)/g, "用量 (" + YEN + ")");
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
