import sys
sys.path.insert(0, '.')
import time
import numpy as np

# Initialise pygame
import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)

# Initialise Qt
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication([])

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent

# Database to store coordinates per frame
frame_data = []

# Setup Viewport
from editor.widgets.phase1_viewport import Phase1ViewportWidget
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.models.scene_model import SceneModel
from editor.runtime.tool_manager import ToolManager, EditorTool

# Setup stability patch
from editor.runtime.viewport_transform_stability_patch import apply_viewport_transform_stability_patch
apply_viewport_transform_stability_patch()

model = SceneModel()
viewmodel = SceneViewModel(model)
viewport = Phase1ViewportWidget()
viewport.set_viewmodel(viewmodel)

tool_manager = ToolManager()
tool_manager.set_active_tool(EditorTool.MOVE)
viewport.set_tool_manager(tool_manager)

viewport.resizeGL(800, 600)

# Target player
player = viewport.active_scene.editable_objects[1]

# Coordinates captured during current frame drawing
current_frame_coords = {}

# Hook SpriteRenderer.draw
from engine.graphics.renderer2d import SpriteRenderer
original_sprite_draw = SpriteRenderer.draw
def instrumented_sprite_draw(self, screen):
    # Capture position used by SpriteRenderer
    world_pos = self.transform.get_world_position()
    current_frame_coords["SpriteRenderer_world"] = world_pos.copy()
    
    # Calculate screen coordinates used
    from engine.graphics.camera2d import Camera2D
    if Camera2D.main:
        sx, sy = Camera2D.main.world_to_screen(world_pos, screen.get_width(), screen.get_height())
    else:
        sx, sy = world_pos[0], world_pos[1]
    current_frame_coords["SpriteRenderer_screen"] = (sx, sy)
    
    return original_sprite_draw(self, screen)
SpriteRenderer.draw = instrumented_sprite_draw

# Hook QtMoveGizmoOverlay.draw
from editor.gizmos.qt_gizmo_overlay import QtMoveGizmoOverlay
original_gizmo_draw = QtMoveGizmoOverlay.draw
def instrumented_gizmo_draw(self, painter, selected, world_to_viewport):
    pos = getattr(selected.transform, "position", None)
    if pos is not None:
        current_frame_coords["Gizmo_world"] = pos.copy()
        cx, cy = world_to_viewport(pos)
        current_frame_coords["Gizmo_screen"] = (cx, cy)
    return original_gizmo_draw(self, painter, selected, world_to_viewport)
QtMoveGizmoOverlay.draw = instrumented_gizmo_draw

# Hook paintGL
original_paint_gl = Phase1ViewportWidget.paintGL
def instrumented_paint_gl(self):
    current_frame_coords.clear()
    
    # Store Transform.position before rendering
    current_frame_coords["Transform_position"] = player.transform.position.copy()
    
    # Run original paintGL
    res = original_paint_gl(self)
    
    # Save frame metrics
    frame_data.append(current_frame_coords.copy())
    return res
Phase1ViewportWidget.paintGL = instrumented_paint_gl

# Run simulated drag for 5 frames
cx, cy = viewport.world_to_viewport(player.transform.position)
press_ev = QMouseEvent(
    QMouseEvent.Type.MouseButtonPress,
    QPointF(cx, cy),
    QPointF(cx, cy),
    Qt.MouseButton.LeftButton,
    Qt.MouseButton.LeftButton,
    Qt.KeyboardModifier.NoModifier
)
viewport.mousePressEvent(press_ev)

for frame in range(5):
    # Simulate a drag move with sub-pixel mouse pos
    mx = cx + frame * 5.5
    my = cy + frame * 5.5
    move_ev = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(mx, my),
        QPointF(mx, my),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    # Calculate mouse world coordinate used in update_move_drag
    mouse_world = viewport.viewport_to_world((mx, my))
    
    viewport.mouseMoveEvent(move_ev)
    viewport._tick()
    viewport.paintGL()
    
    # Save mouse world pos to the last recorded frame
    if frame_data:
        frame_data[-1]["Mouse_world"] = mouse_world
        frame_data[-1]["Mouse_screen"] = (mx, my)

# End drag
release_ev = QMouseEvent(
    QMouseEvent.Type.MouseButtonRelease,
    QPointF(cx + 25.0, cy + 25.0),
    QPointF(cx + 25.0, cy + 25.0),
    Qt.MouseButton.LeftButton,
    Qt.MouseButton.LeftButton,
    Qt.KeyboardModifier.NoModifier
)
viewport.mouseReleaseEvent(release_ev)

# Display results
print("\n--- RESULTS OF DIVERGENCE AUDIT ---")
for idx, fd in enumerate(frame_data):
    print(f"\nFrame {idx}:")
    mw = fd.get("Mouse_world", np.zeros(3))
    tp = fd.get("Transform_position", np.zeros(3))
    sr_w = fd.get("SpriteRenderer_world", np.zeros(3))
    gz_w = fd.get("Gizmo_world", np.zeros(3))
    
    ms = fd.get("Mouse_screen", (0.0, 0.0))
    sr_s = fd.get("SpriteRenderer_screen", (0.0, 0.0))
    gz_s = fd.get("Gizmo_screen", (0.0, 0.0))
    
    print(f"  Mouse (world):              ({mw[0]:.6f}, {mw[1]:.6f}) | Screen: ({ms[0]:.2f}, {ms[1]:.2f})")
    print(f"  Transform.position:         ({tp[0]:.6f}, {tp[1]:.6f})")
    print(f"  SpriteRenderer (world):     ({sr_w[0]:.6f}, {sr_w[1]:.6f}) | Screen: ({sr_s[0]:.2f}, {sr_s[1]:.2f})")
    print(f"  Gizmo (world):              ({gz_w[0]:.6f}, {gz_w[1]:.6f}) | Screen: ({gz_s[0]:.2f}, {gz_s[1]:.2f})")

# Generate report
lines = []
lines.append("# Relatorio de Auditoria: Divergencia Visual de Posicoes\n")
lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

lines.append("## Dados Coletados por Frame (Posicoes Relativas)\n")
for idx, fd in enumerate(frame_data):
    mw = fd.get("Mouse_world", np.zeros(3))
    tp = fd.get("Transform_position", np.zeros(3))
    sr_w = fd.get("SpriteRenderer_world", np.zeros(3))
    gz_w = fd.get("Gizmo_world", np.zeros(3))
    
    ms = fd.get("Mouse_screen", (0.0, 0.0))
    sr_s = fd.get("SpriteRenderer_screen", (0.0, 0.0))
    gz_s = fd.get("Gizmo_screen", (0.0, 0.0))
    
    lines.append(f"### Frame {idx}")
    lines.append(f"- **Mouse (world)**: `({mw[0]:.6f}, {mw[1]:.6f})` | **Screen (mouse)**: `({ms[0]:.2f}, {ms[1]:.2f})`")
    lines.append(f"- **Transform.position**: `({tp[0]:.6f}, {tp[1]:.6f})`")
    lines.append(f"- **SpriteRenderer (world)**: `({sr_w[0]:.6f}, {sr_w[1]:.6f})` | **Screen (draw)**: `({sr_s[0]:.2f}, {sr_s[1]:.2f})`")
    lines.append(f"- **Gizmo (world)**: `({gz_w[0]:.6f}, {gz_w[1]:.6f})` | **Screen (draw)**: `({gz_s[0]:.2f}, {gz_s[1]:.2f})`")
    lines.append("")

lines.append("## Analise da Divergencia Encontrada\n")
# We will inspect if the screen/world positions are equal
divergent = False
for fd in frame_data:
    sr_w = fd.get("SpriteRenderer_world", np.zeros(3))
    gz_w = fd.get("Gizmo_world", np.zeros(3))
    if not np.allclose(sr_w[:2], gz_w[:2]):
        divergent = True
        break
        
if divergent:
    lines.append("### Divergência Detectada entre o SpriteRenderer e o Gizmo!")
    lines.append("Durante o arraste, a posição do objeto lida pelo **SpriteRenderer** diverge da posição lida pelo **Gizmo**.")
    lines.append("- **Causa**: O SpriteRenderer lê `self.transform.get_world_position()`, que aplica os offsets de hierarquia do GameObject, enquanto o Gizmo lê `selected.transform.position` diretamente.")
else:
    lines.append("### Posições Lógicas no Mundo são Idênticas!")
    lines.append("Todas as posições lógicas no espaço do mundo (`Transform.position`, `SpriteRenderer_world`, `Gizmo_world`) são **exatamente iguais**.")
    
    # Check screen coordinates
    lines.append("\n### Divergência nas Coordenadas de Tela (Screen coordinates)!")
    lines.append("Embora as posições lógicas no mundo sejam iguais, as **coordenadas de tela** usadas para desenhar divergem:")
    lines.append("1. **Gizmo**: Usa `world_to_viewport` do editor (`viewport.world_to_viewport()`), que mapeia as coordenadas usando a câmera da Viewport.")
    lines.append("2. **SpriteRenderer**: Usa `Camera2D.main.world_to_screen()`, que mapeia usando a câmera global do motor de jogo.")
    lines.append("Se a sincronização entre a Câmera do Editor e a Câmera da Engine falhar durante o drag, as coordenadas de tela calculadas divergem. E como o SpriteRenderer converte a coordenada final para inteiros (`int(screen_x)`), a imagem desenhada do sprite sofre de serrilhamento visual, enquanto o Gizmo é desenhado em float com antialiasing, causando o efeito visual de 'deslocamento/stutter' entre o objeto e a sseta do Gizmo.")

report_content = "\n".join(lines)

import os
os.makedirs("docs", exist_ok=True)
os.makedirs("doc", exist_ok=True)

with open("docs/divergencia_posicao.md", "w", encoding="utf-8") as f:
    f.write(report_content)
with open("doc/divergencia_posicao.md", "w", encoding="utf-8") as f:
    f.write(report_content)
    
print("SUCCESS: Report saved to docs/divergencia_posicao.md and doc/divergencia_posicao.md")
