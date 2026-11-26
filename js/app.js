// UI controller. All clinical state lives in the in-memory `state` object only:
// no cookies, no localStorage/sessionStorage/IndexedDB, nothing in the URL.
import * as E from "./engine.js";
import { STRINGS, KIND_LABELS } from "./i18n.js";

const state = {
  data: null,
  lang: "pt",
  screen: "home", // home | flow
  query: "",
  protocol: null,
  session: null,
  depth: 0, // history depth (no clinical data in history entries)
};

const app = document.getElementById("app");
const t = (k, ...a) => {
  const v = STRINGS[state.lang][k];
  return typeof v === "function" ? v(...a) : v;
};

/* ---------- tiny DOM helper (no innerHTML with data) ---------- */
function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "style") Object.entries(v).forEach(([prop, val]) => el.style.setProperty(prop, val)); // CSSOM: CSP-safe
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, "");
    else el.setAttribute(k, v);
  }
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (el.hidden = true), 2600);
}

const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

/* ---------- navigation ---------- */
function push() {
  state.depth += 1;
  history.pushState({ d: state.depth }, "");
}

function openProtocol(p) {
  state.protocol = p;
  state.session = E.createSession(p);
  state.screen = "flow";
  push();
  render();
}

function choose(optionId) {
  state.session = E.choose(state.protocol, state.session, optionId);
  push();
  render();
}

function chooseAllergy(v) {
  state.session = E.setAllergy(state.session, v);
  push();
  render();
}

function goBack() {
  if (state.screen !== "flow") return;
  const s = state.session;
  if (s.steps.length === 0 && s.allergy === null) return goHome();
  state.session = E.back(state.protocol, s);
  render();
}

function jumpTo(index) {
  const s = state.session;
  state.session = index >= s.steps.length ? E.setAllergy(s, null) : E.back(state.protocol, s, index);
  push();
  render();
}

function goHome() {
  state.screen = "home";
  state.protocol = null;
  state.session = null;
  render();
}

/** Reset / New patient: wipe all clinical state immediately. */
function resetAll() {
  state.protocol = null;
  state.session = null;
  state.query = "";
  state.screen = "home";
  state.depth = 0;
  history.replaceState({ d: 0 }, "");
  render();
  toast(t("resetConfirmed"));
}

window.addEventListener("popstate", () => {
  if (state.screen === "flow") goBack();
});

/* ---------- shared pieces ---------- */
function topBar() {
  return h("header", { class: "topbar" },
    h("button", { class: "icon-btn", type: "button", onclick: () => history.back(), "aria-label": t("back") },
      h("span", { "aria-hidden": "true" }, "←"), h("span", { class: "btn-label" }, t("back"))),
    h("div", { class: "topbar-title" },
      h("span", { class: "topbar-code" }, state.protocol.code),
      h("span", { class: "topbar-name" }, state.protocol.title)),
    h("button", { class: "icon-btn reset", type: "button", onclick: resetAll },
      h("span", { "aria-hidden": "true" }, "⟲"), h("span", { class: "btn-label" }, t("reset"))));
}

function progressBar() {
  const p = E.progress(state.protocol, state.session);
  const pct = Math.round(p.ratio * 100);
  return h("div", { class: "progress-wrap" },
    h("div", { class: "progress", role: "progressbar", "aria-valuemin": "0", "aria-valuemax": "100", "aria-valuenow": String(pct), "aria-label": t("step", Math.min(p.done + 1, p.total), p.total) },
      h("div", { class: "progress-fill", style: { width: `${pct}%` } })),
    h("div", { class: "progress-label" }, E.isComplete(state.protocol, state.session) ? t("recommendation") : t("step", p.done + 1, p.total)));
}

function crumbBar() {
  const cs = E.crumbs(state.protocol, state.session);
  if (!cs.length) return null;
  return h("nav", { class: "crumbs", "aria-label": t("yourAnswers") },
    h("ol", {}, cs.map((c) => h("li", {},
      h("button", { type: "button", class: "chip", title: `${c.question} — ${t("editHint")}`, onclick: () => jumpTo(c.index) }, c.label)))));
}

function definitionBlocks(refs, open) {
  return (refs || []).map((ref) => {
    const d = state.protocol.definitions[ref];
    if (!d) return null;
    return h("details", { class: "def", open: open && d.items.length <= 9 },
      h("summary", {}, d.label),
      h("ul", {}, d.items.map((i) => h("li", {}, i))),
      h("p", { class: "src" }, `${state.protocol.code} · ${d.source.section}${d.source.page ? ` · ${t("page")} ${d.source.page}` : ""}`));
  });
}

/* ---------- screens ---------- */
function renderHome() {
  const q = norm(state.query);
  const list = state.data.protocols.filter((p) => !q || norm([p.title, p.titleEn, p.code, ...(p.keywords || [])].join(" ")).includes(q));
  const grid = h("ul", { class: "grid", id: "grid" },
    list.length ? list.map((p) => h("li", {},
      h("button", { type: "button", class: "card proto", onclick: () => openProtocol(p) },
        h("span", { class: "proto-title" }, p.title),
        state.lang === "en" ? h("span", { class: "proto-en" }, p.titleEn) : null,
        h("span", { class: "proto-code" }, `${p.code} · ${p.edition}`))))
      : h("li", { class: "empty" }, t("noResults")));

  const search = h("input", {
    type: "search", class: "search", placeholder: t("search"), "aria-label": t("searchLabel"),
    value: state.query, autocomplete: "off", autocorrect: "off", spellcheck: "false",
    oninput: (e) => { state.query = e.target.value; const g = renderHome().querySelector("#grid"); document.getElementById("grid").replaceWith(g); },
  });

  return h("div", { class: "home" },
    h("header", { class: "brand" },
      h("div", { class: "brand-row" },
        h("picture", { class: "logo" },
          h("source", { srcset: "assets/logo-ulssj-branco.png", media: "(prefers-color-scheme: dark)" }),
          h("img", { src: "assets/logo-ulssj.png", alt: "ULS São João — Cuidados de Saúde Primários", width: "1200", height: "398" })),
        h("button", { type: "button", class: "lang", "aria-label": t("langLabel"), onclick: toggleLang }, t("lang"))),
      h("h1", { tabindex: "-1" }, t("appTitle")),
      h("p", { class: "subtitle" }, t("appSubtitle"))),
    h("main", { class: "content" }, search, grid));
}

function renderQuestion() {
  const p = state.protocol;
  const n = E.node(p, state.session.current);
  const intro = state.session.steps.length === 0 && (p.intro || []).length
    ? h("div", { class: "intro" }, p.intro.map((x) => h("p", {}, x.text))) : null;
  return h("main", { class: "content flow" },
    intro,
    h("h2", { class: "prompt", tabindex: "-1" }, n.prompt),
    n.help ? h("p", { class: "help" }, n.help) : null,
    definitionBlocks(n.definitionRefs, true),
    h("div", { class: "options", role: "group", "aria-label": n.prompt },
      n.options.map((o) => h("button", { type: "button", class: "option", onclick: () => choose(o.id) }, o.label))));
}

function renderAllergyQuestion() {
  const p = state.protocol;
  return h("main", { class: "content flow" },
    h("h2", { class: "prompt", tabindex: "-1" }, p.allergyQuestion.prompt),
    h("div", { class: "options", role: "group" },
      h("button", { type: "button", class: "option", onclick: () => chooseAllergy("sim") }, "Sim"),
      h("button", { type: "button", class: "option", onclick: () => chooseAllergy("nao") }, "Não")));
}

function regimenCard(r) {
  const ns = h("abbr", { title: t("notStatedLegend") }, t("notStated"));
  const rows = (r.drugs || []).map((d) => h("tr", {},
    h("th", { scope: "row" }, d.drug, d.note ? h("span", { class: "drug-note" }, ` (${d.note})`) : null),
    h("td", {}, d.dose || ns.cloneNode(true)),
    h("td", {}, d.route || ns.cloneNode(true)),
    h("td", {}, d.interval || ns.cloneNode(true))));
  return h("div", { class: "regimen" },
    r.label ? h("p", { class: "reg-label" }, r.label) : null,
    rows.length ? h("div", { class: "table-wrap" }, h("table", {},
      h("thead", {}, h("tr", {}, h("th", { scope: "col" }, t("drug")), h("th", { scope: "col" }, t("dose")), h("th", { scope: "col" }, t("route")), h("th", { scope: "col" }, t("interval")))),
      h("tbody", {}, rows))) : null,
    h("p", { class: "verbatim" }, h("span", { class: "vb-label" }, `${t("protocolText")}: `), r.verbatim));
}

function regimenSection(title, list, cls) {
  if (!list || !list.length) return null;
  return h("section", { class: `card ${cls}` }, h("h3", {}, title), list.map(regimenCard));
}

function renderResult() {
  const p = state.protocol;
  const res = E.resolve(p, state.session);
  const kinds = E.NOTE_ORDER.filter((k) => res.notes[k] && res.notes[k].length);

  const head = h("section", { class: `card verdict ${res.antibiotherapy ? "atb" : "no-atb"}` },
    h("p", { class: "eyebrow" }, res.antibiotherapy ? t("recommendation") : t("noAtb")),
    h("h2", { tabindex: "-1" }, res.title));

  const primary = res.antibiotherapy
    ? regimenSection(res.allergic ? t("allergyPrimary") : t("firstLine"), res.primary, res.allergic ? "primary allergy" : "primary")
    : null;

  const other = res.other && res.other.length
    ? h("details", { class: "card other" },
        h("summary", {}, res.otherKind === "allergy" ? t("allergyRegimen") : t("nonAllergy")),
        res.other.map(regimenCard))
    : null;

  // Key sections stay open; secondary ones are collapsible to keep the screen scannable.
  const OPEN = new Set(["warning", "duration", "microbiology"]);
  const noteItems = (k) => res.notes[k].map((n) => h("div", { class: "note-item" },
    h("p", {}, n.text),
    h("p", { class: "src" }, `${n.source.section}${n.source.page ? ` · ${t("page")} ${n.source.page}` : ""}`)));
  const notes = kinds.map((k) => OPEN.has(k)
    ? h("section", { class: `card note note-${k}` }, h("h3", {}, KIND_LABELS[state.lang][k] || k), noteItems(k))
    : h("details", { class: `card note note-${k}` }, h("summary", {}, KIND_LABELS[state.lang][k] || k), noteItems(k)));

  const sources = h("details", { class: "card sources" },
    h("summary", {}, t("sources")),
    h("dl", {},
      h("dt", {}, t("sourceFile")), h("dd", {}, `${p.code} — ${p.title}`),
      h("dt", {}, t("edition")), h("dd", {}, `${p.edition} (aprovação ${p.approved})`)),
    h("ul", {}, res.sources.map((s) => h("li", {},
      h("strong", {}, s.section), s.page ? ` · ${t("page")} ${s.page}` : "", s.element ? ` · ${s.element}` : ""))));

  return h("main", { class: "content flow result" },
    res.pending ? h("p", { class: "pending", role: "alert" }, t("pending")) : null,
    head,
    primary,
    regimenSection(t("addOns"), res.addOns, "addons"),
    regimenSection(t("alternatives"), res.secondary, "alternatives"),
    other,
    notes,
    sources,
    h("div", { class: "actions" },
      h("button", { type: "button", class: "btn primary", onclick: copyRegimen }, t("copy")),
      h("button", { type: "button", class: "btn", onclick: resetAll }, t("reset"))));
}

async function copyRegimen() {
  const text = E.clipboardText(state.protocol, state.session);
  try {
    await navigator.clipboard.writeText(text);
    toast(t("copied"));
  } catch {
    const ta = h("textarea", { class: "sr-only", readonly: true });
    ta.value = text;
    document.body.append(ta);
    ta.select();
    const ok = document.execCommand && document.execCommand("copy");
    ta.remove();
    toast(ok ? t("copied") : t("copyFail"));
  }
}

function toggleLang() {
  state.lang = state.lang === "pt" ? "en" : "pt";
  document.documentElement.lang = state.lang === "pt" ? "pt-PT" : "en";
  render();
}

function footer() {
  return h("footer", { class: "footer" },
    h("p", { class: "disclaimer" }, t("disclaimerShort")),
    h("p", { class: "meta" }, `${t("protocolsVersion")} · ${t("privacy")}`),
    h("p", { class: "meta" }, "Unidade Local de Saúde São João"));
}

function render() {
  const frag = [];
  if (state.screen === "home") {
    frag.push(renderHome());
  } else {
    frag.push(topBar(), progressBar(), crumbBar());
    if (!E.atResult(state.protocol, state.session)) frag.push(renderQuestion());
    else if (E.needsAllergyAnswer(state.protocol, state.session)) frag.push(renderAllergyQuestion());
    else frag.push(renderResult());
  }
  frag.push(footer());
  app.replaceChildren(...frag.filter(Boolean));
  const focusTarget = app.querySelector(state.screen === "home" ? "h1" : "h2");
  if (focusTarget && state.depth > 0) focusTarget.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}

/* ---------- disclaimer + boot ---------- */
function showDisclaimer() {
  const dlg = document.getElementById("disclaimer");
  dlg.querySelector("h2").textContent = t("disclaimerTitle");
  dlg.querySelector("p").textContent = t("disclaimer");
  dlg.querySelector("button").textContent = t("accept");
  if (typeof dlg.showModal === "function") dlg.showModal();
  else dlg.setAttribute("open", "");
  dlg.addEventListener("cancel", (e) => e.preventDefault()); // must be acknowledged
}

async function boot() {
  history.replaceState({ d: 0 }, "");
  try {
    const res = await fetch("data/protocols.json", { cache: "no-cache" });
    state.data = await res.json();
  } catch (e) {
    app.replaceChildren(h("main", { class: "content" }, h("p", { class: "pending" }, "Erro a carregar data/protocols.json")));
    return;
  }
  render();
  showDisclaimer();

  if ("serviceWorker" in navigator) {
    const hadController = Boolean(navigator.serviceWorker.controller);
    navigator.serviceWorker.register("./sw.js").catch(() => {});
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (!hadController) return; // first install: nothing to refresh
      const bar = document.getElementById("update");
      bar.querySelector("span").textContent = t("updateReady");
      bar.querySelector("button").textContent = t("reload");
      bar.hidden = false;
    });
  }
}

document.getElementById("update-btn").addEventListener("click", () => location.reload());
document.getElementById("disclaimer-ok").addEventListener("click", () => document.getElementById("disclaimer").close());
boot();
