/**
 * TWNG FB Archive — Content Script
 *
 * Captures Facebook post URLs and nearby text excerpts from the
 * currently rendered page. Does NOT navigate, scroll, or automate
 * any interaction with Facebook.
 */

(() => {
  /** Patterns that identify a Facebook post link. */
  const POST_PATTERNS = [
    /\/groups\/[^/]+\/posts\/\d+/,
    /\/permalink\.php/,
  ];

  /** Tracking params to strip from URLs. */
  const TRACKING_PREFIXES = [
    "ref", "refid", "__cft__", "__tn__", "__xts__", "fref",
    "comment_tracking", "notif_id", "notif_t", "acontext",
    "hc_ref", "rc", "action_history",
  ];

  function isTrackingParam(key) {
    return TRACKING_PREFIXES.some(
      (prefix) => key === prefix || key.startsWith(prefix + "[")
    );
  }

  function normalizeUrl(rawUrl) {
    try {
      const url = new URL(rawUrl);
      // Force www + https
      url.protocol = "https:";
      if (url.hostname === "m.facebook.com" || url.hostname === "facebook.com") {
        url.hostname = "www.facebook.com";
      }
      // Strip tracking params
      const cleaned = new URLSearchParams();
      for (const [k, v] of url.searchParams) {
        if (!isTrackingParam(k)) cleaned.set(k, v);
      }
      url.search = cleaned.toString();
      // Strip trailing slash from pathname
      url.pathname = url.pathname.replace(/\/+$/, "") || "/";
      url.hash = "";
      return url.toString();
    } catch {
      return rawUrl;
    }
  }

  function getExcerpt(anchor) {
    // Walk up to find a reasonable container, then grab its text
    let container = anchor;
    for (let i = 0; i < 6; i++) {
      if (!container.parentElement) break;
      container = container.parentElement;
      // Stop at a role="article" or a div with a lot of text
      if (
        container.getAttribute("role") === "article" ||
        (container.innerText && container.innerText.length > 80)
      ) {
        break;
      }
    }
    const text = (container.innerText || "").trim();
    return text.slice(0, 300);
  }

  function captureResults() {
    const anchors = document.querySelectorAll("a[href]");
    const seen = new Set();
    const results = [];

    for (const a of anchors) {
      const href = a.href;
      if (!POST_PATTERNS.some((p) => p.test(href))) continue;

      const normalized = normalizeUrl(href);
      if (seen.has(normalized)) continue;
      seen.add(normalized);

      const excerpt = getExcerpt(a);
      // Try to get a title from the link text or nearby heading
      const title =
        a.innerText?.trim().slice(0, 200) ||
        a.getAttribute("aria-label")?.trim().slice(0, 200) ||
        null;

      results.push({
        source_url: normalized,
        title: title || null,
        excerpt: excerpt || null,
      });
    }

    return results;
  }

  // Listen for messages from the popup
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.action === "capture") {
      const results = captureResults();
      sendResponse({ results });
    }
    return true; // async response
  });
})();
