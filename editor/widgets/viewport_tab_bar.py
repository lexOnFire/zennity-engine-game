"""
editor/widgets/viewport_tab_bar.py
====================================
Aba Scene / Game acima da viewport.

Uso:
    from editor.widgets.viewport_tab_bar import ViewportContainer
    container = ViewportContainer(viewmodel, parent)
    # container.viewport é o ViewportWidget original
"""

from __future__ import annotations

from typing import Optional

import pygame
import numpy as np

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QImage
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QFrame,
)

from editor.widgets.viewport_widget import ViewportWidget
from editor.viewmodels.scene_viewmodel import SceneViewModel


# ──────────────────────────────────────────────────────────────────────────────
# Constantes de estilo
# ──────────────────────────────────────────────────────────────────────────────

_TAB_H = 28          # altura da barra de abas (px)
_TAB_ACTIVE   = "#1e1f26"   # fundo da aba ativa
_TAB_INACTIVE = "#141519"   # fundo da aba inativa
_TEXT_ACTIVE  = "#e0e0e0"
_TEXT_INACTIVE = "#808080"
_ACCENT       = "#3c8eff"   # borda inferior da aba ativa
_TOOLBAR_BG   = "#0f1014"   # barra de abas

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
# Barra de abas
# ──────────────────────────────────────────────────────────────────────────────

class ViewportTabBar(QWidget):
    """
    Faixa horizontal com dois botões: Scene | Game.
    Emite o modo escolhido para o ViewportContainer via callback.
    """

    def __init__(self, on_change, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("ViewportTabBar")
        self.setFixedHeight(_TAB_H)
        self.setStyleSheet(_STYLE_BAR)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._on_change = on_change
        self._current = "scene"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._btn_scene = QPushButton("  Scene  ", self)
        self._btn_game  = QPushButton("  Game  ",  self)

        for btn in (self._btn_scene, self._btn_game):
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)

        layout.addStretch()

        self._btn_scene.clicked.connect(lambda: self._switch("scene"))
        self._btn_game.clicked.connect(lambda: self._switch("game"))

        self._refresh_styles()

    def _switch(self, mode: str) -> None:
        if mode == self._current:
            return
        self._current = mode
        self._refresh_styles()
        self._on_change(mode)

    def force_switch(self, mode: str) -> None:
        """
        Força a troca visual da aba sem passar pela guarda de modo atual.
        Usado pelo MainWindow para sincronizar a aba com o estado de play/stop
        sem disparar o callback _on_change (que causaria double-emit).
        """
        self._current = mode
        self._refresh_styles()

    def _refresh_styles(self) -> None:
        self._btn_scene.setStyleSheet(_btn_style(self._current == "scene"))
        self._btn_game.setStyleSheet(_btn_style(self._current == "game"))

    @property
    def current_mode(self) -> str:
        return self._current


# ──────────────────────────────────────────────────────────────────────────────
# Viewport com modo Game
# ──────────────────────────────────────────────────────────────────────────────

class _GameViewport(ViewportWidget):
    """
    Subclasse do ViewportWidget que, quando em modo Game:
      - Suprime o grid
      - Aplica a câmera ativa como ponto de vista
      - Mostra o nome da cena no canto inferior esquerdo
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._game_mode: bool = False

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def set_game_mode(self, enabled: bool) -> None:
        self._game_mode = enabled

    # ------------------------------------------------------------------
    # Override de paintGL
    # ------------------------------------------------------------------

    def paintGL(self) -> None:
        if not self.pg_surface or not self.active_scene:
            return

        if self._game_mode:
            # Modo Game: renderização própria sem grid, com câmera ativa
            self._render_game_view()
            raw = pygame.image.tostring(self.pg_surface, "RGBA")
            img = QImage(
                raw, self._vp_w, self._vp_h,
                self._vp_w * 4, QImage.Format_RGBA8888,
            )
            p = QPainter(self)
            p.drawImage(0, 0, img)
            p.end()
        else:
            # Modo Scene: delega inteiramente ao pai para respeitar os shims
            # aplicados por _apply_qt_shims() (grid, draw monkey-patch, etc.)
            super().paintGL()

    # ------------------------------------------------------------------
    # Renderização Game
    # ------------------------------------------------------------------

    def _render_game_view(self) -> None:
        """
        Renderiza a cena sem grid, usando a câmera ativa como ponto de vista.
        """
        scene  = self.active_scene
        surf   = self.pg_surface
        w, h   = self._vp_w, self._vp_h

        surf.fill((15, 15, 20))   # fundo preto-azulado (cor de jogo)

        # ── Detecta câmera ativa ───────────────────────────────────────
        cam2d = self._get_camera2d()
        cam3d = self._get_camera3d()

        if cam2d:
            self._draw_game_2d(surf, scene, cam2d, w, h)
        elif cam3d:
            self._draw_game_3d(surf, scene, cam3d, w, h)
        else:
            # Sem câmera — renderiza objetos centrados
            self._draw_game_no_camera(surf, scene, w, h)

        # Overlay: nome da cena no canto inferior esquerdo
        self._draw_scene_label(surf, w, h)

    # ------------------------------------------------------------------
    # Câmeras
    # ------------------------------------------------------------------

    def _get_camera2d(self):
        try:
            from engine.graphics.camera2d import Camera2D
            return Camera2D.main
        except Exception:
            return None

    def _get_camera3d(self):
        scene = self.active_scene
        return getattr(scene, "camera_comp", None)

    # ------------------------------------------------------------------
    # Renderização 2D com câmera
    # ------------------------------------------------------------------

    def _draw_game_2d(
        self,
        surf: pygame.Surface,
        scene,
        cam2d,
        w: int,
        h: int,
    ) -> None:
        """
        Traduz todos os game_objects pelo offset da câmera 2D e os desenha
        sem grid.
        """
        # Offset de câmera
        cx = getattr(cam2d.transform, "position", [0, 0])[0]
        cy = getattr(cam2d.transform, "position", [0, 0])[1]
        zoom = getattr(cam2d, "zoom", 1.0) or 1.0

        ox = w / 2 - cx * zoom
        oy = h / 2 - cy * zoom

        for go in getattr(scene, "game_objects", []):
            if not getattr(go, "active", True):
                continue
            self._draw_go_offset(surf, go, ox, oy, zoom)

    def _draw_go_offset(
        self,
        surf: pygame.Surface,
        go,
        ox: float,
        oy: float,
        zoom: float,
    ) -> None:
        """
        Salva a posição real, desenha com offset, restaura.
        Suporte para Transform com position como lista/array.
        """
        tr = getattr(go, "transform", None)
        if tr is None:
            go.draw(surf)
            return

        pos = tr.position
        orig_x, orig_y = float(pos[0]), float(pos[1])

        # Aplica offset temporário
        pos[0] = orig_x * zoom + ox
        pos[1] = orig_y * zoom + oy

        try:
            go.draw(surf)
        finally:
            pos[0] = orig_x
            pos[1] = orig_y

    # ------------------------------------------------------------------
    # Renderização 3D com câmera
    # ------------------------------------------------------------------

    def _draw_game_3d(
        self,
        surf: pygame.Surface,
        scene,
        cam3d,
        w: int,
        h: int,
    ) -> None:
        """
        Renderiza a cena 3D sem grid, câmera ocupa toda a viewport.
        """
        try:
            from engine.graphics.renderer3d import Camera3D
            cam3d.viewport_x      = 0
            cam3d.viewport_y      = 0
            cam3d.viewport_width  = w
            cam3d.viewport_height = h
            cam3d.update(0.0)
            Camera3D.main = cam3d
        except Exception:
            pass

        for go in getattr(scene, "game_objects", []):
            if getattr(go, "active", True):
                go.draw(surf)

    # ------------------------------------------------------------------
    # Sem câmera — renderização direta
    # ------------------------------------------------------------------

    def _draw_game_no_camera(
        self,
        surf: pygame.Surface,
        scene,
        w: int,
        h: int,
    ) -> None:
        """Sem câmera ativa: simplesmente chama draw() de cada objeto."""
        for go in getattr(scene, "game_objects", []):
            if getattr(go, "active", True):
                try:
                    go.draw(surf)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Overlay: label com nome da cena
    # ------------------------------------------------------------------

    def _draw_scene_label(self, surf: pygame.Surface, w: int, h: int) -> None:
        """
        Exibe "▶ <NomeDaCena>" no canto inferior esquerdo da viewport de jogo.
        """
        try:
            font = pygame.font.SysFont("monospace", 13)
        except Exception:
            return

        scene_name = "Scene"
        if self.active_scene:
            scene_name = getattr(
                self.active_scene,
                "name",
                type(self.active_scene).__name__,
            )

        label = f"▶  {scene_name}"
        text  = font.render(label, True, (200, 200, 200))
        tx, ty = 10, h - text.get_height() - 10

        # Sombra suave
        shadow = font.render(label, True, (0, 0, 0))
        surf.blit(shadow, (tx + 1, ty + 1))
        surf.blit(text,   (tx, ty))

        # Indicador "CAM" se há câmera
        if self._get_camera2d() or self._get_camera3d():
            cam_text = font.render("CAM", True, (60, 200, 100))
            surf.blit(cam_text, (w - cam_text.get_width() - 10, h - cam_text.get_height() - 10))


# ──────────────────────────────────────────────────────────────────────────────
# Container público
# ──────────────────────────────────────────────────────────────────────────────

class ViewportContainer(QWidget):
    """
    Widget composto: aba Scene/Game + viewport embaixo.

    Uso na MainWindow::

        container = ViewportContainer(parent=central_widget)
        container.set_viewmodel(viewmodel)
        layout.addWidget(container)

        # acesso ao viewport original
        container.viewport.create_object("circle")
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("ViewportContainer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra de abas
        self._tab_bar = ViewportTabBar(on_change=self._on_tab_changed, parent=self)
        layout.addWidget(self._tab_bar)

        # Viewport (usa a subclasse com suporte a Game mode)
        self._viewport = _GameViewport(parent=self)
        layout.addWidget(self._viewport, stretch=1)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    @property
    def viewport(self) -> _GameViewport:
        """Acesso ao ViewportWidget interno."""
        return self._viewport

    @property
    def tab_bar(self) -> ViewportTabBar:
        return self._tab_bar

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        """Delega para o viewport interno."""
        self._viewport.set_viewmodel(viewmodel)

    # ------------------------------------------------------------------
    # Troca de aba
    # ------------------------------------------------------------------

    def _on_tab_changed(self, mode: str) -> None:
        """
        Chamado quando o usuário clica manualmente em Scene ou Game.

        Responsabilidade única: atualizar o modo de renderização da viewport.
        O controle de play/stop é responsabilidade exclusiva do MainWindow
        via EventBus — não emitimos EVENT_PLAY_STATE_CHANGED aqui para evitar
        double-emit com on_play_clicked / on_stop_clicked.
        """
        game = mode == "game"
        self._viewport.set_game_mode(game)
        self._viewport.update()
