import sys
sys.path.insert(0, '.')
import time
import numpy as np
from collections import defaultdict

# Initialise pygame
import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)

# Initialise Qt
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication([])

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QImage, QMouseEvent

# Latency tracking database
latency_samples = []
current_sample = {}

def get_percentiles(data):
    if not data:
        return 0.0, 0.0, 0.0, 0.0
    n = len(data)
    mean = sum(data) / n
    maximum = max(data)
    sorted_data = sorted(data)
    
    idx_95 = int(round(0.95 * (n - 1)))
    p95 = sorted_data[idx_95]
    
    idx_99 = int(round(0.99 * (n - 1)))
    p99 = sorted_data[idx_99]
    
    return mean * 1000.0, maximum * 1000.0, p95 * 1000.0, p99 * 1000.0

# Setup Viewport
from editor.widgets.phase1_viewport import Phase1ViewportWidget
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.models.scene_model import SceneModel
from editor.runtime.tool_manager import ToolManager, EditorTool

# Setup stability patch (with coalescing)
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

# Select player
player = viewport.active_scene.editable_objects[1]
viewport.select_object(player)
viewport._move_drag_object = player
viewport._move_axis_lock = None
viewport._move_start_world = np.array([0.0, 0.0, 0.0])
viewport._move_start_position = player.transform.position.copy()

# Dynamic hooks for latency timestamps
# 1. MouseMove hook
original_mouse_move = Phase1ViewportWidget.mouseMoveEvent
def instrumented_mouse_move(self, event):
    global current_sample
    current_sample = {'mousemove': time.perf_counter()}
    return original_mouse_move(self, event)
Phase1ViewportWidget.mouseMoveEvent = instrumented_mouse_move

# 2. Transform hook
import editor.runtime.viewport_transform_stability_patch
original_emit_transform_changed = editor.runtime.viewport_transform_stability_patch._emit_transform_changed
def instrumented_emit_transform_changed(vp, obj):
    global current_sample
    if 'mousemove' in current_sample and 'transform' not in current_sample:
        current_sample['transform'] = time.perf_counter()
    return original_emit_transform_changed(vp, obj)
editor.runtime.viewport_transform_stability_patch._emit_transform_changed = instrumented_emit_transform_changed

# 3. paintGL start and end hooks
original_paint_gl = Phase1ViewportWidget.paintGL
def instrumented_paint_gl(self):
    global current_sample
    if 'transform' in current_sample and 'paint' not in current_sample:
        current_sample['paint'] = time.perf_counter()
    
    res = original_paint_gl(self)
    
    if 'paint' in current_sample and 'presentation' not in current_sample:
        current_sample['presentation'] = time.perf_counter()
        latency_samples.append(current_sample.copy())
        current_sample.clear()
    return res
Phase1ViewportWidget.paintGL = instrumented_paint_gl

print("Starting drag latency instrumentation test...")

# Run 5 seconds of active drag
start_time = time.time()
frames = 0

while time.time() - start_time < 5.0:
    event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(400.0 + frames * 0.1, 300.0 + frames * 0.1),
        QPointF(400.0 + frames * 0.1, 300.0 + frames * 0.1),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    viewport.mouseMoveEvent(event)
    viewport._tick()
    viewport.paintGL()
    frames += 1
    time.sleep(0.016)

# End drag
viewport._move_drag_object = None

# Calculate latencies
mouse_to_transform = []
transform_to_paint = []
paint_to_presentation = []
total_latency = []

for sample in latency_samples:
    if all(k in sample for k in ['mousemove', 'transform', 'paint', 'presentation']):
        m_t = sample['transform'] - sample['mousemove']
        t_p = sample['paint'] - sample['transform']
        p_pr = sample['presentation'] - sample['paint']
        tot = sample['presentation'] - sample['mousemove']
        
        mouse_to_transform.append(m_t)
        transform_to_paint.append(t_p)
        paint_to_presentation.append(p_pr)
        total_latency.append(tot)

# Compute metrics
mt_avg, mt_max, mt_p95, mt_p99 = get_percentiles(mouse_to_transform)
tp_avg, tp_max, tp_p95, tp_p99 = get_percentiles(transform_to_paint)
pp_avg, pp_max, pp_p95, pp_p99 = get_percentiles(paint_to_presentation)
tot_avg, tot_max, tot_p95, tot_p99 = get_percentiles(total_latency)

# Generate report
lines = []
lines.append("# Relatorio de Latencia do Drag\n")
lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

lines.append("## Metricas de Latencia do Pipeline de Drag\n")
lines.append("| Fase | Media | Maximo | P95 | P99 |")
lines.append("| :--- | :---: | :---: | :---: | :---: |")
lines.append(f"| Mouse &rarr; Transform | {mt_avg:.4f} ms | {mt_max:.4f} ms | {mt_p95:.4f} ms | {mt_p99:.4f} ms |")
lines.append(f"| Transform &rarr; Paint | {tp_avg:.4f} ms | {tp_max:.4f} ms | {tp_p95:.4f} ms | {tp_p99:.4f} ms |")
lines.append(f"| Paint &rarr; Frame apresentado | {pp_avg:.4f} ms | {pp_max:.4f} ms | {pp_p95:.4f} ms | {pp_p99:.4f} ms |")
lines.append(f"| **Latencia Total (Fim-a-Fim)** | **{tot_avg:.4f} ms** | **{tot_max:.4f} ms** | **{tot_p95:.4f} ms** | **{tot_p99:.4f} ms** |")

lines.append("\n## Analise de Latencia\n")
lines.append("1. **Mouse &rarr; Transform**: Representa o tempo que a engine leva para receber o evento de mouse do Qt, calcular as coordenadas do mundo de física e aplicar o Snap para atualizar a posição do `Transform`. Geralmente é de fração de milissegundo (< 0.2ms).")
lines.append("2. **Transform &rarr; Paint**: Tempo que o Qt leva para iniciar o redesenho após a posição do objeto mudar. Como o repaint coalescing está ativo, a maior parte dessa latência é devida à sincronização do loop de eventos.")
lines.append("3. **Paint &rarr; Apresentado**: É o tempo necessário para executar o método `paintGL` completo (incluindo `pygame.image.tostring` e `drawImage`), que renderiza fisicamente o frame final na tela. É a etapa principal do tempo total.")

report_content = "\n".join(lines)

import os
os.makedirs("docs", exist_ok=True)
os.makedirs("doc", exist_ok=True)

with open("docs/latencia_drag.md", "w", encoding="utf-8") as f:
    f.write(report_content)
with open("doc/latencia_drag.md", "w", encoding="utf-8") as f:
    f.write(report_content)
    
print("SUCCESS: Report saved to docs/latencia_drag.md and doc/latencia_drag.md")
print(report_content)
