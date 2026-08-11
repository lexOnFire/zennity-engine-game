"""Phase 9.5 — READ-ONLY audit of the Zennity Logic Graph node system.

Produces counts and contract-violation reports for:
  * declarative NodeDefinition objects (engine/logic/node_definitions/*)
  * legacy NODE_DEFINITIONS dict
  * runtime executors / evaluators (engine/logic/runtime/nodes/*)
  * registration-path divergence (nodes/__init__ vs LogicProvider.boot)
  * port contract mismatches between definition and runtime usage

This script NEVER writes to production code.  It only reads, imports and
prints.  Run with:  python scripts/audit_node_system.py [--json out.json]
"""
from __future__ import annotations

import argparse
import ast
import collections
import importlib
import io
import json
import os
import pathlib
import re
import sys
import contextlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

DEF_PKG = ROOT / "engine" / "logic" / "node_definitions"
RT_PKG = ROOT / "engine" / "logic" / "runtime" / "nodes"

FLOW_TYPES = {"exec", "flow"}


# --------------------------------------------------------------------------
# Static pass — parse source, no import side effects
# --------------------------------------------------------------------------
def static_registrations(pkg: pathlib.Path) -> dict[str, dict[str, list[str]]]:
    """Map module -> {'executors': [...], 'evaluators': [...]} from decorators."""
    out: dict[str, dict[str, list[str]]] = {}
    for path in sorted(pkg.glob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), str(path))
        execs: list[str] = []
        evals: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                fn = dec.func
                name = getattr(fn, "attr", None)
                if name not in ("register_executor", "register_evaluator"):
                    continue
                target = execs if name == "register_executor" else evals
                for arg in dec.args:
                    for lit in _literal_strings(arg):
                        target.append(lit)
        out[path.stem] = {"executors": execs, "evaluators": evals}
    return out


def _literal_strings(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        res: list[str] = []
        for elt in node.elts:
            res.extend(_literal_strings(elt))
        return res
    return []


def module_list_in_source(path: pathlib.Path, prefix: str) -> set[str]:
    """Extract `import <prefix>.<mod>` / `from . import <mod>` module names."""
    text = path.read_text(encoding="utf-8", errors="replace")
    found = set(re.findall(rf"import\s+{re.escape(prefix)}\.(\w+)", text))
    found |= set(re.findall(r"^from \. import (\w+)", text, re.M))
    return found


# --------------------------------------------------------------------------
# Dynamic pass — import everything and introspect the real registries
# --------------------------------------------------------------------------
def dynamic_pass() -> dict:
    buf = io.StringIO()
    result: dict = {"import_errors": {}}
    with contextlib.redirect_stdout(buf):
        from engine.logic.runtime.registry import registry

        for path in sorted(RT_PKG.glob("*.py")):
            if path.name == "__init__.py":
                continue
            try:
                importlib.import_module(f"engine.logic.runtime.nodes.{path.stem}")
            except Exception as exc:  # audit tool: report, never crash
                result["import_errors"][f"runtime.nodes.{path.stem}"] = repr(exc)

        defs: dict[str, object] = {}
        for path in sorted(DEF_PKG.glob("*.py")):
            if path.name in ("__init__.py", "registry.py"):
                continue
            try:
                mod = importlib.import_module(f"engine.logic.node_definitions.{path.stem}")
            except Exception as exc:
                result["import_errors"][f"node_definitions.{path.stem}"] = repr(exc)
                continue
            for value in vars(mod).values():
                d = getattr(value, "__node_definition__", None)
                if d is None and type(value).__name__ == "NodeDefinition":
                    d = value
                if d is None:
                    continue
                nid = str(getattr(d, "id", "")).strip()
                if nid:
                    defs.setdefault(nid, []).append((path.stem, d)) if False else None
                    defs[nid] = (path.stem, d)

        try:
            from engine.logic.node_definitions import NODE_DEFINITIONS
            legacy = dict(NODE_DEFINITIONS)
        except Exception as exc:
            result["import_errors"]["NODE_DEFINITIONS"] = repr(exc)
            legacy = {}

    result["stdout_noise"] = buf.getvalue()
    result["executors"] = sorted(registry.executors)
    result["evaluators"] = sorted(registry.evaluators)
    result["declarative"] = defs
    result["legacy"] = legacy
    return result


def pins(definition, attr: str) -> list[tuple[str, str]]:
    out = []
    for p in list(getattr(definition, attr, []) or []):
        pid = str(getattr(p, "id", ""))
        ptype = str(getattr(getattr(p, "pin_type", ""), "value", getattr(p, "pin_type", "")))
        out.append((pid, ptype.lower()))
    return out


def legacy_pins(entry: dict, key: str) -> list[tuple[str, str]]:
    out = []
    for p in entry.get(key, []) or []:
        if isinstance(p, (tuple, list)) and len(p) >= 2:
            out.append((str(p[0]), str(p[1]).lower()))
        elif isinstance(p, str):
            out.append((p, "any"))
    return out


# --------------------------------------------------------------------------
# Runtime port usage — what ports the executor code actually touches
# --------------------------------------------------------------------------
# Capture the whole return expression, not just the first bracket group:
# `return [f"then_{i}" for i in ...] + ["next"]` has two lists, and stopping at
# the first `]` hid the "next" port.
RETURN_RE = re.compile(r'return\s+(\[.*)$', re.M)
# A node may build its exec ports dynamically, e.g. `sequence` returns
# [f"then_{index}" for index in range(outputs)].  The f-string prefix names a
# port *family*, not a literal port.  Treating it as a literal is what produced
# the bogus "then_{index}" violation reported in Phase 9.5A.
DYNAMIC_PORT_RE = re.compile(r'f"([a-z_]+?)_\{')
READ_RE = re.compile(r'_read_input\(\s*node_id\s*,\s*["\']([^"\']+)["\']')
STORE_RE = re.compile(r'_store\(\s*node_id\s*,\s*["\']([^"\']+)["\']')


def runtime_port_usage() -> dict[str, dict[str, set[str]]]:
    """node_type -> {'returns': set, 'reads': set, 'stores': set} (best effort)."""
    usage: dict[str, dict[str, set[str]]] = {}
    for path in sorted(RT_PKG.glob("*.py")):
        if path.name == "__init__.py":
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src, str(path))
        lines = src.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            ids: list[str] = []
            kind = None
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and getattr(dec.func, "attr", None) in (
                    "register_executor",
                    "register_evaluator",
                ):
                    kind = dec.func.attr
                    for a in dec.args:
                        ids.extend(_literal_strings(a))
            if not ids:
                continue
            body = "\n".join(lines[node.lineno - 1 : node.end_lineno])
            returns: set[str] = set()
            dynamic: set[str] = set()
            for m in RETURN_RE.finditer(body):
                seg = m.group(1)
                for family in DYNAMIC_PORT_RE.findall(seg):
                    dynamic.add(family + "_")
                for tok in re.findall(r'["\']([^"\']+)["\']', seg):
                    if "{" in tok:
                        continue  # f-string template; recorded as a family above
                    returns.add(tok)
            reads = set(READ_RE.findall(body))
            stores = set(STORE_RE.findall(body))
            for nid in ids:
                slot = usage.setdefault(
                    nid, {"returns": set(), "reads": set(), "stores": set(),
                          "kinds": set(), "dynamic": set()}
                )
                slot["dynamic"] |= dynamic
                slot["returns"] |= returns
                slot["reads"] |= reads
                slot["stores"] |= stores
                slot["kinds"].add(kind)
    return usage


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write machine-readable report here")
    ap.add_argument(
        "--ci", action="store_true",
        help="exit non-zero on any hard contract violation (Phase 9.5B Stage 1)",
    )
    args = ap.parse_args()

    static_rt = static_registrations(RT_PKG)
    dyn = dynamic_pass()
    usage = runtime_port_usage()

    executors = set(dyn["executors"])
    evaluators = set(dyn["evaluators"])
    declarative = dyn["declarative"]
    legacy = dyn["legacy"]
    all_defs = set(declarative) | set(legacy)

    # --- registration path divergence -------------------------------------
    init_mods = module_list_in_source(RT_PKG / "__init__.py", "engine.logic.runtime.nodes")
    prov_mods = module_list_in_source(
        ROOT / "engine" / "logic" / "provider.py", "engine.logic.runtime.nodes"
    )
    all_rt_mods = {p.stem for p in RT_PKG.glob("*.py")} - {"__init__"}
    missing_from_init = sorted(all_rt_mods - init_mods)

    # --- duplicate registrations ------------------------------------------
    exec_owner: dict[str, list[str]] = collections.defaultdict(list)
    eval_owner: dict[str, list[str]] = collections.defaultdict(list)
    for mod, kinds in static_rt.items():
        for nid in kinds["executors"]:
            exec_owner[nid].append(mod)
        for nid in kinds["evaluators"]:
            eval_owner[nid].append(mod)
    dup_exec = {k: v for k, v in exec_owner.items() if len(v) > 1}
    dup_eval = {k: v for k, v in eval_owner.items() if len(v) > 1}

    # --- duplicate display names ------------------------------------------
    titles: dict[str, list[str]] = collections.defaultdict(list)
    for nid, entry in legacy.items():
        t = str(entry.get("title", "")).strip().lower()
        if t:
            titles[t].append(nid)
    dup_titles = {k: v for k, v in titles.items() if len(v) > 1}

    # --- categories --------------------------------------------------------
    cats: dict[str, list[str]] = collections.defaultdict(list)
    for nid, entry in legacy.items():
        cats[str(entry.get("category", "?"))].append(nid)

    # --- node classification ----------------------------------------------
    flow_nodes, pure_data, event_nodes = [], [], []
    for nid, entry in legacy.items():
        ins = legacy_pins(entry, "inputs")
        outs = legacy_pins(entry, "outputs")
        has_flow = any(t in FLOW_TYPES for _, t in ins + outs)
        if nid.startswith("event_") or (not ins and any(t in FLOW_TYPES for _, t in outs)):
            event_nodes.append(nid)
        elif has_flow:
            flow_nodes.append(nid)
        else:
            pure_data.append(nid)

    # --- contract violations ----------------------------------------------
    violations: list[dict] = []

    def add(nid, kind, detail):
        violations.append({"node": nid, "kind": kind, "detail": detail})

    # Phase 9.5B Stage 1: the audit tool no longer carries its own copy of the
    # rules.  engine.logic.contracts.validate_catalogue is the single validator,
    # shared with the tests and with boot-time validation, so "what counts as a
    # violation" is defined exactly once.
    from engine.logic.contracts import (
        DefinitionContract, ExecutionModel, RuntimeContract, validate_catalogue,
    )

    definitions: dict[str, DefinitionContract] = {}
    for nid in sorted(all_defs):
        entry = legacy.get(nid, {})
        # execution_model / dynamic prefixes live on the declarative
        # NodeDefinition; the legacy dict is only pins.
        decl = declarative.get(nid)
        obj = decl[1] if isinstance(decl, tuple) else None
        raw_model = str(
            entry.get("execution_model")
            or getattr(obj, "execution_model", "action")
            or "action"
        )
        try:
            model = ExecutionModel(raw_model)
        except ValueError:
            model = ExecutionModel.ACTION
        prefixes = tuple(
            entry.get("dynamic_exec_prefixes")
            or getattr(obj, "dynamic_exec_prefixes", ())
            or ()
        )
        outputs = legacy_pins(entry, "outputs")
        inputs = legacy_pins(entry, "inputs")
        if obj is None and not outputs and not inputs:
            model = ExecutionModel.PURE_DATA
        definitions[nid] = DefinitionContract(
            node_id=nid,
            inputs=inputs,
            outputs=outputs,
            properties=set((entry.get("properties") or {}).keys()),
            execution_model=model,
            dynamic_prefixes=prefixes,
            deprecated=bool(entry.get("deprecated")
                            or getattr(obj, "deprecated", False)),
        )

    runtimes: dict[str, RuntimeContract] = {}
    for nid in sorted(executors | evaluators | set(usage)):
        u = usage.get(nid, {})
        runtimes[nid] = RuntimeContract(
            node_id=nid,
            reads=set(u.get("reads", ())),
            stores=set(u.get("stores", ())),
            returns=set(u.get("returns", ())),
            has_executor=nid in executors,
            has_evaluator=nid in evaluators,
            dynamic=set(u.get("dynamic", ())),
        )

    for v in validate_catalogue(definitions, runtimes):
        add(v.node_id, v.kind, v.detail)

    # --- legacy / deprecated markers --------------------------------------
    legacy_markers: list[str] = []
    for path in list(DEF_PKG.glob("*.py")) + list(RT_PKG.glob("*.py")):
        src = path.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"(?i)\b(deprecated|legacy|alias|backward compat|compat)\b", src):
            line = src[: m.start()].count("\n") + 1
            legacy_markers.append(f"{path.relative_to(ROOT)}:{line}: {m.group(0)}")

    # ----------------------------------------------------------------- print
    P = print
    P("=" * 70)
    P("ZENNITY PHASE 9.5 — NODE SYSTEM AUDIT")
    P("=" * 70)
    P(f"TOTAL NODE DEFINITIONS (resolved):   {len(all_defs)}")
    P(f"  declarative NodeDefinition objs:   {len(declarative)}")
    P(f"  legacy NODE_DEFINITIONS entries:   {len(legacy)}")
    P(f"EXECUTORS:                           {len(executors)}")
    P(f"EVALUATORS:                          {len(evaluators)}")
    P(f"PURE DATA NODES:                     {len(pure_data)}")
    P(f"FLOW NODES:                          {len(flow_nodes)}")
    P(f"EVENT NODES:                         {len(event_nodes)}")
    P("")
    P(f"Nodes with definition but no runtime: "
      f"{len([v for v in violations if v['kind'] == 'NO_RUNTIME'])}")
    P(f"Runtime handlers with no definition:  "
      f"{len([v for v in violations if v['kind'] == 'NO_DEFINITION'])}")
    P(f"Duplicate executor IDs:               {len(dup_exec)}")
    P(f"Duplicate evaluator IDs:              {len(dup_eval)}")
    P(f"Duplicate display names:              {len(dup_titles)}")
    P(f"Legacy/deprecated markers:            {len(legacy_markers)}")
    P("")
    P("-" * 70)
    P("REGISTRATION PATH DIVERGENCE")
    P("-" * 70)
    P(f"runtime/nodes/__init__.py imports:  {len(init_mods)} modules")
    P(f"LogicProvider.boot imports:         {len(prov_mods)} modules")
    P(f"runtime node modules on disk:       {len(all_rt_mods)}")
    P(f"NOT imported by nodes/__init__.py:  {missing_from_init}")
    P(f"NOT imported by LogicProvider:      {sorted(all_rt_mods - prov_mods)}")
    P("")
    P("-" * 70)
    P("NODES PER CATEGORY (legacy palette source)")
    P("-" * 70)
    for cat, ids in sorted(cats.items(), key=lambda kv: -len(kv[1])):
        flag = ""
        if len(ids) > 50:
            flag = "  <<< >50 SPLIT REQUIRED"
        elif len(ids) > 30:
            flag = "  <<< >30 review"
        P(f"  {cat:<24} {len(ids):>4}{flag}")
    P("")
    P("-" * 70)
    P(f"NODE CONTRACT VIOLATIONS: {len(violations)}")
    P("-" * 70)
    by_kind = collections.Counter(v["kind"] for v in violations)
    for k, n in by_kind.most_common():
        P(f"  {k:<24} {n}")
    P("")
    for v in violations:
        P(f"  [{v['kind']}] {v['node']}: {v['detail']}")
    P("")
    if dup_exec:
        P("DUPLICATE EXECUTORS (last registration wins):")
        for k, v in sorted(dup_exec.items()):
            P(f"  {k}: {v}")
    if dup_eval:
        P("DUPLICATE EVALUATORS (last registration wins):")
        for k, v in sorted(dup_eval.items()):
            P(f"  {k}: {v}")
    if dup_titles:
        P("")
        P("DUPLICATE / CONFUSING DISPLAY NAMES:")
        for k, v in sorted(dup_titles.items()):
            P(f"  {k!r}: {v}")
    if dyn["import_errors"]:
        P("")
        P("IMPORT ERRORS:")
        for k, v in dyn["import_errors"].items():
            P(f"  {k}: {v}")
    if dyn["stdout_noise"].strip():
        P("")
        P(f"IMPORT-TIME STDOUT NOISE: {len(dyn['stdout_noise'].splitlines())} lines "
          f"printed just by importing node modules")

    P("")
    P("-" * 70)
    P("FILE ORGANIZATION")
    P("-" * 70)
    P(f"{'file':<58}{'lines':>7}{'nodes':>7}")
    for pkg, label in ((DEF_PKG, "definitions"), (RT_PKG, "runtime")):
        P(f"  -- {label} --")
        for path in sorted(pkg.glob("*.py")):
            n_lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
            st = static_rt.get(path.stem, {"executors": [], "evaluators": []})
            n_nodes = len(set(st["executors"]) | set(st["evaluators"])) if pkg is RT_PKG else \
                sum(1 for nid, (mod, _) in declarative.items() if mod == path.stem)
            P(f"  {str(path.relative_to(ROOT)):<56}{n_lines:>7}{n_nodes:>7}")

    if args.json:
        payload = {
            "totals": {
                "definitions": len(all_defs),
                "declarative": len(declarative),
                "legacy": len(legacy),
                "executors": len(executors),
                "evaluators": len(evaluators),
                "pure_data": len(pure_data),
                "flow": len(flow_nodes),
                "event": len(event_nodes),
                "violations": len(violations),
            },
            "violations": violations,
            "categories": {k: len(v) for k, v in cats.items()},
            "duplicate_executors": dup_exec,
            "duplicate_evaluators": dup_eval,
            "duplicate_titles": dup_titles,
            "missing_from_init": missing_from_init,
            "import_errors": dyn["import_errors"],
        }
        pathlib.Path(args.json).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        P(f"\nJSON written to {args.json}")

    # ------------------------------------------------------------- CI gate
    # Phase 9.5B Stage 1, item 26.  Duplicate registrations and the port
    # contract classes are hard failures.  DEPRECATED_NO_RUNTIME is a warning:
    # those nodes are hidden from the palette and unreachable by an author.
    hard_kinds = {
        "EXEC_PORT_MISMATCH", "UNREACHABLE_EXEC_PORT", "NO_DEFINITION",
        "DATA_PORT_MISMATCH", "INPUT_PORT_MISMATCH", "NO_RUNTIME",
        "PURE_DATA_HAS_EXEC", "TERMINAL_HAS_EXEC", "TERMINAL_RETURNS_EXEC",
        "ALIAS_WITHOUT_TARGET",
    }
    hard = [v for v in violations if v["kind"] in hard_kinds]
    soft = [v for v in violations if v["kind"] not in hard_kinds]
    if args.ci:
        P("")
        P("=" * 70)
        if dup_exec or dup_eval:
            P("CI GATE: FAIL — duplicate executor/evaluator registrations")
            return 1
        if hard:
            P(f"CI GATE: FAIL — {len(hard)} hard contract violation(s)")
            for v in hard:
                P(f"  [{v['kind']}] {v['node']}: {v['detail']}")
            return 1
        P(f"CI GATE: PASS — 0 hard violations, {len(soft)} warning(s)")
        for v in soft:
            P(f"  (warning) [{v['kind']}] {v['node']}")
        P("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
