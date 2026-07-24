from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parent.parent

graph = {}

for file in ROOT.rglob("*.py"):

    if ".git" in str(file):
        continue

    try:
        source = file.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        continue

    imports = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    graph[str(file.relative_to(ROOT))] = sorted(set(imports))

out = ROOT / ".ai" / "dependencies.json"

out.write_text(
    json.dumps(graph, indent=2),
    encoding="utf-8"
)

print("Dependências salvas em:")
print(out)