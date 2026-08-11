"""
PHASE 3D: Canonical Node Definition Registry
PHASE 9.5B Stage 2: the registry is now the ONE mutable definition source.

Beyond the original canonical/legacy resolution it owns:

* ``_resolved``    -- the unified definition dict per node id (the source)
* ``_port_schema`` -- the pins per node id, derived from the same build
* owner metadata   -- which module defined a node, which module implements it

``engine.logic.node_definitions.NODE_DEFINITIONS`` and
``engine.logic.graph_asset.NODE_PORT_DEFINITIONS`` are read-only views over
this store.  Nothing outside :mod:`engine.logic.node_definitions.catalogue`
should mutate it.
"""
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class NodeDefinitionConflictError(Exception):
    """Raised when two definitions for the same node ID conflict."""

    def __init__(self, node_id: str, existing: Any, new: Any):
        self.node_id = node_id
        self.existing = existing
        self.new = new

        msg = f"\nNode '{node_id}' has conflicting definitions:\n"
        msg += f"  Existing: {self._fingerprint(existing)}\n"
        msg += f"  New: {self._fingerprint(new)}"

        super().__init__(msg)

    @staticmethod
    def _fingerprint(definition) -> str:
        """Create a short fingerprint of a definition."""
        if hasattr(definition, 'id'):
            inputs = [p.id for p in getattr(definition, 'inputs', [])]
            outputs = [p.id for p in getattr(definition, 'outputs', [])]
            return f"id={definition.id}, inputs={inputs}, outputs={outputs}"
        elif isinstance(definition, dict):
            inputs = [p[0] if isinstance(p, tuple) else p for p in definition.get('inputs', [])]
            outputs = [p[0] if isinstance(p, tuple) else p for p in definition.get('outputs', [])]
            return f"id={definition.get('id')}, inputs={inputs}, outputs={outputs}"
        return str(definition)


class NodeDefinitionRegistry:
    """
    Central registry for node definitions.

    Strategy:
    1. Canonical (class-based) definitions are primary
    2. Legacy (dict-based) definitions are fallback
    3. Conflicts are detected and raise errors
    4. Adapters convert legacy to canonical on-demand
    """

    def __init__(self):
        self._canonical: Dict[str, Any] = {}
        self._legacy: Dict[str, Any] = {}
        self._adapters: Dict[str, Any] = {}
        # Stage 2 -- unified catalogue storage.
        self._resolved: Dict[str, dict] = {}
        self._port_schema: Dict[str, dict] = {}
        self._definition_owner: Dict[str, str] = {}
        self._runtime_owner: Dict[str, str] = {}
        self._execution_model: Dict[str, str] = {}
        self._definitions_view: Optional[Mapping[str, dict]] = None
        self._port_schema_view: Optional[Mapping[str, dict]] = None

    def register_canonical(self, definition: Any, allow_override: bool = False):
        """Register a canonical (class-based) definition."""
        node_id = definition.id

        if node_id in self._canonical:
            if not allow_override:
                raise NodeDefinitionConflictError(
                    node_id, self._canonical[node_id], definition
                )
            logger.warning(f"Overriding canonical definition for {node_id}")

        self._canonical[node_id] = definition
        logger.debug(f"Registered canonical node: {node_id}")

    def register_legacy(self, node_id: str, definition: dict, allow_override: bool = False):
        """
        Register a legacy (dict-based) definition as fallback.

        Legacy definitions are only used if no canonical definition exists.
        """
        if node_id in self._legacy:
            if not allow_override:
                logger.warning(f"Legacy definition for {node_id} already exists, skipping")
                return

        self._legacy[node_id] = definition
        logger.debug(f"Registered legacy node (fallback): {node_id}")

    def get(self, node_id: str) -> Optional[Any]:
        """
        Get a definition by ID, resolving canonical → legacy.

        Returns:
            Canonical definition if exists, else adapted legacy, else None
        """
        # Canonical first
        if node_id in self._canonical:
            return self._canonical[node_id]

        # Fallback to legacy (with adapter)
        if node_id in self._legacy:
            if node_id not in self._adapters:
                # Lazy-adapt legacy definition
                self._adapters[node_id] = self._adapt_legacy(node_id, self._legacy[node_id])

            return self._adapters[node_id]

        return None

    def contains(self, node_id: str) -> bool:
        """Check if a definition exists."""
        return node_id in self._canonical or node_id in self._legacy

    def all_canonical(self) -> Dict[str, Any]:
        """Return all canonical definitions."""
        return dict(self._canonical)

    def all_legacy(self) -> Dict[str, Any]:
        """Return all legacy definitions."""
        return dict(self._legacy)

    def all_resolved(self) -> Dict[str, Any]:
        """Return all definitions (canonical + adapted legacy)."""
        result = {}

        # Canonical nodes
        result.update(self._canonical)

        # Legacy nodes (only if not overridden by canonical)
        for node_id, legacy_def in self._legacy.items():
            if node_id not in result:
                result[node_id] = self.get(node_id)

        return result

    def get_stats(self) -> dict:
        """Return statistics about registry."""
        return {
            "canonical_count": len(self._canonical),
            "legacy_count": len(self._legacy),
            "overlap_count": len(
                set(self._canonical.keys()) & set(self._legacy.keys())
            ),
            "legacy_only_count": len(
                set(self._legacy.keys()) - set(self._canonical.keys())
            ),
            "canonical_only_count": len(
                set(self._canonical.keys()) - set(self._legacy.keys())
            ),
            "total_unique": len(self.all_resolved()),
        }

    def _adapt_legacy(self, node_id: str, legacy: dict) -> Any:
        """
        Adapt a legacy definition to the NodeDefinition interface.

        This is a placeholder - the actual adapter should be in a separate module
        to keep concerns separated.
        """
        logger.debug(f"Adapting legacy definition: {node_id}")

        # Mark as legacy
        legacy_adapted = dict(legacy)
        legacy_adapted["_legacy"] = True

        return legacy_adapted

    def detect_conflicts(self) -> list[str]:
        """
        Detect definitions with the same ID but different contracts.

        Returns:
            List of node IDs with conflicts
        """
        conflicts = []

        for node_id in self._canonical:
            if node_id in self._legacy:
                # Check if contracts match
                canonical_fp = self._fingerprint_canonical(self._canonical[node_id])
                legacy_fp = self._fingerprint_legacy(self._legacy[node_id])

                if canonical_fp != legacy_fp:
                    conflicts.append(node_id)
                    logger.warning(f"Conflict detected for {node_id}")

        return conflicts

    @staticmethod
    def _fingerprint_canonical(definition) -> str:
        """Create fingerprint of canonical definition."""
        if not hasattr(definition, 'id'):
            return str(definition)

        inputs = tuple(p.id for p in getattr(definition, 'inputs', []))
        outputs = tuple(p.id for p in getattr(definition, 'outputs', []))

        return f"{definition.id}|{inputs}|{outputs}"

    @staticmethod
    def _fingerprint_legacy(definition: dict) -> str:
        """Create fingerprint of legacy definition."""
        node_id = definition.get('id')
        inputs = tuple(
            p[0] if isinstance(p, tuple) else p
            for p in definition.get('inputs', [])
        )
        outputs = tuple(
            p[0] if isinstance(p, tuple) else p
            for p in definition.get('outputs', [])
        )

        return f"{node_id}|{inputs}|{outputs}"


    # ------------------------------------------------------------------
    # Stage 2: unified catalogue storage
    # ------------------------------------------------------------------

    def reset_catalogue(self) -> None:
        """Drop the built catalogue so it can be rebuilt from the seeds."""
        self._resolved.clear()
        self._port_schema.clear()
        self._definition_owner.clear()
        self._execution_model.clear()
        self._canonical.clear()
        self._adapters.clear()
        self._definitions_view = None
        self._port_schema_view = None

    def set_resolved(self, node_id: str, definition: dict) -> None:
        self._resolved[node_id] = definition
        self._definitions_view = None

    def set_port_schema(self, node_id: str, schema: dict) -> None:
        self._port_schema[node_id] = schema
        self._port_schema_view = None

    def set_definition_owner(self, node_id: str, module_name: str) -> None:
        self._definition_owner[node_id] = module_name

    def set_runtime_owner(self, node_id: str, module_name: str) -> None:
        self._runtime_owner[node_id] = module_name

    def set_execution_model(self, node_id: str, model: str) -> None:
        self._execution_model[node_id] = model

    def definitions_view(self) -> Mapping[str, dict]:
        """Read-only mapping of node id -> resolved definition."""
        if self._definitions_view is None:
            self._definitions_view = MappingProxyType(self._resolved)
        return self._definitions_view

    def port_schema_view(self) -> Mapping[str, dict]:
        """Read-only mapping of node id -> {"inputs": [...], "outputs": [...]}."""
        if self._port_schema_view is None:
            self._port_schema_view = MappingProxyType(self._port_schema)
        return self._port_schema_view

    @property
    def definitions(self) -> Mapping[str, dict]:
        """Resolved definitions, building the catalogue on first access."""
        from .catalogue import ensure_catalogue_loaded

        ensure_catalogue_loaded()
        return self.definitions_view()

    def definition_owner(self, node_id: str) -> Optional[str]:
        return self._definition_owner.get(node_id)

    def runtime_owner(self, node_id: str) -> Optional[str]:
        return self._runtime_owner.get(node_id)

    def execution_model(self, node_id: str) -> Optional[str]:
        return self._execution_model.get(node_id)

    def schema_drift(self) -> list[str]:
        """Node ids whose definition pins disagree with the port schema.

        By construction this must always be empty; a non-empty result means
        something re-introduced an independent port table.
        """
        drift: list[str] = []
        for node_id, definition in self._resolved.items():
            schema = self._port_schema.get(node_id)
            if schema is None:
                drift.append(node_id)
                continue
            same_inputs = [tuple(p) for p in definition.get("inputs", [])] == [
                tuple(p) for p in schema.get("inputs", [])
            ]
            same_outputs = [tuple(p) for p in definition.get("outputs", [])] == [
                tuple(p) for p in schema.get("outputs", [])
            ]
            if not (same_inputs and same_outputs):
                drift.append(node_id)
        return drift


# Singleton instance
_registry: Optional[NodeDefinitionRegistry] = None


def get_registry() -> NodeDefinitionRegistry:
    """Get or create the singleton registry."""
    global _registry

    if _registry is None:
        _registry = NodeDefinitionRegistry()

    return _registry


#: Canonical singleton accessor used by the runtime port validator.
node_registry = get_registry()


def resolve_node_definition(node_id: str) -> Optional[Any]:
    """
    Resolve a node definition from the registry.

    Canonical first, then legacy fallback.
    """
    return get_registry().get(node_id)
