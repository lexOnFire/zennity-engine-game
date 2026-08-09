"""Trava o contrato entre executores e portas declaradas.

O runtime casa o ``from_port`` de uma aresta com o nome que o executor retorna
(ver ``LogicGraphRuntime._follow``). Se um executor retorna um nome que nao existe
nas portas declaradas do no, o editor nunca consegue desenhar essa aresta e o fluxo
morre em silencio -- sem erro, sem aviso, sem falha de validacao.

Esses dois testes varrem todos os executores registrados e falham se a divergencia
voltar a aparecer.
"""
from __future__ import annotations

import ast
import collections
import pathlib

from engine.logic.graph_asset import node_port_definitions

NODES_DIR = pathlib.Path(__file__).resolve().parents[2] / "engine" / "logic" / "runtime" / "nodes"


def _registered_types(decorator: ast.expr) -> list[str]:
    """Tipos de no declarados em @registry.register_executor(...)."""
    if not isinstance(decorator, ast.Call):
        return []
    name = getattr(decorator.func, "attr", getattr(decorator.func, "id", ""))
    if name != "register_executor" or not decorator.args:
        return []
    arg = decorator.args[0]
    if isinstance(arg, ast.Constant):
        return [arg.value]
    if isinstance(arg, (ast.Tuple, ast.List)):
        return [e.value for e in arg.elts if isinstance(e, ast.Constant)]
    return []


def _returned_ports(fn: ast.FunctionDef) -> set[str]:
    """Strings literais devolvidas em ``return [...]`` dentro do executor."""
    ports: set[str] = set()
    for node in ast.walk(fn):
        if not (isinstance(node, ast.Return) and isinstance(node.value, (ast.List, ast.Tuple))):
            continue
        for element in node.value.elts:
            candidates = (
                [element] if isinstance(element, ast.Constant)
                else [element.body, element.orelse] if isinstance(element, ast.IfExp)
                else []
            )
            for candidate in candidates:
                if isinstance(candidate, ast.Constant) and isinstance(candidate.value, str):
                    ports.add(candidate.value)
    return ports


def _collect() -> dict[str, list[tuple[str, int, set[str]]]]:
    """type -> [(arquivo, linha, portas retornadas)], na ordem de registro."""
    found: dict[str, list[tuple[str, int, set[str]]]] = collections.defaultdict(list)
    for path in sorted(NODES_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in tree.body:
            if not isinstance(fn, ast.FunctionDef):
                continue
            for decorator in fn.decorator_list:
                for node_type in _registered_types(decorator):
                    found[node_type].append((path.name, fn.lineno, _returned_ports(fn)))
    return found


def test_no_duplicate_executor_registrations():
    """Registrar o mesmo tipo duas vezes apaga a primeira implementacao em silencio."""
    duplicates = {
        node_type: [f"{f}:{line}" for f, line, _ in regs]
        for node_type, regs in _collect().items()
        if len(regs) > 1
    }
    assert not duplicates, (
        "Tipos com mais de um executor (o ultimo registrado vence e apaga os outros): "
        f"{duplicates}"
    )


def test_executors_only_return_declared_flow_ports():
    """Toda porta devolvida por um executor precisa existir na definicao do no."""
    offenders = {}
    for node_type, regs in _collect().items():
        source_file, line, returned = regs[-1]
        if not returned:
            continue
        declared = {port for port, _kind in node_port_definitions(node_type).get("outputs", [])}
        if not declared:
            continue
        unknown = returned - declared
        if unknown:
            offenders[node_type] = {
                "onde": f"{source_file}:{line}",
                "retorna": sorted(unknown),
                "declaradas": sorted(declared),
            }
    assert not offenders, (
        "Executores devolvendo portas que o no nao declara -- o fluxo morre nesses nos: "
        f"{offenders}"
    )
