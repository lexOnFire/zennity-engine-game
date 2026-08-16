"""Sandbox restrito e contexto de execução para Custom Script Nodes (Pure Data).

SECURITY MODEL:
Trusted Local Project + Restricted Python Surface.
Esta camada restringe a superfície de execução e previne erros comuns e acessos
indesejados no contexto do grafo, mas não constitui uma barreira de segurança
absoluta contra código malicioso arbitrário.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import logging
from types import CodeType
from typing import Any, Mapping

_log = logging.getLogger(__name__)

# Whitelist estrita de funções e tipos built-in permitidos
ALLOWED_BUILTINS: Mapping[str, Any] = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "len": len,
    "bool": bool,
    "float": float,
    "int": int,
    "str": str,
}

# Nós de AST proibidos
DISALLOWED_AST_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
    ast.Global,
    ast.Nonlocal,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.Raise,
    ast.Yield,
    ast.YieldFrom,
    ast.Await,
)

# Funções e identificadores globais proibidos
DISALLOWED_CALL_NAMES = frozenset({
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "help",
    "input",
    "print",
    "exit",
    "quit",
})

# Cache em memória para scripts compilados: hash(source) -> CodeType
_COMPILED_SCRIPT_CACHE: dict[str, CodeType] = {}


class ScriptContext:
    """Contexto de execução restrito passado para scripts de nós customizados."""

    def __init__(
        self,
        inputs: Mapping[str, Any],
        declared_inputs: set[str],
        declared_outputs: set[str],
    ) -> None:
        self._inputs = inputs
        self._declared_inputs = declared_inputs
        self._declared_outputs = declared_outputs
        self._outputs: dict[str, Any] = {}

    def get_input(self, name: str, default: Any = None) -> Any:
        """Lê o valor de uma porta de entrada conectada ou seu valor padrão."""
        if not isinstance(name, str):
            raise TypeError("O nome da porta de entrada deve ser uma string.")
        if name not in self._declared_inputs:
            raise ValueError(f"Porta de entrada '{name}' não foi declarada neste nó.")
        if name in self._inputs:
            return self._inputs[name]
        return default

    def set_output(self, name: str, value: Any) -> None:
        """Define o valor para uma porta de saída declarada."""
        if not isinstance(name, str):
            raise TypeError("O nome da porta de saída deve ser uma string.")
        if name not in self._declared_outputs:
            raise ValueError(f"Porta de saída '{name}' não foi declarada neste nó.")
        self._outputs[name] = value

    @property
    def outputs(self) -> dict[str, Any]:
        """Retorna os outputs gerados pelo script."""
        return self._outputs


class CustomScriptSecurityVisitor(ast.NodeVisitor):
    """Varredor de AST para garantir conformidade com a superfície restrita do MVP."""

    def __init__(self, declared_inputs: set[str], declared_outputs: set[str]) -> None:
        self.declared_inputs = declared_inputs
        self.declared_outputs = declared_outputs
        self.errors: list[str] = []

    def generic_visit(self, node: ast.AST) -> None:
        if isinstance(node, DISALLOWED_AST_NODES):
            node_name = node.__class__.__name__
            self.errors.append(f"Uso de '{node_name}' não é permitido em scripts customizados (linha {getattr(node, 'lineno', '?')}).")
            return
        super().generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("__"):
            self.errors.append(f"Acesso a atributos dunder ('{node.attr}') é proibido (linha {node.lineno}).")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id.startswith("__"):
            self.errors.append(f"Identificador reservado ('{node.id}') é proibido (linha {node.lineno}).")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Checa chamadas a funções globais proibidas
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in DISALLOWED_CALL_NAMES:
                self.errors.append(f"Chamada a '{func_name}()' é proibida (linha {node.lineno}).")

        # Checa chamadas a ctx.get_input / ctx.set_output
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "ctx":
            method_name = node.func.attr
            if method_name not in {"get_input", "set_output"}:
                self.errors.append(f"Método 'ctx.{method_name}()' não existe no contexto do script (linha {node.lineno}).")
            else:
                if not node.args:
                    self.errors.append(f"Chamada a 'ctx.{method_name}()' requer o nome da porta como argumento (linha {node.lineno}).")
                else:
                    first_arg = node.args[0]
                    if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
                        self.errors.append(
                            f"Chamada a 'ctx.{method_name}()' deve usar nome literal de porta entre aspas (linha {node.lineno})."
                        )
                    else:
                        port_name = first_arg.value
                        if method_name == "get_input" and port_name not in self.declared_inputs:
                            self.errors.append(
                                f"Porta de entrada '{port_name}' lida em ctx.get_input() não está declarada no nó (linha {node.lineno})."
                            )
                        elif method_name == "set_output" and port_name not in self.declared_outputs:
                            self.errors.append(
                                f"Porta de saída '{port_name}' escrita em ctx.set_output() não está declarada no nó (linha {node.lineno})."
                            )

        self.generic_visit(node)


def validate_custom_script(
    source: str,
    declared_inputs: set[str] | list[str],
    declared_outputs: set[str] | list[str],
) -> tuple[bool, str]:
    """Valida sintaxe e conformidade de segurança do script com as portas declaradas."""
    if not str(source).strip():
        return True, ""

    try:
        tree = ast.parse(source, filename="<custom_script>", mode="exec")
    except SyntaxError as e:
        return False, f"Erro de sintaxe na linha {e.lineno}: {e.msg}"

    visitor = CustomScriptSecurityVisitor(set(declared_inputs), set(declared_outputs))
    visitor.visit(tree)

    if visitor.errors:
        return False, "\n".join(visitor.errors)

    return True, ""


def compile_custom_script(source: str, script_id: str = "custom_script") -> CodeType:
    """Compila o script Python com cache em memória baseado em hash."""
    source_clean = str(source or "")
    source_hash = hashlib.sha256(source_clean.encode("utf-8")).hexdigest()

    if source_hash in _COMPILED_SCRIPT_CACHE:
        return _COMPILED_SCRIPT_CACHE[source_hash]

    code = compile(source_clean, f"<{script_id}>", "exec")
    _COMPILED_SCRIPT_CACHE[source_hash] = code
    return code


def execute_custom_script(
    code: CodeType,
    ctx: ScriptContext,
) -> None:
    """Executa o script compilado em ambiente estritamente restrito."""
    restricted_globals: dict[str, Any] = {
        "__builtins__": dict(ALLOWED_BUILTINS),
        "ctx": ctx,
    }
    local_vars: dict[str, Any] = {}
    exec(code, restricted_globals, local_vars)
