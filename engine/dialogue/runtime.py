"""Sessões executáveis para Dialogue Graphs da Zennity Engine."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping


class DialogueSession:
    """Navega falas, escolhas, condições, eventos e encerramento."""

    def __init__(
        self,
        graph: Mapping[str, Any],
        variables: Mapping[str, Any] | None = None,
        event_sink: Callable[[str, Any], None] | None = None,
    ) -> None:
        if str(graph.get("format", "")) != "zennity.generic_graph":
            raise ValueError("Formato de Dialogue Graph inválido.")
        if str(graph.get("category", "")).casefold() != "dialogue":
            raise ValueError("O documento não pertence à categoria Dialogue.")
        self.nodes = {
            str(node["id"]): dict(node)
            for node in graph.get("nodes", [])
            if isinstance(node, Mapping) and node.get("id")
        }
        self.routes: dict[str, dict[str, str]] = {}
        incoming: set[str] = set()
        for edge in graph.get("edges", []):
            if not isinstance(edge, Mapping):
                continue
            source, target = str(edge.get("source_node", "")), str(edge.get("target_node", ""))
            port = str(edge.get("source_port", "out"))
            if source in self.nodes and target in self.nodes:
                self.routes.setdefault(source, {})[port] = target
                incoming.add(target)
        roots = [node_id for node_id in self.nodes if node_id not in incoming]
        self.entry = roots[0] if roots else (next(iter(self.nodes), ""))
        self.variables = dict(variables or {})
        self.event_sink = event_sink or (lambda _name, _payload: None)
        self.current_id = ""
        self.active = False

    @classmethod
    def load(cls, path: str | Path, **kwargs: Any) -> "DialogueSession":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data, **kwargs)

    def start(self) -> dict[str, Any]:
        self.current_id = self.entry
        self.active = bool(self.current_id)
        return self._resolve_automatic()

    def advance(self) -> dict[str, Any]:
        if not self.active:
            return self.snapshot()
        self.current_id = self.routes.get(self.current_id, {}).get("out", "")
        return self._resolve_automatic()

    def choose(self, option: int | str) -> dict[str, Any]:
        if not self.active or self._kind() != "dialogue.choice":
            raise RuntimeError("Não há uma escolha ativa.")
        port = str(option)
        if port.isdigit():
            port = f"option_{port}"
        self.current_id = self.routes.get(self.current_id, {}).get(port, "")
        return self._resolve_automatic()

    def set_variable(self, name: str, value: Any) -> None:
        self.variables[str(name)] = value

    def snapshot(self) -> dict[str, Any]:
        node = self.nodes.get(self.current_id, {})
        values = node.get("inputs", {}) if isinstance(node.get("inputs"), Mapping) else {}
        kind = str(node.get("type", ""))
        routes = self.routes.get(self.current_id, {})
        options = [
            {"index": int(port.rsplit("_", 1)[-1]), "port": port}
            for port in sorted(routes)
            if port.startswith("option_") and port.rsplit("_", 1)[-1].isdigit()
        ]
        return {
            "active": self.active,
            "node_id": self.current_id,
            "type": kind,
            "speaker": str(values.get("speaker", "")),
            "text": str(values.get("text", values.get("prompt", ""))),
            "options": options,
            "finished": not self.active,
        }

    def _kind(self) -> str:
        return str(self.nodes.get(self.current_id, {}).get("type", ""))

    def _resolve_automatic(self) -> dict[str, Any]:
        visited: set[str] = set()
        while self.current_id and self.current_id not in visited:
            visited.add(self.current_id)
            node = self.nodes.get(self.current_id)
            if node is None:
                self.active = False
                break
            kind = str(node.get("type", ""))
            values = node.get("inputs", {}) if isinstance(node.get("inputs"), Mapping) else {}
            if kind in {"dialogue.speech", "dialogue.choice"}:
                self.active = True
                return self.snapshot()
            if kind == "dialogue.condition":
                value = bool(self.variables.get(str(values.get("condition_var", "")), False))
                self.current_id = self.routes.get(self.current_id, {}).get("true" if value else "false", "")
                continue
            if kind == "dialogue.event":
                self.event_sink(str(values.get("event_name", "")), values.get("payload"))
                self.current_id = self.routes.get(self.current_id, {}).get("out", "")
                continue
            if kind == "dialogue.end":
                self.active = False
                return self.snapshot()
            self.active = False
            break
        if self.current_id in visited and self._kind() not in {"dialogue.speech", "dialogue.choice", "dialogue.end"}:
            self.active = False
        return self.snapshot()
