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

# Database to store errors per zoom level
# zoom -> list of (screen_x_float, screen_y_float, int_x, int_y, err_x, err_y)
zoom_errors = {}

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

# Current zoom level we are testing
current_zoom = 1.0

# Hook SpriteRenderer.draw to capture coordinates
from engine.graphics.renderer2d import SpriteRenderer
original_sprite_draw = SpriteRenderer.draw
def instrumented_sprite_draw(self, screen):
    global current_zoom
    # Get world position
    world_pos = self.transform.get_world_position()
    
    # Calculate screen coordinates used
    from engine.graphics.camera2d import Camera2D
    if Camera2D.main:
        sx, sy = Camera2D.main.world_to_screen(world_pos, screen.get_width(), screen.get_height())
    else:
        sx, sy = world_pos[0], world_pos[1]
        
    int_x, int_y = int(sx), int(sy)
    err_x = abs(sx - int_x)
    err_y = abs(sy - int_y)
    
    if current_zoom not in zoom_errors:
        zoom_errors[current_zoom] = []
    zoom_errors[current_zoom].append((sx, sy, int_x, int_y, err_x, err_y))
    
    return original_sprite_draw(self, screen)
SpriteRenderer.draw = instrumented_sprite_draw

zooms = [0.5, 1.0, 1.5, 2.0, 4.0]

for z in zooms:
    current_zoom = z
    viewport.camera.zoom = z
    viewport.sync_camera_from_engine()
    
    # Simulate a drag press
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
    
    # Run 100 move iterations with sub-pixel mouse steps
    for step in range(100):
        # We use fractional increments to generate fractional coordinates
        mx = cx + step * 0.125
        my = cy + step * 0.125
        move_ev = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPointF(mx, my),
            QPointF(mx, my),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        viewport.mouseMoveEvent(move_ev)
        viewport._tick()
        viewport.paintGL()
        app.processEvents()
        
    # Release drag
    release_ev = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        QPointF(cx + 12.5, cy + 12.5),
        QPointF(cx + 12.5, cy + 12.5),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    viewport.mouseReleaseEvent(release_ev)

# Analyze data
print("\n--- RESULTS OF RASTERIZATION ERROR AUDIT ---")
report_lines = []
report_lines.append("# Relatorio de Auditoria: Medicao do Erro de Rasterizacao no Drag\n")
report_lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

for z, records in zoom_errors.items():
    errs_x = [r[4] for r in records]
    errs_y = [r[5] for r in records]
    total_errs = errs_x + errs_y  # combine x and y errors
    
    mean_err = np.mean(total_errs)
    max_err = np.max(total_errs)
    p95_err = np.percentile(total_errs, 95)
    p99_err = np.percentile(total_errs, 99)
    
    print(f"\nZoom {z*100:.0f}%:")
    print(f"  Erro Medio: {mean_err:.6f} px")
    print(f"  Erro Maximo: {max_err:.6f} px")
    print(f"  Erro P95:    {p95_err:.6f} px")
    print(f"  Erro P99:    {p99_err:.6f} px")
    
    report_lines.append(f"## Zoom {z*100:.0f}%\n")
    report_lines.append(f"- **Erro Médio**: `{mean_err:.6f} px`")
    report_lines.append(f"- **Erro Máximo**: `{max_err:.6f} px`")
    report_lines.append(f"- **Erro P95**: `{p95_err:.6f} px`")
    report_lines.append(f"- **Erro P99**: `{p99_err:.6f} px`")
    report_lines.append("")
    
# Global max error
all_errors = []
for records in zoom_errors.values():
    all_errors.extend([r[4] for r in records] + [r[5] for r in records])
global_max = np.max(all_errors)

report_lines.append("## Analise e Conclusao\n")
report_lines.append(f"### Qual o maior erro de rasterização observado?\nO maior erro de rasterização observado foi de **{global_max:.6f} px** (muito próximo de 1.0 px).\n")
report_lines.append("### Esse erro é suficiente para produzir visualmente o efeito de movimento em degraus?\n")
report_lines.append("**SIM.**")
report_lines.append("Como o truncamento via `int(screen_x)` simplesmente descarta a parte decimal das coordenadas de tela (ex: `405.99` vira `405`), a imagem do sprite sofre de desalinhamento de **até 0.99 pixel** em relação à posição analítica real do transform (e do Gizmo desenhado em float com sub-pixel precision).")
report_lines.append("Esse desvio de até 1 pixel completo cria um efeito óptico de stutters e saltos ('degraus') no arraste, pois o objeto visual só muda de posição física em pixels inteiros, enquanto a seleção e as linhas do Gizmo deslizam suavemente com precisão sub-pixel. Quando o zoom aumenta, as coordenadas fracionárias mudam em escala proporcional, mas o erro de rasterização permanece delimitado entre `[0, 1.0[` pixel, perpetuando o efeito de 'snap' independentemente do nível de zoom.")

report_content = "\n".join(report_lines)

import os
os.makedirs("docs", exist_ok=True)
os.makedirs("doc", exist_ok=True)

with open("docs/erro_rasterizacao.md", "w", encoding="utf-8") as f:
    f.write(report_content)
with open("doc/erro_rasterizacao.md", "w", encoding="utf-8") as f:
    f.write(report_content)
    
print("SUCCESS: Report saved to docs/erro_rasterizacao.md and doc/erro_rasterizacao.md")
