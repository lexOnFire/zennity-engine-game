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

from editor.widgets.phase1_viewport import Phase1ViewportWidget
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.models.scene_model import SceneModel
from editor.runtime.tool_manager import ToolManager, EditorTool

# Create widget
model = SceneModel()
viewmodel = SceneViewModel(model)
viewport = Phase1ViewportWidget()
viewport.set_viewmodel(viewmodel)

# Set tool manager
tool_manager = ToolManager()
tool_manager.set_active_tool(EditorTool.MOVE)
viewport.set_tool_manager(tool_manager)

# Setup viewport resolution to 800x600
viewport.resizeGL(800, 600)

print("Starting tostring cost instrumentation...")

# Instrument pygame.image.tostring
original_tostring = pygame.image.tostring
tostring_times = []
bytes_copied_list = []

def instrumented_tostring(surface, format, flipped=False):
    t0 = time.perf_counter()
    res = original_tostring(surface, format, flipped)
    t1 = time.perf_counter()
    tostring_times.append(t1 - t0)
    bytes_copied_list.append(len(res))
    return res

pygame.image.tostring = instrumented_tostring

# Helper to run a test block and gather statistics
def run_scenario(name, duration=2.0, action_fn=None):
    tostring_times.clear()
    bytes_copied_list.clear()
    
    start_time = time.time()
    frames = 0
    
    # We maintain a loop as fast as possible to measure actual achievable FPS
    # paintGL is synchronous
    while time.time() - start_time < duration:
        if action_fn:
            action_fn(frames)
        viewport._tick()
        viewport.paintGL()
        frames += 1
        
    actual_duration = time.time() - start_time
    fps = frames / actual_duration
    
    avg_tostring = sum(tostring_times) / len(tostring_times) * 1000.0 if tostring_times else 0.0
    bytes_per_frame = bytes_copied_list[0] if bytes_copied_list else 0
    mb_per_frame = bytes_per_frame / (1024.0 * 1024.0)
    mb_s_copied = mb_per_frame * fps
    
    print(f"Scenario: {name} | FPS: {fps:.2f} | tostring avg: {avg_tostring:.4f} ms | MB/s: {mb_s_copied:.2f}")
    
    return {
        "name": name,
        "fps": fps,
        "avg_tostring": avg_tostring,
        "bytes_per_frame": bytes_per_frame,
        "mb_s_copied": mb_s_copied
    }

# 1. Editor Parado (Rest)
def rest_fn(frame):
    pass
res_rest = run_scenario("Editor Parado", duration=2.0, action_fn=rest_fn)

# 2. Camera Movendo (Panning)
def camera_pan_fn(frame):
    viewport.camera.pan(1.0, 0.5)
res_cam = run_scenario("Câmera Movendo", duration=2.0, action_fn=camera_pan_fn)

# 3. Objeto sendo Arrastado (Dragging)
player = viewport.active_scene.editable_objects[1]
viewport.select_object(player)
viewport._move_drag_object = player
viewport._move_axis_lock = None
viewport._move_start_world = np.array([0.0, 0.0, 0.0])
viewport._move_start_position = player.transform.position.copy()

def drag_fn(frame):
    # Simulate move drag
    viewport._update_move_drag(400.0 + frame * 0.1, 300.0 + frame * 0.1)
res_drag = run_scenario("Objeto Arrastado", duration=2.0, action_fn=drag_fn)

# Stop dragging
viewport._move_drag_object = None

# 4. 100 Objetos na cena
# Let's spawn 100 objects in active scene
original_objects_count = len(viewport.active_scene.game_objects)
from engine.core.game_object import GameObject
for i in range(100):
    go = GameObject(name=f"Sprite_{i}")
    # add to scene
    viewport.active_scene.add_game_object(go)
    viewport.active_scene.editable_objects.append(go)
    
res_100 = run_scenario("100 Objetos", duration=2.0, action_fn=rest_fn)

# 5. 500 Objetos na cena
for i in range(400): # Spawning 400 more to make 500 total
    go = GameObject(name=f"Sprite_Extra_{i}")
    viewport.active_scene.add_game_object(go)
    viewport.active_scene.editable_objects.append(go)
    
res_500 = run_scenario("500 Objetos", duration=2.0, action_fn=rest_fn)

# Gather results and generate report
resolution = f"{viewport._vp_w}x{viewport._vp_h}"
bytes_per_frame = res_rest["bytes_per_frame"]

lines = []
lines.append("# Relatorio de Custo do pygame.image.tostring()\n")
lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
lines.append("## Informacoes do Framebuffer\n")
lines.append(f"- **Resolucao do Framebuffer**: {resolution}")
lines.append(f"- **Bytes copiados por frame**: {bytes_per_frame} bytes ({bytes_per_frame / (1024.0 * 1024.0):.3f} MB)\n")

lines.append("## Tabela de Metricas por Cenario\n")
lines.append("| Cenario | FPS Alcancado | Tempo tostring() Medio | MB/s Copiados | % do Frame Budget (16.6ms) |")
lines.append("| :--- | :---: | :---: | :---: | :---: |")

scenarios = [res_rest, res_cam, res_drag, res_100, res_500]
for s in scenarios:
    pct_frame = (s["avg_tostring"] / 16.6) * 100.0
    lines.append(f"| {s['name']} | {s['fps']:.2f} FPS | {s['avg_tostring']:.4f} ms | {s['mb_s_copied']:.2f} MB/s | {pct_frame:.2f}% |")

lines.append("\n## Analise do Impacto Tecnico\n")
lines.append("1. **Custo de CPU**: O `pygame.image.tostring` roda na CPU principal em uma thread síncrona. Ele bloqueia o pipeline de renderização enquanto extrai a memória do buffer do SDL/Pygame.")
lines.append("2. **Volume de Dados**: Copiar pixels brutos de um framebuffer a cada frame satura os barramentos de memória do sistema. Para 800x600 pixels a 60 FPS, são cerca de **110+ MB/s** transferidos continuamente.")
lines.append("3. **Impacto na Escabilidade**: Conforme a quantidade de objetos na cena cresce (de 100 para 500), a carga de renderização do Pygame aumenta, mas o custo de transferência do framebuffer (`tostring`) permanece constante e fixo a cada frame, limitando o teto de FPS da engine no Qt.")

report_content = "\n".join(lines)

import os
os.makedirs("docs", exist_ok=True)
os.makedirs("doc", exist_ok=True)

with open("docs/custo_tostring.md", "w", encoding="utf-8") as f:
    f.write(report_content)
with open("doc/custo_tostring.md", "w", encoding="utf-8") as f:
    f.write(report_content)
    
print("SUCCESS: Report saved to docs/custo_tostring.md and doc/custo_tostring.md")
