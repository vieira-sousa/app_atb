/**
 * Decision engine for data/protocols.json.
 * Pure functions, no DOM, no storage — imported by the UI (js/app.js) and by tools/test_engine.mjs.
 *
 * Session shape (immutable, in-memory only):
 *   { protocolId, steps: [{ nodeId, optionId }], current: nodeId, allergy: null | "sim" | "nao" }
 */

export const NOTE_ORDER = [
  "warning", "duration", "microbiology", "source_control", "oral",
  "deescalation", "followup", "renal", "info",
];

export function createSession(protocol) {
  return { protocolId: protocol.id, steps: [], current: protocol.start, allergy: null };
}

export function node(protocol, nodeId) {
  const n = protocol.nodes[nodeId];
  if (!n) throw new Error(`Unknown node ${nodeId} in ${protocol.id}`);
  return n;
}

export function answerKey(protocol, nodeId) {
  return protocol.nodes[nodeId].answerKey || nodeId;
}

/** Map answerKey -> optionId for the answers given so far. */
export function answers(protocol, session) {
  const a = {};
  for (const s of session.steps) a[answerKey(protocol, s.nodeId)] = s.optionId;
  return a;
}

export function choose(protocol, session, optionId) {
  const n = node(protocol, session.current);
  if (n.type !== "question") throw new Error("Current node is not a question");
  const opt = n.options.find((o) => o.id === optionId);
  if (!opt) throw new Error(`Option ${optionId} not in ${session.current}`);
  return {
    ...session,
    steps: [...session.steps, { nodeId: session.current, optionId }],
    current: opt.next,
    allergy: null,
  };
}

/** Go back to step index `i` (0 = first question). Default: one step back. */
export function back(protocol, session, i) {
  if (session.allergy !== null && i === undefined) return { ...session, allergy: null };
  const idx = i === undefined ? session.steps.length - 1 : i;
  if (idx < 0) return session;
  const target = session.steps[idx];
  if (!target) return session;
  return { ...session, steps: session.steps.slice(0, idx), current: target.nodeId, allergy: null };
}

export function setAllergy(session, value) {
  return { ...session, allergy: value };
}

export function atResult(protocol, session) {
  return node(protocol, session.current).type === "result";
}

export function needsAllergyAnswer(protocol, session) {
  if (!atResult(protocol, session)) return false;
  const r = node(protocol, session.current);
  return Boolean(r.antibiotherapy && protocol.allergyQuestion && (r.allergy || []).length && session.allergy === null);
}

export function isComplete(protocol, session) {
  return atResult(protocol, session) && !needsAllergyAnswer(protocol, session);
}

export function matches(item, ans) {
  if (!item || !item.when) return true;
  return Object.entries(item.when).every(([k, v]) => (Array.isArray(v) ? v : [v]).includes(ans[k]));
}

const filt = (list, ans) => (list || []).filter((x) => matches(x, ans));

/** Longest remaining number of questions from nodeId (for the progress bar). */
export function maxRemaining(protocol, nodeId, memo = {}) {
  if (nodeId in memo) return memo[nodeId];
  const n = protocol.nodes[nodeId];
  let v;
  if (n.type === "result") {
    v = n.antibiotherapy && protocol.allergyQuestion && (n.allergy || []).length ? 1 : 0;
  } else {
    v = 1 + Math.max(...n.options.map((o) => maxRemaining(protocol, o.next, memo)));
  }
  memo[nodeId] = v;
  return v;
}

export function progress(protocol, session) {
  const done = session.steps.length + (session.allergy !== null ? 1 : 0);
  const remaining = isComplete(protocol, session) ? 0 : maxRemaining(protocol, session.current) - (session.allergy !== null ? 1 : 0);
  const total = done + Math.max(0, remaining);
  return { done, total, ratio: total ? done / total : 1 };
}

export function crumbs(protocol, session) {
  const out = session.steps.map((s, i) => {
    const q = node(protocol, s.nodeId);
    const o = q.options.find((x) => x.id === s.optionId);
    return { index: i, nodeId: s.nodeId, label: o.crumb || o.label, question: q.prompt };
  });
  if (session.allergy !== null) {
    out.push({ index: session.steps.length, nodeId: "__allergy", label: session.allergy === "sim" ? "Alergia a β-lactâmicos" : "Sem alergia a β-lactâmicos", question: protocol.allergyQuestion.prompt });
  }
  return out;
}

/** Resolve the recommendation for a completed session. */
export function resolve(protocol, session) {
  const r = node(protocol, session.current);
  const ans = answers(protocol, session);
  const allergic = session.allergy === "sim";
  const firstLine = filt(r.firstLine, ans);
  const allergy = filt(r.allergy, ans);
  const alternatives = filt(r.alternatives, ans);
  const addOns = filt(allergic ? r.allergyAddOns || [] : r.addOns, ans);
  const notes = [...filt(r.duration, ans), ...filt(r.notes, ans)];
  const grouped = {};
  for (const n of notes) (grouped[n.kind || "info"] ||= []).push(n);
  const sources = [];
  const seen = new Set();
  const addSrc = (s, ctx) => {
    if (!s) return;
    const k = `${s.section}|${s.page}|${s.element || ""}`;
    if (seen.has(k)) return;
    seen.add(k);
    sources.push({ ...s, context: ctx });
  };
  session.steps.forEach((s) => addSrc(node(protocol, s.nodeId).source, node(protocol, s.nodeId).prompt));
  (r.source || []).forEach((s) => addSrc(s, r.title));
  [...firstLine, ...allergy, ...alternatives, ...addOns].forEach((x) => addSrc(x.source, x.label || x.verbatim));
  return {
    result: r,
    title: r.title,
    antibiotherapy: Boolean(r.antibiotherapy),
    pending: Boolean(r.pending),
    allergic,
    primary: allergic ? allergy : firstLine,
    primaryKind: allergic ? "allergy" : "firstLine",
    secondary: allergic ? [] : alternatives,
    other: allergic ? firstLine : allergy,
    otherKind: allergic ? "firstLine" : "allergy",
    addOns,
    notes: grouped,
    sources,
    crumbs: crumbs(protocol, session),
  };
}

const KIND_LABEL_PT = {
  warning: "Alertas", microbiology: "Colheitas microbiológicas", duration: "Duração",
  source_control: "Controlo de foco", oral: "Transição para via oral", deescalation: "Terapêutica dirigida / de-escalação",
  followup: "Seguimento", renal: "Função renal", info: "Notas",
};
export const kindLabelPt = (k) => KIND_LABEL_PT[k] || k;

/** Plain-text summary for clinical notes. Contains no patient identifiers. */
export function clipboardText(protocol, session) {
  const res = resolve(protocol, session);
  const L = [];
  L.push(`Antibioterapia empírica — ${protocol.title} (${protocol.code}, ${protocol.edition})`);
  L.push(`Critérios: ${res.crumbs.map((c) => c.label).join("; ")}`);
  if (!res.antibiotherapy) {
    L.push(`Recomendação: ${res.title}`);
  } else {
    L.push(res.allergic ? "Esquema (alergia a β-lactâmicos):" : "Esquema de 1.ª linha:");
    res.primary.forEach((x) => L.push(`- ${x.verbatim}`));
    if (res.addOns.length) {
      L.push("Considerar associar:");
      res.addOns.forEach((x) => L.push(`- ${x.verbatim}`));
    }
  }
  (res.notes.duration || []).forEach((n, i) => L.push(`${i ? "  " : "Duração: "}${n.text}`));
  const regSrc = [...new Set(res.primary.map((x) => `${x.source.section}${x.source.page ? `, p. ${x.source.page}` : ""}`))];
  L.push(`Fonte: ${protocol.code}${regSrc.length ? ` — ${regSrc.join("; ")}` : ""}`);
  L.push("Apoio à decisão baseado em protocolo institucional ULS São João; não substitui o juízo clínico.");
  return L.join("\n");
}
