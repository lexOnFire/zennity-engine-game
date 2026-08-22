"""Behavior Tree helpers for :mod:`editor.runtime.viewport_logic_api`."""
from __future__ import annotations

import json
from pathlib import Path

from typing import Any

try:
    from engine.behavior.controller_asset import BehaviorControllerRunner, load_behavior_controller
    from engine.behavior.graph_runtime import BehaviorGraphRunner
except ModuleNotFoundError:  # Runtime autocontido criado pelo exportador.
    from .behavior_controller import BehaviorControllerRunner, load_behavior_controller
    from .behavior_graph_runtime import BehaviorGraphRunner


class PlayBehaviorTreeMixin:
    def start_behavior_tree(self, path: str) -> bool:
        """Carrega e executa uma Behavior Tree (.zbehavior) no objeto atual."""
        behavior = self.obj.setdefault("behavior", {})
        clean_path = str(path).strip() or str(behavior.get("controller_path", "")).strip()
        if not clean_path:
            self._emit_runtime_log("ERROR", f"{self.name}: nenhum Behavior Tree vinculado")
            return False
        behavior["controller_path"] = clean_path
        p = Path(clean_path)
        if not p.is_absolute():
            p = self._project_root / p
        try:
            if p.suffix.lower() != ".zbehavior" or not p.is_file():
                raise ValueError(f"asset não encontrado: {clean_path}")
            resolved_path = str(p.resolve())
            existing = self._behavior_runners.get(self.name) if self._behavior_runners is not None else None
            if existing is not None and behavior.get("_active_path") == resolved_path:
                return True
            raw = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("documento inválido")
            if raw.get("format") == "zennity.generic_graph":
                runner = BehaviorGraphRunner(raw, project_root=self._project_root)
                behavior["graph"] = raw
                behavior.pop("controller", None)
            else:
                controller = load_behavior_controller(p)
                runner = BehaviorControllerRunner(
                    controller, self._project_root, behavior.get("parameters", {})
                )
                behavior["controller"] = controller
                behavior.pop("graph", None)
            previous = existing
            if previous is not None:
                previous.stop(self)
            self.behavior.bind(runner, self)
            runner.start(self)
            if self._behavior_runners is not None:
                self._behavior_runners[self.name] = runner
            behavior["_active_path"] = resolved_path
            self.obj["_behavior_state"] = runner.current_state
            return True
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self._emit_runtime_log(
                "ERROR",
                f"{self.name}: falha ao iniciar Behavior Tree '{clean_path}': {exc}",
            )
            return False

