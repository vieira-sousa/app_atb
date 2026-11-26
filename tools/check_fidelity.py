#!/usr/bin/env python3
"""
Fidelity check: every regimen / note text in data/protocols.json must match its source PDF.

For each regimen `verbatim` (and each note `text`) whose source is a PDF section, the
normalised string — or, failing an exact match, every dose/interval token in it — must
appear in the text layer of that protocol's PDF (pdftotext, poppler-utils).

Exempt, and reported separately:
  - items whose source cites "Validação clínica" (clinical decisions, CLINICAL_AUDIT.md §10);
  - items sourced only from raster flowcharts without a text layer
    (PAC178 Figura 1, PAC174 Fluxograma) — verified visually, see CLINICAL_AUDIT.md.

Usage: python3 tools/check_fidelity.py   (requires `pdftotext`)
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
RASTER = {("ULSSJ-PAC178-0", "Figura 1"), ("ULSSJ-PAC174-0", "Fluxograma")}
TOKEN = re.compile(r"\d+[\d.,-]*\s?(?:mg/kg/dia|mg/kg|mg/dia|g/dia|mg|ml|g|h)\b")

if not shutil.which("pdftotext"):
    sys.exit("pdftotext not found (install poppler-utils)")


def norm(x):
    x = unicodedata.normalize("NFKC", x).lower().replace("²", "").replace("⁄", "/")
    x = re.sub(r"\s+", " ", x)
    return x.strip()


def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


data = json.loads((ROOT / "data/protocols.json").read_text(encoding="utf-8"))
fails, exact, token_ok, validated, raster = [], 0, 0, 0, 0
for p in data["protocols"]:
    pdf = ROOT / p["sourceFile"]
    txt = norm(subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True).stdout)
    txt_nospace = txt.replace(" ", "")
    seen = set()
    for o in walk(p["nodes"]):
        s = o.get("verbatim") or (o.get("text") if "kind" in o else None)
        if not s or s in seen or "source" not in o:
            continue
        seen.add(s)
        sec = o["source"]["section"]
        if "Validação clínica" in sec:
            validated += 1
            continue
        v = norm(s)
        if v in txt:
            exact += 1
            continue
        toks = TOKEN.findall(v)
        missing = [t for t in toks if t.replace(" ", "") not in txt_nospace]
        if not missing:
            token_ok += 1
            continue
        if any(code == p["code"] and fig in sec for code, fig in RASTER):
            raster += 1
            continue
        fails.append(f"{p['code']} [{sec}] missing {missing}: {s[:100]}")

print(f"exact text match: {exact} · all dose/interval tokens found: {token_ok} · "
      f"clinical-validation items: {validated} · raster-figure items (visual check): {raster}")
for f in fails:
    print("FAIL", f)
sys.exit(1 if fails else 0)
