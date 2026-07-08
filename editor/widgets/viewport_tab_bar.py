"""
editor/widgets/viewport_tab_bar.py
====================================
Barra de abas da Viewport: Scene | Game | Animator | Script
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

import pygame
import numpy as np

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QImage, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSizePolicy, QFrame, QStackedWidget, QLabel,
    QListWidget, QListWidgetItem, QSplitter,
    QPlainTextEdit, QToolBar, QAction,
)

from editor.widgets.viewport_widget import ViewportWidget
from editor.viewmodels.scene_viewmodel import SceneViewModel


# ──────────────────────────────────────────────────────────────────────────────
_TAB_H        = 28
_TAB_ACTIVE   = "#1e1f26"
_TAB_INACTIVE = "#141519"
_TEXT_ACTIVE  = "#e0e0e0"
_TEXT_INACTIVE = "#808080"
_ACCENT       = "#3c8eff"
_TOOLBAR_BG   = "#0f1014"

_STYLE_BAR = f"""
    QWidget#ViewportTabBar {{
        background: {_TOOLBAR_BG};
        border-bottom: 1px solid #000;
    }}
"""

_STYLE_BTN = """
    QPushButton {{
        background: {bg};
        color: {fg};
        border: none;
        border-bottom: 2px solid {bottom};
        padding: 0 14px;
        font-size: 12px;
        font-weight: {fw};
        min-height: 28px;
        max-height: 28px;
        border-radius: 0;
    }}
    QPushButton:hover {{
        background: #23242d;
    }}
"""


def _btn_style(active: bool) -> str:
    return _STYLE_BTN.format(
        bg=_TAB_ACTIVE if active else _TAB_INACTIVE,
        fg=_TEXT_ACTIVE if active else _TEXT_INACTIVE,
        bottom=_ACCENT if active else "transparent",
        fw="600" if active else "400",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Aba Animator
# ──────────────────────────────────────────────────────────────────────────────

_ANIMATOR_BG = "background:#0d0f14; color:#9ca3af;"
_LIST_STYLE = (
    "QListWidget{background:#0f1117;border:1px solid #2a2d3a;border-radius:4px;"
    "color:#c9cdd6;font-size:11px;}"
    "QListWidget::item:selected{background:#1e3a5f;color:#fff;}"
    "QListWidget::item:hover{background:#1b1e27;}"
)
_BTN_SMALL = (
    "QPushButton{background:#1b1e27;border:1px solid #2a2d3a;border-radius:4px;"
    "color:#6b7280;padding:3px 10px;font-size:11px;}"
    "QPushButton:hover{background:#252839;color:#9ca3af;}"
)


class AnimatorTab(QWidget):
    """Aba Animator MVP: lista de estados + área de descrição."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_ANIMATOR_BG)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        lbl = QLabel("Animator")
        lbl.setStyleSheet("color:#e0e0e0;font-weight:700;font-size:13px;")
        toolbar.addWidget(lbl)
        toolbar.addStretch()

        self.btn_new_state = QPushButton("+ Estado")
        self.btn_new_state.setStyleSheet(_BTN_SMALL)
        self.btn_new_state.clicked.connect(self._add_state)
        toolbar.addWidget(self.btn_new_state)

        self.btn_new_clip = QPushButton("+ Clip")
        self.btn_new_clip.setStyleSheet(_BTN_SMALL)
        toolbar.addWidget(self.btn_new_clip)
        root.addLayout(toolbar)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#1f2330;border:none;max-height:1px;")
        root.addWidget(sep)

        # Splitter: lista de estados | detalhes
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle{background:#1f2330;}")

        # Painel esquerdo: estados
        left = QWidget(); lv = QVBoxLayout(left); lv.setContentsMargins(0, 0, 0, 0)
        lv.addWidget(QLabel("Estados"))
        self.state_list = QListWidget()
        self.state_list.setStyleSheet(_LIST_STYLE)
        for default in ("Entry", "Any State", "Exit"):
            item = QListWidgetItem(default)
            self.state_list.addItem(item)
        lv.addWidget(self.state_list)
        splitter.addWidget(left)

        # Painel direito: detalhes do estado
        right = QWidget(); rv = QVBoxLayout(right); rv.setContentsMargins(0, 0, 0, 0)
        rv.addWidget(QLabel("Detalhes do Estado"))
        self.detail_label = QLabel("Selecione um estado para ver detalhes.")
        self.detail_label.setStyleSheet("color:#6b7280;font-size:11px;")
        self.detail_label.setWordWrap(True)
        rv.addWidget(self.detail_label)
        rv.addStretch()
        splitter.addWidget(right)

        splitter.setSizes([180, 400])
        root.addWidget(splitter, 1)

        self.state_list.currentItemChanged.connect(
            lambda cur, _: self.detail_label.setText(
                f"Estado: {cur.text()}" if cur else "Selecione um estado."
            )
        )

    def _add_state(self) -> None:
        count = self.state_list.count() - 2  # exclui Entry/Exit
        item = QListWidgetItem(f"State {count}")
        # Insere antes de Exit
        self.state_list.insertItem(self.state_list.count() - 1, item)
        self.state_list.setCurrentItem(item)


# ──────────────────────────────────────────────────────────────────────────────
# Aba Script Editor
# ──────────────────────────────────────────────────────────────────────────────

_EDITOR_STYLE = (
    "QPlainTextEdit{"
    "background:#0b0d12;color:#c9cdd6;font-family:'Consolas','Fira Code','Courier New',monospace;"
    "font-size:12px;border:none;padding:8px;"
    "}"
)
_EDITOR_TOOLBAR = (
    "QToolBar{background:#0f1014;border-bottom:1px solid #1f2330;spacing:4px;}"
    "QToolButton{color:#6b7280;padding:2px 8px;background:transparent;border:none;font-size:11px;}"
    "QToolButton:hover{color:#c9cdd6;background:#1b1e27;border-radius:3px;}"
)


class ScriptEditorTab(QWidget):
    """Aba Script Editor MVP: abre e edita scripts .py do projeto."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:#0b0d12;")
        self._current_path: Optional[str] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet(_EDITOR_TOOLBAR)
        tbl = QHBoxLayout(toolbar)
        tbl.setContentsMargins(6, 3, 6, 3); tbl.setSpacing(6)

        self.lbl_filename = QLabel("Nenhum arquivo aberto")
        self.lbl_filename.setStyleSheet("color:#9ca3af;font-size:11px;")
        tbl.addWidget(self.lbl_filename)
        tbl.addStretch()

        self.btn_save = QPushButton("Salvar")
        self.btn_save.setStyleSheet(_BTN_SMALL)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._save)
        tbl.addWidget(self.btn_save)

        self.btn_close = QPushButton("Fechar")
        self.btn_close.setStyleSheet(_BTN_SMALL)
        self.btn_close.setEnabled(False)
        self.btn_close.clicked.connect(self._close_file)
        tbl.addWidget(self.btn_close)

        root.addWidget(toolbar)

        # Editor de texto
        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet(_EDITOR_STYLE)
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        fnt = QFont("Consolas", 12)
        fnt.setStyleHint(QFont.Monospace)
        self.editor.setFont(fnt)
        self.editor.setPlaceholderText("# Arraste um script .py ou use 'Editar Script' no Inspector...")
        self.editor.setEnabled(False)
        root.addWidget(self.editor, 1)

    # ── API pública ────────────────────────────────────────────────────────

    def open_file(self, path: str) -> None:
        """Abre um arquivo de script no editor."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as exc:
            self.editor.setPlainText(f"# Erro ao abrir: {exc}")
            return
        self._current_path = path
        self.editor.setPlainText(content)
        self.editor.setEnabled(True)
        self.btn_save.setEnabled(True)
        self.btn_close.setEnabled(True)
        self.lbl_filename.setText(path.split("/")[-1].split("\\")[-1])

    def _save(self) -> None:
        if not self._current_path:
            return
        try:
            with open(self._current_path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
        except OSError as exc:
            self.lbl_filename.setText(f"Erro: {exc}")

    def _close_file(self) -> None:
        self._current_path = None
        self.editor.clear()
        self.editor.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.btn_close.setEnabled(False)
        self.lbl_filename.setText("Nenhum arquivo aberto")


# ──────────────────────────────────────────────────────────────────────────────
# Viewport com Game mode (preservado do original)
# ──────────────────────────────────────────────────────────────────────────────

class _GameViewport(ViewportWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._game_mode: bool = False

    def set_game_mode(self, enabled: bool) -> None:
        self._game_mode = enabled

    def paintGL(self) -> None:
        if not self.pg_surface or not self.active_scene:
            return
        if self._game_mode:
            self._render_game_view()
        else:
            self.active_scene.draw(self.pg_surface)
        raw = pygame.image.tostring(self.pg_surface, "RGBA")
        img = QImage(raw, self._vp_w, self._vp_h, self._vp_w * 4, QImage.Format_RGBA8888)
        p = QPainter(self)
        p.drawImage(0, 0, img)
        p.end()

    def _render_game_view(self) -> None:
        scene = self.active_scene
        surf  = self.pg_surface
        w, h  = self._vp_w, self._vp_h
        surf.fill((15, 15, 20))
        cam2d = self._get_camera2d()
        cam3d = self._get_camera3d()
        if cam2d:
            self._draw_game_2d(surf, scene, cam2d, w, h)
        elif cam3d:
            self._draw_game_3d(surf, scene, cam3d, w, h)
        else:
            self._draw_game_no_camera(surf, scene, w, h)
        self._draw_scene_label(surf, w, h)

    def _get_camera2d(self):
        try:
            from engine.graphics.camera2d import Camera2D
            return Camera2D.main
        except Exception:
            return None

    def _get_camera3d(self):
        return getattr(self.active_scene, "camera_comp", None)

    def _draw_game_2d(self, surf, scene, cam2d, w, h):
        cx = getattr(cam2d.transform, "position", [0, 0])[0]
        cy = getattr(cam2d.transform, "position", [0, 0])[1]
        zoom = getattr(cam2d, "zoom", 1.0) or 1.0
        ox = w / 2 - cx * zoom
        oy = h / 2 - cy * zoom
        for go in getattr(scene, "game_objects", []):
            if not getattr(go, "active", True):
                continue
            self._draw_go_offset(surf, go, ox, oy, zoom)

    def _draw_go_offset(self, surf, go, ox, oy, zoom):
        tr = getattr(go, "transform", None)
        if tr is None:
            go.draw(surf)
            return
        pos = tr.position
        orig_x, orig_y = float(pos[0]), float(pos[1])
        pos[0] = orig_x * zoom + ox
        pos[1] = orig_y * zoom + oy
        try:
            go.draw(surf)
        finally:
            pos[0] = orig_x
            pos[1] = orig_y

    def _draw_game_3d(self, surf, scene, cam3d, w, h):
        try:
            from engine.graphics.renderer3d import Camera3D
            cam3d.viewport_x = 0; cam3d.viewport_y = 0
            cam3d.viewport_width = w; cam3d.viewport_height = h
            cam3d.update(0.0)
            Camera3D.main = cam3d
        except Exception:
            pass
        for go in getattr(scene, "game_objects", []):
            if getattr(go, "active", True):
                go.draw(surf)

    def _draw_game_no_camera(self, surf, scene, w, h):
        for go in getattr(scene, "game_objects", []):
            if getattr(go, "active", True):
                try:
                    go.draw(surf)
                except Exception:
                    pass

    def _draw_scene_label(self, surf, w, h):
        try:
            font = pygame.font.SysFont("monospace", 13)
        except Exception:
            return
        scene_name = getattr(self.active_scene, "name",
                             type(self.active_scene).__name__) if self.active_scene else "Scene"
        label = f"▶  {scene_name}"
        text   = font.render(label, True, (200, 200, 200))
        tx, ty = 10, h - text.get_height() - 10
        shadow = font.render(label, True, (0, 0, 0))
        surf.blit(shadow, (tx + 1, ty + 1))
        surf.blit(text, (tx, ty))
        if self._get_camera2d() or self._get_camera3d():
            ct = font.render("CAM", True, (60, 200, 100))
            surf.blit(ct, (w - ct.get_width() - 10, h - ct.get_height() - 10))


# ──────────────────────────────────────────────────────────────────────────────
# ViewportTabBar — agora com 4 abas
# ──────────────────────────────────────────────────────────────────────────────

_TABS: List[tuple[str, str]] = [
    ("scene",   "  Scene  "),
    ("game",    "  Game  "),
    ("animator","  Animator  "),
    ("script",  "  Script  "),
]


class ViewportTabBar(QWidget):
    """Faixa horizontal com abas Scene | Game | Animator | Script."""

    def __init__(self, on_change: Callable[[str], None], parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("ViewportTabBar")
        self.setFixedHeight(_TAB_H)
        self.setStyleSheet(_STYLE_BAR)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._on_change = on_change
        self._current = "scene"
        self._buttons: Dict[str, QPushButton] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for key, label in _TABS:
            btn = QPushButton(label, self)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self._switch(k))
            layout.addWidget(btn)
            self._buttons[key] = btn

        layout.addStretch()
        self._refresh_styles()

    def _switch(self, mode: str) -> None:
        if mode == self._current:
            return
        self._current = mode
        self._refresh_styles()
        self._on_change(mode)

    def _refresh_styles(self) -> None:
        for key, btn in self._buttons.items():
            btn.setStyleSheet(_btn_style(key == self._current))

    @property
    def current_mode(self) -> str:
        return self._current


# ──────────────────────────────────────────────────────────────────────────────
# ViewportContainer — 4 abas com QStackedWidget
# ──────────────────────────────────────────────────────────────────────────────

class ViewportContainer(QWidget):
    """
    Widget composto: aba Scene/Game/Animator/Script + conteúdo embaixo.

    Uso na MainWindow::

        container = ViewportContainer(parent=central_widget)
        container.set_viewmodel(viewmodel)
        layout.addWidget(container)
        container.viewport.create_object("circle")  # acesso ao viewport
        container.script_editor.open_file(path)      # acesso ao editor
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("ViewportContainer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tab_bar = ViewportTabBar(on_change=self._on_tab_changed, parent=self)
        layout.addWidget(self._tab_bar)

        # Stacked: 0=Scene, 1=Game(mesmo widget), 2=Animator, 3=Script
        self._stack = QStackedWidget(self)

        self._viewport = _GameViewport(parent=self)
        self._animator_tab = AnimatorTab(parent=self)
        self._script_editor = ScriptEditorTab(parent=self)

        self._stack.addWidget(self._viewport)       # index 0 — Scene
        self._stack.addWidget(self._animator_tab)   # index 1 — Animator
        self._stack.addWidget(self._script_editor)  # index 2 — Script

        layout.addWidget(self._stack, stretch=1)

    # ── API pública ────────────────────────────────────────────────────────

    @property
    def viewport(self) -> _GameViewport:
        return self._viewport

    @property
    def tab_bar(self) -> ViewportTabBar:
        return self._tab_bar

    @property
    def animator_tab(self) -> AnimatorTab:
        return self._animator_tab

    @property
    def script_editor(self) -> ScriptEditorTab:
        return self._script_editor

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        self._viewport.set_viewmodel(viewmodel)

    # ── troca de aba ────────────────────────────────────────────────────────

    def _on_tab_changed(self, mode: str) -> None:
        _mode_to_stack = {"scene": 0, "game": 0, "animator": 1, "script": 2}
        self._stack.setCurrentIndex(_mode_to_stack.get(mode, 0))

        # Scene <-> Game: controle de play mode
        is_game = mode == "game"
        self._viewport.set_game_mode(is_game)

        scene = self._viewport.active_scene
        if scene and hasattr(scene, "playing"):
            if is_game and not scene.playing:
                from editor.core.event_bus import EventBus, EVENT_PLAY_STATE_CHANGED
                EventBus.emit(EVENT_PLAY_STATE_CHANGED, state="play")
            elif not is_game and mode in ("scene", "animator", "script") and scene.playing:
                from editor.core.event_bus import EventBus, EVENT_PLAY_STATE_CHANGED
                EventBus.emit(EVENT_PLAY_STATE_CHANGED, state="stop")

        if mode in ("scene", "game"):
            self._viewport.update()
