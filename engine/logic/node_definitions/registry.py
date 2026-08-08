"""
PHASE 3D: Canonical Node Definition Registry

Single source of truth for all node definitions.
Supports gradual migration from legacy to canonical.
"""
from typing import Dict, Optional, Any
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


# Singleton instance
_registry: Optional[NodeDefinitionRegistry] = None


def get_registry() -> NodeDefinitionRegistry:
    """Get or create the singleton registry."""
    global _registry

    if _registry is None:
        _registry = NodeDefinitionRegistry()

    return _registry


def resolve_node_definition(node_id: str) -> Optional[Any]:
    """
    Resolve a node definition from the registry.

    Canonical first, then legacy fallback.
    """
    return get_registry().get(node_id)
