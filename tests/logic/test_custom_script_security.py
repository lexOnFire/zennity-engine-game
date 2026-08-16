"""Testes de segurança e AST sandbox para o Custom Script Node (Pure Data)."""
from __future__ import annotations

import pytest

from engine.logic.runtime.custom_script_sandbox import (
    ScriptContext,
    compile_custom_script,
    execute_custom_script,
    validate_custom_script,
)


def test_disallowed_imports_rejected():
    source = "import os\nctx.set_output('out', 1)"
    valid, err = validate_custom_script(source, {"in"}, {"out"})
    assert valid is False
    assert "Import" in err


def test_disallowed_import_from_rejected():
    source = "from subprocess import Popen\nctx.set_output('out', 1)"
    valid, err = validate_custom_script(source, {"in"}, {"out"})
    assert valid is False
    assert "ImportFrom" in err


def test_disallowed_functions_and_classes_rejected():
    for construct in ("def evil(): pass", "class Evil: pass", "lambda x: x"):
        valid, err = validate_custom_script(f"{construct}\nctx.set_output('out', 1)", {"in"}, {"out"})
        assert valid is False, f"Expected {construct} to be rejected"


def test_disallowed_calls_rejected():
    for evil_call in ("eval('1+1')", "exec('a=1')", "open('secret.txt')", "__import__('os')"):
        valid, err = validate_custom_script(f"{evil_call}\nctx.set_output('out', 1)", {"in"}, {"out"})
        assert valid is False, f"Expected call {evil_call} to be rejected"


def test_disallowed_dunder_attributes_rejected():
    for dunder in ("().__class__", "ctx.__class__", "object.__subclasses__()"):
        valid, err = validate_custom_script(f"x = {dunder}\nctx.set_output('out', 1)", {"in"}, {"out"})
        assert valid is False, f"Expected dunder {dunder} to be rejected"


def test_non_literal_port_names_rejected():
    source = """
name = 'base_damage'
val = ctx.get_input(name)
ctx.set_output('out', val)
"""
    valid, err = validate_custom_script(source, {"base_damage"}, {"out"})
    assert valid is False
    assert "nome literal de porta entre aspas" in err


def test_undeclared_port_names_rejected():
    source = "ctx.set_output('missing_out', 42)"
    valid, err = validate_custom_script(source, {"in"}, {"out"})
    assert valid is False
    assert "não está declarada no nó" in err
