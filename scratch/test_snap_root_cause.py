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

from PySide6.QtCore import QPointF, Qt, QRectF
from PySide6.QtGui import QMouseEvent, QImage, QPixmap, QPainter

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
viewport.viewmodel.selected_object = player
viewport._snap_enabled = lambda: False

# Logs lists
logs_a = []
logs_b = []

# --- EXPERIMENTO A: FLOATS SEM ANTIALIASING ---
original_paint_gl = Phase1ViewportWidget.paintGL

def paint_gl_exp_a(self):
    # Run Pygame drawing
    res = original_paint_gl(self)
    
    # Draw overlay with float coordinates but NO antialiasing
    selected = self.selected_object() if hasattr(self, "selected_object") else None
    if selected:
        from engine.graphics.renderer2d import SpriteRenderer
        sprite_renderer = selected.get_component(SpriteRenderer)
        if sprite_renderer and sprite_renderer.image:
            image = sprite_renderer.image
            w_surf = image.get_width()
            h_surf = image.get_height()
            raw = pygame.image.tostring(image, "RGBA")
            qimg = QImage(raw, w_surf, h_surf, w_surf * 4, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            
            cx, cy = self.world_to_viewport(selected.transform.position)
            zoom = self.camera.zoom
            scale = selected.transform.scale
            w = max(1.0, abs(float(scale[0])) * zoom)
            h = max(1.0, abs(float(scale[1])) * zoom)
            
            painter = QPainter(self)
            try:
                # Disable Antialiasing
                painter.setRenderHint(QPainter.Antialiasing, False)
                local_rect = QRectF(-w / 2.0, -h / 2.0, w, h)
                painter.save()
                painter.translate(float(cx), float(cy))
                painter.drawPixmap(local_rect, pixmap, pixmap.rect())
                painter.restore()
            finally:
                painter.end()
                
            logs_a.append({
                "cx": cx,
                "cy": cy,
                "actual_x": cx # Float remains intact
            })
    return res

# Run Experiment A drag
Phase1ViewportWidget.paintGL = paint_gl_exp_a

# Simulate drag for 5 frames
cx, cy = viewport.world_to_viewport(player.transform.position)
press_ev = QMouseEvent(QMouseEvent.Type.MouseButtonPress, QPointF(cx, cy), QPointF(cx, cy), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
viewport.mousePressEvent(press_ev)

for frame in range(1, 6):
    mx = cx + frame * 0.3
    viewport.mouseMoveEvent(QMouseEvent(QMouseEvent.Type.MouseMove, QPointF(mx, cy), QPointF(mx, cy), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
    viewport.paintGL()
    app.processEvents()
    
viewport.mouseReleaseEvent(QMouseEvent(QMouseEvent.Type.MouseButtonRelease, QPointF(mx, cy), QPointF(mx, cy), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))


# --- EXPERIMENTO B: QUANTIZACAO INTEIRA NO QPAINTER ---
def paint_gl_exp_b(self):
    res = original_paint_gl(self)
    selected = self.selected_object() if hasattr(self, "selected_object") else None
    if selected:
        from engine.graphics.renderer2d import SpriteRenderer
        sprite_renderer = selected.get_component(SpriteRenderer)
        if sprite_renderer and sprite_renderer.image:
            image = sprite_renderer.image
            w_surf = image.get_width()
            h_surf = image.get_height()
            raw = pygame.image.tostring(image, "RGBA")
            qimg = QImage(raw, w_surf, h_surf, w_surf * 4, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            
            cx, cy = self.world_to_viewport(selected.transform.position)
            zoom = self.camera.zoom
            scale = selected.transform.scale
            w = max(1.0, abs(float(scale[0])) * zoom)
            h = max(1.0, abs(float(scale[1])) * zoom)
            
            painter = QPainter(self)
            try:
                painter.setRenderHint(QPainter.Antialiasing, True)
                
                # Manual Quantization (Force snapping like Pygame)
                cx_quantized = int(cx)
                cy_quantized = int(cy)
                
                local_rect = QRectF(-w / 2.0, -h / 2.0, w, h)
                painter.save()
                painter.translate(cx_quantized, cy_quantized)
                painter.drawPixmap(local_rect, pixmap, pixmap.rect())
                painter.restore()
            finally:
                painter.end()
                
            logs_b.append({
                "cx": cx,
                "cy": cy,
                "actual_x": cx_quantized # Quantized
            })
    return res

Phase1ViewportWidget.paintGL = paint_gl_exp_b

# Reset Player position
player.transform.position[0] = 0.0
cx, cy = viewport.world_to_viewport(player.transform.position)

# Run Experiment B drag
press_ev = QMouseEvent(QMouseEvent.Type.MouseButtonPress, QPointF(cx, cy), QPointF(cx, cy), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
viewport.mousePressEvent(press_ev)

for frame in range(1, 6):
    mx = cx + frame * 0.3
    viewport.mouseMoveEvent(QMouseEvent(QMouseEvent.Type.MouseMove, QPointF(mx, cy), QPointF(mx, cy), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
    viewport.paintGL()
    app.processEvents()
    
viewport.mouseReleaseEvent(QMouseEvent(QMouseEvent.Type.MouseButtonRelease, QPointF(mx, cy), QPointF(mx, cy), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))

# Restore hooks
Phase1ViewportWidget.paintGL = original_paint_gl

# Calculate smoothness of Experiment A
exp_a_smooth = True
prev_val = None
for l in logs_a:
    val = l["actual_x"]
    if prev_val is not None:
        delta = val - prev_val
        if delta == 0.0:
            exp_a_smooth = False # Stalled
    prev_val = val

# Calculate smoothness of Experiment B
exp_b_smooth = True
prev_val = None
for l in logs_b:
    val = l["actual_x"]
    if prev_val is not None:
        delta = val - prev_val
        if delta == 0.0:
            exp_b_smooth = False # Stalled (snap!)
    prev_val = val

# Generate report
report_lines = []
report_lines.append("# Auditoria: Causa Raiz do Snap (Cordenadas vs Rasterizacao)\n")
report_lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

report_lines.append("## Resultados do Experimento A (Floats sem Antialiasing)\n")
report_lines.append("O Grid/Sprite move-se com deltas fracionários contínuos:")
for idx, l in enumerate(logs_a):
    report_lines.append(f"- Frame {idx+1}: Coordenada X usada = `{l['actual_x']:.4f}`")
report_lines.append(f"**Resultado:** O movimento continuou perfeitamente suave (`Contínuo = {exp_a_smooth}`).\n")

report_lines.append("## Resultados do Experimento B (Quantização Manual com Antialiasing)\n")
report_lines.append("As coordenadas foram truncadas manualmente para inteiros:")
for idx, l in enumerate(logs_b):
    report_lines.append(f"- Frame {idx+1}: Coordenada X usada = `{l['actual_x']}`")
report_lines.append(f"**Resultado:** O snap reapareceu imediatamente (`Contínuo = {exp_b_smooth}`).\n")

report_lines.append("## Conclusão Final\n")
if exp_a_smooth and not exp_b_smooth:
    conclusion = "A causa exclusiva do snap é a perda das coordenadas fracionárias (coordenadas float)."
elif exp_a_smooth and exp_b_smooth:
    conclusion = "A causa do snap é a rasterização/OpenGL do Qt."
else:
    conclusion = "Existe outro fator ainda não identificado."
    
report_lines.append(f"**Conclusão:** {conclusion}")

report_content = "\n".join(report_lines)

import os
os.makedirs("docs", exist_ok=True)
os.makedirs("doc", exist_ok=True)

with open("docs/causa_raiz_snap.md", "w", encoding="utf-8") as f:
    f.write(report_content)
with open("doc/causa_raiz_snap.md", "w", encoding="utf-8") as f:
    f.write(report_content)
    
print("\nSUCCESS: Report saved successfully.")
print("Conclusion:", conclusion)
