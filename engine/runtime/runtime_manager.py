from __future__ import annotations

from enum import Enum
from typing import Any

from engine.input import Input
from engine.runtime.input_manager import InputManager
from engine.runtime.runtime_scene import RuntimeScene
from engine.time import Time


class RuntimeState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED  = "paused"


class RuntimeManager:
    """Owns the lifecycle of the isolated Play Mode world."""

    def __init__(self) -> None:
        self.state = RuntimeState.STOPPED
        self.runtime_scene: RuntimeScene | None = None
        self.input = InputManager()
        self._snapshot: Any = None  # snapshot JSON da cena de editor

    # ------------------------------------------------------------------ #
    # Properties                                                          #
    # ------------------------------------------------------------------ #

    @property
    def is_playing(self) -> bool:
        return self.state == RuntimeState.PLAYING

    @property
    def is_paused(self) -> bool:
        return self.state == RuntimeState.PAUSED

    # ------------------------------------------------------------------ #
    # Play / Pause / Stop                                                 #
    # ------------------------------------------------------------------ #

    def start_play(self, editor_scene: Any) -> RuntimeScene:
        """Inicia o Play Mode. Ignora chamadas duplicadas com segurança."""
        if self.state == RuntimeState.PLAYING:
            # Guard: ja esta rodando, nao recria
            return self.runtime_scene  # type: ignore[return-value]

        # Snapshot profundo da cena de editor para restauracao fiel
        self._snapshot = self._take_snapshot(editor_scene)

        Time._runtime_reset()
        self.input.start()
        Input.bind_manager(self.input)

        self.runtime_scene = RuntimeScene(editor_scene)
        self.runtime_scene.start_runtime()
        self.state = RuntimeState.PLAYING
        return self.runtime_scene

    def pause(self) -> None:
        """Pausa o Play Mode sem destruir a RuntimeScene."""
        if self.state == RuntimeState.PLAYING:
            self.state = RuntimeState.PAUSED

    def resume(self) -> None:
        """Retoma um Play Mode pausado."""
        if self.state == RuntimeState.PAUSED:
            self.state = RuntimeState.PLAYING

    def tick(self, delta_time: float) -> None:
        if self.state != RuntimeState.PLAYING or self.runtime_scene is None:
            return
        scaled_dt = Time._runtime_tick(delta_time)
        self.input.update()
        self.runtime_scene.update(float(scaled_dt))

    def stop_play(self) -> Any | None:
        """
        Para o Play Mode e retorna o snapshot da cena de editor
        capturado no momento do Play para que o caller possa restaurar
        o estado visual se necessario.
        """
        if self.runtime_scene is not None:
            try:
                self.runtime_scene.stop_runtime()
            except Exception:  # nao deixa o stop travar o editor
                import traceback
                traceback.print_exc()
            try:
                self.runtime_scene.destroy()
            except Exception:
                import traceback
                traceback.print_exc()

        self.runtime_scene = None

        try:
            Input.unbind_manager(self.input)
        except Exception:
            pass

        try:
            self.input.stop()
        except Exception:
            pass

        try:
            Time._runtime_reset()
        except Exception:
            pass

        self.state = RuntimeState.STOPPED
        snapshot = self._snapshot
        self._snapshot = None
        return snapshot

    # ------------------------------------------------------------------ #
    # Input forwarding                                                    #
    # ------------------------------------------------------------------ #

    def handle_input_event(self, event: Any) -> None:
        if self.state != RuntimeState.PLAYING:
            return
        self.input.handle_event(event)

    # ------------------------------------------------------------------ #
    # Snapshot helpers                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _take_snapshot(editor_scene: Any) -> Any:
        """
        Tira um snapshot leve do estado da cena de editor:
        posicoes, rotacoes, escalas e visibilidade de cada GameObject raiz.
        Usado para detectar desvio pos-play e permitir restauracao.
        """
        snapshot: list[dict] = []
        objs = getattr(editor_scene, "editable_objects", None)
        if objs is None:
            objs = getattr(editor_scene, "game_objects", [])
        for obj in objs:
            t = getattr(obj, "transform", None)
            if t is None:
                continue
            import numpy as np
            snapshot.append({
                "id":       str(getattr(obj, "id", "")),
                "name":     str(getattr(obj, "name", "")),
                "active":   bool(getattr(obj, "active", True)),
                "position": np.array(t.position, dtype=np.float32).copy(),
                "rotation": np.array(t.rotation, dtype=np.float32).copy(),
                "scale":    np.array(t.scale,    dtype=np.float32).copy(),
            })
        return snapshot

    def restore_snapshot(self, editor_scene: Any) -> None:
        """
        Restaura as transforms da cena de editor ao estado do snapshot
        capturado antes do Play. Chamado pelo editor apos stop_play().
        """
        if not self._snapshot and not hasattr(self, "_last_snapshot"):
            return
        snap = self._snapshot or getattr(self, "_last_snapshot", [])
        objs = getattr(editor_scene, "editable_objects", None)
        if objs is None:
            objs = getattr(editor_scene, "game_objects", [])
        index: dict[str, Any] = {str(getattr(o, "id", "")): o for o in objs}
        for entry in snap:
            obj = index.get(entry["id"])
            if obj is None:
                continue
            t = getattr(obj, "transform", None)
            if t is None:
                continue
            import numpy as np
            t.position = entry["position"].copy()
            t.rotation = entry["rotation"].copy()
            t.scale    = entry["scale"].copy()
            obj.active = entry["active"]
