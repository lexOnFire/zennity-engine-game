"""Registro e descobrimento de Custom Nodes reutilizáveis (.znode) para o Logic Editor."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from engine.logic.custom_node_asset import (
    CANONICAL_CUSTOM_NODE_DIR,
    load_custom_node_asset,
)
from engine.logic.graph_asset import NODE_DEFINITIONS

_log = logging.getLogger(__name__)


class CustomNodeRegistry:
    """Gerencia assets .znode descobertos e os disponibiliza para a paleta do Logic Editor."""

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._nodes: dict[str, dict[str, Any]] = {}
        self._conflicts: dict[str, list[str]] = {}

    def refresh(self) -> None:
        """Varre o diretório canônico de custom nodes e carrega os assets válidos."""
        self._nodes.clear()
        self._conflicts.clear()

        custom_dir = self.project_root / CANONICAL_CUSTOM_NODE_DIR
        if not custom_dir.exists():
            return

        found_by_id: dict[str, list[tuple[Path, dict[str, Any]]]] = {}

        for file_path in sorted(custom_dir.glob("*.znode")):
            try:
                data = load_custom_node_asset(file_path)
                node_id = data["node_id"]
                if node_id in NODE_DEFINITIONS:
                    _log.warning(
                        f"Custom node em '{file_path.name}' rejeitado: node_id '{node_id}' colide com built-in."
                    )
                    continue

                found_by_id.setdefault(node_id, []).append((file_path, data))
            except Exception as exc:
                _log.warning(f"Erro ao carregar custom node '{file_path.name}': {exc}")

        # Trata colisões entre custom nodes
        for node_id, instances in found_by_id.items():
            if len(instances) > 1:
                paths = [str(p.name) for p, _ in instances]
                self._conflicts[node_id] = paths
                _log.error(
                    f"Colisão de node_id '{node_id}' entre múltiplos assets .znode: {paths}. Todos foram rejeitados."
                )
            else:
                fpath, data = instances[0]
                data["_file_path"] = str(fpath.relative_to(self.project_root)).replace("\\", "/")
                self._nodes[node_id] = data

    @property
    def nodes(self) -> dict[str, dict[str, Any]]:
        """Retorna todos os custom nodes registrados com sucesso."""
        return self._nodes

    @property
    def conflicts(self) -> dict[str, list[str]]:
        """Retorna colisões encontradas."""
        return self._conflicts

    def instantiate_node_data(self, node_id: str, new_node_id: str = "custom_1") -> dict[str, Any]:
        """Gera uma instância de nó independente baseada em Snapshot Semantics."""
        if node_id not in self._nodes:
            raise KeyError(f"Custom node '{node_id}' não está registrado.")

        asset_data = self._nodes[node_id]
        return {
            "id": new_node_id,
            "type": "custom_script",
            "title": asset_data.get("title", "Custom Node"),
            "properties": {
                "execution_model": asset_data.get("execution_model", "pure_data"),
                "inputs": list(asset_data.get("inputs", [])),
                "outputs": list(asset_data.get("outputs", [])),
                "script": str(asset_data.get("script", "")),
                "custom_asset_id": node_id,
                "custom_asset_path": asset_data.get("_file_path", ""),
            },
        }


# Instância global singleton para o editor
_GLOBAL_CUSTOM_NODE_REGISTRY: CustomNodeRegistry | None = None


def get_custom_node_registry(project_root: str | Path | None = None) -> CustomNodeRegistry:
    global _GLOBAL_CUSTOM_NODE_REGISTRY
    if _GLOBAL_CUSTOM_NODE_REGISTRY is None or project_root is not None:
        _GLOBAL_CUSTOM_NODE_REGISTRY = CustomNodeRegistry(project_root)
        _GLOBAL_CUSTOM_NODE_REGISTRY.refresh()
    return _GLOBAL_CUSTOM_NODE_REGISTRY
