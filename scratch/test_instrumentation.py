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

from editor.runtime.viewport_transform_stability_patch import apply_viewport_transform_stability_patch, drag_stats
from editor.widgets.phase1_viewport import Phase1ViewportWidget
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.models.scene_model import SceneModel
from editor.runtime.tool_manager import ToolManager, EditorTool
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import QPointF, Qt

# Apply patch
apply_viewport_transform_stability_patch()

# Mock viewModel and Scene
model = SceneModel()
viewmodel = SceneViewModel(model)
viewport = Phase1ViewportWidget()
viewport.set_viewmodel(viewmodel)

# Set tool manager and active tool
tool_manager = ToolManager()
tool_manager.set_active_tool(EditorTool.MOVE)
viewport.set_tool_manager(tool_manager)

# Resize to create the pg_surface for real rendering!
viewport.resizeGL(800, 600)

print("Starting 10-second simulated drag test with diagnostic loops enabled...")

# Select the player object (index 1 in editable_objects)
selected = viewport.active_scene.editable_objects[1]
viewport.select_object(selected)

# Start measuring
drag_stats.start_drag()

# Set up drag state
viewport._move_drag_object = selected
viewport._move_axis_lock = None
viewport._move_start_world = np.array([0.0, 0.0, 0.0])
viewport._move_start_position = selected.transform.position.copy()

# Run loop at ~60 FPS for 10 seconds
start_time = time.time()
frame_interval = 1.0 / 60.0 # 16.6ms

current_x = 400.0
current_y = 300.0

# Count frames
frames = 0

while time.time() - start_time < 10.0:
    loop_start = time.perf_counter()
    
    # 1. Simulate mouseMoveEvent
    current_x += 0.5
    current_y += 0.2
    event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(current_x, current_y),
        QPointF(current_x, current_y),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    viewport.mouseMoveEvent(event)
    
    # 2. Simulate QTimer tick & sync selection
    viewport._tick()
    viewport._sync_selection_to_model()
    
    # 3. PaintGL
    viewport.paintGL()
    
    frames += 1
    
    # Sleep to maintain ~60 FPS
    elapsed = time.perf_counter() - loop_start
    sleep_time = frame_interval - elapsed
    if sleep_time > 0:
        time.sleep(sleep_time)

# End drag
viewport._move_drag_object = None
drag_stats.stop_drag_and_save()

print(f"SIMULATION COMPLETED SUCCESSFULLY! Simulated {frames} frames.")
