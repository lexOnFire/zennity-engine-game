"""
PHASE 3C: Graph migration - Legacy impure nodes → Pure data nodes

Core principle:
- Remove flow edges from nodes that became pure
- Bypass flow if 1 input + 1 output (semantic preservation)
- Never convert flow edge to data edge by renaming
- Validate type compatibility
"""
from typing import Any, Mapping, Optional
import logging

logger = logging.getLogger(__name__)


# Nodes that changed from impure to pure
IMPURE_TO_PURE_NODES = {
    "get_progress_bar_value",
    # Add more as needed
}


class GraphMigrationWarning:
    """Track migration issues that need human review."""

    def __init__(self, node_id: str, node_type: str, issue: str):
        self.node_id = node_id
        self.node_type = node_type
        self.issue = issue

    def __repr__(self):
        return f"GraphMigrationWarning({self.node_id}: {self.issue})"


class GraphMigration:
    """Migrate legacy graph format to canonical."""

    def __init__(self, graph: dict):
        self.graph = graph
        self.nodes = {n["id"]: n for n in graph.get("nodes", [])}
        self.edges = list(graph.get("edges", []))
        self.warnings: list[GraphMigrationWarning] = []

    def migrate(self) -> tuple[dict, list[GraphMigrationWarning]]:
        """Perform migration and return (migrated_graph, warnings)."""

        format_version = self.graph.get("format_version", 1)

        if format_version >= 2:
            return self.graph, []  # Already canonical

        logger.info(f"Migrating graph from v{format_version} to v2")

        # Handle v1 → v2 migrations
        if format_version < 2:
            self._migrate_impure_to_pure_nodes()

        # Update format version
        self.graph["format_version"] = 2
        self.graph["edges"] = self.edges

        return self.graph, self.warnings

    def _migrate_impure_to_pure_nodes(self):
        """Remove flow edges from nodes that became pure."""

        edges_to_remove = []
        edges_to_add = []

        for node_id, node in self.nodes.items():
            node_type = node.get("type", "")

            if node_type not in IMPURE_TO_PURE_NODES:
                continue

            logger.debug(f"Migrating {node_type} node '{node_id}' from impure to pure")

            # Find all flow edges connected to this node
            incoming_flow = self._find_edges(
                lambda e: e.get("to_node") == node_id and e.get("kind") == "flow"
            )
            outgoing_flow = self._find_edges(
                lambda e: e.get("from_node") == node_id and e.get("kind") == "flow"
            )
            data_edges = self._find_edges(
                lambda e: (e.get("to_node") == node_id or e.get("from_node") == node_id)
                         and e.get("kind") == "data"
            )

            logger.debug(
                f"  incoming_flow={len(incoming_flow)}, "
                f"outgoing_flow={len(outgoing_flow)}, "
                f"data_edges={len(data_edges)}"
            )

            # Handle based on flow edge count
            if len(incoming_flow) == 0 and len(outgoing_flow) == 0:
                # Pure node with no flow - already correct
                logger.debug(f"  Node '{node_id}' already has no flow edges")
                continue

            elif len(incoming_flow) == 1 and len(outgoing_flow) == 1:
                # Single input, single output - bypass
                self._bypass_node_flow(
                    node_id, incoming_flow[0], outgoing_flow[0],
                    edges_to_remove, edges_to_add
                )

            elif len(incoming_flow) == 0 and len(outgoing_flow) >= 1:
                # No input flow, remove output flow(s)
                logger.debug(f"  Node '{node_id}' has no incoming flow, removing outgoing")
                edges_to_remove.extend(outgoing_flow)

            elif len(incoming_flow) >= 1 and len(outgoing_flow) == 0:
                # Has input flow but no output - just remove input
                logger.debug(f"  Node '{node_id}' has no outgoing flow, removing incoming")
                edges_to_remove.extend(incoming_flow)

            else:
                # Multiple incoming or outgoing flow edges - ambiguous
                logger.debug(
                    f"  Node '{node_id}' has {len(incoming_flow)} in, {len(outgoing_flow)} out"
                )
                self._handle_ambiguous_flow(
                    node_id, node_type, incoming_flow, outgoing_flow
                )

        # Apply edge changes
        for edge in edges_to_remove:
            self.edges.remove(edge)

        self.edges.extend(edges_to_add)

        logger.info(
            f"Migration: removed {len(edges_to_remove)} flow edges, "
            f"added {len(edges_to_add)} bypass edges"
        )

    def _find_edges(self, predicate) -> list[dict]:
        """Find edges matching predicate."""
        return [e for e in self.edges if predicate(e)]

    def _bypass_node_flow(self, node_id: str, incoming: dict, outgoing: dict,
                         remove_list: list, add_list: list):
        """Bypass flow when node has exactly 1 in and 1 out."""

        logger.debug(
            f"Bypassing flow: {incoming['from_node']}:{incoming['from_port']} "
            f"→ {outgoing['to_node']}:{outgoing['to_port']}"
        )

        # Create bypass edge
        bypass_edge = {
            "id": f"{incoming['id']}_bypass_{outgoing['id']}",
            "from_node": incoming["from_node"],
            "from_port": incoming["from_port"],
            "to_node": outgoing["to_node"],
            "to_port": outgoing["to_port"],
            "kind": "flow",
            "order": incoming.get("order", 0),
        }

        remove_list.append(incoming)
        remove_list.append(outgoing)
        add_list.append(bypass_edge)

    def _handle_ambiguous_flow(self, node_id: str, node_type: str,
                              incoming: list, outgoing: list):
        """Handle ambiguous migration scenarios."""

        warning = GraphMigrationWarning(
            node_id,
            node_type,
            f"Ambiguous flow migration: {len(incoming)} incoming, {len(outgoing)} outgoing flow edges. "
            f"Cannot automatically bypass. Manual review required."
        )

        self.warnings.append(warning)
        logger.warning(f"  {warning}")

        # Conservative: remove all flow edges and let data edges work
        for edge in incoming + outgoing:
            if edge in self.edges:
                self.edges.remove(edge)


def migrate_graph_if_needed(graph: dict) -> tuple[dict, list[GraphMigrationWarning]]:
    """
    Load and migrate graph to canonical format if needed.

    Returns:
        (migrated_graph, migration_warnings)
    """

    format_version = graph.get("format_version", 1)

    if format_version >= 2:
        return graph, []

    migration = GraphMigration(graph)
    return migration.migrate()
