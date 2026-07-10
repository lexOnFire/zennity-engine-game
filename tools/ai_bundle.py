import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOOLS = [
    "generate_ai_context.py",
    "analyze_project.py",
    "dependency_graph.py",
    "architecture_report.py",
    "dashboard.py",
]

print("=" * 60)
print("ZENNITY AI TOOLKIT")
print("=" * 60)

for tool in TOOLS:
    print(f"\n>> Executando {tool}")

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / tool)],
        cwd=ROOT
    )

    if result.returncode != 0:
        print(f"\nERRO em {tool}")
        break

print("\nTudo concluído.")