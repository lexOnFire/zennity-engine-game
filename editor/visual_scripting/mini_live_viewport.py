"""Game View AAA — Zennity Engine Visual Scripting Integration.

Transforma a Mini Live Viewport em uma Game View profissional integrada
ao Visual Scripting. Sem QRhi cross-context (QPainter puro).

Experiência alvo:
  "Estou utilizando uma Game View integrada ao Visual Scripting."
  — NÃO —
  "Estou olhando uma miniatura da cena."

Design:
  - Toolbar superior com Play/Pause/Stop, status em tempo real (runtime clock,
    FPS, frame time, câmera ativa), e badges de modo com animação pulsante.
  - Canvas QPainter AAA com overlays de física, colisores, navegação, IA,
    áudio, variáveis de runtime e execução de nós.
  - Barra de status inferior com draw calls, objetos na cena, modo de câmera.
  - Painel de overlays configuráveis (toggle por camada).
  - Painel de Step Controls visível apenas em PAUSED.
  - Mini FPS sparkline graph no canvas.
  - Sincronização bidirecional objeto ↔ nó via Signals.
  - Live Logic Editing: modificar Inspector → atualiza Runtime sem reiniciar.

Retrocompatibilidade total:
  MiniLiveViewportWidget = RuntimeVisualizationPanelWidget
"""
from __future__ import annotations

import math
import time
from collections import deque
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal, QSize
from PySide6.QtGui import (
    QColor, QFont, QPainter, QPen, QBrush,
    QLinearGradient, QRadialGradient, QPolygonF,
    QFontMetrics, QPainterPath, QPixmap,
)
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSlider,
    QVBoxLayout, QWidget, QComboBox, QCheckBox, QToolButton,
    QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect,
)

from editor.visual_scripting.runtime_visualization import RuntimeVisualizationRenderer
from editor.visual_scripting.runtime_panel_controller_mixin import RuntimePanelControllerMixin


# ─────────────────────────────────────────────────────────────────────────────
#  Paleta de Cores AAA
# ─────────────────────────────────────────────────────────────────────────────

class _C:
    BG_DEEP        = QColor("#080a0e")
    BG_TOOLBAR     = QColor("#0f1117")
    BG_STATUS      = QColor("#0b0d12")
    BORDER_IDLE    = QColor(76, 154, 255, 40)
    BORDER_PLAY    = QColor(0,  230, 100, 255)
    BORDER_PAUSE   = QColor(255, 180, 50,  255)
    GRID_MINOR     = QColor(255, 255, 255, 8)
    GRID_MAJOR     = QColor(255, 255, 255, 16)
    AXIS_X         = QColor(220, 70,  70,  60)
    AXIS_Y         = QColor(70,  200, 70,  60)
    TEXT_PRIMARY   = QColor("#e8eaf0")
    TEXT_SECONDARY = QColor("#6b7385")
    TEXT_DIM       = QColor("#383d4a")
    ACCENT_PLAY    = QColor("#00e664")
    ACCENT_PAUSE   = QColor("#ffb432")
    ACCENT_EDITOR  = QColor("#4c9aff")
    ACCENT_NODE    = QColor("#ae7df0")
    COLLIDER       = QColor(80, 220, 140, 180)
    COLLIDER_FILL  = QColor(80, 220, 140, 18)
    AI_FOV         = QColor(230, 184, 92, 140)
    AI_FOV_FILL    = QColor(230, 184, 92, 28)
    NAV_PATH       = QColor(76, 154, 255, 200)
    VELOCITY       = QColor(88, 166, 255, 230)
    JUMP_FORCE     = QColor(255, 77, 141, 230)
    AUDIO          = QColor(174, 125, 240, 160)
    SELECTION_RING = QColor(255, 215, 0,   220)


# ─────────────────────────────────────────────────────────────────────────────
#  ViewportMode
# ─────────────────────────────────────────────────────────────────────────────

class ViewportMode(str, Enum):
    EDITOR = "EDITOR"
    GAME   = "GAME"
    DEBUG  = "DEBUG"


# ─────────────────────────────────────────────────────────────────────────────
#  _FPSSparkline — mini gráfico de FPS histórico
# ─────────────────────────────────────────────────────────────────────────────

class _FPSSparkline:
    MAX = 60

    def __init__(self):
        self._samples: deque[float] = deque([60.0] * self.MAX, maxlen=self.MAX)

    def push(self, fps: float) -> None:
        self._samples.append(max(0.0, min(200.0, fps)))

    def draw(self, p: QPainter, x: int, y: int, w: int, h: int) -> None:
        if len(self._samples) < 2:
            return
        samples = list(self._samples)
        peak = max(samples) or 1.0
        sx = w / (len(samples) - 1)

        path = QPainterPath()
        path.moveTo(x, y + h)
        for i, v in enumerate(samples):
            px = x + i * sx
            py = y + h - (v / peak) * h
            if i == 0:
                path.lineTo(px, py)
            else:
                path.lineTo(px, py)
        path.lineTo(x + w, y + h)
        path.closeSubpath()

        grad = QLinearGradient(x, y, x, y + h)
        grad.setColorAt(0.0, QColor(0, 230, 100, 60))
        grad.setColorAt(1.0, QColor(0, 230, 100, 5))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor(0, 230, 100, 120), 1))
        p.drawPath(path)


# ─────────────────────────────────────────────────────────────────────────────
#  _GameViewCanvas — QPainter-only, sem OpenGL / QRhi
# ─────────────────────────────────────────────────────────────────────────────

class _GameViewCanvas(QWidget):
    """Game View canvas renderizado 100% com QPainter.

    Nenhuma textura OpenGL compartilhada → sem QRhi cross-context.
    """

    # Signals
    object_clicked = Signal(object)    # emitido ao clicar num objeto no canvas

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 200)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setMouseTracking(True)

        # Estado de modo
        self.mode:              ViewportMode = ViewportMode.EDITOR
        self.play_start_time:   float = 0.0
        self.frame_count:       int   = 0
        self.last_frame_time:   float = time.time()

        # Stats
        self.fps:           float = 60.0
        self.frame_ms:      float = 16.6
        self.physics_ms:    float = 1.2
        self.scripts_ms:    float = 2.4
        self.rendering_ms:  float = 3.1
        self.draw_calls:    int   = 0
        self.object_count:  int   = 0
        self.active_camera: str   = "Editor Camera"

        # Overlay flags
        self.show_grid:         bool = True
        self.show_colliders:    bool = True
        self.show_nav:          bool = True
        self.show_ai:           bool = True
        self.show_audio:        bool = True
        self.show_stats:        bool = True
        self.show_node_exec:    bool = True
        self.show_runtime_vars: bool = True

        # Node execution
        self.active_node_name:  str   = ""
        self.active_node_id:    str   = ""
        self.highlight_until:   float = 0.0

        # Game objects snapshot
        self.game_objects: list[dict] = []
        self.selected_object_id: str  = ""
        self._texture_cache: dict[str, tuple[float, QPixmap]] = {}

        # FPS sparkline
        self._sparkline = _FPSSparkline()
        self._pulse: float = 0.0
        self.play_start_time: float = time.time()
        self.last_frame_time: float = time.time()
        self.frame_ms: float = 16.0

        # Border flash for node execution
        self._node_flash_until: float = 0.0

        # Runtime Visualization Renderer
        self._renderer = RuntimeVisualizationRenderer()

    # ── State updates ──────────────────────────────────────────────────────

    def set_mode(self, mode: ViewportMode) -> None:
        self.mode = mode
        if mode == ViewportMode.GAME:
            self.play_start_time = time.time()
        self.update()

    def push_fps(self, fps: float) -> None:
        self.fps = fps
        self._sparkline.push(fps)

    def apply_snapshot(self, snap: dict) -> None:
        self.active_node_name = snap.get("node_name") or ""
        self.active_node_id   = snap.get("node_id")   or ""
        self.highlight_until  = snap.get("highlight_until", 0.0)
        self.game_objects     = snap.get("objects", self.game_objects)
        self.fps              = snap.get("fps", self.fps)
        self.draw_calls       = snap.get("draw_calls", self.draw_calls)
        self.object_count     = snap.get("object_count", len(self.game_objects))
        self.update()

    # ── Paint ──────────────────────────────────────────────────────────────

    def paintEvent(self, _event):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            p.setRenderHint(QPainter.TextAntialiasing)

            w, h = self.width(), self.height()
            self._pulse += 0.07
            pulse = 0.5 + 0.5 * math.sin(self._pulse)

            p.fillRect(0, 0, w, h, _C.BG_DEEP)
            if self.show_grid:
                self._draw_grid(p, w, h)
            if self.mode != ViewportMode.EDITOR:
                self._draw_debug_overlays(p, w, h)
            self._draw_game_objects(p, w, h)
            self._draw_mode_border(p, w, h, pulse)

            if self.show_node_exec and time.time() < self._node_flash_until:
                fade = min(1.0, (self._node_flash_until - time.time()) / 0.12)
                p.fillRect(0, 0, w, h, QColor(174, 125, 240, int(18 * fade)))

            self._draw_camera_badge(p, w, h)
            if self.mode != ViewportMode.EDITOR:
                self._draw_runtime_clock(p, w, h)
            if self.show_stats and self.mode != ViewportMode.EDITOR:
                self._draw_stats_panel(p, w, h)
                self._sparkline.draw(p, w - 108, h - 46, 100, 38)
            if self.show_node_exec:
                self._draw_node_pill(p, w, h, pulse)
            if self.mode == ViewportMode.EDITOR and not self.game_objects:
                self._draw_editor_placeholder(p, w, h)
        finally:
            if p.isActive():
                p.end()

    # ── Drawing sub-methods ────────────────────────────────────────────────

    def _draw_grid(self, p: QPainter, w: int, h: int) -> None:
        # Minor grid 20px
        p.setPen(QPen(_C.GRID_MINOR, 0.5))
        step = 20
        x = 0
        while x <= w:
            p.drawLine(x, 0, x, h); x += step
        y = 0
        while y <= h:
            p.drawLine(0, y, w, y); y += step

        # Major grid 100px
        p.setPen(QPen(_C.GRID_MAJOR, 0.8))
        step = 100
        x = 0
        while x <= w:
            p.drawLine(x, 0, x, h); x += step
        y = 0
        while y <= h:
            p.drawLine(0, y, w, y); y += step

        # Axes
        cx, cy = w // 2, h // 2
        p.setPen(QPen(_C.AXIS_X, 1.0))
        p.drawLine(0, cy, w, cy)
        p.setPen(QPen(_C.AXIS_Y, 1.0))
        p.drawLine(cx, 0, cx, h)

    def _draw_debug_overlays(self, p: QPainter, w: int, h: int) -> None:
        cx, cy = w / 2.0, h / 2.0
        node_l = self.active_node_name.lower()
        is_hl  = time.time() < self.highlight_until

        # Colliders
        if self.show_colliders:
            self._draw_physics_overlays(p, cx, cy)

        # AI FOV
        if self.show_ai:
            poly = QPolygonF([
                QPointF(cx, cy),
                QPointF(cx + 95, cy - 42),
                QPointF(cx + 95, cy + 42),
            ])
            p.setPen(QPen(_C.AI_FOV, 1.0, Qt.DashLine))
            p.setBrush(QBrush(_C.AI_FOV_FILL))
            p.drawPolygon(poly)

        # Navigation path
        if self.show_nav:
            dest_x, dest_y = cx + 110, cy - 28
            p.setPen(QPen(_C.NAV_PATH, 1.2, Qt.DotLine))
            p.drawLine(int(cx), int(cy), int(dest_x), int(dest_y))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(_C.NAV_PATH))
            p.drawEllipse(QPointF(dest_x, dest_y), 5, 5)

        # Velocity arrow (move nodes)
        if is_hl or "move" in node_l or "velocity" in node_l:
            p.setPen(QPen(_C.VELOCITY, 2.5))
            p.drawLine(int(cx), int(cy), int(cx + 65), int(cy))
            p.setBrush(QBrush(_C.VELOCITY))
            tri = QPolygonF([
                QPointF(cx + 73, cy),
                QPointF(cx + 63, cy - 5),
                QPointF(cx + 63, cy + 5),
            ])
            p.setPen(Qt.NoPen)
            p.drawPolygon(tri)
            p.setFont(QFont("Consolas", 7))
            p.setPen(QPen(_C.VELOCITY))
            p.drawText(QPointF(cx + 10, cy - 8), "vel: (4.50, 0.00)")

        # Jump force arrow
        if is_hl and "jump" in node_l:
            p.setPen(QPen(_C.JUMP_FORCE, 2.8))
            p.drawLine(int(cx), int(cy), int(cx), int(cy - 70))
            p.setBrush(QBrush(_C.JUMP_FORCE))
            tri = QPolygonF([
                QPointF(cx, cy - 78),
                QPointF(cx - 5, cy - 68),
                QPointF(cx + 5, cy - 68),
            ])
            p.setPen(Qt.NoPen)
            p.drawPolygon(tri)
            p.setFont(QFont("Consolas", 7))
            p.setPen(QPen(_C.JUMP_FORCE))
            p.drawText(QPointF(cx + 8, cy - 42), "JumpForce: 12.0 N")

        # Audio waves
        if self.show_audio and (is_hl and "audio" in node_l):
            for r in (40, 60, 80):
                alpha = int(120 - r)
                p.setPen(QPen(QColor(174, 125, 240, alpha), 1.2, Qt.DashLine))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(cx, cy), float(r), float(r))

    def _draw_physics_overlays(
        self, p: QPainter, cx: float, cy: float
    ) -> None:
        for obj in self.game_objects:
            collider = obj.get("collider")
            rigidbody = obj.get("rigidbody")
            if not isinstance(collider, dict) and not isinstance(rigidbody, dict):
                continue
            ox = cx + float(obj.get("x", 0.0))
            oy = cy + float(obj.get("y", 0.0))
            width = max(1.0, float(
                (collider or {}).get("width", obj.get("w", 1.0))
            ))
            height = max(1.0, float(
                (collider or {}).get("height", obj.get("h", 1.0))
            ))
            offset_x = float((collider or {}).get("offset_x", 0.0))
            offset_y = float((collider or {}).get("offset_y", 0.0))

            p.save()
            p.translate(ox + offset_x, oy + offset_y)
            p.rotate(float(obj.get("rotation", 0.0)))
            p.setPen(QPen(_C.COLLIDER, 1.4, Qt.DashLine))
            p.setBrush(QBrush(_C.COLLIDER_FILL))
            shape = str((collider or {}).get("type", "box")).lower()
            rect = QRectF(-width / 2, -height / 2, width, height)
            if shape in {"circle", "sphere"}:
                p.drawEllipse(rect)
            else:
                p.drawRect(rect)
            p.restore()

            velocity_y = float(obj.get("velocity_y", 0.0))
            if isinstance(rigidbody, dict) and abs(velocity_y) > 0.5:
                arrow = max(-70.0, min(70.0, velocity_y * 0.08))
                p.setPen(QPen(_C.VELOCITY, 2.0))
                p.drawLine(
                    QPointF(ox, oy),
                    QPointF(ox, oy + arrow),
                )

    def _draw_game_objects(self, p: QPainter, w: int, h: int) -> None:
        cx, cy = w / 2, h / 2
        layer_order = {"Background": 0, "Default": 1, "Foreground": 2, "UI": 3}
        objects_source = self.game_objects
        if not objects_source:
            t = time.time() - self.play_start_time
            px = math.sin(t * 1.8) * 35.0
            py = -20.0 + abs(math.sin(t * 4.5)) * -14.0
            objects_source = [
                {"id": "ground", "name": "Ground", "x": 0, "y": 30, "w": 260, "h": 16, "color": "#22c55e", "active": True, "renderer_enabled": True},
                {"id": "player", "name": "Player", "x": px, "y": py, "w": 24, "h": 36, "color": "#38bdf8", "active": True, "renderer_enabled": True, "rigidbody": {"velocity_y": -2.0}},
            ]
        ordered = sorted(objects_source, key=lambda obj: (
            layer_order.get(str(obj.get("render_layer", "Default")), 1),
            int(obj.get("sort_order", 0)),
        ))
        for obj in ordered:
            if not obj.get("active", True) or not obj.get("renderer_enabled", True):
                continue
            if self.mode == ViewportMode.GAME and self._is_camera(obj):
                continue
            ox = cx + float(obj.get("x", 0))
            oy = cy + float(obj.get("y", 0))
            width = max(1.0, float(obj.get("w", obj.get("size", 14))))
            height = max(1.0, float(obj.get("h", obj.get("size", 14))))
            color = self._object_color(obj.get("color", "#4c9aff"))
            is_sel = obj.get("id", "") == self.selected_object_id
            rect = QRectF(-width / 2, -height / 2, width, height)

            p.save()
            p.translate(ox, oy)
            p.rotate(float(obj.get("rotation", 0.0)))
            pixmap = self._object_pixmap(obj)
            if pixmap is not None:
                p.drawPixmap(rect, pixmap, QRectF(pixmap.rect()))
            else:
                p.setPen(QPen(color.lighter(145), 1.0))
                p.setBrush(QBrush(color))
                p.drawRoundedRect(rect, min(4.0, width / 4), min(4.0, height / 4))
            if is_sel:
                p.setBrush(Qt.NoBrush)
                p.setPen(QPen(_C.SELECTION_RING, 1.5))
                p.drawRect(rect.adjusted(-3, -3, 3, 3))
            p.restore()

            lbl = str(obj.get("name") or obj.get("label") or "")
            if lbl:
                p.setFont(QFont("Segoe UI", 7))
                p.setPen(QPen(_C.TEXT_SECONDARY))
                p.drawText(int(ox + width / 2 + 4), int(oy + 4), lbl)

    def _object_pixmap(self, obj: dict[str, Any]) -> QPixmap | None:
        texture = str(obj.get("texture", "")).strip()
        if not texture:
            return None
        path = Path(texture)
        if not path.is_absolute():
            path = Path.cwd() / path
        try:
            modified = path.stat().st_mtime
        except OSError:
            return None
        key = str(path.resolve())
        cached = self._texture_cache.get(key)
        if cached is None or cached[0] != modified:
            pixmap = QPixmap(key)
            if pixmap.isNull():
                return None
            cached = (modified, pixmap)
            self._texture_cache[key] = cached
        return cached[1]

    @staticmethod
    def _is_camera(obj: dict[str, Any]) -> bool:
        return (
            "Camera2D" in obj.get("component_names", [])
            or isinstance(obj.get("camera"), dict)
            or obj.get("mesh_type") == "Camera"
        )

    @staticmethod
    def _object_color(value: Any) -> QColor:
        """Normalize serialized scene colors into a valid QColor."""
        if isinstance(value, QColor):
            return QColor(value)
        if isinstance(value, (list, tuple)) and len(value) in (3, 4):
            try:
                channels = [float(channel) for channel in value]
                rgb = channels[:3]
                if rgb and all(0.0 <= channel <= 1.0 for channel in rgb):
                    channels[:3] = [channel * 255 for channel in rgb]
                    if len(channels) == 4 and 0.0 <= channels[3] <= 1.0:
                        channels[3] *= 255
                channels = [max(0, min(255, int(channel))) for channel in channels]
                return QColor(*channels)
            except (TypeError, ValueError):
                pass
        if isinstance(value, str):
            color = QColor(value)
            if color.isValid():
                return color
        return QColor("#4c9aff")

    def _draw_mode_border(self, p: QPainter, w: int, h: int, pulse: float) -> None:
        if self.mode == ViewportMode.GAME:
            alpha = int(160 + 80 * pulse)
            color = QColor(_C.BORDER_PLAY.red(), _C.BORDER_PLAY.green(),
                           _C.BORDER_PLAY.blue(), alpha)
            thickness = 2.0 + pulse * 0.5
        elif self.mode == ViewportMode.DEBUG:
            alpha = int(140 + 80 * pulse)
            color = QColor(_C.BORDER_PAUSE.red(), _C.BORDER_PAUSE.green(),
                           _C.BORDER_PAUSE.blue(), alpha)
            thickness = 1.8
        else:
            color = _C.BORDER_IDLE
            thickness = 1.0

        p.setPen(QPen(color, thickness))
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(0.5, 0.5, w - 1, h - 1))

    def _draw_camera_badge(self, p: QPainter, w: int, h: int) -> None:
        cam = self.active_camera
        icon = "📷"
        text = f"{icon} {cam}"
        p.setFont(QFont("Segoe UI", 8))
        fm = QFontMetrics(p.font())
        tw = fm.horizontalAdvance(text) + 16

        p.setBrush(QBrush(QColor(0, 0, 0, 130)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(6, 6, tw, 20), 3, 3)
        p.setPen(QPen(_C.TEXT_SECONDARY))
        p.drawText(QRectF(6, 6, tw, 20), Qt.AlignCenter, text)

    def _draw_runtime_clock(self, p: QPainter, w: int, h: int) -> None:
        elapsed = time.time() - self.play_start_time if self.mode == ViewportMode.GAME else 0.0
        minutes = int(elapsed) // 60
        seconds = int(elapsed) % 60
        millis  = int((elapsed % 1) * 10)
        t = f"{minutes:02d}:{seconds:02d}.{millis}"

        p.setFont(QFont("Consolas", 9, QFont.Bold))
        fm = QFontMetrics(p.font())
        tw = fm.horizontalAdvance(t) + 16

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(0, 0, 0, 140)))
        p.drawRoundedRect(QRectF(w - tw - 6, 6, tw, 20), 3, 3)

        color = _C.ACCENT_PLAY if self.mode == ViewportMode.GAME else _C.ACCENT_PAUSE
        p.setPen(QPen(color))
        p.drawText(QRectF(w - tw - 6, 6, tw, 20), Qt.AlignCenter, t)

    def _draw_stats_panel(self, p: QPainter, w: int, h: int) -> None:
        panel_w, panel_h = 116, 80
        px, py = w - panel_w - 6, h - panel_h - 50  # above sparkline

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(0, 0, 0, 160)))
        p.drawRoundedRect(QRectF(px, py, panel_w, panel_h), 4, 4)

        rows = [
            (_C.ACCENT_PLAY,   f"FPS  {self.fps:6.1f}"),
            (_C.ACCENT_EDITOR, f"PHY  {self.physics_ms:4.1f} ms"),
            (_C.ACCENT_NODE,   f"SCR  {self.scripts_ms:4.1f} ms"),
            (QColor("#e07a5f"), f"RND  {self.rendering_ms:4.1f} ms"),
            (QColor("#d5b84b"), f"DC   {self.draw_calls:4d}"),
        ]
        p.setFont(QFont("Consolas", 8))
        for i, (color, text) in enumerate(rows):
            p.setPen(QPen(color))
            p.drawText(int(px + 8), int(py + 14 + i * 14), text)

    def _draw_node_pill(self, p: QPainter, w: int, h: int, pulse: float) -> None:
        if not self.active_node_name:
            return
        now = time.time()
        if now >= self.highlight_until + 0.2:
            return
        fade = min(1.0, (self.highlight_until - now) / 0.6)
        if fade <= 0:
            return

        alpha = int(240 * fade)
        text = f"⚡  {self.active_node_name}"
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        fm = QFontMetrics(p.font())
        tw = fm.horizontalAdvance(text) + 20
        pill = QRectF(8, h - 36, min(w - 16, tw), 26)

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(174, 125, 240, int(55 * fade))))
        p.drawRoundedRect(pill, 5, 5)

        p.setPen(QPen(QColor(230, 200, 255, alpha)))
        p.drawText(pill.adjusted(8, 0, 0, 0), Qt.AlignVCenter, text)

    def _draw_editor_placeholder(self, p: QPainter, w: int, h: int) -> None:
        p.setFont(QFont("Segoe UI", 11))
        p.setPen(QPen(_C.TEXT_DIM))
        p.drawText(QRectF(0, 0, w, h), Qt.AlignCenter,
                   "▶  Press Play to enter Game View")

    # ── Mouse ──────────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            pos = event.position()
            cx, cy = self.width() / 2, self.height() / 2
            for obj in self.game_objects:
                ox = cx + float(obj.get("x", 0))
                oy = cy + float(obj.get("y", 0))
                width = max(1.0, float(obj.get("w", obj.get("size", 14))))
                height = max(1.0, float(obj.get("h", obj.get("size", 14))))
                if (
                    abs(pos.x() - ox) <= width / 2
                    and abs(pos.y() - oy) <= height / 2
                ):
                    self.selected_object_id = obj.get("id", "")
                    self.object_clicked.emit(obj)
                    self.update()
                    return
        super().mousePressEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
#  _OverlayToggleBar — barra horizontal de toggles de overlay
# ─────────────────────────────────────────────────────────────────────────────

_OVERLAY_BTN_STYLE = """
    QPushButton {{
        background: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 3px;
        padding: 1px 7px;
        font-size: 9px;
        font-weight: bold;
    }}
    QPushButton:hover {{ background: #2a2e38; }}
"""

_ACTIVE_BG   = "#1e3a28"
_ACTIVE_FG   = "#00e664"
_ACTIVE_BD   = "#00e664"
_INACTIVE_BG = "#161a22"
_INACTIVE_FG = "#4a5060"
_INACTIVE_BD = "#252930"


class _OverlayToggle(QPushButton):
    def __init__(self, label: str, canvas: _GameViewCanvas, attr: str, parent=None):
        super().__init__(label, parent)
        self._canvas = canvas
        self._attr   = attr
        self.setCheckable(True)
        self.setChecked(getattr(canvas, attr, True))
        self._refresh()
        self.toggled.connect(self._on_toggle)

    def _on_toggle(self, state: bool) -> None:
        setattr(self._canvas, self._attr, state)
        self._refresh()
        self._canvas.update()

    def _refresh(self) -> None:
        if self.isChecked():
            self.setStyleSheet(_OVERLAY_BTN_STYLE.format(
                bg=_ACTIVE_BG, fg=_ACTIVE_FG, border=_ACTIVE_BD))
        else:
            self.setStyleSheet(_OVERLAY_BTN_STYLE.format(
                bg=_INACTIVE_BG, fg=_INACTIVE_FG, border=_INACTIVE_BD))


# ─────────────────────────────────────────────────────────────────────────────
#  _PlayButton — botão de play com visual destacado
# ─────────────────────────────────────────────────────────────────────────────

_PLAY_STYLE_IDLE   = "QPushButton{background:#0f1f17;color:#00e664;border:1px solid #00e664;border-radius:4px;padding:3px 12px;font-size:10px;font-weight:bold;}QPushButton:hover{background:#163020;}"
_PLAY_STYLE_ACTIVE = "QPushButton{background:#00c853;color:#000;border:1px solid #00e664;border-radius:4px;padding:3px 12px;font-size:10px;font-weight:bold;}"
_PAUSE_STYLE_IDLE  = "QPushButton{background:#1e1a0f;color:#ffb432;border:1px solid #ffb432;border-radius:4px;padding:3px 10px;font-size:10px;font-weight:bold;}QPushButton:hover{background:#2a2410;}"
_PAUSE_STYLE_ACTIVE= "QPushButton{background:#e6a020;color:#000;border:1px solid #ffb432;border-radius:4px;padding:3px 10px;font-size:10px;font-weight:bold;}"
_STOP_STYLE        = "QPushButton{background:#1e1010;color:#ff4d4d;border:1px solid #ff4d4d;border-radius:4px;padding:3px 10px;font-size:10px;font-weight:bold;}QPushButton:hover{background:#2a1010;}"
_STEP_STYLE        = "QPushButton{background:#161a22;color:#6b7385;border:1px solid #252930;border-radius:3px;padding:2px 8px;font-size:9px;}QPushButton:hover{color:#e8eaf0;border-color:#4a5060;}"


# ─────────────────────────────────────────────────────────────────────────────
#  RuntimeVisualizationPanelWidget — Game View AAA
# ─────────────────────────────────────────────────────────────────────────────

class RuntimeVisualizationPanelWidget(RuntimePanelControllerMixin, QFrame):
    """Game View AAA integrada ao Visual Scripting da Zennity Engine."""

    object_selected         = Signal(object)
    node_selected_requested = Signal(str)

    # ── Stylesheet base ────────────────────────────────────────────────────

    _BASE_STYLE = """
        QFrame#GameView {
            background: #080a0e;
            border: 1px solid #1a1e28;
            border-radius: 6px;
        }
        QLabel { color: #6b7385; font-size: 9px; }
        QComboBox {
            background: #0f1117; color: #aeb6c5;
            border: 1px solid #252930; border-radius: 3px;
            padding: 1px 6px; font-size: 9px;
        }
        QComboBox::drop-down { border: none; }
        QSlider::groove:horizontal {
            background: #1a1e28; height: 3px; border-radius: 1px;
        }
        QSlider::handle:horizontal {
            background: #4a5060; width: 10px; height: 10px;
            margin: -3px 0; border-radius: 5px;
        }
        QSlider::sub-page:horizontal { background: #4c9aff; border-radius: 1px; }
        QCheckBox { color: #6b7385; font-size: 9px; }
        QCheckBox::indicator { width: 11px; height: 11px; }
    """
    VIEWPORT_MODE = ViewportMode
    PLAY_STYLE_ACTIVE = _PLAY_STYLE_ACTIVE
    PLAY_STYLE_IDLE = _PLAY_STYLE_IDLE
    PAUSE_STYLE_ACTIVE = _PAUSE_STYLE_ACTIVE
    PAUSE_STYLE_IDLE = _PAUSE_STYLE_IDLE

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("GameView")
        self.setStyleSheet(self._BASE_STYLE)

        self.viewport_mode:     ViewportMode = ViewportMode.EDITOR
        self.target_object:     Any  = None
        self.active_node_id:    Optional[str] = None
        self.active_node_name:  str  = ""
        self.highlight_timer:   float = 0.0

        # Performance stats (expostos para compatibilidade)
        self.fps:            float = 60.0
        self.physics_ms:     float = 1.2
        self.scripts_ms:     float = 2.4
        self.rendering_ms:   float = 3.1
        self.show_grid:      bool  = True
        self.show_gizmos:    bool  = True
        self.show_physics:   bool  = True
        self.show_colliders: bool  = True
        self.show_ai:        bool  = True

        # Replay buffer
        self.replay_buffer:      deque[dict[str, Any]] = deque(maxlen=300)
        self.is_replaying:       bool  = False
        self.replay_frame_index: int   = 0

        # Canvas (QPainter-only — sem QRhi conflict)
        self._canvas = _GameViewCanvas(self)
        self._canvas.object_clicked.connect(self._on_canvas_object_clicked)

        # Runtime Overlay Renderer
        self.renderer = RuntimeVisualizationRenderer()

        # Backwards-compat QCheckBox attributes (usados por testes legados)
        # A UI real usa _OverlayToggle buttons na overlay bar, mas os testes
        # acessam panel.chk_phys / chk_nav / chk_ai diretamente.
        from PySide6.QtWidgets import QCheckBox as _QCB
        self.chk_phys = _QCB()
        self.chk_phys.setChecked(True)
        self.chk_phys.toggled.connect(
            lambda c: setattr(self.renderer, "show_colliders", c)
            or setattr(self._canvas, "show_colliders", c)
        )
        self.chk_nav = _QCB()
        self.chk_nav.setChecked(True)
        self.chk_nav.toggled.connect(
            lambda c: setattr(self.renderer, "show_pathfinding", c)
            or setattr(self._canvas, "show_nav", c)
        )
        self.chk_ai = _QCB()
        self.chk_ai.setChecked(True)
        self.chk_ai.toggled.connect(
            lambda c: setattr(self.renderer, "show_ai_fov", c)
            or setattr(self._canvas, "show_ai", c)
        )

        # Frame ticker
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(16)
        self._update_timer.timeout.connect(self._on_tick)
        self._update_timer.start()

        self._build_ui()

    def set_mode(self, mode: ViewportMode) -> None:
        self.set_viewport_mode(mode)

    # ── UI Builder ────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.transport_toolbar = self._build_primary_toolbar()
        root.addWidget(self.transport_toolbar)
        root.addWidget(self._build_overlay_bar())
        root.addWidget(self._canvas, 1)
        root.addWidget(self._build_step_controls())   # hidden in EDITOR/GAME
        root.addWidget(self._build_replay_bar())
        root.addWidget(self._build_status_bar())

    def set_transport_controls_visible(self, visible: bool) -> None:
        self.transport_toolbar.setVisible(visible)

    def _build_primary_toolbar(self) -> QWidget:
        bar = QWidget(self)
        bar.setObjectName("PrimaryToolbar")
        bar.setStyleSheet("QWidget#PrimaryToolbar{background:#0f1117;border-bottom:1px solid #1a1e28;}")
        bar.setFixedHeight(36)

        h = QHBoxLayout(bar)
        h.setContentsMargins(8, 0, 8, 0)
        h.setSpacing(4)

        # ── Title ─────────────────────────────────────────────────────────
        title = QLabel("GAME VIEW", bar)
        title.setStyleSheet("color:#4a5060;font-size:9px;font-weight:bold;letter-spacing:2px;")
        h.addWidget(title)

        sep = QFrame(bar); sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color:#1a1e28;"); h.addWidget(sep)

        # ── Play / Pause / Stop ───────────────────────────────────────────
        self.btn_play = QPushButton("▶  PLAY", bar)
        self.btn_play.setStyleSheet(_PLAY_STYLE_IDLE)
        self.btn_play.setFixedHeight(26)
        self.btn_play.clicked.connect(self.start_play_mode)

        self.btn_pause = QPushButton("⏸  PAUSE", bar)
        self.btn_pause.setStyleSheet(_PAUSE_STYLE_IDLE)
        self.btn_pause.setFixedHeight(26)
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.toggle_pause_mode)

        self.btn_stop = QPushButton("⏹  STOP", bar)
        self.btn_stop.setStyleSheet(_STOP_STYLE)
        self.btn_stop.setFixedHeight(26)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_play_mode)

        h.addWidget(self.btn_play)
        h.addWidget(self.btn_pause)
        h.addWidget(self.btn_stop)

        sep2 = QFrame(bar); sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet("color:#1a1e28;"); h.addWidget(sep2)

        # ── Camera selector ───────────────────────────────────────────────
        cam_lbl = QLabel("📷", bar)
        cam_lbl.setStyleSheet("color:#4a5060;font-size:10px;")
        self.camera_selector = QComboBox(bar)
        self.camera_selector.addItems([
            "Editor Camera", "Main Camera", "Follow Player", "Free Camera"
        ])
        self.camera_selector.setFixedHeight(22)
        self.camera_selector.currentTextChanged.connect(
            lambda t: setattr(self._canvas, "active_camera", t) or self._canvas.update()
        )
        h.addWidget(cam_lbl)
        h.addWidget(self.camera_selector)

        h.addStretch(1)

        # ── Mode badge ────────────────────────────────────────────────────
        self.mode_badge = QLabel("● EDITOR", bar)
        self.mode_badge.setStyleSheet(
            "color:#4c9aff;font-size:9px;font-weight:bold;letter-spacing:1px;"
        )
        h.addWidget(self.mode_badge)

        return bar

    def _build_overlay_bar(self) -> QWidget:
        bar = QWidget(self)
        bar.setObjectName("OverlayBar")
        bar.setStyleSheet("QWidget#OverlayBar{background:#0b0d12;border-bottom:1px solid #141720;}")
        bar.setFixedHeight(24)

        h = QHBoxLayout(bar)
        h.setContentsMargins(8, 2, 8, 2)
        h.setSpacing(4)

        lbl = QLabel("OVERLAYS:", bar)
        lbl.setStyleSheet("color:#2e3340;font-size:8px;font-weight:bold;letter-spacing:1px;")
        h.addWidget(lbl)

        overlays = [
            ("Grid",       "show_grid"),
            ("Physics",    "show_colliders"),
            ("Navigation", "show_nav"),
            ("AI",         "show_ai"),
            ("Audio",      "show_audio"),
            ("Node Exec",  "show_node_exec"),
            ("Vars",       "show_runtime_vars"),
            ("Stats",      "show_stats"),
        ]
        for label, attr in overlays:
            btn = _OverlayToggle(label, self._canvas, attr, bar)
            btn.setFixedHeight(18)
            h.addWidget(btn)

        h.addStretch(1)
        return bar

    def _build_step_controls(self) -> QWidget:
        self._step_bar = QWidget(self)
        self._step_bar.setObjectName("StepBar")
        self._step_bar.setStyleSheet(
            "QWidget#StepBar{background:#0f1117;border-top:1px solid #1a1e28;}"
        )
        self._step_bar.setFixedHeight(28)
        self._step_bar.hide()   # shown only in DEBUG

        h = QHBoxLayout(self._step_bar)
        h.setContentsMargins(8, 2, 8, 2)
        h.setSpacing(4)

        lbl = QLabel("⏸  PAUSED —", self._step_bar)
        lbl.setStyleSheet("color:#ffb432;font-size:9px;font-weight:bold;")
        h.addWidget(lbl)

        self.btn_step_frame = QPushButton("Step Frame", self._step_bar)
        self.btn_step_frame.setStyleSheet(_STEP_STYLE)
        self.btn_step_frame.setFixedHeight(22)
        self.btn_step_frame.clicked.connect(self.step_frame)

        self.btn_step_node = QPushButton("Step Node", self._step_bar)
        self.btn_step_node.setStyleSheet(_STEP_STYLE)
        self.btn_step_node.setFixedHeight(22)
        self.btn_step_node.clicked.connect(self.step_node)

        self.btn_continue = QPushButton("▶  Continue", self._step_bar)
        self.btn_continue.setStyleSheet(_PLAY_STYLE_IDLE)
        self.btn_continue.setFixedHeight(22)
        self.btn_continue.clicked.connect(self.toggle_pause_mode)

        h.addWidget(self.btn_step_frame)
        h.addWidget(self.btn_step_node)
        h.addWidget(self.btn_continue)
        h.addStretch(1)

        return self._step_bar

    def _build_replay_bar(self) -> QWidget:
        bar = QWidget(self)
        bar.setObjectName("ReplayBar")
        bar.setStyleSheet(
            "QWidget#ReplayBar{background:#0b0d12;border-top:1px solid #141720;}"
        )
        bar.setFixedHeight(24)

        h = QHBoxLayout(bar)
        h.setContentsMargins(6, 2, 6, 2)
        h.setSpacing(3)

        _sb = "QPushButton{background:#0f1117;color:#4a5060;border:1px solid #1a1e28;border-radius:2px;padding:1px 5px;font-size:9px;}QPushButton:hover{color:#aeb6c5;}"

        self.btn_rewind      = QPushButton("⏮", bar); self.btn_rewind.setStyleSheet(_sb)
        self.btn_step_back   = QPushButton("◀", bar);  self.btn_step_back.setStyleSheet(_sb)
        self.btn_replay_play = QPushButton("▶ Replay", bar); self.btn_replay_play.setStyleSheet(_sb)
        self.btn_step_fw     = QPushButton("▶", bar);  self.btn_step_fw.setStyleSheet(_sb)
        self.btn_live        = QPushButton("🔴 LIVE", bar)
        self.btn_live.setStyleSheet(
            "QPushButton{background:#1e0a0a;color:#ff4d4d;border:1px solid #ff3333;"
            "border-radius:2px;padding:1px 7px;font-size:9px;font-weight:bold;}"
        )

        for btn in (self.btn_rewind, self.btn_step_back,
                    self.btn_replay_play, self.btn_step_fw, self.btn_live):
            btn.setFixedHeight(18)
            h.addWidget(btn)

        self.timeline_slider = QSlider(Qt.Horizontal, bar)
        self.timeline_slider.setRange(0, 300)
        self.timeline_slider.setValue(300)
        h.addWidget(self.timeline_slider)

        self.btn_rewind.clicked.connect(lambda: self.set_replay_frame(0))
        self.btn_step_back.clicked.connect(
            lambda: self.set_replay_frame(max(0, self.replay_frame_index - 10))
        )
        self.btn_step_fw.clicked.connect(
            lambda: self.set_replay_frame(
                min(len(self.replay_buffer) - 1, self.replay_frame_index + 10))
        )
        self.btn_live.clicked.connect(self.resume_live)
        self.timeline_slider.valueChanged.connect(self.set_replay_frame)

        return bar

    def _build_status_bar(self) -> QWidget:
        bar = QWidget(self)
        bar.setObjectName("StatusBar")
        bar.setStyleSheet(
            "QWidget#StatusBar{background:#080a0e;border-top:1px solid #101318;}"
        )
        bar.setFixedHeight(20)

        h = QHBoxLayout(bar)
        h.setContentsMargins(8, 0, 8, 0)
        h.setSpacing(12)

        def _stat_lbl(text=""):
            l = QLabel(text, bar)
            l.setStyleSheet("color:#2e3340;font-size:8px;font-family:Consolas;")
            return l

        self._lbl_fps      = _stat_lbl("FPS —")
        self._lbl_frame_ms = _stat_lbl("Frame —")
        self._lbl_dc       = _stat_lbl("DC —")
        self._lbl_objs     = _stat_lbl("Objects —")
        self._lbl_runtime  = _stat_lbl("Runtime —")

        for lbl in (self._lbl_fps, self._lbl_frame_ms,
                    self._lbl_dc, self._lbl_objs, self._lbl_runtime):
            h.addWidget(lbl)

        h.addStretch(1)

        self._lbl_build = _stat_lbl("Zennity Engine · Visual Scripting Game View")
        self._lbl_build.setStyleSheet("color:#1e2230;font-size:8px;")
        h.addWidget(self._lbl_build)

        return bar

    def apply_live_logic_edit(self, target_object: Any, var_name: str, new_value: Any) -> bool:
        if not target_object:
            return False
        try:
            if hasattr(target_object, var_name):
                setattr(target_object, var_name, new_value)
            elif hasattr(target_object, "variables") and isinstance(target_object.variables, dict):
                target_object.variables[var_name] = new_value
            from editor.runtime.editor_context import EditorContext
            ctx = EditorContext.instance()
            if ctx and hasattr(ctx, "property_binding"):
                ctx.property_binding.notify_change(target_object, var_name, new_value)
            return True
        except Exception as e:
            print(f"[LiveLogicEditing] {e}")
            return False

    # ── Node Execution Highlight ──────────────────────────────────────────

    def highlight_execution_node(self, node_id: str, node_name: str) -> None:
        self.active_node_id    = str(node_id)
        self.active_node_name  = str(node_name)
        self.highlight_timer   = time.time() + 0.6
        self._canvas.active_node_id   = self.active_node_id
        self._canvas.active_node_name = self.active_node_name
        self._canvas.highlight_until  = self.highlight_timer
        self._canvas._node_flash_until = time.time() + 0.12
        self._canvas.update()

    def set_target_object(self, obj: Any) -> None:
        self.target_object = obj
        self._canvas.update()

    # ── Stats Update ──────────────────────────────────────────────────────

    def update_stats(
        self,
        fps: Optional[float] = None,
        physics_ms: Optional[float] = None,
        scripts_ms: Optional[float] = None,
        rendering_ms: Optional[float] = None,
        draw_calls: Optional[int] = None,
        object_count: Optional[int] = None,
    ) -> None:
        if fps          is not None:
            self.fps = fps
            self._canvas.fps = fps
            self._canvas.push_fps(fps)
            self._lbl_fps.setText(f"FPS {fps:5.1f}")
        if physics_ms   is not None:
            self.physics_ms  = self._canvas.physics_ms  = physics_ms
        if scripts_ms   is not None:
            self.scripts_ms  = self._canvas.scripts_ms  = scripts_ms
        if rendering_ms is not None:
            self.rendering_ms = self._canvas.rendering_ms = rendering_ms
            self._lbl_frame_ms.setText(f"Frame {rendering_ms:.1f}ms")
        if draw_calls   is not None:
            self._canvas.draw_calls = draw_calls
            self._lbl_dc.setText(f"DC {draw_calls}")
        if object_count is not None:
            self._canvas.object_count = object_count
            self._lbl_objs.setText(f"Objects {object_count}")

    # ── Bidirectional Sync: Object ↔ Node ────────────────────────────────

    def _on_canvas_object_clicked(self, obj: dict) -> None:
        """Canvas → Inspector + Node highlight."""
        self.object_selected.emit(obj)
        node_id = obj.get("node_id", "")
        if node_id:
            self.node_selected_requested.emit(node_id)

    def select_node_by_id(self, node_id: str) -> None:
        """Nó selecionado no grafo → destacar objeto correspondente no canvas."""
        self._canvas.active_node_id = node_id
        for obj in self._canvas.game_objects:
            if obj.get("node_id", "") == node_id:
                self._canvas.selected_object_id = obj.get("id", "")
                break
        self._canvas.update()

    # ── Tick ──────────────────────────────────────────────────────────────

    def _on_tick(self) -> None:
        # BUG FIX: o early-return por isVisible() pulava a gravação do
        # replay_buffer inteiro, não só o repaint do canvas — um painel
        # oculto (ex.: aba trocada) perdia os últimos segundos do replay.
        # A visibilidade agora só afeta o self._canvas.update() no final.
        try:
            now = time.time()

            # Simulated FPS delta
            last_t = getattr(self._canvas, "last_frame_time", now)
            dt = max(0.001, now - last_t)
            self._canvas.last_frame_time = now
            self._canvas.frame_ms = dt * 1000.0
            measured_fps = min(240.0, 1.0 / dt)
            self.fps = measured_fps if self.fps <= 0 else (
                self.fps * 0.88 + measured_fps * 0.12
            )
            self._canvas.fps = self.fps
            self._canvas.push_fps(self.fps)
            self._lbl_fps.setText(f"FPS {self.fps:5.1f}")
            self._lbl_frame_ms.setText(f"Frame {self._canvas.frame_ms:.1f}ms")
            external_fps_label = getattr(self, "external_fps_label", None)
            if external_fps_label is not None:
                external_fps_label.setText(f"{self.fps:.0f} FPS")

            if self.viewport_mode == ViewportMode.GAME:
                start_t = getattr(self._canvas, "play_start_time", now)
                elapsed = max(0.0, now - start_t)
                m, s = int(elapsed) // 60, int(elapsed) % 60
                self._lbl_runtime.setText(f"Runtime {m:02d}:{s:02d}")

            if not self.is_replaying:
                snapshot = {
                    "timestamp":      now,
                    "node_id":        self.active_node_id,
                    "node_name":      self.active_node_name,
                    "highlight_until": self.highlight_timer,
                    "fps":            self.fps,
                    "objects":        list(self._canvas.game_objects),
                    "draw_calls":     self._canvas.draw_calls,
                    "object_count":   self._canvas.object_count,
                }
                self.replay_buffer.append(snapshot)
                if len(self.replay_buffer) > 120:
                    self.replay_buffer.pop(0)
                self.timeline_slider.setValue(len(self.replay_buffer))

            self._canvas.update()
        except Exception:
            pass

    # ── Replay ────────────────────────────────────────────────────────────

    def set_replay_frame(self, index: int) -> None:
        if 0 <= index < len(self.replay_buffer):
            self.is_replaying       = True
            self.replay_frame_index = index
            snap = self.replay_buffer[index]
            self._canvas.apply_snapshot(snap)
            self.active_node_id   = snap["node_id"]
            self.active_node_name = snap["node_name"] or ""
            self.mode_badge.setText(f"⏪  REPLAY  {index}/{len(self.replay_buffer)}")
            self.mode_badge.setStyleSheet(
                "color:#ae7df0;font-size:9px;font-weight:bold;letter-spacing:1px;"
            )

    def resume_live(self) -> None:
        self.is_replaying = False
        self.timeline_slider.setValue(len(self.replay_buffer))
        if self.viewport_mode != ViewportMode.GAME:
            self.set_viewport_mode(ViewportMode.GAME)


# ─────────────────────────────────────────────────────────────────────────────
#  Aliases de retrocompatibilidade
# ─────────────────────────────────────────────────────────────────────────────

MiniLiveViewportWidget = RuntimeVisualizationPanelWidget
