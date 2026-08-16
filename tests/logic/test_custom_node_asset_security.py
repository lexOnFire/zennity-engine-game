"""Testes de segurança e validação estrita para assets .znode (D2.4)."""
from __future__ import annotations

from pathlib import Path
import pytest

from engine.logic.custom_node_asset import (
    save_custom_node_asset,
    validate_custom_node_asset,
)


def test_custom_node_asset_security_blocks_import():
    """Testa que tentativa de importar módulos no .znode é bloqueada."""
    data = {
        "node_id": "malicious_node",
        "title": "Malicious Node",
        "category": "Custom",
        "execution_model": "pure_data",
        "inputs": [],
        "outputs": [],
        "script": "import os\nctx.set_output('out', 1)",
    }
    valid, err = validate_custom_node_asset(data)
    assert valid is False
    assert "Import" in err


def test_custom_node_asset_security_blocks_dunder():
    """Testa que acessos a atributos dunder no .znode são bloqueados."""
    data = {
        "node_id": "dunder_node",
        "title": "Dunder Node",
        "category": "Custom",
        "execution_model": "pure_data",
        "inputs": [],
        "outputs": [],
        "script": "x = ().__class__.__bases__",
    }
    valid, err = validate_custom_node_asset(data)
    assert valid is False
    assert "dunder" in err


def test_custom_node_asset_rejects_empty_or_invalid_id():
    """Testa que IDs vazios ou com caracteres proibidos (ex: path separators) são rejeitados."""
    for invalid_id in ("", " ", "my-node", "../evil", "My Node", "calc/damage"):
        data = {
            "node_id": invalid_id,
            "title": "Test",
            "execution_model": "pure_data",
            "inputs": [],
            "outputs": [],
            "script": "",
        }
        valid, err = validate_custom_node_asset(data)
        assert valid is False, f"Expected {invalid_id!r} to be rejected"
