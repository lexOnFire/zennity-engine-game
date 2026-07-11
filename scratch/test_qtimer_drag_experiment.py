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

# Counters
paintgl_calls = 0
update_calls = 0
mousemove_calls = 0

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

# Instrumented hooks
original_paint_gl = Phase1ViewportWidget.paintGL
def instrumented_paint_gl(self):
    global paintgl_calls
    paintgl_calls += 1
    return original_paint_gl(self)
Phase1ViewportWidget.paintGL = instrumented_paint_gl

from PySide6.QtWidgets import QWidget
original_update = QWidget.update
def instrumented_update(self):
    global update_calls
    # Only track if it's the viewport widget
    if hasattr(self, "_move_drag_object"):
        update_calls += 1
    return original_update(self)
QWidget.update = instrumented_update

original_mousemove = Phase1ViewportWidget.mouseMoveEvent
def instrumented_mousemove(self, event):
    global mousemove_calls
    mousemove_calls += 1
    return original_mousemove(self, event)
Phase1ViewportWidget.mouseMoveEvent = instrumented_mousemove

# Get target player
player = viewport.active_scene.editable_objects[1]

# Simulating dragging for 5 seconds
print("Starting 5-second simulated drag experiment...")

start_time = time.time()
frames = 0

# 1. DRAG START (Triggered by mouse press on target object position)
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

# 2. DRAG MOVE loop
while time.time() - start_time < 5.0:
    move_ev = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(cx + frames * 0.5, cy + frames * 0.5),
        QPointF(cx + frames * 0.5, cy + frames * 0.5),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    viewport.mouseMoveEvent(move_ev)
    
    # Process event queue to let Qt process repaints and timers
    app.processEvents()
    
    frames += 1
    time.sleep(0.016)

# 3. DRAG END
release_ev = QMouseEvent(
    QMouseEvent.Type.MouseButtonRelease,
    QPointF(cx + frames * 0.5, cy + frames * 0.5),
    QPointF(cx + frames * 0.5, cy + frames * 0.5),
    Qt.MouseButton.LeftButton,
    Qt.MouseButton.LeftButton,
    Qt.KeyboardModifier.NoModifier
)
viewport.mouseReleaseEvent(release_ev)

dur = time.time() - start_time
print("\n--- RESULTS ---")
print(f"MouseMove/s: {mousemove_calls / dur:.2f}")
print(f"update/s: {update_calls / dur:.2f}")
print(f"paintGL/s: {paintgl_calls / dur:.2f}")
print(f"QTimer active at the end: {viewport._timer.isActive()}")
