"""Phase 9.5 — READ-ONLY structural audit of the Zennity codebase.

Reports:
  * large production files (>500 / >1000 / >2000 lines) with responsibility hints
  * module-level mutable global state and singletons
  * threads / timers / subprocesses and their lifecycle
  * import-direction violations (engine -> editor) and import cycles
  * import-time side effects

Run:  python scripts/audit_large_files.py [--top 30] [--json out.json]
This script never modifies production code.
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRODUCTION_DIRS = ["engine", "editor"]
EXCLUDE_PARTS = {"__pycache__", "tests", "scratch", "demos", "examples",
                 "editor_legacy", ".git", "build", "dist"}


def iter_files():
    for d in PRODUCTION_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if EXCLUDE_PARTS & set(path.parts):
                continue
            if path.name.startswith("test_"):
                continue
            yield path


def rel(path: pathlib.Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def module_name(path: pathlib.Path) -> str:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


# ---------------------------------------------------------------- large files
def file_profile(path: pathlib.Path, tree: ast.AST, src: str) -> dict:
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    methods = sum(
        1 for c in classes for n in c.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    longest = 0
    longest_name = ""
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            size = (n.end_lineno or n.lineno) - n.lineno
            if size > longest:
                longest, longest_name = size, n.name
    imports = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)))
    return {
        "file": rel(path),
        "lines": len(src.splitlines()),
        "classes": len(classes),
        "class_names": [c.name for c in classes][:6],
        "top_funcs": len(funcs),
        "methods": methods,
        "longest_func": longest,
        "longest_func_name": longest_name,
        "imports": imports,
    }


# --------------------------------------------------------------- global state
MUTABLE_CALLS = {"dict", "list", "set", "defaultdict", "OrderedDict", "Counter",
                 "deque", "WeakValueDictionary", "WeakKeyDictionary"}


def module_globals(tree: ast.AST) -> list[dict]:
    out = []
    for node in tree.body:
        targets = []
        value = None
        if isinstance(node, ast.Assign):
            targets = [t for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target]
            value = node.value
        if not targets:
            continue
        for t in targets:
            name = t.id
            kind = None
            if isinstance(value, (ast.Dict, ast.List, ast.Set)):
                kind = "literal container"
            elif isinstance(value, ast.Call):
                fn = value.func
                fname = getattr(fn, "id", getattr(fn, "attr", ""))
                if fname in MUTABLE_CALLS:
                    kind = f"{fname}()"
                elif fname and fname[:1].isupper():
                    kind = f"instance of {fname}()"
            if kind is None:
                continue
            if name.isupper() and kind == "literal container":
                kind += " (CONST-cased but still mutable)"
            out.append({"name": name, "kind": kind, "line": node.lineno})
    return out


SINGLETON_RE = re.compile(
    r"def\s+(get_\w*(?:instance|registry|manager|service|bus|hub|cache)\w*)\s*\(|"
    r"def\s+(instance|current)\s*\(\s*cls", re.I)


# ------------------------------------------------------------------- threads
THREAD_PATTERNS = {
    "threading.Thread": r"threading\.Thread\s*\(",
    "Thread(": r"(?<!threading\.)\bThread\s*\(",
    "QThread": r"\bQThread\b",
    "QTimer": r"\bQTimer\b",
    "QThreadPool": r"\bQThreadPool\b",
    "multiprocessing.Process": r"(multiprocessing|mp)\.Process\s*\(",
    "concurrent.futures": r"\b(ThreadPoolExecutor|ProcessPoolExecutor)\b",
    "QFileSystemWatcher": r"\bQFileSystemWatcher\b",
    "watchdog Observer": r"\bObserver\s*\(",
}
LIFECYCLE_PATTERNS = {
    "daemon=True": r"daemon\s*=\s*True",
    ".start()": r"\.start\s*\(",
    ".join(": r"\.join\s*\(",
    ".stop()": r"\.stop\s*\(",
    ".terminate()": r"\.terminate\s*\(",
    ".quit()": r"\.quit\s*\(",
    "cancel_join_thread": r"cancel_join_thread",
}


# ---------------------------------------------------------- import direction
def local_imports(tree: ast.AST) -> set[str]:
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative
                continue
            if node.module:
                mods.add(node.module)
    return {m for m in mods if m.split(".")[0] in ("engine", "editor")}


def toplevel_side_effects(tree: ast.AST) -> list[str]:
    """Module-level expression statements that call something (import-time work)."""
    out = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            fn = node.value.func
            name = getattr(fn, "id", None) or getattr(fn, "attr", None) or "<call>"
            if name in ("print",):
                name = "print"
            out.append(f"{name}() @ line {node.lineno}")
    return out


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--json")
    args = ap.parse_args()

    profiles: list[dict] = []
    globals_by_file: dict[str, list[dict]] = {}
    singletons: list[str] = []
    threads_by_file: dict[str, dict[str, int]] = {}
    lifecycle_by_file: dict[str, set[str]] = {}
    imports_by_module: dict[str, set[str]] = {}
    side_effects: dict[str, list[str]] = {}
    file_of_module: dict[str, str] = {}
    parse_errors: list[str] = []

    for path in iter_files():
        src = path.read_text(encoding="utf-8", errors="replace")
        r = rel(path)
        try:
            tree = ast.parse(src, r)
        except SyntaxError as exc:
            parse_errors.append(f"{r}: {exc}")
            continue

        profiles.append(file_profile(path, tree, src))

        g = module_globals(tree)
        if g:
            globals_by_file[r] = g

        for m in SINGLETON_RE.finditer(src):
            name = m.group(1) or m.group(2)
            line = src[: m.start()].count("\n") + 1
            singletons.append(f"{r}:{line}  {name}()")

        hits = {}
        for label, pat in THREAD_PATTERNS.items():
            n = len(re.findall(pat, src))
            if n:
                hits[label] = n
        if hits:
            threads_by_file[r] = hits
            lifecycle_by_file[r] = {
                lbl for lbl, pat in LIFECYCLE_PATTERNS.items() if re.search(pat, src)
            }

        mod = module_name(path)
        file_of_module[mod] = r
        imports_by_module[mod] = local_imports(tree)

        se = toplevel_side_effects(tree)
        if se:
            side_effects[r] = se

    # ---- import direction violations -------------------------------------
    engine_to_editor = []
    for mod, deps in imports_by_module.items():
        if not mod.startswith("engine"):
            continue
        for d in sorted(deps):
            if d.startswith("editor"):
                engine_to_editor.append(f"{file_of_module[mod]}  ->  {d}")

    # ---- cycles (module-graph SCC via Tarjan, package-collapsed too) -----
    def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
        index = {}
        low = {}
        onstack = {}
        stack: list[str] = []
        counter = [0]
        result: list[list[str]] = []

        def strongconnect(v):
            index[v] = low[v] = counter[0]
            counter[0] += 1
            stack.append(v)
            onstack[v] = True
            for w in graph.get(v, ()):
                if w not in graph:
                    continue
                if w not in index:
                    strongconnect(w)
                    low[v] = min(low[v], low[w])
                elif onstack.get(w):
                    low[v] = min(low[v], index[w])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    onstack[w] = False
                    comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1:
                    result.append(sorted(comp))
        sys.setrecursionlimit(10000)
        for v in list(graph):
            if v not in index:
                strongconnect(v)
        return result

    # normalise: an import of `engine.a.b` may name a module or a symbol's module
    norm_graph: dict[str, set[str]] = {}
    known = set(imports_by_module)
    for mod, deps in imports_by_module.items():
        resolved = set()
        for d in deps:
            if d in known:
                resolved.add(d)
            else:
                parent = ".".join(d.split(".")[:-1])
                if parent in known:
                    resolved.add(parent)
        norm_graph[mod] = resolved
    cycles = find_cycles(norm_graph)

    # package-level cycles
    def pkg(m: str, depth: int = 2) -> str:
        return ".".join(m.split(".")[:depth])

    pkg_graph: dict[str, set[str]] = collections.defaultdict(set)
    for mod, deps in norm_graph.items():
        for d in deps:
            if pkg(mod) != pkg(d):
                pkg_graph[pkg(mod)].add(pkg(d))
    pkg_cycles = find_cycles(dict(pkg_graph))

    # ---------------------------------------------------------------- print
    P = print
    over500 = [p for p in profiles if p["lines"] > 500]
    over1000 = [p for p in profiles if p["lines"] > 1000]
    over2000 = [p for p in profiles if p["lines"] > 2000]
    total_lines = sum(p["lines"] for p in profiles)

    P("=" * 78)
    P("ZENNITY PHASE 9.5 — STRUCTURAL / ARCHITECTURE AUDIT")
    P("=" * 78)
    P(f"production .py files:  {len(profiles)}")
    P(f"total production LOC:  {total_lines}")
    P(f"files >  500 lines:    {len(over500)}")
    P(f"files > 1000 lines:    {len(over1000)}")
    P(f"files > 2000 lines:    {len(over2000)}")
    P("")
    P("-" * 78)
    P(f"TOP {args.top} LARGEST PRODUCTION FILES")
    P("-" * 78)
    P(f"{'file':<58}{'lines':>6}{'cls':>5}{'meth':>6}{'maxfn':>7}")
    for p in sorted(profiles, key=lambda x: -x["lines"])[: args.top]:
        P(f"{p['file']:<58}{p['lines']:>6}{p['classes']:>5}{p['methods']:>6}"
          f"{p['longest_func']:>7}")
    P("")
    P("responsibility hints for the 12 biggest (top-level classes):")
    for p in sorted(profiles, key=lambda x: -x["lines"])[:12]:
        P(f"  {p['file']}")
        P(f"      classes: {', '.join(p['class_names']) or '(module-level functions only)'}")
        P(f"      longest function: {p['longest_func_name']}() = {p['longest_func']} lines; "
          f"{p['imports']} imports")

    P("")
    P("-" * 78)
    n_globals = sum(len(v) for v in globals_by_file.values())
    P(f"MODULE-LEVEL MUTABLE GLOBAL STATE: {n_globals} across "
      f"{len(globals_by_file)} files")
    P("-" * 78)
    for f, entries in sorted(globals_by_file.items(), key=lambda kv: -len(kv[1]))[:30]:
        P(f"  {f}")
        for e in entries:
            P(f"      L{e['line']:<6} {e['name']:<34} {e['kind']}")

    P("")
    P("-" * 78)
    P(f"SINGLETON / GLOBAL ACCESSORS: {len(singletons)}")
    P("-" * 78)
    for s in singletons:
        P(f"  {s}")

    P("")
    P("-" * 78)
    P(f"THREADS / TIMERS / SUBPROCESSES: {len(threads_by_file)} files")
    P("-" * 78)
    for f, hits in sorted(threads_by_file.items()):
        life = lifecycle_by_file.get(f, set())
        risk = []
        if ".start()" in life and ".join(" not in life:
            risk.append("START-WITHOUT-JOIN")
        if "daemon=True" in life:
            risk.append("daemon")
        if not life:
            risk.append("no lifecycle calls found")
        P(f"  {f}")
        P(f"      {', '.join(f'{k} x{v}' for k, v in hits.items())}")
        P(f"      lifecycle: {', '.join(sorted(life)) or '(none)'}"
          f"{'   <<< ' + ' / '.join(risk) if risk else ''}")

    P("")
    P("-" * 78)
    P("IMPORT DIRECTION")
    P("-" * 78)
    P(f"engine -> editor violations: {len(engine_to_editor)}")
    for v in engine_to_editor:
        P(f"  {v}")
    P("")
    P(f"module-level import cycles (SCC): {len(cycles)}")
    for c in cycles[:20]:
        P(f"  cycle({len(c)}): {' <-> '.join(c)}")
    P("")
    P(f"package-level cycles: {len(pkg_cycles)}")
    for c in pkg_cycles[:20]:
        P(f"  {' <-> '.join(c)}")

    P("")
    P("-" * 78)
    P(f"IMPORT-TIME SIDE EFFECTS: {sum(len(v) for v in side_effects.values())} "
      f"calls in {len(side_effects)} modules")
    P("-" * 78)
    for f, calls in sorted(side_effects.items(), key=lambda kv: -len(kv[1]))[:25]:
        P(f"  {f}: {', '.join(calls[:6])}")

    if parse_errors:
        P("")
        P("PARSE ERRORS:")
        for e in parse_errors:
            P(f"  {e}")

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps({
            "totals": {
                "files": len(profiles), "loc": total_lines,
                "over500": len(over500), "over1000": len(over1000),
                "over2000": len(over2000),
                "globals": n_globals, "global_files": len(globals_by_file),
                "singletons": len(singletons),
                "thread_files": len(threads_by_file),
                "engine_to_editor": len(engine_to_editor),
                "cycles": len(cycles), "pkg_cycles": len(pkg_cycles),
            },
            "largest": sorted(profiles, key=lambda x: -x["lines"])[:60],
            "globals": globals_by_file,
            "singletons": singletons,
            "threads": {k: {"hits": v, "lifecycle": sorted(lifecycle_by_file.get(k, []))}
                        for k, v in threads_by_file.items()},
            "engine_to_editor": engine_to_editor,
            "cycles": cycles, "pkg_cycles": pkg_cycles,
            "side_effects": side_effects,
        }, indent=2), encoding="utf-8")
        P(f"\nJSON written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
