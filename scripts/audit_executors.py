"""
PHASE 3E AUDITORIA: Análise completa de todos os executores

Encontra:
- Todos os @registry.register_executor
- Tipos de retorno (literal + variável)
- Portas retornadas vs definição canônica
- Casos de multi-output
"""
import ast
import re
from pathlib import Path
from collections import defaultdict


class ExecutorAnalyzer(ast.NodeVisitor):
    """Analisa executores usando AST para capturar padrões de retorno."""

    def __init__(self, filename: str):
        self.filename = filename
        self.executors = defaultdict(dict)
        self.current_function = None
        self.current_executor_id = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Rastreia função sendo analisada."""
        self.current_function = node.name

        # Procurar decorador @registry.register_executor
        for decorator in node.decorator_list:
            if self._is_executor_decorator(decorator):
                # Extrair node_id do decorador
                if isinstance(decorator, ast.Call):
                    if decorator.args:
                        arg = decorator.args[0]
                        if isinstance(arg, ast.Constant):
                            self.current_executor_id = arg.value

                            self.executors[self.current_executor_id] = {
                                "function": node.name,
                                "file": self.filename,
                                "line": node.lineno,
                                "return_statements": [],
                                "return_patterns": set(),
                            }

        self.generic_visit(node)
        self.current_function = None
        self.current_executor_id = None

    def visit_Return(self, node: ast.Return):
        """Analisa statements de return."""
        if not self.current_executor_id:
            return

        if node.value is None:
            # return sem valor
            self.executors[self.current_executor_id]["return_statements"].append(
                {"type": "empty", "line": node.lineno}
            )
            self.executors[self.current_executor_id]["return_patterns"].add("[]")

        elif isinstance(node.value, ast.List):
            # return ["a", "b", ...]
            items = []
            for elt in node.value.elts:
                if isinstance(elt, ast.Constant):
                    items.append(str(elt.value))
                elif isinstance(elt, ast.Name):
                    items.append(f"${elt.id}")  # Variável
                else:
                    items.append("<?unknown>")

            pattern = "[" + ", ".join(items) + "]"
            self.executors[self.current_executor_id]["return_statements"].append(
                {"type": "list", "items": items, "line": node.lineno}
            )
            self.executors[self.current_executor_id]["return_patterns"].add(pattern)

        elif isinstance(node.value, ast.Name):
            # return variable
            var_name = node.value.id
            self.executors[self.current_executor_id]["return_statements"].append(
                {"type": "variable", "name": var_name, "line": node.lineno}
            )
            self.executors[self.current_executor_id]["return_patterns"].add(
                f"${var_name}"
            )

        elif isinstance(node.value, ast.Call):
            # return function_call()
            func_name = self._get_call_name(node.value)
            self.executors[self.current_executor_id]["return_statements"].append(
                {"type": "call", "function": func_name, "line": node.lineno}
            )
            self.executors[self.current_executor_id]["return_patterns"].add(
                f"${func_name}()"
            )

        else:
            # Outro tipo
            self.executors[self.current_executor_id]["return_statements"].append(
                {"type": "unknown", "line": node.lineno}
            )

    def _is_executor_decorator(self, decorator) -> bool:
        """Verifica se decorador é @registry.register_executor."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                if (
                    isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "registry"
                    and decorator.func.attr == "register_executor"
                ):
                    return True
        return False

    def _get_call_name(self, call_node) -> str:
        """Extrai nome da função sendo chamada."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return "unknown"


def analyze_all_executors():
    """Analisa todos os executores em runtime/nodes."""
    runtime_nodes_dir = Path("engine/logic/runtime/nodes")

    all_executors = {}

    for py_file in sorted(runtime_nodes_dir.glob("*.py")):
        print(f"\nAnalisando {py_file.name}...", end=" ")

        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            analyzer = ExecutorAnalyzer(py_file.name)
            analyzer.visit(tree)

            if analyzer.executors:
                print(f"Encontrado: {len(analyzer.executors)} executor(es)")
                all_executors.update(analyzer.executors)
            else:
                print("Nenhum executor")

        except Exception as e:
            print(f"ERRO: {e}")

    return all_executors


def classify_executor(executor_info: dict) -> str:
    """Classifica um executor."""
    patterns = executor_info.get("return_patterns", set())

    # Casos especiais conhecidos
    node_id = executor_info.get("node_id")

    if node_id == "get_progress_bar_value":
        return "PURE_NODE_SHOULD_HAVE_NO_EXECUTOR"

    # Analisar padrões de retorno
    if len(patterns) == 0 or patterns == {"[]"}:
        return "PURE_NODE_SHOULD_HAVE_NO_EXECUTOR"

    if len(patterns) == 1:
        pattern = list(patterns)[0]
        if pattern in {"['next']", "['success']", "['failure']"}:
            return "CONDITIONAL_SINGLE_BRANCH"
        if "if" in str(executor_info.get("return_statements", [])):
            return "CONDITIONAL_SINGLE_BRANCH"

    if len(patterns) > 1:
        # Múltiplos padrões de retorno
        # Verificar se é legacy compatibility
        if "next" in str(patterns) and "exec_success" in str(patterns):
            return "LEGACY_COMPATIBILITY"

        # Verificar se é intencionalmente multi-branch
        if all("$" in p for p in patterns):  # Todas são variáveis
            return "UNKNOWN"  # Pode ser intencional

        # Padrão literal com múltiplos elementos
        for pattern in patterns:
            if pattern.startswith("[") and "," in pattern:
                return "LEGACY_COMPATIBILITY"

    return "UNKNOWN"


def main():
    print("=" * 80)
    print("PHASE 3E: AUDITORIA COMPLETA DE EXECUTORES")
    print("=" * 80)

    executors = analyze_all_executors()

    print(f"\n{'=' * 80}")
    print(f"Total de executores encontrados: {len(executors)}")
    print(f"{'=' * 80}")

    # Processar cada executor
    audit_results = {}

    for node_id, info in sorted(executors.items()):
        info["node_id"] = node_id
        classification = classify_executor(info)
        info["classification"] = classification

        audit_results[node_id] = info

        # Print resumo
        patterns = info.get("return_patterns", set())
        multi = len(patterns) > 1

        print(f"\n[{node_id}]")
        print(f"  File: {info['file']}")
        print(f"  Function: {info['function']} (line {info['line']})")
        print(f"  Return patterns: {len(patterns)}")
        for pattern in sorted(patterns):
            print(f"    - {pattern}")
        print(f"  Classification: {classification}")
        print(f"  Multi-output: {multi}")

    # Análise agregada
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")

    classification_counts = defaultdict(int)
    for info in audit_results.values():
        classification_counts[info["classification"]] += 1

    print("\nPor classificação:")
    for cls in sorted(classification_counts.keys()):
        print(f"  {cls}: {classification_counts[cls]}")

    multi_output = sum(
        1 for info in audit_results.values()
        if len(info.get("return_patterns", set())) > 1
    )
    print(f"\nExecutores com potencial multi-output: {multi_output}")

    # Salvar relatório
    report_path = Path("PHASE3E_EXECUTOR_AUDIT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# PHASE 3E: AUDITORIA COMPLETA DE EXECUTORES\n\n")
        f.write(f"Total de executores: {len(executors)}\n")
        f.write(f"Data: {Path('.').cwd().name}\n\n")

        f.write("## Resumo por Classificação\n\n")
        for cls in sorted(classification_counts.keys()):
            f.write(f"- {cls}: {classification_counts[cls]}\n")

        f.write(f"\n## Multi-output potencial: {multi_output}\n\n")

        f.write("## Detalhes por Executor\n\n")
        for node_id, info in sorted(audit_results.items()):
            f.write(f"### {node_id}\n\n")
            f.write(f"- File: {info['file']}\n")
            f.write(f"- Function: {info['function']}\n")
            f.write(f"- Classification: {info['classification']}\n")
            f.write(f"- Return patterns:\n")
            for pattern in sorted(info.get("return_patterns", set())):
                f.write(f"  - {pattern}\n")
            f.write("\n")

    print(f"\nRelatório salvo em: {report_path}")

    return audit_results


if __name__ == "__main__":
    main()
