"""Mixin para tradução de eventos Qt (teclado e mouse) para eventos Pygame na ViewportWidget."""

from __future__ import annotations

from typing import Optional

import pygame
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent


class ViewportQtEventsMixin:
    """Isola os manipuladores de eventos de entrada Qt da ViewportWidget."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._held_qt_keys = set()


    def _qt_btn_to_pg(self, btn: Qt.MouseButton) -> int:
        if btn == Qt.LeftButton:
            return 1
        if btn == Qt.MiddleButton:
            return 2
        if btn == Qt.RightButton:
            return 3
        return 0

    _held_qt_keys: set[int] = set()

    def _purge_stuck_keys(self) -> None:
        if not self.active_scene:
            return
        key_map = {
            Qt.Key_A: pygame.K_a,
            Qt.Key_D: pygame.K_d,
            Qt.Key_W: pygame.K_w,
            Qt.Key_S: pygame.K_s,
            Qt.Key_Left: pygame.K_LEFT,
            Qt.Key_Right: pygame.K_RIGHT,
            Qt.Key_Up: pygame.K_UP,
            Qt.Key_Down: pygame.K_DOWN,
            Qt.Key_Space: pygame.K_SPACE,
        }
        for qt_k, pg_k in key_map.items():
            if qt_k not in self._held_qt_keys:
                ev = pygame.event.Event(pygame.KEYUP, key=pg_k, mod=pygame.KMOD_NONE, unicode="")
                self.active_scene.handle_event(ev)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._qt_mouse_pos = (event.x(), event.y())
        if self.active_scene:
            self._purge_stuck_keys()
            pg_ev = pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                pos=self._qt_mouse_pos,
                button=self._qt_btn_to_pg(event.button()),
            )
            self.active_scene.handle_event(pg_ev)
            if not getattr(self.active_scene, "playing", False):
                self._sync_selection_to_model()
        self.request_render("mouse-press")
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._qt_mouse_pos = (event.x(), event.y())
        if self.active_scene:
            self._purge_stuck_keys()
            pg_ev = pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                pos=self._qt_mouse_pos,
                button=self._qt_btn_to_pg(event.button()),
            )
            self.active_scene.handle_event(pg_ev)
            if not getattr(self.active_scene, "playing", False):
                self._sync_selection_to_model()
        self.request_render("mouse-release")
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._qt_mouse_pos = (event.x(), event.y())
        if self.active_scene:
            btns = event.buttons()
            pg_ev = pygame.event.Event(
                pygame.MOUSEMOTION,
                pos=self._qt_mouse_pos,
                buttons=(
                    1 if btns & Qt.LeftButton else 0,
                    1 if btns & Qt.MiddleButton else 0,
                    1 if btns & Qt.RightButton else 0,
                ),
                rel=(0, 0),
            )
            self.active_scene.handle_event(pg_ev)
        self.request_render("mouse-move")
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.active_scene:
            steps = event.angleDelta().y() // 120
            pg_ev = pygame.event.Event(
                pygame.MOUSEWHEEL,
                x=0,
                y=steps,
                flipped=False,
            )
            self.active_scene.handle_event(pg_ev)
        self.request_render("wheel")
        event.accept()

    def _qt_key_to_pg(self, qt_key: Qt.Key) -> Optional[int]:
        _map = {
            Qt.Key_Escape: pygame.K_ESCAPE,
            Qt.Key_Delete: pygame.K_DELETE,
            Qt.Key_Backspace: pygame.K_BACKSPACE,
            Qt.Key_Left: pygame.K_LEFT,
            Qt.Key_Right: pygame.K_RIGHT,
            Qt.Key_Up: pygame.K_UP,
            Qt.Key_Down: pygame.K_DOWN,
            Qt.Key_Space: pygame.K_SPACE,
            Qt.Key_Return: pygame.K_RETURN,
            Qt.Key_Enter: pygame.K_KP_ENTER,
            Qt.Key_Shift: pygame.K_LSHIFT,
            Qt.Key_Control: pygame.K_LCTRL,
            Qt.Key_Alt: pygame.K_LALT,
            Qt.Key_Tab: pygame.K_TAB,
            **{getattr(Qt, f"Key_F{i}"): getattr(pygame, f"K_F{i}") for i in range(1, 13)},
        }
        if Qt.Key_A <= qt_key <= Qt.Key_Z:
            return pygame.K_a + (qt_key - Qt.Key_A)
        if Qt.Key_0 <= qt_key <= Qt.Key_9:
            return pygame.K_0 + (qt_key - Qt.Key_0)
        return _map.get(qt_key)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        self._held_qt_keys.add(event.key())

        # Delete funciona sempre, tanto em edit como em play mode
        if event.key() == Qt.Key_Delete:
            self.delete_selected_object()
            event.accept()
            return

        # Backspace também funciona para deletar
        if event.key() == Qt.Key_Backspace:
            self.delete_selected_object()
            event.accept()
            return

        if not getattr(getattr(self, "active_scene", None), "playing", False):
            if event.key() in (Qt.Key_Q, Qt.Key_W, Qt.Key_E, Qt.Key_R, Qt.Key_T, Qt.Key_F):
                if event.key() == Qt.Key_F:
                    self.focus_camera_on_selected()
                    event.accept()
                    return
                super().keyPressEvent(event)
                return

        if not self.active_scene:
            return

        if event.key() == Qt.Key_D and event.modifiers() & Qt.ControlModifier:
            self.duplicate_selected_object()
            event.accept()
            return

        pg_key = self._qt_key_to_pg(event.key())
        if pg_key is not None:
            if not hasattr(self, "_held_qt_keys"):
                self._held_qt_keys = set()
            self._held_qt_keys.add(event.key())
            mod = pygame.KMOD_NONE
            if event.modifiers() & Qt.ControlModifier:
                mod |= pygame.KMOD_CTRL
            pg_ev = pygame.event.Event(
                pygame.KEYDOWN,
                key=pg_key,
                mod=mod,
                unicode=event.text(),
            )
            self.active_scene.handle_event(pg_ev)
            if not getattr(self.active_scene, "playing", False):
                self._sync_selection_to_model()
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if not event.isAutoRepeat():
            self._held_qt_keys.discard(event.key())
        if not self.active_scene:
            return
        if event.isAutoRepeat():
            event.accept()
            return
        pg_key = self._qt_key_to_pg(event.key())
        if pg_key is not None:
            if hasattr(self, "_held_qt_keys"):
                self._held_qt_keys.discard(event.key())
            mod = pygame.KMOD_NONE
            if event.modifiers() & Qt.ControlModifier:
                mod |= pygame.KMOD_CTRL
            pg_ev = pygame.event.Event(
                pygame.KEYUP,
                key=pg_key,
                mod=mod,
                unicode="",
            )
            self.active_scene.handle_event(pg_ev)
            event.accept()
        else:
            super().keyReleaseEvent(event)

    def focusOutEvent(self, event) -> None:
        if not self.active_scene:
            super().focusOutEvent(event)
            return
        for qt_key in list(self._held_qt_keys):
            pg_key = self._qt_key_to_pg(qt_key)
            if pg_key is not None:
                pg_ev = pygame.event.Event(
                    pygame.KEYUP,
                    key=pg_key,
                    mod=pygame.KMOD_NONE,
                    unicode="",
                )
                self.active_scene.handle_event(pg_ev)
        self._held_qt_keys.clear()
        super().focusOutEvent(event)
