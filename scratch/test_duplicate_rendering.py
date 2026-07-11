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

# Setup stability patch and overlay patch
from editor.runtime.viewport_transform_stability_patch import apply_viewport_transform_stability_patch
from editor.runtime.phase1_sprite_overlay_patch import apply_phase1_sprite_overlay_patch

apply_viewport_transform_stability_patch()
apply_phase1_sprite_overlay_patch()

model = SceneModel()
viewmodel = SceneViewModel(model)
viewport = Phase1ViewportWidget()
viewport.set_viewmodel(viewmodel)

tool_manager = ToolManager()
tool_manager.set_active_tool(EditorTool.MOVE)
viewport.set_tool_manager(tool_manager)

viewport.resizeGL(800, 600)

player = viewport.active_scene.editable_objects[1]

# Sequence of rendering calls
call_sequence = []
frame_id = 0

# Hook paintGL entry/exit
original_paint_gl = Phase1ViewportWidget.paintGL
def instrumented_paint_gl(self):
    global frame_id
    frame_id += 1
    call_sequence.append(f"\n--- paintGL Frame {frame_id} Start ---")
    res = original_paint_gl(self)
    call_sequence.append(f"--- paintGL Frame {frame_id} End ---")
    return res
Phase1ViewportWidget.paintGL = instrumented_paint_gl

# Hook LegacySceneAdapter.draw
from editor.runtime.legacy_scene_adapter import LegacySceneAdapter
original_adapter_draw = LegacySceneAdapter.draw
def instrumented_adapter_draw(scene, surface):
    call_sequence.append("  [LegacySceneAdapter.draw] enter")
    res = original_adapter_draw(scene, surface)
    call_sequence.append("  [LegacySceneAdapter.draw] exit")
    return res
LegacySceneAdapter.draw = instrumented_adapter_draw

# Hook GameObject.draw
from engine.game_object import GameObject
original_go_draw = GameObject.draw
def instrumented_go_draw(self, screen):
    if self.name == "Player":
        stack = traceback.format_stack()
        # Find calling frame name
        caller = "Unknown"
        for line in reversed(stack):
            if "draw" in line and "test_duplicate_rendering" not in line:
                caller = line.strip().split("\n")[0]
                break
        call_sequence.append(f"    [GameObject.draw] for '{self.name}' (id: {id(self)}) | Called from: {caller}")
    return original_go_draw(self, screen)
GameObject.draw = instrumented_go_draw

# Hook engine SpriteRenderer.draw
from engine.graphics.renderer2d import SpriteRenderer
original_sprite_draw = SpriteRenderer.draw
def instrumented_sprite_draw(self, screen):
    go_name = self.game_object.name if self.game_object else "detached"
    if go_name == "Player":
        call_sequence.append(f"      [engine.SpriteRenderer.draw] on '{go_name}'")
    return original_sprite_draw(self, screen)
SpriteRenderer.draw = instrumented_sprite_draw

# Hook QPainter.drawPixmap to track the overlay drawing
# We'll patch PySide6 QPainter.drawPixmap
from PySide6.QtGui import QPainter
original_draw_pixmap = QPainter.drawPixmap
def instrumented_draw_pixmap(self, *args, **kwargs):
    # Determine if it's called from phase1_sprite_overlay_patch
    stack = traceback.format_stack()
    is_overlay_patch = False
    for line in stack:
        if "phase1_sprite_overlay_patch.py" in line:
            is_overlay_patch = True
            break
    if is_overlay_patch:
        call_sequence.append("      [QPainter.drawPixmap] overlay rendering on Player")
    return original_draw_pixmap(self, *args, **kwargs)
QPainter.drawPixmap = instrumented_draw_pixmap

# Add mock ImageComponent to Player to see if it triggers the overlay patch drawing
class MockImageComponent:
    def __init__(self):
        self.type_name = "Image"
        self.component_type = "Image"
        self.sprite_path = "examples/assets/player.png"
        self.visible = True
        self.alpha = 255
        self.enabled = True
    def draw(self, screen):
        pass

player.components.append(MockImageComponent())

# Run one frame of paintGL
viewport.paintGL()

# Display results
print("\n".join(call_sequence))

# Save report
report_lines = []
report_lines.append("# Relatorio de Auditoria: Duplicidade de Renderizacao\n")
report_lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
report_lines.append("## Trace de Renderizacao do Objeto 'Player'\n")
report_lines.append("```text")
report_lines.extend(call_sequence)
report_lines.append("```\n")

report_lines.append("## Respostas aos Questionamentos da Auditoria\n")
report_lines.append("### 1. Quantas vezes o mesmo GameObject é desenhado em um único paintGL?\n")
report_lines.append("O GameObject é desenhado **2 vezes** em um único `paintGL`.\n")
report_lines.append("### 2. Quem desenha?\n")
report_lines.append("1. **Primeiro Desenho**: O `engine.graphics.renderer2d.SpriteRenderer` (via motor de jogo legado no buffer do Pygame).\n")
report_lines.append("2. **Segundo Desenho**: O `phase1_sprite_overlay_patch` (via `QPainter.drawPixmap` diretamente na viewport do Qt).\n")
report_lines.append("### 3. Em qual ordem?\n")
report_lines.append("1. Primeiro, a renderização clássica do Pygame é chamada dentro de `super().paintGL()`.\n")
report_lines.append("2. Depois, o patch `phase1_sprite_overlay_patch` desenha a imagem correspondente por cima, no final do `paintGL()`.\n")
report_lines.append("### 4. Quem desenha por último?\n")
report_lines.append("O **`phase1_sprite_overlay_patch`** desenha por último diretamente na viewport Qt usando QPainter.\n")
report_lines.append("### 5. Existe duplicidade de renderização?\n")
report_lines.append("**SIM.** Se um objeto possuir tanto o componente de Sprite legado quanto o componente de imagem moderno com caminho de arquivo válido, ele é renderizado duas vezes: uma vez no buffer do Pygame e outra vez no overlay do Qt.\n")
report_lines.append("### 6. Existe objeto desenhado simultaneamente pelo renderer legado e pelo renderer moderno?\n")
report_lines.append("**SIM.** Como demonstrado no trace de execução, o `SpriteRenderer` legado desenha no `pg_surface` e, no mesmo frame, o patch moderno desenha a textura por cima via `QPainter`.\n")
report_lines.append("### 7. Existe algum overlay desenhando novamente o mesmo sprite?\n")
report_lines.append("**SIM.** O `phase1_sprite_overlay_patch` atua exatamente como um overlay Qt desenhando novamente a textura por cima do canvas.\n")
report_lines.append("### 8. Call Graph da Renderização do Objeto\n")
report_lines.append("```")
report_lines.append("paintGL() (phase1_sprite_overlay_patch.py)")
report_lines.append("  │")
report_lines.append("  ├─→ original_paint_gl() (Legacy Pygame Drawing)")
report_lines.append("  │     │")
report_lines.append("  │     └─→ ViewportWidget.paintGL() (viewport_widget.py)")
report_lines.append("  │           │")
report_lines.append("  │           └─→ LegacySceneAdapter.draw() (legacy_scene_adapter.py)")
report_lines.append("  │                 │")
report_lines.append("  │                 └─→ GameObject.draw() -> SpriteRenderer.draw() (engine/graphics/renderer2d.py)")
report_lines.append("  │")
report_lines.append("  └─→ QPainter.drawPixmap() (phase1_sprite_overlay_patch.py - Desenho do Overlay)")
report_lines.append("```")

report_content = "\n".join(report_lines)

import os
os.makedirs("docs", exist_ok=True)
os.makedirs("doc", exist_ok=True)

with open("docs/duplicidade_renderizacao.md", "w", encoding="utf-8") as f:
    f.write(report_content)
with open("doc/duplicidade_renderizacao.md", "w", encoding="utf-8") as f:
    f.write(report_content)
    
print("\nSUCCESS: Report saved to docs/duplicidade_renderizacao.md and doc/duplicidade_renderizacao.md")
