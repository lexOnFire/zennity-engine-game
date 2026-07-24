from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parent.parent

stats = {
    "python_files": 0,
    "classes": 0,
    "functions": 0,
    "methods": 0,
    "tests": 0,
    "lines": 0,
    "largest_files": []
}

largest = []

for file in ROOT.rglob("*.py"):

    if ".git" in str(file):
        continue

    try:
        text = file.read_text(encoding="utf-8")
    except Exception:
        continue

    stats["python_files"] += 1
    stats["lines"] += len(text.splitlines())

    if "tests" in file.parts:
        stats["tests"] += 1

    try:
        tree = ast.parse(text)
    except Exception:
        continue

    classes = 0
    functions = 0
    methods = 0

    for node in tree.body:

        if isinstance(node, ast.ClassDef):

            classes += 1

            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    methods += 1

        elif isinstance(node, ast.FunctionDef):
            functions += 1

    stats["classes"] += classes
    stats["functions"] += functions
    stats["methods"] += methods

    largest.append(
        (len(text.splitlines()), str(file.relative_to(ROOT)))
    )

largest.sort(reverse=True)

stats["largest_files"] = largest[:20]

out = ROOT / ".ai" / "metrics.json"

out.write_text(
    json.dumps(stats, indent=4),
    encoding="utf-8"
)

print()

print("========== ZENNITY PROJECT ==========")

print(f"Python Files : {stats['python_files']}")
print(f"Classes      : {stats['classes']}")
print(f"Functions    : {stats['functions']}")
print(f"Methods      : {stats['methods']}")
print(f"Tests        : {stats['tests']}")
print(f"LOC          : {stats['lines']}")

print()

print("Largest Files")

for size, file in stats["largest_files"]:

    print(f"{size:6d}  {file}")

print()

print("Saved:")

print(out)