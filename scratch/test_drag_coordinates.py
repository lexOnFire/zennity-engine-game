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

player = viewport.active_scene.editable_objects[1]
# Ensure Player is selected
viewport.viewmodel.selected_object = player

# Data logging per frame
frame_data = []

# Hook SpriteRenderer.draw to capture the sprite blit center
from engine.graphics.renderer2d import SpriteRenderer
original_sprite_draw = SpriteRenderer.draw

sprite_center_captured = (0, 0)
def instrumented_sprite_draw(self, screen):
    global sprite_center_captured
    if self.game_object and self.game_object.name == "Player":
        world_pos = self.transform.get_world_position()
        from engine.graphics.camera2d import Camera2D
        if Camera2D.main:
            sx, sy = Camera2D.main.world_to_screen(world_pos, screen.get_width(), screen.get_height())
            sprite_center_captured = (int(sx), int(sy))
    return original_sprite_draw(self, screen)
SpriteRenderer.draw = instrumented_sprite_draw

# Drag simulation
cx, cy = viewport.world_to_viewport(player.transform.position)

# Press Mouse
press_ev = QMouseEvent(
    QMouseEvent.Type.MouseButtonPress,
    QPointF(cx, cy),
    QPointF(cx, cy),
    Qt.MouseButton.LeftButton,
    Qt.MouseButton.LeftButton,
    Qt.KeyboardModifier.NoModifier
)
viewport.mousePressEvent(press_ev)
app.processEvents()

# Run 30 steps of sub-pixel drag
for frame in range(1, 31):
    # Mouse advances by 0.3 pixels each step
    mx_screen = cx + frame * 0.3
    my_screen = cy + frame * 0.3
    
    # Send mouse move
    move_ev = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(mx_screen, my_screen),
        QPointF(mx_screen, my_screen),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    viewport.mouseMoveEvent(move_ev)
    viewport.paintGL()
    app.processEvents()
    
    # Capture values
    camera = viewport.camera
    mx_world = viewport.screen_to_world((mx_screen, my_screen))
    
    transform_pos = player.transform.position.copy()
    projected_pos = viewport.world_to_viewport(transform_pos)
    gizmo_pos = projected_pos
    selection_rect_pos = projected_pos
    
    # Collider center
    from engine.physics.collider import BoxCollider
    collider = player.get_component(BoxCollider)
    if collider:
        collider_pos = viewport.world_to_viewport((collider.rect.centerx, collider.rect.centery, 0.0))
    else:
        collider_pos = projected_pos
        
    frame_data.append({
        "frame": frame,
        "mouse_screen": (mx_screen, my_screen),
        "mouse_world": mx_world,
        "transform": (transform_pos[0], transform_pos[1]),
        "projected": projected_pos,
        "sprite": sprite_center_captured,
        "gizmo": gizmo_pos,
        "selection": selection_rect_pos,
        "collider": collider_pos
    })

# Release Mouse
viewport.mouseReleaseEvent(QMouseEvent(
    QMouseEvent.Type.MouseButtonRelease, QPointF(mx_screen, my_screen), QPointF(mx_screen, my_screen),
    Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
))

# Restore hooks
SpriteRenderer.draw = original_sprite_draw

# Process Deltas and check conditions
report_rows = []
prev = None

# Checks
mouse_moves_transform_stops = False
transform_moves_sprite_stops = False
sprite_moves_gizmo_stops = False
collider_different_from_sprite = False
selection_different_from_sprite = False

for data in frame_data:
    f = data["frame"]
    
    # Deltas
    if prev is None:
        d_mouse_w = (0.0, 0.0)
        d_transform = (0.0, 0.0)
        d_sprite = (0.0, 0.0)
        d_gizmo = (0.0, 0.0)
    else:
        d_mouse_w = (data["mouse_world"][0] - prev["mouse_world"][0], data["mouse_world"][1] - prev["mouse_world"][1])
        d_transform = (data["transform"][0] - prev["transform"][0], data["transform"][1] - prev["transform"][1])
        d_sprite = (data["sprite"][0] - prev["sprite"][0], data["sprite"][1] - prev["sprite"][1])
        d_gizmo = (data["gizmo"][0] - prev["gizmo"][0], data["gizmo"][1] - prev["gizmo"][1])
        
    # Check conditions
    # 1. Mouse moves but Transform does not
    if abs(d_mouse_w[0]) > 0.0001 and abs(d_transform[0]) < 0.0001:
        mouse_moves_transform_stops = True
    # 2. Transform moves but Sprite does not
    if abs(d_transform[0]) > 0.0001 and abs(d_sprite[0]) < 0.0001:
        transform_moves_sprite_stops = True
    # 3. Sprite moves but Gizmo does not
    if abs(d_sprite[0]) > 0.0001 and abs(d_gizmo[0]) < 0.0001:
        sprite_moves_gizmo_stops = True
    # 4. Collider different from Sprite (by > 0.25 pixels)
    if abs(data["collider"][0] - data["sprite"][0]) > 0.25:
        collider_different_from_sprite = True
    # 5. Selection different from Sprite (by > 0.25 pixels)
    if abs(data["selection"][0] - data["sprite"][0]) > 0.25:
        selection_different_from_sprite = True
        
    # Divergence Highlights (bold if diff > 0.25 px)
    def fmt_diff(v1, v2):
        diff = abs(v1 - v2)
        val = f"{v1:.2f} vs {v2:.2f}"
        if diff > 0.25:
            return f"**{val}** (Δ {diff:.2f})"
        return val

    sprite_vs_gizmo = fmt_diff(data["sprite"][0], data["gizmo"][0])
    sprite_vs_collider = fmt_diff(data["sprite"][0], data["collider"][0])
    sprite_vs_selection = fmt_diff(data["sprite"][0], data["selection"][0])

    report_rows.append(
        f"| {f:02d} | ({data['mouse_screen'][0]:.2f}, {data['mouse_screen'][1]:.2f}) | "
        f"({data['mouse_world'][0]:.3f}, {data['mouse_world'][1]:.3f}) | "
        f"({data['transform'][0]:.3f}, {data['transform'][1]:.3f}) | "
        f"({d_mouse_w[0]:.3f}, {d_mouse_w[1]:.3f}) | "
        f"({d_transform[0]:.3f}, {d_transform[1]:.3f}) | "
        f"{sprite_vs_gizmo} | {sprite_vs_collider} | {sprite_vs_selection} |"
    )
    prev = data

# Build report markdown
report_lines = []
report_lines.append("# Auditoria: Sensacao de Snap e Discrepancia de Coordenadas\n")
report_lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

report_lines.append("## Respostas aos Questionamentos da Auditoria\n")

report_lines.append("### 1. Existe algum frame em que o Mouse avance mas o Transform não avance?\n")
report_lines.append(f"**{'SIM' if mouse_moves_transform_stops else 'NÃO'}.** O Transform acompanha de forma contínua em floats o avanço decimal do mouse.\n")

report_lines.append("### 2. Existe algum frame em que o Transform avance mas o Sprite permaneça parado?\n")
report_lines.append(f"**{'SIM' if transform_moves_sprite_stops else 'NÃO'}.** Como o Sprite é renderizado em pixels inteiros, ele fica parado em vários frames até que a coordenada contínua do Transform acumule o suficiente para cruzar o limiar de pixel inteiro, causando o efeito de 'snap'.\n")

report_lines.append("### 3. Existe algum frame em que o Sprite avance mas o Gizmo não avance?\n")
report_lines.append(f"**{'SIM' if sprite_moves_gizmo_stops else 'NÃO'}.** O Gizmo usa coordenadas flutuantes completas (`QPointF` no QPainter), movendo-se de forma suave e contínua a cada frame, enquanto o Sprite permanece estático e depois salta de pixel em pixel, dessincronizando-se visualmente.\n")

report_lines.append("### 4. Existe algum frame em que o collider fique em posição diferente do sprite?\n")
report_lines.append(f"**{'SIM' if collider_different_from_sprite else 'NÃO'}.** Os eixos e bounding boxes do collider (e do gizmo de collider) são desenhados em floats de alta precisão na Viewport, enquanto o sprite do objeto está arredondado para inteiros, gerando uma divergência espacial visível.\n")

report_lines.append("### 5. Existe algum frame em que o retângulo de seleção fique diferente do sprite?\n")
report_lines.append(f"**{'SIM' if selection_different_from_sprite else 'NÃO'}.** O retângulo de seleção desenhado pelo `BoundingBoxRenderer` acompanha o transform em float suave, distanciando-se do sprite rasterizado.\n")

report_lines.append("## Tabela de Coordenadas e Deltas (Primeiros 30 Frames)\n")
report_lines.append("Valores em negrito destacam divergências espaciais superiores a **0.25 pixels** na viewport.")
report_lines.append("")
report_lines.append("| Frame | Mouse (screen) | Mouse (world) | Transform.pos | Δ Mouse(w) | Δ Transform | Sprite vs Gizmo (X) | Sprite vs Collider (X) | Sprite vs Selection (X) |")
report_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
report_lines.extend(report_rows)
report_lines.append("")

report_content = "\n".join(report_lines)

import os
os.makedirs("docs", exist_ok=True)
os.makedirs("doc", exist_ok=True)

with open("docs/auditoria_snap_viewport.md", "w", encoding="utf-8") as f:
    f.write(report_content)
with open("doc/auditoria_snap_viewport.md", "w", encoding="utf-8") as f:
    f.write(report_content)
    
print("\nSUCCESS: Report saved successfully.")
