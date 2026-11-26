// Exhaustive path test through the real engine (js/engine.js).
// For every protocol: enumerates every answer combination (incl. allergy yes/no) and asserts
//  - each path terminates in a result node,
//  - every result node is reached,
//  - antibiotherapy results always yield >=1 primary regimen for both allergy states
//    (an explicit "A discutir caso a caso" entry counts),
//  - every regimen carries a source with section + page,
//  - back() from the result returns to the previous question,
//  - clipboard text contains protocol code + disclaimer and no undefined/NaN.
// Usage: node tools/test_engine.mjs
import { readFileSync } from "node:fs";
import * as E from "../js/engine.js";

const data = JSON.parse(readFileSync(new URL("../data/protocols.json", import.meta.url), "utf8"));
let failures = 0;
let paths = 0;
const fail = (m) => { failures++; console.error("FAIL", m); };

for (const p of data.protocols) {
  const reached = new Set();
  const walk = (s) => {
    const n = E.node(p, s.current);
    if (n.type === "question") {
      for (const o of n.options) walk(E.choose(p, s, o.id));
      return;
    }
    reached.add(s.current);
    const allergyStates = E.needsAllergyAnswer(p, s) ? ["nao", "sim"] : [null];
    for (const a of allergyStates) {
      const fin = a ? E.setAllergy(s, a) : s;
      paths++;
      const label = `${p.id}: ${E.crumbs(p, fin).map((c) => c.label).join(" > ")}`;
      if (!E.isComplete(p, fin)) fail(`${label}: not complete`);
      const r = E.resolve(p, fin);
      if (r.antibiotherapy && r.primary.length === 0) fail(`${label}: no primary regimen`);
      for (const x of [...r.primary, ...r.addOns, ...r.secondary, ...r.other]) {
        if (!x.source || !x.source.section || !("page" in x.source)) fail(`${label}: regimen without source`);
        if (!x.verbatim) fail(`${label}: regimen without verbatim text`);
      }
      const txt = E.clipboardText(p, fin);
      if (!txt.includes(p.code) || !txt.includes("não substitui o juízo clínico") || /undefined|NaN|\[object/.test(txt)) {
        fail(`${label}: bad clipboard text`);
      }
      const prog = E.progress(p, fin);
      if (prog.ratio !== 1) fail(`${label}: progress at result is ${prog.ratio}`);
      const b = E.back(p, fin);
      if (a) { if (b.allergy !== null || b.current !== fin.current) fail(`${label}: back from allergy`); }
      else if (fin.steps.length && E.node(p, b.current).type !== "question") fail(`${label}: back did not return to a question`);
    }
  };
  walk(E.createSession(p));
  for (const [id, n] of Object.entries(p.nodes)) {
    if (n.type === "result" && !reached.has(id)) fail(`${p.id}: result ${id} never reached`);
  }
}

console.log(`${data.protocols.length} protocols, ${paths} complete paths (incl. allergy variants) tested.`);
console.log(failures ? `${failures} failure(s)` : "All engine path tests passed.");
process.exit(failures ? 1 : 0);
