"""Estado determinístico da sessão Play do editor isolado."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EditorPlaySession:
    state: str = "edit"
    _edit_objects: list[dict[str, Any]] | None = field(default=None, repr=False)
    _selected_id: str | None = field(default=None, repr=False)
    _selected_name: str | None = field(default=None, repr=False)
    _restore_pending: bool = field(default=False, repr=False)

    @property
    def is_running(self) -> bool:
        return self.state in {"starting", "play", "pause"}

    def begin(self, objects: list[dict[str, Any]], selected_name: str | None) -> list[dict[str, Any]]:
        """Captura a cena editável uma única vez, antes do primeiro frame."""
        if not self.is_running:
            self._edit_objects = deepcopy(objects)
            selected = next((obj for obj in objects if obj.get("name") == selected_name), None)
            self._selected_id = str(selected.get("id")) if selected and selected.get("id") is not None else None
            self._selected_name = selected_name
            self._restore_pending = False
            self.state = "starting"
        return deepcopy(self._edit_objects or objects)

    def update_scene(self, new_objects: list[dict[str, Any]]) -> None:
        """Atualiza a cópia da cena de edição quando uma nova cena é carregada (e.g. via load_scene)."""
        self._edit_objects = deepcopy(new_objects)
        self._selected_id = None
        self._selected_name = None

    def set_runtime_state(self, state: str) -> None:
        if state not in {"play", "pause"}:
            raise ValueError(f"Estado de runtime inválido: {state}")
        self.state = state

    def finish(self) -> tuple[list[dict[str, Any]], str | None]:
        """Restaura a cópia de edição e aguarda o snapshot final do runtime."""
        restored = deepcopy(self._edit_objects or [])
        selected = self._resolve_selection(restored)
        self.state = "edit"
        self._restore_pending = self._edit_objects is not None
        return restored, selected

    def consume_scene_snapshot(self, runtime_objects: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str | None]:
        """Descarta o snapshot mutado que o runtime envia logo após Stop."""
        if self._restore_pending and self._edit_objects is not None:
            objects = deepcopy(self._edit_objects)
            self._restore_pending = False
            self._edit_objects = None
        else:
            objects = deepcopy(runtime_objects)
        return objects, self._resolve_selection(objects)

    def _resolve_selection(self, objects: list[dict[str, Any]]) -> str | None:
        if self._selected_id is not None:
            selected = next((obj for obj in objects if str(obj.get("id")) == self._selected_id), None)
            if selected is not None:
                return str(selected.get("name"))
        if self._selected_name and any(obj.get("name") == self._selected_name for obj in objects):
            return self._selected_name
        return None

