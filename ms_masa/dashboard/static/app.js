"use strict";

(() => {
  // ── Helpers ──────────────────────────────────────────────────────────
  // All API text is inserted with textContent; never build HTML from data.

  const SVG_NS = "http://www.w3.org/2000/svg";
  const $ = (sel) => document.querySelector(sel);

  function h(tag, attrs, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") node.className = v;
      else if (k === "text") node.textContent = v;
      else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? "" : String(v));
    }
    for (const c of children.flat()) {
      if (c === null || c === undefined || c === false) continue;
      node.append(c instanceof Node ? c : document.createTextNode(String(c)));
    }
    return node;
  }

  function s(tag, attrs) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "text") node.textContent = v;
      else node.setAttribute(k, String(v));
    }
    return node;
  }

  const store = {
    get(area, key) { try { return window[area].getItem(key); } catch { return null; } },
    set(area, key, value) {
      try { value === null ? window[area].removeItem(key) : window[area].setItem(key, value); } catch { /* storage unavailable */ }
    },
  };

  const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
  const whole = new Intl.NumberFormat("en", { maximumFractionDigits: 0 });
  const fmt = {
    usd: (n) => (n == null ? "–" : "$" + compact.format(n)),
    cents: (p) => (p == null ? "–" : (p * 100).toFixed(1) + "¢"),
    pct: (p) => (p == null ? "–" : Math.round(p * 100) + "%"),
    shares: (n) => whole.format(n),
    date: (iso) => {
      if (!iso) return "";
      const d = new Date(iso);
      return isNaN(d) ? "" : d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
    },
  };

  const SIGNALS = {
    wide_spread: ["Wide spread", "Bid–ask gap is unusually large"],
    imbalance_bid_heavy: ["Bid-heavy book", "More resting size on the buy side"],
    imbalance_ask_heavy: ["Ask-heavy book", "More resting size on the sell side"],
    low_liquidity: ["Thin book", "Little total depth to trade against"],
    near_certainty: ["Near certainty", "Priced below 5% or above 95%"],
    high_uncertainty: ["Coin flip", "Priced between 45% and 55%"],
  };
  const PRICE_SIGNALS = new Set(["near_certainty", "high_uncertainty"]);
  const signalLabel = (t) => (SIGNALS[t] || [t.replace(/_/g, " ")])[0];

  function meter(value, label) {
    const fill = h("span");
    fill.style.width = Math.max(0, Math.min(1, value || 0)) * 100 + "%";
    return h("div", { class: "meter", role: "meter", "aria-valuemin": 0, "aria-valuemax": 100,
      "aria-valuenow": Math.round((value || 0) * 100), "aria-label": label }, fill);
  }

  function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  }

  // ── API ──────────────────────────────────────────────────────────────

  class ApiError extends Error {
    constructor(status, message) { super(message); this.status = status; }
  }

  const state = {
    status: null,
    token: store.get("sessionStorage", "ms-masa-token"),
    tab: "markets",
    tag: "",
    sort: "volume",
    q: "",
    signalType: "",
    topic: "platform",
    marketId: null,
    requestSeq: 0,
  };

  async function api(path) {
    const headers = { Accept: "application/json" };
    if (state.token) headers.Authorization = "Bearer " + state.token;
    let res;
    try {
      res = await fetch(path, { headers, cache: "no-store" });
    } catch {
      throw new ApiError(0, "The dashboard server is not responding.");
    }
    let body = null;
    try { body = await res.json(); } catch { /* non-JSON */ }
    if (!res.ok) throw new ApiError(res.status, (body && body.error) || res.statusText);
    return body;
  }

  // ── Shell: banner, badge, theme, routing ─────────────────────────────

  function setBanner(node) {
    const slot = $("#banner-slot");
    slot.replaceChildren();
    if (node) slot.append(node);
  }

  function sampleBanner() {
    return h("div", { class: "banner sample", role: "note" },
      h("span", null, h("strong", { text: "Sample data. " }),
        "These markets are fictional and generated for demos. Restart without ",
        h("code", { text: "--sample-data" }), " for live Polymarket data."));
  }

  function errorBanner(err, retry) {
    let msg = err.message;
    if (err.status === 502) {
      msg = "Couldn't reach Polymarket. Check your internet connection, or restart with --sample-data to explore offline.";
    }
    return h("div", { class: "banner error", role: "alert" },
      h("span", null, h("strong", { text: "Something went wrong. " }), msg),
      retry && h("button", { class: "icon-btn", type: "button", onclick: retry, text: "Retry" }));
  }

  function renderBadge() {
    const badge = $("#mode-badge");
    if (!state.status) { badge.hidden = true; return; }
    const sample = state.status.mode === "sample";
    badge.className = "mode-badge" + (sample ? " sample" : "");
    badge.replaceChildren(h("span", { class: "dot", "aria-hidden": "true" }), sample ? "Sample data" : "Live");
    badge.title = sample ? "Fictional sample markets" : "Live Polymarket data";
    badge.hidden = false;
  }

  const THEMES = ["system", "light", "dark"];
  function applyTheme(theme) {
    if (theme === "system") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = theme;
    $("#theme-btn").setAttribute("aria-label", "Theme: " + theme);
    $("#theme-btn").title = "Theme: " + theme;
  }

  function parseHash() {
    const [tabPart, ...rest] = location.hash.replace(/^#/, "").split("&");
    const params = new URLSearchParams(rest.join("&"));
    const [tab, sub] = tabPart.split("/");
    return { tab: ["markets", "signals", "knowledge"].includes(tab) ? tab : "markets", sub, market: params.get("market") };
  }

  function writeHash() {
    let hash = "#" + state.tab;
    if (state.tab === "knowledge" && state.topic) hash += "/" + state.topic;
    if (state.marketId) hash += "&market=" + encodeURIComponent(state.marketId);
    if (location.hash !== hash) history.replaceState(null, "", hash);
  }

  function selectTab(tab) {
    state.tab = tab;
    document.querySelectorAll(".tab").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === tab)));
    writeHash();
    renderView();
  }

  // ── Views ────────────────────────────────────────────────────────────

  function renderView() {
    const view = $("#view");
    view.replaceChildren();
    if (state.tab === "markets") renderMarkets(view);
    else if (state.tab === "signals") renderSignals(view);
    else renderKnowledge(view);
  }

  function skeletonRows(cols, n = 8) {
    return Array.from({ length: n }, () =>
      h("tr", { class: "skeleton-row", "aria-hidden": "true" },
        Array.from({ length: cols }, (_, i) => {
          const bar = h("div", { class: "skeleton" });
          bar.style.width = i === 0 ? "70%" : "50%";
          return h("td", null, bar);
        })));
  }

  // Markets

  function renderMarkets(view) {
    const search = h("input", {
      class: "field", type: "search", placeholder: "Search questions…", "aria-label": "Search markets",
      value: state.q, maxlength: 100,
    });
    search.addEventListener("input", debounce(() => { state.q = search.value.trim(); loadMarkets(); }, 250));

    const tagSel = h("select", { class: "field", "aria-label": "Category" },
      h("option", { value: "", text: "All categories" }),
      (state.status?.tags || []).map((t) => h("option", { value: t, text: t.replace("-", " "), selected: t === state.tag })));
    tagSel.addEventListener("change", () => { state.tag = tagSel.value; loadMarkets(); });

    const sortLabels = { volume: "Highest volume", liquidity: "Most liquid", uncertainty: "Closest to 50/50", certainty: "Most certain" };
    const sortSel = h("select", { class: "field", "aria-label": "Sort" },
      (state.status?.sorts || Object.keys(sortLabels)).map((v) =>
        h("option", { value: v, text: sortLabels[v] || v, selected: v === state.sort })));
    sortSel.addEventListener("change", () => { state.sort = sortSel.value; loadMarkets(); });

    const stats = h("div", { class: "stats", id: "market-stats" });
    const tbody = h("tbody", null, skeletonRows(6));
    const table = h("div", { class: "card table-wrap" },
      h("table", null,
        h("caption", { class: "sr-only", text: "Markets" }),
        h("thead", null, h("tr", null,
          h("th", { scope: "col", text: "Market" }),
          h("th", { scope: "col", text: "Yes price" }),
          h("th", { scope: "col", class: "num", text: "Volume" }),
          h("th", { scope: "col", class: "num col-optional", text: "Liquidity" }),
          h("th", { scope: "col", class: "num col-optional", text: "Certainty" }),
          h("th", { scope: "col", class: "col-optional", text: "Ends" }))),
        tbody));

    view.append(h("div", { class: "toolbar" }, h("div", { class: "grow" }, search), tagSel, sortSel), stats, table);
    loadMarkets();
  }

  async function loadMarkets() {
    const seq = ++state.requestSeq;
    const tbody = $("#view tbody");
    if (!tbody) return;
    tbody.replaceChildren(...skeletonRows(6));
    const params = new URLSearchParams({ sort: state.sort, limit: "40" });
    if (state.tag) params.set("tag", state.tag);
    if (state.q) params.set("q", state.q);
    try {
      const markets = await api("/api/markets?" + params);
      if (seq !== state.requestSeq) return;
      setBanner(state.status?.mode === "sample" ? sampleBanner() : null);
      renderMarketStats(markets);
      if (!markets.length) {
        tbody.replaceChildren(h("tr", null, h("td", { colspan: 6, class: "empty",
          text: state.q ? `No markets match “${state.q}”.` : "No markets in this category right now." })));
        return;
      }
      tbody.replaceChildren(...markets.map(marketRow));
    } catch (err) {
      if (seq !== state.requestSeq) return;
      if (handleAuthError(err)) return;
      tbody.replaceChildren(h("tr", null, h("td", { colspan: 6, class: "empty", text: "Markets couldn't be loaded." })));
      setBanner(errorBanner(err, loadMarkets));
    }
  }

  function renderMarketStats(markets) {
    const box = $("#market-stats");
    if (!box) return;
    const vol = markets.reduce((a, m) => a + (m.volume || 0), 0);
    const liq = markets.reduce((a, m) => a + (m.liquidity || 0), 0);
    const flips = markets.filter((m) => m.yes_price >= 0.4 && m.yes_price <= 0.6).length;
    const tile = (label, value, note) => h("div", { class: "card stat" },
      h("div", { class: "stat-label", text: label }), h("div", { class: "stat-value", text: value }),
      note && h("div", { class: "stat-note", text: note }));
    box.replaceChildren(
      tile("Markets shown", String(markets.length)),
      tile("Total volume", fmt.usd(vol)),
      tile("Total liquidity", fmt.usd(liq)),
      tile("Contested", String(flips), "priced 40–60%"));
  }

  function marketRow(m) {
    const row = h("tr", { tabindex: 0, "aria-label": `${m.question}, yes ${fmt.cents(m.yes_price)}` },
      h("td", { class: "q-cell" },
        h("div", { class: "q-text", text: m.question }),
        h("div", { class: "tag-label", text: (m.tags || [])[0] || m.category || "" })),
      h("td", null, h("div", { class: "prob" },
        h("span", { class: "prob-value", text: fmt.cents(m.yes_price) }),
        meter(m.yes_price, "Yes price"))),
      h("td", { class: "num", text: fmt.usd(m.volume) }),
      h("td", { class: "num col-optional", text: fmt.usd(m.liquidity) }),
      h("td", { class: "num col-optional", text: fmt.pct(m.certainty) }),
      h("td", { class: "col-optional meta", text: fmt.date(m.end_date) }));
    const open = () => openMarket(m.id, row);
    row.addEventListener("click", open);
    row.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
    return row;
  }

  // Signals

  function renderSignals(view) {
    const chips = h("div", { class: "chip-row", role: "group", "aria-label": "Filter by signal type" });
    const list = h("div", { class: "signal-list" },
      Array.from({ length: 6 }, () => {
        const bar = h("div", { class: "skeleton" });
        bar.style.width = "60%";
        return h("div", { class: "card stat", "aria-hidden": "true" }, bar);
      }));
    view.append(
      h("div", { class: "toolbar" }, chips),
      h("p", { class: "meta", text: "Scans the most active markets' order books and prices. Strongest first." }),
      list);
    loadSignals(chips, list);
  }

  async function loadSignals(chips, list) {
    const seq = ++state.requestSeq;
    try {
      const rows = await api("/api/signals?limit=40");
      if (seq !== state.requestSeq) return;
      setBanner(state.status?.mode === "sample" ? sampleBanner() : null);

      const counts = {};
      rows.forEach((r) => { counts[r.type] = (counts[r.type] || 0) + 1; });
      if (state.signalType && !counts[state.signalType]) state.signalType = "";
      const chip = (type, label, count) => h("button", {
        class: "chip", type: "button", "aria-pressed": String(state.signalType === type),
        onclick: () => { state.signalType = type; draw(); },
      }, label, h("span", { class: "count", text: count }));

      const draw = () => {
        chips.replaceChildren(chip("", "All", rows.length),
          ...Object.keys(counts).sort((a, b) => counts[b] - counts[a]).map((t) => chip(t, signalLabel(t), counts[t])));
        const shown = rows.filter((r) => !state.signalType || r.type === state.signalType);
        if (!shown.length) {
          list.replaceChildren(h("div", { class: "card empty", text: "No signals detected in the scanned markets." }));
          return;
        }
        list.replaceChildren(...shown.map((r) => {
          const btn = h("button", { class: "signal", type: "button" },
            h("div", null,
              h("div", { class: "signal-type", text: signalLabel(r.type) }),
              h("div", { class: "meta", text: (SIGNALS[r.type] || [, ""])[1] })),
            h("div", null,
              h("div", { class: "q-text", text: r.question }),
              h("div", { class: "signal-desc", text: PRICE_SIGNALS.has(r.type)
                ? `Yes at ${fmt.cents(r.yes_price)}` : `Yes at ${fmt.cents(r.yes_price)} · ${r.desc}` })),
            h("div", { class: "strength" }, meter(r.strength, "Signal strength"),
              h("span", { class: "strength-value", text: fmt.pct(r.strength) })));
          btn.addEventListener("click", () => openMarket(r.market_id, btn));
          return btn;
        }));
      };
      draw();
    } catch (err) {
      if (seq !== state.requestSeq) return;
      if (handleAuthError(err)) return;
      list.replaceChildren(h("div", { class: "card empty", text: "Signals couldn't be loaded." }));
      setBanner(errorBanner(err, () => renderView()));
    }
  }

  // Knowledge

  function renderKnowledge(view) {
    const nav = h("nav", { class: "card kb-topics", "aria-label": "Topics" });
    const body = h("article", { class: "card kb-body" });
    view.append(h("div", { class: "kb" }, nav, body));
    setBanner(null);
    api("/api/topics").then((topics) => {
      if (!topics.includes(state.topic)) state.topic = topics[0];
      const draw = () => {
        nav.replaceChildren(...topics.map((t) => h("button", {
          class: "kb-topic", type: "button", "aria-current": String(t === state.topic),
          onclick: () => { state.topic = t; writeHash(); draw(); },
          text: t.replace(/_/g, " "),
        })));
        loadTopic(body);
      };
      draw();
    }).catch((err) => { if (!handleAuthError(err)) setBanner(errorBanner(err, renderView)); });
  }

  async function loadTopic(body) {
    const topic = state.topic;
    body.replaceChildren(h("h2", { text: topic.replace(/_/g, " ") }), h("div", { class: "skeleton" }));
    try {
      const data = await api("/api/explain/" + encodeURIComponent(topic));
      if (topic !== state.topic) return;
      body.replaceChildren(h("h2", { text: topic.replace(/_/g, " ") }), renderValue(data, 0));
    } catch (err) {
      if (!handleAuthError(err)) body.replaceChildren(h("p", { class: "empty", text: "This topic couldn't be loaded." }));
    }
  }

  function renderValue(v, depth) {
    if (Array.isArray(v)) {
      return h("ul", null, v.map((item) => h("li", null, renderValue(item, depth + 1))));
    }
    if (v && typeof v === "object") {
      if (depth > 4) return h("code", { text: JSON.stringify(v) });
      return h("dl", { class: "kv" }, Object.entries(v).flatMap(([k, val]) => [
        h("dt", { text: k.replace(/_/g, " ") }), h("dd", null, renderValue(val, depth + 1)),
      ]));
    }
    const text = String(v);
    return /^0x[0-9a-fA-F]{40}$/.test(text) || /^(GET|POST|DELETE) \//.test(text) || text.startsWith("/")
      ? h("code", { text }) : document.createTextNode(text);
  }

  // ── Market drawer ────────────────────────────────────────────────────

  let lastFocus = null;
  let drawerSeq = 0;
  let resizeObserver = null;

  function openMarket(id, origin) {
    lastFocus = origin || document.activeElement;
    state.marketId = id;
    writeHash();
    const drawer = $("#drawer");
    $("#scrim").classList.add("open");
    drawer.classList.add("open");
    drawer.focus();
    loadMarket(id);
  }

  function closeMarket() {
    state.marketId = null;
    writeHash();
    $("#scrim").classList.remove("open");
    $("#drawer").classList.remove("open");
    if (resizeObserver) { resizeObserver.disconnect(); resizeObserver = null; }
    if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
  }

  async function loadMarket(id) {
    const seq = ++drawerSeq;
    const body = $("#drawer-body");
    $("#drawer-title").textContent = "Loading market…";
    body.replaceChildren(h("div", { class: "skeleton" }));
    try {
      const d = await api("/api/markets/" + encodeURIComponent(id));
      if (seq !== drawerSeq) return;
      renderMarketDetail(d);
    } catch (err) {
      if (seq !== drawerSeq) return;
      if (handleAuthError(err)) { closeMarket(); return; }
      $("#drawer-title").textContent = "Market unavailable";
      body.replaceChildren(errorBanner(err.status === 404 ? new ApiError(404, "This market wasn't found.") : err,
        () => loadMarket(id)));
    }
  }

  function renderMarketDetail(d) {
    const m = d.market;
    const ob = d.order_book || {};
    $("#drawer-title").textContent = m.question;

    const metaBits = [(m.tags || [])[0] || m.category, m.end_date && "Ends " + fmt.date(m.end_date),
      m.neg_risk && "Multi-outcome (neg-risk)", fmt.usd(m.volume) + " volume"].filter(Boolean);
    const tile = (label, value, note) => h("div", { class: "card stat" },
      h("div", { class: "stat-label", text: label }), h("div", { class: "stat-value", text: value }),
      h("div", { class: "stat-note", text: note || " " }));
    const imb = ob.imbalance;
    const imbNote = imb == null ? "" : Math.abs(imb) < 0.05 ? "balanced" : imb > 0 ? "more bids than asks" : "more asks than bids";

    const body = $("#drawer-body");
    body.replaceChildren(
      h("div", { class: "meta", text: metaBits.join(" · ") }),
      h("div", { class: "stats" },
        tile("Yes price", fmt.cents(m.yes_price), `${fmt.pct(m.yes_price)} implied chance`),
        tile("Spread", ob.spread == null ? "–" : fmt.cents(ob.spread),
          ob.best_bid == null ? "no order book" : `${fmt.cents(ob.best_bid)} bid · ${fmt.cents(ob.best_ask)} ask`),
        tile("Liquidity score", d.liquidity_score == null ? "–" : (d.liquidity_score * 100).toFixed(0) + "/100",
          ob.total_depth == null ? "" : fmt.shares(ob.total_depth) + " shares resting"),
        tile("Book imbalance", imb == null ? "–" : (imb > 0 ? "+" : "") + Math.round(imb * 100) + "%", imbNote)));

    const levels = d.levels || { bids: [], asks: [] };
    if (levels.bids.length || levels.asks.length) {
      const tableBox = h("div", { class: "levels", hidden: true });
      const toggle = h("button", { class: "link-btn", type: "button", "aria-expanded": "false", text: "Show levels" });
      toggle.addEventListener("click", () => {
        tableBox.hidden = !tableBox.hidden;
        toggle.setAttribute("aria-expanded", String(!tableBox.hidden));
        toggle.textContent = tableBox.hidden ? "Show levels" : "Hide levels";
      });
      tableBox.append(levelsTable("Bids", levels.bids), levelsTable("Asks", levels.asks));
      const chartCard = h("div", { class: "card chart-card" });
      body.append(
        h("div", { class: "section-title" }, "Order book depth (Yes token)", h("span", { class: "spacer" }), toggle),
        chartCard, tableBox);
      drawDepth(chartCard, levels, ob.midpoint);
    } else {
      body.append(h("div", { class: "section-title", text: "Order book" }),
        h("div", { class: "card empty", text: "No order book is available for this market." }));
    }

    body.append(h("div", { class: "section-title", text: "Signals" }));
    if (d.signals && d.signals.length) {
      body.append(h("div", { class: "signal-mini" }, d.signals.map((sig) =>
        h("div", { class: "signal" },
          h("div", { title: sig.desc }, h("div", { class: "signal-type", text: signalLabel(sig.type) }),
            h("div", { class: "signal-desc", text: (SIGNALS[sig.type] || [, sig.desc])[1] })),
          h("div", { class: "strength" }, meter(sig.strength, "Signal strength"),
            h("span", { class: "strength-value", text: fmt.pct(sig.strength) }))))));
    } else {
      body.append(h("p", { class: "meta", text: "No signals: spread, depth and price are all within normal ranges." }));
    }

    if (m.description) {
      body.append(h("div", { class: "section-title", text: "Resolution" }), h("p", { class: "desc", text: m.description }));
    }
  }

  function levelsTable(title, rows) {
    return h("div", { class: "card table-wrap" }, h("table", null,
      h("caption", { class: "sr-only", text: title }),
      h("thead", null, h("tr", null,
        h("th", { scope: "col", text: title + " price" }), h("th", { scope: "col", class: "num", text: "Size" }))),
      h("tbody", null, rows.map(([p, sz]) => h("tr", null,
        h("td", { text: fmt.cents(p) }), h("td", { class: "num", text: fmt.shares(sz) }))))));
  }

  // ── Depth chart ──────────────────────────────────────────────────────

  function cumulative(levels) {
    let total = 0;
    return levels.map(([p, sz]) => { total += sz; return [p, total]; });
  }

  function drawDepth(card, levels, midpoint) {
    const bids = cumulative(levels.bids);        // best (highest) first
    const asks = cumulative(levels.asks);        // best (lowest) first
    const tooltip = h("div", { class: "tooltip", hidden: true });
    const legend = h("div", { class: "legend", "aria-hidden": "true" },
      h("span", null, h("span", { class: "legend-key bid" }), "Bids (buy Yes)"),
      h("span", null, h("span", { class: "legend-key ask" }), "Asks (sell Yes)"));
    const svgEl = s("svg", { class: "depth-svg", role: "img" });
    card.replaceChildren(legend, svgEl, tooltip);

    const bidTotal = bids.length ? bids[bids.length - 1][1] : 0;
    const askTotal = asks.length ? asks[asks.length - 1][1] : 0;
    svgEl.setAttribute("aria-label",
      `Order book depth. ${fmt.shares(bidTotal)} shares bid from ${fmt.cents(bids[0]?.[0])} down; ` +
      `${fmt.shares(askTotal)} shares offered from ${fmt.cents(asks[0]?.[0])} up. Use "Show levels" for the full table.`);

    const prices = [...levels.bids, ...levels.asks].map((l) => l[0]);
    const span = Math.max(...prices) - Math.min(...prices) || 0.1;
    const x0 = Math.max(0, Math.min(...prices) - span * 0.04);
    const x1 = Math.min(1, Math.max(...prices) + span * 0.04);
    const yMax = niceMax(Math.max(bidTotal, askTotal) * 1.08);

    const render = () => {
      const W = card.clientWidth - 28;
      const H = 220;
      const m = { l: 46, r: 10, t: 14, b: 24 };
      if (W <= 0) return;
      svgEl.setAttribute("viewBox", `0 0 ${W} ${H}`);
      svgEl.replaceChildren();
      const X = (p) => m.l + ((p - x0) / (x1 - x0)) * (W - m.l - m.r);
      const Y = (v) => H - m.b - (v / yMax) * (H - m.t - m.b);

      for (let i = 0; i <= 4; i++) {
        const v = (yMax / 4) * i;
        svgEl.append(s("line", { class: i === 0 ? "baseline" : "grid", x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }));
        svgEl.append(s("text", { class: "tick", x: m.l - 6, y: Y(v) + 4, "text-anchor": "end", text: compact.format(v) }));
      }
      const ticks = 5;
      for (let i = 0; i <= ticks; i++) {
        const p = x0 + ((x1 - x0) / ticks) * i;
        svgEl.append(s("text", { class: "tick", x: X(p), y: H - 6, "text-anchor": "middle", text: fmt.cents(p) }));
      }

      const stepPath = (pts, dir) => {
        if (!pts.length) return "";
        let d = `M${X(pts[0][0])},${Y(0)} L${X(pts[0][0])},${Y(pts[0][1])}`;
        for (let i = 1; i < pts.length; i++) d += ` L${X(pts[i][0])},${Y(pts[i - 1][1])} L${X(pts[i][0])},${Y(pts[i][1])}`;
        const edge = dir < 0 ? x0 : x1;
        return d + ` L${X(edge)},${Y(pts[pts.length - 1][1])}`;
      };
      const close = (d, pts, dir) => d && `${d} L${X(dir < 0 ? x0 : x1)},${Y(0)} Z`;

      const bidLine = stepPath(bids, -1);
      const askLine = stepPath(asks, 1);
      if (bidLine) svgEl.append(s("path", { class: "area-bid", d: close(bidLine, bids, -1) }), s("path", { class: "line-bid", d: bidLine }));
      if (askLine) svgEl.append(s("path", { class: "area-ask", d: close(askLine, asks, 1) }), s("path", { class: "line-ask", d: askLine }));

      if (midpoint != null) {
        svgEl.append(s("line", { class: "mid", x1: X(midpoint), x2: X(midpoint), y1: m.t, y2: Y(0) }));
        svgEl.append(s("text", { class: "mid-label", x: X(midpoint), y: m.t - 3, "text-anchor": "middle", text: "Mid " + fmt.cents(midpoint) }));
      }
      if (bids.length) svgEl.append(s("text", { class: "direct-label", x: X(x0) + 6, y: Math.max(Y(bidTotal) - 6, m.t + 10), text: "Bids" }));
      if (asks.length) svgEl.append(s("text", { class: "direct-label", x: X(x1) - 6, y: Math.max(Y(askTotal) - 6, m.t + 10), "text-anchor": "end", text: "Asks" }));

      const cross = s("line", { class: "crosshair", y1: m.t, y2: Y(0), visibility: "hidden" });
      const dot = s("circle", { class: "hover-dot", r: 5, visibility: "hidden" });
      const hit = s("rect", { x: m.l, y: 0, width: W - m.l - m.r, height: H, fill: "transparent" });
      svgEl.append(cross, dot, hit);

      const hide = () => { cross.setAttribute("visibility", "hidden"); dot.setAttribute("visibility", "hidden"); tooltip.hidden = true; };
      const move = (evt) => {
        const rect = svgEl.getBoundingClientRect();
        const px = ((evt.clientX - rect.left) / rect.width) * W;
        const price = x0 + ((px - m.l) / (W - m.l - m.r)) * (x1 - x0);
        // Snap to the deepest real level the pointer has reached on that side.
        let side = null, depth = 0, level = price;
        if (bids.length && price <= bids[0][0]) {
          side = "bid";
          for (const [p, c] of bids) { if (p >= price) { depth = c; level = p; } else break; }
        } else if (asks.length && price >= asks[0][0]) {
          side = "ask";
          for (const [p, c] of asks) { if (p <= price) { depth = c; level = p; } else break; }
        }
        const x = X(Math.max(x0, Math.min(x1, price)));
        cross.setAttribute("x1", x); cross.setAttribute("x2", x); cross.setAttribute("visibility", "visible");
        const rows = [];
        if (side) {
          dot.setAttribute("cx", x); dot.setAttribute("cy", Y(depth));
          dot.setAttribute("fill", getComputedStyle(svgEl).getPropertyValue(side === "bid" ? "--series-bid" : "--series-ask"));
          dot.setAttribute("visibility", "visible");
          rows.push(h("div", { class: "tt-head" }, h("span", { class: "legend-key " + side }),
            side === "bid" ? `Bids at ${fmt.cents(level)} or more` : `Asks at ${fmt.cents(level)} or less`));
          rows.push(h("div", { class: "tt-row", text: `${fmt.shares(depth)} shares cumulative` }));
        } else {
          dot.setAttribute("visibility", "hidden");
          rows.push(h("div", { class: "tt-head", text: fmt.cents(price) }), h("div", { class: "tt-row", text: "Inside the spread: no resting orders" }));
        }
        tooltip.replaceChildren(...rows);
        tooltip.hidden = false;
        const cardRect = card.getBoundingClientRect();
        const left = Math.max(90, Math.min(cardRect.width - 90, evt.clientX - cardRect.left));
        tooltip.style.left = left + "px";
        tooltip.style.top = (rect.top - cardRect.top) + (side ? Y(depth) : m.t + 30) / H * rect.height + "px";
      };
      hit.addEventListener("pointermove", move);
      hit.addEventListener("pointerdown", move);
      hit.addEventListener("pointerleave", hide);
    };

    render();
    if (resizeObserver) resizeObserver.disconnect();
    resizeObserver = new ResizeObserver(() => render());
    resizeObserver.observe(card);
  }

  function niceMax(v) {
    if (v <= 0) return 1;
    const pow = Math.pow(10, Math.floor(Math.log10(v)));
    const n = v / pow;
    return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * pow;
  }

  // ── Auth ─────────────────────────────────────────────────────────────

  function handleAuthError(err) {
    if (err.status !== 401) return false;
    state.token = null;
    store.set("sessionStorage", "ms-masa-token", null);
    renderLogin(!!err.hadToken);
    return true;
  }

  function renderLogin(failed) {
    setBanner(null);
    $("#mode-badge").hidden = true;
    const input = h("input", { class: "field", type: "password", autocomplete: "current-password",
      placeholder: "Access token", "aria-label": "Access token", required: true });
    const error = h("p", { class: "banner error", role: "alert", hidden: !failed, text: "That token wasn't accepted." });
    const form = h("form", null, input, h("button", { class: "primary-btn", type: "submit", text: "Continue" }));
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      state.token = input.value.trim();
      try {
        await boot();
        store.set("sessionStorage", "ms-masa-token", state.token);
      } catch { /* boot shows its own error */ }
    });
    $("#view").replaceChildren(h("div", { class: "card login" },
      h("h1", { text: "This dashboard is protected" }),
      h("p", { text: "Enter the access token configured on the server (MS_MASA_AUTH_TOKEN). It's kept for this browser tab only." }),
      error, form));
    input.focus();
  }

  // ── Boot ─────────────────────────────────────────────────────────────

  async function boot() {
    const hadToken = !!state.token;
    try {
      state.status = await api("/api/status");
    } catch (err) {
      err.hadToken = hadToken;
      if (handleAuthError(err)) throw err;
      setBanner(errorBanner(err, () => boot().catch(() => {})));
      throw err;
    }
    renderBadge();
    const route = parseHash();
    state.tab = route.tab;
    if (route.tab === "knowledge" && route.sub) state.topic = route.sub;
    selectTab(state.tab);
    if (route.market) openMarket(route.market);
  }

  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => selectTab(b.dataset.tab)));
  $("#refresh-btn").addEventListener("click", () => {
    renderView();
    if (state.marketId) loadMarket(state.marketId);
  });
  let theme = store.get("localStorage", "ms-masa-theme") || "system";
  applyTheme(theme);
  $("#theme-btn").addEventListener("click", () => {
    theme = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length];
    store.set("localStorage", "ms-masa-theme", theme);
    applyTheme(theme);
  });
  $("#scrim").addEventListener("click", closeMarket);
  $("#drawer-close").addEventListener("click", closeMarket);
  document.addEventListener("keydown", (e) => {
    if (!state.marketId) return;
    if (e.key === "Escape") closeMarket();
    if (e.key === "Tab") {
      const focusables = [...$("#drawer").querySelectorAll("button, [href], input, [tabindex]:not([tabindex='-1'])")]
        .filter((el) => !el.closest("[hidden]"));
      if (!focusables.length) return;
      const first = focusables[0], last = focusables[focusables.length - 1];
      if (e.shiftKey && (document.activeElement === first || document.activeElement === $("#drawer"))) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  boot().catch(() => {});
})();
