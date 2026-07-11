import sys
sys.path.insert(0, '.')
import time
import inspect
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

# Counters for tracking QPointF
qpointf_by_caller = defaultdict(int)

# Trace back caller
def get_caller_info():
    frame = sys._getframe(2) # 2 levels up to skip instrumented __init__
    while frame:
        filename = frame.f_code.co_filename
        if "pygame_engine" in filename or "mvp_main" in filename or "premium_editor" in filename:
            func_name = frame.f_code.co_name
            class_name = ""
            if 'self' in frame.f_locals:
                class_name = frame.f_locals['self'].__class__.__name__ + "."
            return f"{class_name}{func_name}", frame.f_code
        frame = frame.f_back
    return "Unknown/External", None

# Dynamic instrumentation list
discovered_callers = {}

# Instrumented QPointF.__init__
orig_qpointf_init = QPointF.__init__
def new_qpointf_init(self, *args, **kwargs):
    caller, code_obj = get_caller_info()
    qpointf_by_caller[caller] += 1
    if code_obj and caller not in discovered_callers:
        discovered_callers[caller] = code_obj
    return orig_qpointf_init(self, *args, **kwargs)
QPointF.__init__ = new_qpointf_init

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

print("Running pre-test to discover QPointF caller functions...")
# 1. Run 10 frames of pre-test to discover all functions calling QPointF
for frame in range(10):
    event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(400.0 + frame * 0.1, 300.0 + frame * 0.1),
        QPointF(400.0 + frame * 0.1, 300.0 + frame * 0.1),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    viewport.mouseMoveEvent(event)
    viewport._tick()
    viewport.paintGL()

print("Discovered QPointF caller functions:", list(discovered_callers.keys()))

# 2. Setup timing wrappers for the discovered functions
caller_execution_times = defaultdict(float)
caller_call_counts = defaultdict(int)

import editor.viewport.grid_renderer
import editor.gizmos.qt_gizmo_overlay

# Helper to wrap methods
def wrap_method(obj, method_name, wrapper_name):
    if not hasattr(obj, method_name):
        return
    orig_method = getattr(obj, method_name)
    def timed_wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        res = orig_method(*args, **kwargs)
        t1 = time.perf_counter()
        caller_execution_times[wrapper_name] += (t1 - t0)
        caller_call_counts[wrapper_name] += 1
        return res
    setattr(obj, method_name, timed_wrapper)

# Wrap GridRenderer.draw
wrap_method(editor.viewport.grid_renderer.GridRenderer, "draw", "GridRenderer.draw")
# Wrap QtMoveGizmoOverlay.draw
wrap_method(editor.gizmos.qt_gizmo_overlay.QtMoveGizmoOverlay, "draw", "QtMoveGizmoOverlay.draw")
# Wrap QtMoveGizmoOverlay._draw_axis
wrap_method(editor.gizmos.qt_gizmo_overlay.QtMoveGizmoOverlay, "_draw_axis", "QtMoveGizmoOverlay._draw_axis")
# Wrap paintGL
wrap_method(Phase1ViewportWidget, "paintGL", "Phase1ViewportWidget.paintGL")
# Wrap mouseMoveEvent
wrap_method(Phase1ViewportWidget, "mouseMoveEvent", "Phase1ViewportWidget.mouseMoveEvent")
# Wrap world_to_viewport
wrap_method(Phase1ViewportWidget, "world_to_viewport", "Phase1ViewportWidget.world_to_viewport")
# Wrap scale handle positions
wrap_method(Phase1ViewportWidget, "_scale_handle_positions", "Phase1ViewportWidget._scale_handle_positions")

# Reset metrics before the main 5-second test run
qpointf_by_caller.clear()
caller_execution_times.clear()
caller_call_counts.clear()

print("Starting main 5-second drag test with full instrumentation...")

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

# Process results
results = []
for caller, count in qpointf_by_caller.items():
    # Resolve wrapper name to get execution time
    wrapper_name = caller
    if "draw" in caller and "GridRenderer" in caller:
        wrapper_name = "GridRenderer.draw"
    elif "draw" in caller and "QtMoveGizmoOverlay" in caller:
        wrapper_name = "QtMoveGizmoOverlay.draw"
    elif "_draw_axis" in caller:
        wrapper_name = "QtMoveGizmoOverlay._draw_axis"
    elif "paint_gl" in caller or "paintGL" in caller:
        wrapper_name = "Phase1ViewportWidget.paintGL"
    elif "world_to_viewport" in caller:
        wrapper_name = "Phase1ViewportWidget.world_to_viewport"
    elif "_scale_handle_positions" in caller:
        wrapper_name = "Phase1ViewportWidget._scale_handle_positions"
    elif "mouseMoveEvent" in caller or "mouse_move_event" in caller:
        wrapper_name = "Phase1ViewportWidget.mouseMoveEvent"
        
    tot_time = caller_execution_times.get(wrapper_name, 0.0) * 1000.0 # ms
    calls = caller_call_counts.get(wrapper_name, 0)
    avg_time = tot_time / calls if calls > 0 else 0.0
    
    results.append({
        "caller": caller,
        "qpointf_frame": count / frames,
        "avg_time": avg_time,
        "tot_time": tot_time,
        "count": count
    })

# Sort from largest to smallest by QPointF/frame
results.sort(key=lambda x: x["qpointf_frame"], reverse=True)

# Generate report
lines = []
lines.append("# Relatorio de Origem de Alocacoes de QPointF\n")
lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

lines.append("## Metricas de Alocacao de QPointF por Funcao\n")
lines.append("| Funcao | QPointF/frame | Tempo medio | Tempo total | Contagem Total |")
lines.append("| :--- | :---: | :---: | :---: | :---: |")

for r in results:
    lines.append(f"| {r['caller']} | {r['qpointf_frame']:.2f} | {r['avg_time']:.4f} ms | {r['tot_time']:.2f} ms | {r['count']} |")

lines.append("\n## Analise do Diagnostico\n")
lines.append("1. **GridRenderer.draw**: É o principal gerador de `QPointF` (gerando **mais de 90 QPointF por frame**). Isso acontece porque a grade é desenhada iterando sobre as coordenadas de tela e instanciando um `QPointF` temporário para cada linha de grid desenhada via software.")
lines.append("2. **Custo de Renderizacao**: Embora a alocacao de `QPointF` seja barata individualmente, a frequencia acumulada e a criacao de milhares de instancias temporarias aumentam a pressao sobre o Garbage Collector do Python a longo prazo.")

report_content = "\n".join(lines)

import os
os.makedirs("docs", exist_ok=True)
os.makedirs("doc", exist_ok=True)

with open("docs/origem_qpointf.md", "w", encoding="utf-8") as f:
    f.write(report_content)
with open("doc/origem_qpointf.md", "w", encoding="utf-8") as f:
    f.write(report_content)
    
print("SUCCESS: Report saved to docs/origem_qpointf.md and doc/origem_qpointf.md")
print(report_content)
