"""
PHASE 3E AUDITORIA V2: Corrige erro de classificação

Diferencia:
- CONDITIONAL_SINGLE_BRANCH: Diferentes retornos possíveis, mas um por vez
- ACTUAL_SIMULTANEOUS_MULTI_OUTPUT: Múltiplos retorna na mesma lista
"""
import ast
from pathlib import Path
from collections import defaultdict


class ExecutorAnalyzerV2(ast.NodeVisitor):
    """Analisa com melhor classificação de multi-output."""

    def __init__(self, filename: str):
        self.filename = filename
        self.executors = defaultdict(dict)
        self.current_executor_id = None
        self.return_lists = []  # Todas as listas retornadas

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Rastreia função."""
        for decorator in node.decorator_list:
            if self._is_executor_decorator(decorator):
                if isinstance(decorator, ast.Call) and decorator.args:
                    arg = decorator.args[0]
                    if isinstance(arg, ast.Constant):
                        self.current_executor_id = arg.value
                        self.return_lists = []

                        self.executors[self.current_executor_id] = {
                            "function": node.name,
                            "file": self.filename,
                            "line": node.lineno,
                            "all_possible_ports": set(),
                            "return_statements": [],
                        }

        self.generic_visit(node)

        if self.current_executor_id:
            # Análise pós-visita
            self._analyze_returns(self.current_executor_id)

        self.current_executor_id = None

    def visit_Return(self, node: ast.Return):
        """Analisa return statements."""
        if not self.current_executor_id:
            return

        if node.value is None:
            self.return_lists.append([])

        elif isinstance(node.value, ast.List):
            items = []
            for elt in node.value.elts:
                if isinstance(elt, ast.Constant):
                    items.append(str(elt.value))
                elif isinstance(elt, ast.Name):
                    items.append(f"${elt.id}")
                else:
                    items.append("<?unknown>")

            self.return_lists.append(items)

            # Adicionar aos portos possíveis
            for item in items:
                self.executors[self.current_executor_id]["all_possible_ports"].add(item)

            self.executors[self.current_executor_id]["return_statements"].append({
                "type": "list",
                "items": items,
                "count": len(items),
                "line": node.lineno,
            })

        elif isinstance(node.value, ast.Name):
            var_name = node.value.id
            self.executors[self.current_executor_id]["return_statements"].append({
                "type": "variable",
                "name": var_name,
                "line": node.lineno,
            })

    def _analyze_returns(self, node_id: str):
        """Analisa padrão de retorno após visitar toda a função."""
        info = self.executors[node_id]
        info["possible_return_lists"] = self.return_lists

        # Contar máximo de elementos em um único return
        max_simultaneous = 0
        if self.return_lists:
            max_simultaneous = max(len(lst) for lst in self.return_lists)

        info["max_simultaneous_outputs"] = max_simultaneous

        # Classificar
        if max_simultaneous == 0:
            info["classification"] = "EMPTY_RETURN"
        elif max_simultaneous == 1:
            info["classification"] = "CONDITIONAL_SINGLE_BRANCH"
        elif max_simultaneous > 1:
            info["classification"] = "ACTUAL_SIMULTANEOUS_MULTI_OUTPUT"

    def _is_executor_decorator(self, decorator) -> bool:
        """Verifica se é @registry.register_executor."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                if (isinstance(decorator.func.value, ast.Name) and
                    decorator.func.value.id == "registry" and
                    decorator.func.attr == "register_executor"):
                    return True
        return False


def analyze_all_executors_v2():
    """Análise corrigida."""
    runtime_nodes_dir = Path("engine/logic/runtime/nodes")
    all_executors = {}

    for py_file in sorted(runtime_nodes_dir.glob("*.py")):
        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            analyzer = ExecutorAnalyzerV2(py_file.name)
            analyzer.visit(tree)

            if analyzer.executors:
                all_executors.update(analyzer.executors)

        except Exception as e:
            print(f"Erro em {py_file.name}: {e}")

    return all_executors


def main():
    print("=" * 80)
    print("PHASE 3E: AUDITORIA V2 - CORRIGIDA")
    print("=" * 80)

    executors = analyze_all_executors_v2()

    print(f"\nTotal de executores: {len(executors)}\n")

    # Contar por classificação
    classifications = defaultdict(int)
    for info in executors.values():
        classifications[info["classification"]] += 1

    print("Por classificação:")
    for cls in sorted(classifications.keys()):
        count = classifications[cls]
        print(f"  {cls}: {count}")

    # Listar multi-output real
    print("\n" + "=" * 80)
    print("ACTUAL SIMULTANEOUS MULTI-OUTPUT (max > 1):")
    print("=" * 80)

    multi_output = {
        node_id: info
        for node_id, info in executors.items()
        if info.get("max_simultaneous_outputs", 0) > 1
    }

    for node_id, info in sorted(multi_output.items()):
        print(f"\n{node_id}")
        print(f"  File: {info['file']}")
        print(f"  Max simultaneous: {info['max_simultaneous_outputs']}")
        print(f"  Possible ports: {', '.join(sorted(info['all_possible_ports']))}")
        print(f"  Return lists:")
        for lst in info.get("possible_return_lists", []):
            print(f"    {lst}")

    # Gerar relatório
    with open("PHASE3E_EXECUTOR_AUDIT_V2.md", "w", encoding="utf-8") as f:
        f.write("# PHASE 3E: AUDITORIA CORRIGIDA (V2)\n\n")
        f.write(f"Total de executores: {len(executors)}\n\n")

        f.write("## Classificação Corrigida\n\n")
        for cls in sorted(classifications.keys()):
            count = classifications[cls]
            f.write(f"- {cls}: {count}\n")

        f.write(f"\n## Actual Simultaneous Multi-Output\n\n")
        f.write(f"Total: {len(multi_output)}\n\n")

        for node_id, info in sorted(multi_output.items()):
            f.write(f"### {node_id}\n\n")
            f.write(f"- Max simultaneous: {info.get('max_simultaneous_outputs')}\n")
            f.write(f"- Possible ports: {', '.join(sorted(info['all_possible_ports']))}\n")
            f.write(f"- Return patterns:\n")
            for lst in info.get("possible_return_lists", []):
                f.write(f"  - {lst}\n")
            f.write("\n")

    print("\n" + "=" * 80)
    print(f"Relatório salvo: PHASE3E_EXECUTOR_AUDIT_V2.md")
    print("=" * 80)

    return executors


if __name__ == "__main__":
    main()
