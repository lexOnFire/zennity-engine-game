from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".ai" / "architecture.md"

modules = {}

for file in ROOT.rglob("*.py"):
    if ".git" in str(file):
        continue

    try:
        source = file.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        continue

    classes = []
    functions = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)

        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)

    modules[str(file.relative_to(ROOT))] = {
        "classes": classes,
        "functions": functions,
    }

with OUT.open("w", encoding="utf-8") as f:

    f.write("# Zennity Architecture Report\n\n")

    for module, data in sorted(modules.items()):

        f.write(f"## {module}\n\n")

        if data["classes"]:
            f.write("### Classes\n")
            for c in data["classes"]:
                f.write(f"- {c}\n")
            f.write("\n")

        if data["functions"]:
            f.write("### Functions\n")
            for fn in data["functions"]:
                f.write(f"- {fn}\n")
            f.write("\n")

print("Saved:", OUT)