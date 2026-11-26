# ATB Cirurgia · ULS São João

Offline-first PWA for **empirical antibiotic therapy in General Surgery**. It is built only from the 7 institutional Clinical Protocols (PAC173–PAC179, Março 2026) of the Unidade Local de Saúde São João.

> Decision-support tool. It does not replace clinical judgement.

## Protocols
| Code | Protocol |
|---|---|
| ULSSJ-PAC176-0 | Abordagem terapêutica da apendicite aguda |
| ULSSJ-PAC178-0 | Abordagem farmacológica da diverticulite aguda |
| ULSSJ-PAC177-0 | Antibioterapia na colecistite aguda |
| ULSSJ-PAC175-0 | Antibioterapia nas infeções das vias biliares |
| ULSSJ-PAC174-0 | Antibioterapia na infeção associada à pancreatite aguda |
| ULSSJ-PAC179-0 | Antibioterapia na úlcera gastroduodenal perfurada |
| ULSSJ-PAC173-0 | Abordagem terapêutica do abcesso anorretal |

## Design constraints
- **No backend, no stored data.** All clinical state is held in memory. There are no cookies, no localStorage/sessionStorage/IndexedDB, and no answers in the URL. "Novo doente" wipes the state immediately. A strict Content-Security-Policy allows only same-origin resources.
- **Offline.** `sw.js` precaches the app shell and `data/protocols.json` using relative paths, so it works under `https://<user>.github.io/<repo>/`.
- **Branding.** Colours, typeface and logo come from `docs/branding/` (Manual de Normas ULS São João). The main logo is used unmodified, at a size that keeps the symbol at 13 mm or more.

## Structure
```
index.html, manifest.json, sw.js
css/styles.css
js/engine.js        pure decision engine (also used by tests)
js/app.js           UI controller
js/i18n.js          PT/EN UI strings (clinical content stays PT-PT)
data/protocols.json decision trees, regimens, notes, source references
assets/             logo + PWA icons
CLINICAL_AUDIT.md   extraction audit, discrepancies and clinical decisions
tools/              builder + validators
```

## Editing clinical content
`data/protocols.json` is generated. Edit `tools/build_protocols.py`, then run:
```bash
python3 tools/build_protocols.py
```
```bash
python3 tools/validate_protocols.py
```
```bash
python3 tools/check_fidelity.py
```
```bash
node tools/test_engine.mjs
```
Record every clinical decision that departs from the PDF wording in `CLINICAL_AUDIT.md` §10.

## Run locally
```bash
python3 -m http.server 8000
```
Then open http://localhost:8000/.

## Deploy
`.github/workflows/pages.yml` runs all validators on every PR and push. On `main` it deploys to GitHub Pages; set Settings → Pages → Source to **GitHub Actions**.
