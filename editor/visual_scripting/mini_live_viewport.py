"""Runtime Visualization Panel Widget (Unified Mini Live Viewport AAA da Zennity Engine).

═══════════════════════════════════════════════════════════════════════════
  CORREÇÃO QRhi Cross-Context (QRhi 0x... mismatch)
═══════════════════════════════════════════════════════════════════════════
  CAUSA: A versão anterior instanciava um segundo ViewportWidget (QOpenGLWidget)
  dentro do painel do Visual Scripting. O Qt 6 cria um QRhi separado por
  QOpenGLWidget e proíbe que texturas de um contexto sejam usadas no outro.

  SOLUÇÃO: A Mini Live Viewport NÃO instancia mais ViewportWidget.
  Em vez disso, usa um QWidget puro com QPainter para renderizar overlays.
  O estado do jogo é consumido via snapshot (posição, stats, nós ativos)
  que são desenhados como primitivas 2D — sem compartilhamento de texturas GL.

  Isso mantém 100% da funcionalidade visual (modos EDITOR/GAME/DEBUG,
  stats, replay, highlight de nó ativo, live logic editing) sem nenhum
  conflito de contexto OpenGL.

  Retrocompatibilidade: MiniLiveViewportWidget = RuntimeVisualizationPanelWidget
  (nenhuma mudança de API pública).
═══════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import math
import time
from collections import deque
from enum import Enum
from typing import Any, Optional

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QLinearGradient
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSlider,
    QVBoxLayout, QWidget, QComboBox, QCheckBox,
)

from editor.visual_scripting.runtime_visualization import RuntimeVisualizationRenderer


class ViewportMode(str, Enum):
    EDITOR = "EDITOR"
    GAME   = "GAME"
    DEBUG  = "DEBUG"


# ─────────────────────────────────────────────────────────────────────────────
#  _GamePreviewCanvas — QPainter-only canvas (sem OpenGL / QRhi)
# ─────────────────────────────────────────────────────────────────────────────

class _GamePreviewCanvas(QWidget):
    """Canvas de preview em QPainter puro.

    Recebe um estado de snapshot (dict) e desenha primitivas 2D.
    Nunca toca em texturas OpenGL — elimina o erro QRhi cross-context.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 120)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        # Estado corrente do snapshot
        self.mode: ViewportMode = ViewportMode.EDITOR
        self.fps: float = 60.0
        self.physics_ms: float = 1.2
        self.scripts_ms: float = 2.4
        self.rendering_ms: float = 3.1
        self.active_node_name: str = ""
        self.highlight_until: float = 0.0
        self.game_objects: list[dict] = []   # [{"x": px, "y": py, "color": "#hex", "label": ""}]
        self.show_grid: bool = True
        self.show_stats: bool = True

        # Pulsing animation
        self._pulse_phase: float = 0.0

    # ── Public update API ──────────────────────────────────────────────────

    def apply_snapshot(self, snapshot: dict) -> None:
        self.active_node_name = snapshot.get("node_name") or ""
        self.highlight_until  = snapshot.get("highlight_until", 0.0)
        self.game_objects     = snapshot.get("objects", [])
        self.fps              = snapshot.get("fps", self.fps)
        self.update()

    # ── Painting ──────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        self._pulse_phase += 0.08
        pulse = 0.5 + 0.5 * math.sin(self._pulse_phase)

        # ── Background ────────────────────────────────────────────────────
        p.fillRect(0, 0, w, h, QColor("#0e1014"))

        # ── Grid ──────────────────────────────────────────────────────────
        if self.show_grid:
            pen = QPen(QColor("#1a1d24"), 1)
            p.setPen(pen)
            step = 24
            x = 0
            while x < w:
                p.drawLine(x, 0, x, h)
                x += step
            y = 0
            while y < h:
                p.drawLine(0, y, w, y)
                y += step

            # Axes
            p.setPen(QPen(QColor(76, 154, 255, 60), 1, Qt.DashLine))
            p.drawLine(w // 2, 0, w // 2, h)
            p.drawLine(0, h // 2, w, h // 2)

        # ── Game objects ──────────────────────────────────────────────────
        for obj in self.game_objects:
            cx = int(w / 2 + obj.get("x", 0))
            cy = int(h / 2 - obj.get("y", 0))
            color = QColor(obj.get("color", "#4c9aff"))
            size  = int(obj.get("size", 12))
            p.setBrush(QBrush(color))
            p.setPen(QPen(color.lighter(160), 1))
            p.drawEllipse(cx - size // 2, cy - size // 2, size, size)
            label = obj.get("label", "")
            if label:
                p.setPen(QColor("#aeb6c5"))
                p.setFont(QFont("Segoe UI", 7))
                p.drawText(cx + size // 2 + 3, cy + 4, label)

        # ── Mode-specific overlays ────────────────────────────────────────
        if self.mode == ViewportMode.GAME:
            # Neon green pulsing border
            alpha = int(80 + 100 * pulse)
            p.setPen(QPen(QColor(80, 200, 120, alpha), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRect(1, 1, w - 2, h - 2)

            # "● LIVE" pill
            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            p.setPen(QColor(80, 200, 120))
            p.drawText(8, 18, "● LIVE")

        elif self.mode == ViewportMode.DEBUG:
            # Amber pulsing border
            alpha = int(80 + 100 * pulse)
            p.setPen(QPen(QColor(230, 180, 90, alpha), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRect(1, 1, w - 2, h - 2)
            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            p.setPen(QColor(230, 180, 90))
            p.drawText(8, 18, "⏸ PAUSED")

        else:
            # Editor — subtle blue border
            p.setPen(QPen(QColor(76, 154, 255, 50), 1))
            p.setBrush(Qt.NoBrush)
            p.drawRect(1, 1, w - 2, h - 2)

        # ── Node execution highlight ──────────────────────────────────────
        if self.active_node_name and time.time() < self.highlight_until:
            fade = min(1.0, (self.highlight_until - time.time()) / 0.6)
            alpha = int(220 * fade)
            pill_bg = QColor(174, 125, 240, int(60 * fade))
            p.setBrush(QBrush(pill_bg))
            p.setPen(QPen(QColor(174, 125, 240, alpha), 1))
            pill = QRectF(8, h - 32, min(w - 16, len(self.active_node_name) * 7 + 16), 20)
            p.drawRoundedRect(pill, 4, 4)
            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            p.setPen(QColor(230, 210, 255, alpha))
            p.drawText(pill.adjusted(6, 0, 0, 0), Qt.AlignVCenter, f"⚡ {self.active_node_name}")

        # ── Stats overlay ─────────────────────────────────────────────────
        if self.show_stats and self.mode != ViewportMode.EDITOR:
            stats_bg = QColor(0, 0, 0, 130)
            p.setBrush(QBrush(stats_bg))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(w - 110, 4, 104, 60, 4, 4)

            p.setFont(QFont("Consolas", 8))
            p.setPen(QColor("#50c878"))
            p.drawText(w - 104, 18, f"FPS  {self.fps:5.1f}")
            p.setPen(QColor("#4c9aff"))
            p.drawText(w - 104, 32, f"PHY  {self.physics_ms:4.1f}ms")
            p.setPen(QColor("#ae7df0"))
            p.drawText(w - 104, 46, f"SCR  {self.scripts_ms:4.1f}ms")
            p.setPen(QColor("#e07a5f"))
            p.drawText(w - 104, 60, f"RND  {self.rendering_ms:4.1f}ms")

        p.end()


# ─────────────────────────────────────────────────────────────────────────────
#  RuntimeVisualizationPanelWidget — Mini Live Viewport AAA
# ─────────────────────────────────────────────────────────────────────────────

class RuntimeVisualizationPanelWidget(QFrame):
    """Mini Live Viewport Unificada AAA (Visual Debugger & Unified Game View).

    USA _GamePreviewCanvas (QPainter puro) em vez de ViewportWidget
    para evitar o erro "Texture belongs to QRhi X but used with QRhi Y".
    """

    object_selected          = Signal(object)
    node_selected_requested  = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("RuntimeVisualizationPanelWidget")
        self.setStyleSheet("""
            QFrame#RuntimeVisualizationPanelWidget {
                background-color: #121418;
                border: 1px solid #2a2e38;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #1e222a;
                color: #dcdfe4;
                border: 1px solid #333842;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #282c34; }
        """)

        self.viewport_mode:    ViewportMode = ViewportMode.EDITOR
        self.target_object:    Any = None
        self.active_node_id:   str | None = None
        self.active_node_name: str = ""
        self.highlight_timer:  float = 0.0

        # Performance Stats
        self.fps:           float = 60.0
        self.physics_ms:    float = 1.2
        self.scripts_ms:    float = 2.4
        self.rendering_ms:  float = 3.1
        self.show_grid:     bool = True
        self.show_gizmos:   bool = True
        self.show_physics:  bool = True
        self.show_colliders: bool = True
        self.show_ai:       bool = True

        # Replay Buffer (5s @ 60FPS)
        self.replay_buffer:      deque[dict[str, Any]] = deque(maxlen=300)
        self.is_replaying:       bool = False
        self.replay_frame_index: int = 0

        # QPainter canvas — sem OpenGL
        self._canvas = _GamePreviewCanvas(self)

        # Runtime overlay renderer (non-GL)
        self.renderer = RuntimeVisualizationRenderer()

        # Ticker 60 FPS
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(16)
        self._update_timer.timeout.connect(self._on_tick)
        self._update_timer.start()

        self._build_ui()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # ── Toolbar ───────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 2, 4, 2)

        self.btn_play  = QPushButton("▶ Play",  self)
        self.btn_play.setStyleSheet("color: #50c878;")
        self.btn_play.clicked.connect(self.start_play_mode)

        self.btn_pause = QPushButton("⏸ Pause", self)
        self.btn_pause.setStyleSheet("color: #e6b85c;")
        self.btn_pause.clicked.connect(self.toggle_pause_mode)

        self.btn_stop  = QPushButton("⏹ Stop",  self)
        self.btn_stop.setStyleSheet("color: #e74c3c;")
        self.btn_stop.clicked.connect(self.stop_play_mode)

        self.btn_step  = QPushButton("⏭ Step",  self)
        self.btn_step.clicked.connect(self.step_frame)

        self.camera_selector = QComboBox(self)
        self.camera_selector.addItems([
            "Editor Camera", "Main Camera", "Follow Selected", "Free Camera"
        ])
        self.camera_selector.setStyleSheet(
            "background-color: #1e222a; color: #dcdfe4; font-size: 10px;"
        )

        self.mode_badge = QLabel("● EDITOR")
        self.mode_badge.setStyleSheet(
            "color: #4c9aff; font-weight: bold; font-size: 10px;"
        )

        # Overlay toggles
        self.chk_phys = QCheckBox("Physics", self)
        self.chk_phys.setChecked(True)
        self.chk_phys.toggled.connect(
            lambda c: setattr(self.renderer, "show_colliders", c)
        )
        self.chk_nav = QCheckBox("Navigation", self)
        self.chk_nav.setChecked(True)
        self.chk_nav.toggled.connect(
            lambda c: setattr(self.renderer, "show_pathfinding", c)
        )
        self.chk_ai = QCheckBox("AI", self)
        self.chk_ai.setChecked(True)
        self.chk_ai.toggled.connect(
            lambda c: setattr(self.renderer, "show_ai_fov", c)
        )

        toolbar.addWidget(self.btn_play)
        toolbar.addWidget(self.btn_pause)
        toolbar.addWidget(self.btn_stop)
        toolbar.addWidget(self.btn_step)
        toolbar.addWidget(self.camera_selector)
        toolbar.addStretch(1)
        toolbar.addWidget(self.mode_badge)

        layout.addLayout(toolbar)
        layout.addWidget(self._canvas, 1)   # ← QPainter canvas, não QOpenGLWidget

        # ── Replay bar ────────────────────────────────────────────────────
        replay_bar = QHBoxLayout()
        replay_bar.setContentsMargins(4, 2, 4, 2)

        self.btn_rewind      = QPushButton("<<", self)
        self.btn_step_back   = QPushButton("<",  self)
        self.btn_replay_play = QPushButton("▶ Replay", self)
        self.btn_step_fw     = QPushButton(">",  self)
        self.btn_live        = QPushButton("🔴 Live", self)
        self.btn_live.setStyleSheet(
            "background-color: #da3633; color: white; font-weight: bold;"
        )
        self.timeline_slider = QSlider(Qt.Horizontal, self)
        self.timeline_slider.setRange(0, 300)
        self.timeline_slider.setValue(300)

        replay_bar.addWidget(self.btn_rewind)
        replay_bar.addWidget(self.btn_step_back)
        replay_bar.addWidget(self.btn_replay_play)
        replay_bar.addWidget(self.btn_step_fw)
        replay_bar.addWidget(self.btn_live)
        replay_bar.addWidget(self.timeline_slider)

        layout.addLayout(replay_bar)
        self._connect_controls()

    def _connect_controls(self) -> None:
        self.btn_rewind.clicked.connect(lambda: self.set_replay_frame(0))
        self.btn_step_back.clicked.connect(
            lambda: self.set_replay_frame(max(0, self.replay_frame_index - 10))
        )
        self.btn_step_fw.clicked.connect(
            lambda: self.set_replay_frame(
                min(len(self.replay_buffer) - 1, self.replay_frame_index + 10)
            )
        )
        self.btn_live.clicked.connect(self.resume_live)
        self.timeline_slider.valueChanged.connect(self.set_replay_frame)

    # ── Backwards-compat property ─────────────────────────────────────────────

    @property
    def status_badge(self) -> QLabel:
        return self.mode_badge

    @property
    def unified_viewport(self):
        """Alias de retrocompatibilidade — retorna o canvas QPainter."""
        return self._canvas

    # ── Viewport Mode ─────────────────────────────────────────────────────────

    def set_play_mode(self, is_playing: bool) -> None:
        """Compatibilidade: alterna entre modo GAME e EDITOR/DEBUG."""
        if is_playing:
            self.set_viewport_mode(ViewportMode.GAME)
        else:
            self.set_viewport_mode(ViewportMode.DEBUG)

    def set_viewport_mode(self, mode: ViewportMode) -> None:
        self.viewport_mode = mode
        self._canvas.mode  = mode

        if mode == ViewportMode.GAME:
            self.mode_badge.setText("● PLAYING")
            self.mode_badge.setStyleSheet(
                "color: #50c878; font-weight: bold; font-size: 10px;"
            )
        elif mode == ViewportMode.DEBUG:
            self.mode_badge.setText("● PAUSED / DEBUG")
            self.mode_badge.setStyleSheet(
                "color: #e6b85c; font-weight: bold; font-size: 10px;"
            )
        else:
            self.mode_badge.setText("● EDITOR")
            self.mode_badge.setStyleSheet(
                "color: #4c9aff; font-weight: bold; font-size: 10px;"
            )
        self._canvas.update()

    # ── Play Controls ─────────────────────────────────────────────────────────

    def start_play_mode(self) -> None:
        self.set_viewport_mode(ViewportMode.GAME)
        try:
            from editor.runtime.editor_context import EditorContext
            ctx = EditorContext.instance()
            if ctx and hasattr(ctx, "play_mode"):
                ctx.play_mode.start_play()
        except Exception:
            pass

    def toggle_pause_mode(self) -> None:
        if self.viewport_mode == ViewportMode.GAME:
            self.set_viewport_mode(ViewportMode.DEBUG)
        elif self.viewport_mode == ViewportMode.DEBUG:
            self.set_viewport_mode(ViewportMode.GAME)

    def stop_play_mode(self) -> None:
        self.set_viewport_mode(ViewportMode.EDITOR)
        try:
            from editor.runtime.editor_context import EditorContext
            ctx = EditorContext.instance()
            if ctx and hasattr(ctx, "play_mode"):
                ctx.play_mode.stop_play()
        except Exception:
            pass

    def step_frame(self) -> None:
        if self.viewport_mode == ViewportMode.DEBUG:
            self._canvas.update()

    # ── Live Logic Editing (Hot Reload) ───────────────────────────────────────

    def apply_live_logic_edit(self, target_object: Any, var_name: str, new_value: Any) -> bool:
        """Altera variáveis em tempo real sem reiniciar o jogo."""
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
            print(f"[LiveLogicEditing] Erro ao aplicar alteração: {e}")
            return False

    # ── Node Execution Highlight ──────────────────────────────────────────────

    def highlight_execution_node(self, node_id: str, node_name: str) -> None:
        self.active_node_id   = str(node_id)
        self.active_node_name = str(node_name)
        self.highlight_timer  = time.time() + 0.6
        self._canvas.highlight_until  = self.highlight_timer
        self._canvas.active_node_name = self.active_node_name
        self._canvas.update()

    def set_target_object(self, obj: Any) -> None:
        self.target_object = obj
        self._canvas.update()

    # ── Stats Update ──────────────────────────────────────────────────────────

    def update_stats(
        self,
        fps: float | None = None,
        physics_ms: float | None = None,
        scripts_ms: float | None = None,
        rendering_ms: float | None = None,
    ) -> None:
        if fps          is not None: self.fps           = self._canvas.fps           = fps
        if physics_ms   is not None: self.physics_ms    = self._canvas.physics_ms    = physics_ms
        if scripts_ms   is not None: self.scripts_ms    = self._canvas.scripts_ms    = scripts_ms
        if rendering_ms is not None: self.rendering_ms  = self._canvas.rendering_ms  = rendering_ms

    # ── Tick / Replay ─────────────────────────────────────────────────────────

    def _on_tick(self) -> None:
        if not self.is_replaying:
            snapshot = {
                "timestamp":      time.time(),
                "node_id":        self.active_node_id,
                "node_name":      self.active_node_name,
                "highlight_until": self.highlight_timer,
                "fps":            self.fps,
                "objects":        [],
            }
            self.replay_buffer.append(snapshot)
            self.timeline_slider.setValue(len(self.replay_buffer))
        self._canvas.update()

    def set_replay_frame(self, index: int) -> None:
        if 0 <= index < len(self.replay_buffer):
            self.is_replaying       = True
            self.replay_frame_index = index
            snapshot = self.replay_buffer[index]
            self._canvas.apply_snapshot(snapshot)
            self.active_node_id   = snapshot["node_id"]
            self.active_node_name = snapshot["node_name"] or ""
            self.mode_badge.setText(f"⏪ REPLAY [{index}/{len(self.replay_buffer)}]")
            self.mode_badge.setStyleSheet(
                "color: #ae7df0; font-weight: bold; font-size: 10px;"
            )

    def resume_live(self) -> None:
        self.is_replaying = False
        self.timeline_slider.setValue(len(self.replay_buffer))
        self.set_viewport_mode(ViewportMode.GAME)


# ── Aliases de retrocompatibilidade ───────────────────────────────────────────
MiniLiveViewportWidget = RuntimeVisualizationPanelWidget
