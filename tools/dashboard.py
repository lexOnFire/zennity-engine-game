from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
AI = ROOT / ".ai"

print("=" * 60)
print("              ZENNITY ENGINE DASHBOARD")
print("=" * 60)

# Branch
branch = AI / "git_branch.txt"
if branch.exists():
    print("\n[Git Branch]")
    print(branch.read_text(encoding="utf-8").strip())

# Status
status = AI / "git_status.txt"
if status.exists():
    print("\n[Git Status]")
    lines = status.read_text(encoding="utf-8").splitlines()
    for line in lines[:10]:
        print(line)

# Métricas
metrics = AI / "metrics.json"
if metrics.exists():
    data = json.loads(metrics.read_text(encoding="utf-8"))

    print("\n[Projeto]")
    print(f"Arquivos Python : {data['python_files']}")
    print(f"Classes         : {data['classes']}")
    print(f"Funções         : {data['functions']}")
    print(f"Métodos         : {data['methods']}")
    print(f"Testes          : {data['tests']}")
    print(f"Linhas          : {data['lines']}")

# Pytest
pytest = AI / "pytest.txt"
if pytest.exists():
    print("\n[Último Pytest]")
    print(pytest.read_text(encoding="utf-8").strip())

print("\n" + "=" * 60)
print("Dashboard concluído.")