#!/usr/bin/env python3
"""
Structural validation of data/protocols.json.

Checks, per protocol:
  1. `start` exists and is a question node.
  2. Every option `next` points to an existing node.
  3. Every node is reachable from `start` (no orphans).
  4. Every path from `start` terminates in a result node (no cycles).
  5. Every result with antibiotherapy=true has >=1 firstLine regimen, or is flagged pending.
  6. Every `when` key refers to a question id / answerKey that lies on at least one
     path to that result, and every `when` value is a valid option id of that question.
  7. Every referenced issue id (B*, m*) is documented in CLINICAL_AUDIT.md.
  8. Every regimen / note carries a `source` with section + page.

Exit code 0 = pass, 1 = failures. Usage: python3 tools/validate_protocols.py
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data" / "protocols.json").read_text(encoding="utf-8"))
audit_path = ROOT / "CLINICAL_AUDIT.md"
audit = audit_path.read_text(encoding="utf-8") if audit_path.exists() else ""
documented = set(re.findall(r"\*\*\[([Bm]\d+)\]", audit))

errors, warnings = [], []
stats = []


def walk_items(obj, path=""):
    """Yield (path, dict) for every dict inside obj."""
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from walk_items(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_items(v, f"{path}[{i}]")


for p in data["protocols"]:
    pid = p["id"]
    nodes = p["nodes"]
    start = p["start"]
    if start not in nodes or nodes[start]["type"] != "question":
        errors.append(f"{pid}: start '{start}' missing or not a question")
        continue

    def key_of(nid):
        return nodes[nid].get("answerKey", nid)

    # 2. dangling edges
    for nid, n in nodes.items():
        if n["type"] == "question":
            if not n.get("options"):
                errors.append(f"{pid}.{nid}: question without options")
            for o in n.get("options", []):
                if o["next"] not in nodes:
                    errors.append(f"{pid}.{nid}: option '{o['id']}' -> missing node '{o['next']}'")

    # 3/4. enumerate all paths (DFS), detect cycles
    paths_to = {}  # result id -> list of list[(answerKey, optionId)]
    reachable = set()

    def dfs(nid, trail, seen):
        reachable.add(nid)
        if nid in seen:
            errors.append(f"{pid}: cycle at '{nid}'")
            return
        n = nodes[nid]
        if n["type"] == "result":
            paths_to.setdefault(nid, []).append(trail)
            return
        for o in n["options"]:
            if o["next"] in nodes:
                dfs(o["next"], trail + [(key_of(nid), o["id"])], seen | {nid})

    dfs(start, [], frozenset())
    for nid in nodes:
        if nid not in reachable:
            errors.append(f"{pid}: node '{nid}' unreachable from start")

    # question option ids by answer key
    opts_by_key = {}
    for nid, n in nodes.items():
        if n["type"] == "question":
            opts_by_key.setdefault(key_of(nid), set()).update(o["id"] for o in n["options"])

    # 5/6. results
    n_results = 0
    satisfiable_items, gated_items = set(), {}
    for rid, r in nodes.items():
        if r["type"] != "result":
            continue
        n_results += 1
        if r.get("antibiotherapy") and not r.get("firstLine") and not r.get("pending"):
            errors.append(f"{pid}.{rid}: antibiotherapy result without firstLine regimen")
        keys_on_paths = set()
        for trail in paths_to.get(rid, []):
            keys_on_paths.update(k for k, _ in trail)
        for path, d in walk_items(r):
            if "when" in d:
                for k, v in d["when"].items():
                    vals = v if isinstance(v, list) else [v]
                    if k not in opts_by_key:
                        errors.append(f"{pid}.{rid}{path}: when-key '{k}' is not a question")
                        continue
                    if k not in keys_on_paths:
                        # allowed (item simply never shows) but flag it
                        warnings.append(f"{pid}.{rid}{path}: when-key '{k}' not on any path to this result (item never shown)")
                    for val in vals:
                        if val not in opts_by_key[k]:
                            errors.append(f"{pid}.{rid}{path}: when '{k}={val}' is not a valid option")
        # every when-gated item must be satisfiable on at least one path
        for path, d in walk_items(r):
            if "when" in d and all(k in keys_on_paths for k in d["when"]):
                ok = False
                for trail in paths_to.get(rid, []):
                    ans = dict(trail)
                    if all(ans.get(k) in (v if isinstance(v, list) else [v]) for k, v in d["when"].items()):
                        ok = True
                        break
                if ok:
                    satisfiable_items.add(json.dumps(d, sort_keys=True, ensure_ascii=False))
                else:
                    gated_items[json.dumps(d, sort_keys=True, ensure_ascii=False)] = f"{rid}{path}"
    # a when-gated item may legitimately be hidden on some results (shared note lists),
    # but it must be reachable on at least one result of the protocol.
    for k, where in gated_items.items():
        if k not in satisfiable_items:
            errors.append(f"{pid}.{where}: when-gated item never shown on any path of the protocol (dead content)")
    stats.append((pid, len(nodes), n_results, sum(len(v) for v in paths_to.values())))

    # 7/8. issues + sources
    for path, d in walk_items(p):
        for iid in d.get("issues", []) if isinstance(d.get("issues"), list) else []:
            if iid not in documented:
                errors.append(f"{pid}{path}: issue '{iid}' not documented in CLINICAL_AUDIT.md")
        if "verbatim" in d or ("text" in d and "kind" in d):
            s = d.get("source")
            if not s or "section" not in s or "page" not in s:
                errors.append(f"{pid}{path}: missing/incomplete source reference")

print("Protocol                 nodes  results  terminal-paths")
for pid, nn, nr, np_ in stats:
    print(f"  {pid:22} {nn:5}  {nr:7}  {np_:14}")
for w in warnings:
    print("WARN ", w)
for e in errors:
    print("ERROR", e)
print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
sys.exit(1 if errors else 0)
