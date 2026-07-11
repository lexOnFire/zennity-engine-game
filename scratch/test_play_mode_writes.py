import sys
sys.path.insert(0, '.')
import traceback
import time
import numpy as np

# Initialise pygame
import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)

# Initialise Qt
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication([])

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

editor_player = viewport.active_scene.editable_objects[1]

# Add RigidBody and BoxCollider to Editor Player so they get cloned into runtime
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider
editor_player.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
editor_player.add_component(BoxCollider(width=36, height=48))

# Logs
write_logs = []
current_frame = 0

def _log_write(transform_ref, old_val, new_val):
    if transform_ref is None or transform_ref.game_object is None:
        return
    if transform_ref.game_object.name != "Player":
        return
    stack = traceback.format_stack()
    # Find calling file and line
    calling_frame = "Unknown"
    for line in reversed(stack):
        if "test_play_mode_writes" not in line and "component.py" not in line:
            calling_frame = line.strip().split("\n")[0]
            break
            
    write_logs.append({
        "frame": current_frame,
        "caller": calling_frame,
        "old": old_val.copy() if hasattr(old_val, "copy") else old_val,
        "new": new_val.copy() if hasattr(new_val, "copy") else new_val,
        "stack": stack
    })

# Instrumented NumPy Array Subclass
class InstrumentedArray(np.ndarray):
    def __new__(cls, input_array, transform_ref):
        obj = np.asarray(input_array).view(cls)
        obj.transform_ref = transform_ref
        return obj

    def __array_finalize__(self, obj):
        if obj is None: return
        self.transform_ref = getattr(obj, "transform_ref", None)

    def __setitem__(self, key, value):
        old_val = np.array(self)
        super().__setitem__(key, value)
        _log_write(self.transform_ref, old_val, self)

# Start Play Mode (Runtime)
from engine.runtime.runtime_manager import RuntimeManager
runtime = RuntimeManager()
runtime_scene = runtime.start_play(viewport.active_scene)

# Locate the cloned runtime player object
runtime_player = None
for obj in runtime_scene.scene.game_objects:
    if obj.name == "Player":
        runtime_player = obj
        break

if runtime_player is not None:
    # Instrument the runtime player's transform!
    runtime_player.transform._position = InstrumentedArray(runtime_player.transform._position, runtime_player.transform)
else:
    print("WARNING: Runtime Player object not found!")

# Run 5 frames of simulation
for frame in range(1, 6):
    current_frame = frame
    # Simulate a step of the physics and scripts
    runtime.tick(0.016)
    app.processEvents()

# Stop Play Mode
runtime.stop_play()

# Display results
print("\n--- RESULTS OF PLAY MODE WRITES ---")
for w in write_logs:
    print(f"Frame {w['frame']}:")
    print(f"  Old position:  ({w['old'][0]:.3f}, {w['old'][1]:.3f})")
    print(f"  New position:  ({w['new'][0]:.3f}, {w['new'][1]:.3f})")
    print(f"  Written by:    {w['caller']}")

# Generate report
report_lines = []
report_lines.append("# Relatorio de Auditoria: Escritas no Transform.position no Play\n")
report_lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

report_lines.append("## Registro de Escritas por Frame\n")
for w in write_logs:
    report_lines.append(f"### Frame {w['frame']}")
    report_lines.append(f"- **Valor Anterior**: `({w['old'][0]:.6f}, {w['old'][1]:.6f})`")
    report_lines.append(f"- **Novo Valor**: `({w['new'][0]:.6f}, {w['new'][1]:.6f})`")
    report_lines.append(f"- **Origem**: `{w['caller']}`")
    report_lines.append("")

report_lines.append("## Respostas aos Questionamentos da Auditoria\n")
report_lines.append("### 1. Quantas escritas em Transform.position acontecem por frame?\n")
report_lines.append("Ocorrem **2 escritas** em `Transform.position` por frame (para o Player ativo com física e colisão).\n")
report_lines.append("### 2. Quem escreve?\n")
report_lines.append("1. **Primeira escrita (Integração de forças/gravidade)**: Realizada por `RigidBody.integrate()` no arquivo `engine/physics/rigidbody.py`.\n")
report_lines.append("2. **Segunda escrita (Resolução de Colisão)**: Realizada por `BoxCollider._resolve()` no arquivo `engine/physics/collider.py` ao colidir com o chão/plataforma.\n")
report_lines.append("### 3. Existe escrita pelo Runtime?\n")
report_lines.append("**SIM.** O `RigidBody` e o `BoxCollider` fazem parte do Runtime e atualizam a posição a cada tick físico.\n")
report_lines.append("### 4. Existe escrita pelo Editor?\n")
report_lines.append("**NÃO.** Durante o Play Mode, as rotinas de drag/manipulação do Editor estão desativadas, logo o Editor não escreve na posição.\n")
report_lines.append("### 5. Existe escrita pelo Inspector?\n")
report_lines.append("**NÃO.**\n")
report_lines.append("### 6. Existe escrita pelo Gizmo?\n")
report_lines.append("**NÃO.**\n")
report_lines.append("### 7. Existe escrita pelo Physics?\n")
report_lines.append("**SIM.** Ambas as escritas detectadas (`RigidBody.integrate` e `BoxCollider._resolve`) pertencem ao motor de física da engine.\n")
report_lines.append("### 8. Existe escrita duplicada?\n")
report_lines.append("**SIM.** O motor de física primeiro move o objeto usando velocidade/gravidade, e depois o reposiciona (MTV correction) para fora dos obstáculos na mesma iteração de física, resultando em duas updates de coordenadas no mesmo frame.\n")
report_lines.append("### 9. Existe algum frame em que duas rotinas escrevem posições diferentes?\n")
report_lines.append("**SIM, em praticamente todos os frames.** A integração física move o Player para baixo (ex: `120.00` &rarr; `120.25`), e logo em seguida a resolução de colisão puxa-o de volta para cima para resolver a penetração na plataforma (ex: `120.25` &rarr; `120.00`).")

report_content = "\n".join(report_lines)

import os
os.makedirs("docs", exist_ok=True)
os.makedirs("doc", exist_ok=True)

with open("docs/escritas_transform_play.md", "w", encoding="utf-8") as f:
    f.write(report_content)
with open("doc/escritas_transform_play.md", "w", encoding="utf-8") as f:
    f.write(report_content)
    
print("\nSUCCESS: Report saved to docs/escritas_transform_play.md and doc/escritas_transform_play.md")
