"""Phase 9.5 — READ-ONLY audit of exception handling and error observability.

Classifies every `except` handler in production code as SAFE / QUESTIONABLE /
DANGEROUS, and reports on the global error-boundary and logging architecture.

Classification rules
--------------------
DANGEROUS    broad handler (bare `except:` or `except Exception`) whose body
             neither logs nor re-raises — the error vanishes completely.
QUESTIONABLE broad handler that only `print()`s, or a narrow handler that
             swallows silently, or a broad handler returning a falsy sentinel
             while also logging (still hides control flow).
SAFE         handler that logs with a logger AND/OR re-raises, or a narrow
             handler with a deliberate logged fallback.

Run:  python scripts/audit_silent_exceptions.py [--top N] [--json out.json]
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
EXCLUDE_PARTS = {"__pycache__", "tests", "test", "scratch", "demos", "examples",
                 "editor_legacy", ".git", "build", "dist"}

LOG_CALL = re.compile(
    r"\b(logger|log|_log|LOGGER|logging)\s*\.\s*"
    r"(debug|info|warning|warn|error|exception|critical|fatal)\b"
    # Phase 9.5B Stage 0: the shared error-boundary API in engine.diagnostics
    # logs with full context and traceback, so a handler using it is observable.
    r"|\b(report_error|report_crash|write_crash_report)\s*\("
    # ScriptRuntime funnels every script failure through these two methods,
    # which call report_error() (engine/runtime/script_runtime.py:181).
    # They are the only definitions of these names in production code.
    r"|\bself\._(handle|record)_error\s*\("
)
PRINT_CALL = re.compile(r"\bprint\s*\(")
BROAD = {"Exception", "BaseException"}

# Handlers inside the diagnostics layer itself are deliberately defensive: an
# exception hook or a log handler that raises would destroy the very reporting
# path it implements. They are counted separately rather than as defects.
INFRASTRUCTURE_PREFIXES = ("engine/diagnostics/",)


def iter_production_files():
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


def handler_type_names(handler: ast.ExceptHandler) -> list[str]:
    t = handler.type
    if t is None:
        return ["<bare>"]
    if isinstance(t, ast.Name):
        return [t.id]
    if isinstance(t, ast.Attribute):
        return [t.attr]
    if isinstance(t, ast.Tuple):
        out = []
        for e in t.elts:
            out.extend(handler_type_names(ast.ExceptHandler(type=e, name=None, body=[])))
        return out
    return [ast.dump(t)[:40]]


def analyse_handler(handler: ast.ExceptHandler, src_lines: list[str]) -> dict:
    names = handler_type_names(handler)
    is_broad = names == ["<bare>"] or any(n in BROAD for n in names)
    body_src = "\n".join(src_lines[handler.body[0].lineno - 1: handler.body[-1].end_lineno])

    only_pass = len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass)
    only_continue = len(handler.body) == 1 and isinstance(handler.body[0], ast.Continue)

    returns_sentinel = False
    for n in ast.walk(handler):
        if isinstance(n, ast.Return):
            v = n.value
            if v is None or (isinstance(v, ast.Constant) and v.value in (None, False, 0, "")):
                returns_sentinel = True
            if isinstance(v, (ast.List, ast.Dict, ast.Tuple)) and not getattr(v, "elts", getattr(v, "keys", [1])):
                returns_sentinel = True

    reraises = any(isinstance(n, ast.Raise) for n in ast.walk(handler))
    logs = bool(LOG_CALL.search(body_src))
    prints = bool(PRINT_CALL.search(body_src))

    silent = not (logs or prints or reraises)

    if is_broad and silent:
        verdict = "DANGEROUS"
    elif is_broad and not logs and prints:
        verdict = "QUESTIONABLE"
    elif is_broad and returns_sentinel and not reraises:
        verdict = "QUESTIONABLE"
    elif not is_broad and silent and not only_continue:
        verdict = "QUESTIONABLE"
    else:
        verdict = "SAFE"

    return {
        "types": names,
        "broad": is_broad,
        "silent": silent,
        "logs": logs,
        "prints": prints,
        "reraises": reraises,
        "only_pass": only_pass,
        "returns_sentinel": returns_sentinel,
        "verdict": verdict,
        "line": handler.lineno,
    }


def enclosing_function(tree: ast.AST) -> dict[int, str]:
    """line number -> enclosing function/class qualified name."""
    mapping: dict[int, str] = {}

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}.{child.name}" if prefix else child.name
                for ln in range(child.lineno, (child.end_lineno or child.lineno) + 1):
                    mapping.setdefault(ln, name)
                walk(child, name)
            else:
                walk(child, prefix)

    walk(tree, "")
    return mapping


# Hot paths where a swallowed exception is worst
HOT_PATH_HINTS = (
    "update", "tick", "step", "run", "loop", "paint", "render", "draw",
    "execute", "_execute", "dispatch", "emit", "handle", "on_", "start",
    "stop", "load", "save", "boot", "shutdown", "close",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    records: list[dict] = []
    parse_errors: list[str] = []
    per_file = collections.Counter()

    print_stmts = 0
    print_files = collections.Counter()
    logging_files = set()

    for path in iter_production_files():
        src = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        lines = src.splitlines()
        n_print = len(PRINT_CALL.findall(src))
        if n_print:
            print_stmts += n_print
            print_files[rel] = n_print
        if re.search(r"^\s*import logging|^\s*from logging", src, re.M):
            logging_files.add(rel)
        try:
            tree = ast.parse(src, rel)
        except SyntaxError as exc:
            parse_errors.append(f"{rel}: {exc}")
            continue
        fnmap = enclosing_function(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            info = analyse_handler(node, lines)
            fn = fnmap.get(node.lineno, "<module>")
            info["file"] = rel
            info["func"] = fn
            base = fn.rsplit(".", 1)[-1].lower()
            info["hot_path"] = any(h in base for h in HOT_PATH_HINTS)
            info["infrastructure"] = rel.startswith(INFRASTRUCTURE_PREFIXES)
            if info["infrastructure"] and info["verdict"] == "DANGEROUS":
                # Defensive-by-design; reported under its own heading.
                info["verdict"] = "INFRASTRUCTURE"
            records.append(info)
            per_file[rel] += 1

    total = len(records)
    broad = [r for r in records if r["broad"]]
    silent = [r for r in records if r["silent"]]
    logged = [r for r in records if r["logs"]]
    printed = [r for r in records if r["prints"] and not r["logs"]]
    rethrown = [r for r in records if r["reraises"]]
    dangerous = [r for r in records if r["verdict"] == "DANGEROUS"]
    infrastructure = [r for r in records if r["verdict"] == "INFRASTRUCTURE"]
    questionable = [r for r in records if r["verdict"] == "QUESTIONABLE"]
    safe = [r for r in records if r["verdict"] == "SAFE"]
    bare = [r for r in records if r["types"] == ["<bare>"]]
    pass_only = [r for r in records if r["only_pass"]]

    p0 = [r for r in dangerous if r["hot_path"]]
    p1 = [r for r in dangerous if not r["hot_path"]]

    P = print
    P("=" * 72)
    P("ZENNITY PHASE 9.5 — SILENT EXCEPTION / ERROR OBSERVABILITY AUDIT")
    P("=" * 72)
    P(f"production files scanned:            "
      f"{len(set(r['file'] for r in records)) } (with handlers)")
    P(f"TOTAL exception handlers:            {total}")
    P(f"TOTAL broad exception handlers:      {len(broad)}"
      f"   ({len(broad) * 100 // max(total,1)}%)")
    P(f"  bare `except:`                     {len(bare)}")
    P(f"SILENT (no log, no print, no raise): {len(silent)}")
    P(f"  of which body is only `pass`:      {len(pass_only)}")
    P(f"LOGGED (via logging module):         {len(logged)}")
    P(f"PRINTED only (not a real log):       {len(printed)}")
    P(f"RETHROWN:                            {len(rethrown)}")
    P("")
    P(f"DANGEROUS:    {len(dangerous)}")
    P(f"INFRASTRUCTURE (diagnostics layer, defensive by design): {len(infrastructure)}")
    P(f"QUESTIONABLE: {len(questionable)}")
    P(f"SAFE:         {len(safe)}")
    P("")
    P(f"P0 (DANGEROUS on a hot/lifecycle path): {len(p0)}")
    P(f"P1 (DANGEROUS elsewhere):               {len(p1)}")
    P("")
    P("-" * 72)
    P(f"TOP {args.top} P0 — swallowed exceptions on hot / lifecycle paths")
    P("-" * 72)
    for r in sorted(p0, key=lambda r: (r["file"], r["line"]))[: args.top]:
        kind = "bare except" if r["types"] == ["<bare>"] else f"except {'/'.join(r['types'])}"
        tail = " [pass]" if r["only_pass"] else (" [returns sentinel]" if r["returns_sentinel"] else "")
        P(f"  {r['file']}:{r['line']}  {r['func']}()  {kind}{tail}")
    P("")
    P("-" * 72)
    P("FILES WITH THE MOST HANDLERS")
    P("-" * 72)
    for f, n in per_file.most_common(20):
        d = sum(1 for r in records if r["file"] == f and r["verdict"] == "DANGEROUS")
        P(f"  {f:<62}{n:>4} handlers, {d:>3} dangerous")
    P("")
    P("-" * 72)
    P("LOGGING ARCHITECTURE")
    P("-" * 72)
    P(f"production files importing `logging`: {len(logging_files)}")
    P(f"total print() calls in production:    {print_stmts}")
    P("top print() offenders:")
    for f, n in print_files.most_common(15):
        P(f"  {f:<62}{n:>5}")

    # ---- global error boundary probes ------------------------------------
    P("")
    P("-" * 72)
    P("CENTRAL ERROR BOUNDARY PROBES")
    P("-" * 72)
    probes = {
        "sys.excepthook": r"sys\.excepthook",
        "threading.excepthook": r"threading\.excepthook",
        "qInstallMessageHandler": r"qInstallMessageHandler",
        "faulthandler": r"faulthandler",
        "CrashReporter": r"class\s+\w*CrashReport\w*",
        "ExceptionHandler class": r"class\s+\w*ExceptionHandler\w*",
        "logging.basicConfig": r"logging\.basicConfig",
        "FileHandler / RotatingFileHandler": r"(RotatingFileHandler|logging\.FileHandler)",
        "atexit": r"\batexit\b",
        "unraisablehook": r"unraisablehook",
    }
    all_src = {}
    for path in iter_production_files():
        all_src[str(path.relative_to(ROOT)).replace("\\", "/")] = path.read_text(
            encoding="utf-8", errors="replace")
    for entry in ("zennity_run.py", "conftest.py"):
        p = ROOT / entry
        if p.exists():
            all_src[entry] = p.read_text(encoding="utf-8", errors="replace")
    probe_results = {}
    for label, pattern in probes.items():
        hits = [f for f, s in all_src.items() if re.search(pattern, s)]
        probe_results[label] = hits
        status = f"FOUND in {len(hits)} file(s)" if hits else "ABSENT"
        P(f"  {label:<38} {status}")
        for h in hits[:4]:
            P(f"      {h}")

    if parse_errors:
        P("")
        P("PARSE ERRORS:")
        for e in parse_errors:
            P(f"  {e}")

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps({
            "totals": {
                "handlers": total, "broad": len(broad), "bare": len(bare),
                "silent": len(silent), "pass_only": len(pass_only),
                "logged": len(logged), "printed_only": len(printed),
                "rethrown": len(rethrown), "dangerous": len(dangerous),
                "questionable": len(questionable), "safe": len(safe),
                "infrastructure": len(infrastructure),
                "p0": len(p0), "p1": len(p1), "print_calls": print_stmts,
            },
            "p0": p0, "probes": {k: v for k, v in probe_results.items()},
            "per_file": dict(per_file.most_common(50)),
        }, indent=2), encoding="utf-8")
        P(f"\nJSON written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
