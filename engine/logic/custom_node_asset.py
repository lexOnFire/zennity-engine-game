"""Asset loader, serializer e validador para nós customizados reutilizáveis (.znode)."""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Mapping

from engine.logic.graph_asset import NODE_DEFINITIONS
from engine.logic.runtime.custom_script_sandbox import validate_custom_script

_log = logging.getLogger(__name__)

CUSTOM_NODE_FORMAT = "zennity.custom_node"
CUSTOM_NODE_FORMAT_VERSION = 1
CANONICAL_CUSTOM_NODE_DIR = "Assets/Logic/CustomNodes"

VALID_NODE_ID_REGEX = re.compile(r"^[a-z0-9_]+$")
ALLOWED_PORT_TYPES = frozenset({"number", "bool", "text", "object", "any"})


def is_valid_custom_node_id(node_id: str) -> bool:
    """Verifica se o node_id é uma string snake_case válida."""
    if not isinstance(node_id, str):
        return False
    node_id_clean = node_id.strip()
    if not node_id_clean:
        return False
    return bool(VALID_NODE_ID_REGEX.match(node_id_clean))


def validate_custom_node_asset(data: Mapping[str, Any]) -> tuple[bool, str]:
    """Valida a conformidade de dados de um asset .znode com o schema versionado."""
    if not isinstance(data, Mapping):
        return False, "O conteúdo do asset .znode deve ser um objeto JSON."

    format_name = data.get("format", CUSTOM_NODE_FORMAT)
    if format_name != CUSTOM_NODE_FORMAT:
        return False, f"Formato inválido: '{format_name}'. Esperado: '{CUSTOM_NODE_FORMAT}'."

    version = data.get("format_version", CUSTOM_NODE_FORMAT_VERSION)
    if version != CUSTOM_NODE_FORMAT_VERSION:
        return False, f"Versão de formato não suportada: {version}. Versão atual suportada: {CUSTOM_NODE_FORMAT_VERSION}."

    node_id = str(data.get("node_id", "")).strip()
    if not node_id:
        return False, "Campo 'node_id' não pode ser vazio."

    if not is_valid_custom_node_id(node_id):
        return False, f"'node_id' inválido: '{node_id}'. Deve ser snake_case alfanumérico (ex: calculate_damage)."

    # Verifica colisão com nós built-in
    if node_id in NODE_DEFINITIONS:
        return False, f"Colisão de node_id: '{node_id}' já é um nó built-in da engine."

    title = str(data.get("title", "")).strip()
    if not title:
        return False, "Campo 'title' não pode ser vazio."

    execution_model = str(data.get("execution_model", "pure_data")).lower()
    if execution_model not in ("pure_data", "action"):
        return False, f"execution_model inválido: '{execution_model}'. Esperado 'pure_data' ou 'action'."

    inputs = data.get("inputs", [])
    if not isinstance(inputs, list):
        return False, "Campo 'inputs' deve ser uma lista."

    declared_in: set[str] = set()
    for idx, pin in enumerate(inputs):
        if not isinstance(pin, Mapping):
            return False, f"Input no índice {idx} deve ser um objeto."
        name = str(pin.get("name", "")).strip()
        if not name:
            return False, f"Input no índice {idx} possui nome vazio."
        if name in declared_in:
            return False, f"Porta de input duplicada: '{name}'."
        ptype = str(pin.get("type", "number"))
        if ptype not in ALLOWED_PORT_TYPES:
            return False, f"Tipo de input inválido: '{ptype}' na porta '{name}'."
        declared_in.add(name)

    outputs = data.get("outputs", [])
    if not isinstance(outputs, list):
        return False, "Campo 'outputs' deve ser uma lista."

    declared_out: set[str] = set()
    for idx, pin in enumerate(outputs):
        if not isinstance(pin, Mapping):
            return False, f"Output no índice {idx} deve ser um objeto."
        name = str(pin.get("name", "")).strip()
        if not name:
            return False, f"Output no índice {idx} possui nome vazio."
        if name in declared_out:
            return False, f"Porta de output duplicada: '{name}'."
        ptype = str(pin.get("type", "number"))
        if ptype not in ALLOWED_PORT_TYPES:
            return False, f"Tipo de output inválido: '{ptype}' na porta '{name}'."
        declared_out.add(name)

    script_source = str(data.get("script", ""))
    valid_script, err_msg = validate_custom_script(
        script_source,
        declared_in,
        declared_out,
        execution_model=execution_model,
    )
    if not valid_script:
        return False, f"Erro de validação no script: {err_msg}"

    return True, ""


def load_custom_node_asset(path: str | Path) -> dict[str, Any]:
    """Carrega e valida um asset .znode a partir do disco."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Arquivo .znode não encontrado: {path}")

    content = p.read_text(encoding="utf-8")
    data = json.loads(content)

    valid, err_msg = validate_custom_node_asset(data)
    if not valid:
        raise ValueError(f"Asset .znode inválido ({p.name}): {err_msg}")

    return data


def save_custom_node_asset(path: str | Path, data: Mapping[str, Any]) -> None:
    """Valida e salva um asset .znode formatado e determinístico no disco."""
    valid, err_msg = validate_custom_node_asset(data)
    if not valid:
        raise ValueError(f"Não é possível salvar asset .znode inválido: {err_msg}")

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    ordered_data: dict[str, Any] = {
        "format": CUSTOM_NODE_FORMAT,
        "format_version": CUSTOM_NODE_FORMAT_VERSION,
        "node_id": str(data["node_id"]).strip(),
        "title": str(data.get("title", data["node_id"])).strip(),
        "category": str(data.get("category", "Custom")).strip() or "Custom",
        "execution_model": str(data.get("execution_model", "pure_data")).lower(),
        "inputs": list(data.get("inputs", [])),
        "outputs": list(data.get("outputs", [])),
        "script": str(data.get("script", "")),
    }

    if "description" in data and data["description"]:
        ordered_data["description"] = str(data["description"]).strip()

    content = json.dumps(ordered_data, indent=2, ensure_ascii=False) + "\n"
    p.write_text(content, encoding="utf-8")
