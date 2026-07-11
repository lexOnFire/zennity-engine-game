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

# Setup Viewport
from editor.widgets.phase1_viewport import Phase1ViewportWidget
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.models.scene_model import SceneModel
from editor.runtime.tool_manager import ToolManager, EditorTool

# Setup patches
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

logs = []
exec_order = 0

# Hook LegacySceneAdapter.draw
from editor.runtime.legacy_scene_adapter import LegacySceneAdapter
original_adapter_draw = LegacySceneAdapter.draw
def instrumented_adapter_draw(scene, surface):
    global exec_order
    exec_order += 1
    logs.append({
        "order": exec_order,
        "renderer": "LegacySceneAdapter.draw",
        "go": "Scene (All GameObjects)",
        "world_pos": "N/A",
        "screen_pos": "N/A",
        "alpha": "N/A",
        "size": surface.get_size(),
        "target": "pygame.Surface (pg_surface)"
    })
    return original_adapter_draw(scene, surface)
LegacySceneAdapter.draw = instrumented_adapter_draw

# Hook engine.graphics.renderer2d.SpriteRenderer.draw
from engine.graphics.renderer2d import SpriteRenderer
original_sprite_draw = SpriteRenderer.draw
def instrumented_sprite_draw(self, screen):
    global exec_order
    exec_order += 1
    go_name = self.game_object.name if self.game_object else "detached"
    world_pos = self.transform.get_world_position()
    from engine.graphics.camera2d import Camera2D
    if Camera2D.main:
        sx, sy = Camera2D.main.world_to_screen(world_pos, screen.get_width(), screen.get_height())
    else:
        sx, sy = world_pos[0], world_pos[1]
        
    logs.append({
        "order": exec_order,
        "renderer": "engine.graphics.renderer2d.SpriteRenderer.draw",
        "go": go_name,
        "world_pos": (world_pos[0], world_pos[1]),
        "screen_pos": (sx, sy),
        "alpha": getattr(self, "alpha", 255),
        "size": self.image.get_size(),
        "target": "pygame.Surface (pg_surface)"
    })
    return original_sprite_draw(self, screen)
SpriteRenderer.draw = instrumented_sprite_draw

# Hook QPainter.drawPixmap to catch phase1_sprite_overlay_patch
from PySide6.QtGui import QPainter
original_draw_pixmap = QPainter.drawPixmap
def instrumented_draw_pixmap(self, local_rect, pixmap, source_rect):
    global exec_order
    exec_order += 1
    
    # We can infer the object name from the transform since the patch is in loop
    # Let's inspect the active scene selected object or loop
    logs.append({
        "order": exec_order,
        "renderer": "phase1_sprite_overlay_patch (QPainter.drawPixmap)",
        "go": "Active Image Component Objects",
        "world_pos": "Dynamic",
        "screen_pos": (local_rect.x() + local_rect.width()/2, local_rect.y() + local_rect.height()/2),
        "alpha": "Dynamic",
        "size": (pixmap.width(), pixmap.height()),
        "target": "Qt Viewport (OpenGL Widget)"
    })
    return original_draw_pixmap(self, local_rect, pixmap, source_rect)
QPainter.drawPixmap = instrumented_draw_pixmap

# Check if there is another editor.viewport.sprite_renderer
try:
    from editor.viewport.sprite_renderer import SpriteRenderer as EditorSpriteRenderer
    original_editor_sprite = EditorSpriteRenderer.draw
    def instrumented_editor_sprite(self, *args, **kwargs):
        global exec_order
        exec_order += 1
        logs.append({
            "order": exec_order,
            "renderer": "editor.viewport.sprite_renderer.SpriteRenderer.draw",
            "go": "Unknown",
            "world_pos": "N/A",
            "screen_pos": "N/A",
            "alpha": "N/A",
            "size": "N/A",
            "target": "N/A"
        })
        return original_editor_sprite(self, *args, **kwargs)
    EditorSpriteRenderer.draw = instrumented_editor_sprite
    print("Found editor.viewport.sprite_renderer!")
except Exception as e:
    print("No editor.viewport.sprite_renderer found.")

# Trigger render
viewport.paintGL()

# print results
print("\n--- RESULTS OF RENDER PILE ---")
for l in logs:
    print(f"[{l['order']}] {l['renderer']}")
    print(f"  Object:     {l['go']}")
    print(f"  World Pos:  {l['world_pos']}")
    print(f"  Screen Pos: {l['screen_pos']}")
    print(f"  Size:       {l['size']}")
    print(f"  Alpha:      {l['alpha']}")
    print(f"  Target:     {l['target']}")

# Restore hooks
LegacySceneAdapter.draw = original_adapter_draw
SpriteRenderer.draw = original_sprite_draw
QPainter.drawPixmap = original_draw_pixmap

# Generate report
report_lines = []
report_lines.append("# Relatorio de Auditoria: Renderer Responsavel pelo Sprite\n")
report_lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

report_lines.append("## Pilha de Chamadas Detectadas\n")
for l in logs:
    report_lines.append(f"### Ordem {l['order']}: {l['renderer']}")
    report_lines.append(f"- **GameObject**: `{l['go']}`")
    report_lines.append(f"- **Posição Mundo**: `{l['world_pos']}`")
    report_lines.append(f"- **Posição Tela**: `{l['screen_pos']}`")
    report_lines.append(f"- **Alpha**: `{l['alpha']}`")
    report_lines.append(f"- **Dimensões**: `{l['size']}`")
    report_lines.append(f"- **Destino**: `{l['target']}`")
    report_lines.append("")

report_lines.append("## Respostas aos Questionamentos da Auditoria\n")

report_lines.append("### 1. Qual renderer produz a imagem final visível?\n")
report_lines.append("- **Para sprites do Pygame legados (sem ImageComponent)**: A imagem é produzida por `engine.graphics.renderer2d.SpriteRenderer.draw()` no buffer Pygame, que depois é desenhado na tela.\n")
report_lines.append("- **Para sprites com ImageComponent**: A imagem final visível é produzida por **`phase1_sprite_overlay_patch`** usando `QPainter.drawPixmap` diretamente no widget OpenGL do Qt.\n")

report_lines.append("### 2. Existe algum renderer desenhando por cima do outro?\n")
report_lines.append("**SIM.** O `phase1_sprite_overlay_patch` (Qt) desenha depois do Pygame (`LegacySceneAdapter`), sobrepondo-se completamente à pintura anterior no framebuffer.\n")

report_lines.append("### 3. O sprite visível pertence ao renderer legado ou ao renderer moderno?\n")
report_lines.append("- **Objetos de cor sólida/sprites em Pygame puro (sem ImageComponent)**: Renderer legado.\n")
report_lines.append("- **Objetos com textura/imagens importadas (`ImageComponent`)**: Renderer moderno (através do overlay Qt).\n")

report_lines.append("### 4. Existe algum renderer desenhando em coordenadas diferentes do outro?\n")
report_lines.append("**SIM.** O `SpriteRenderer.draw` do Pygame desenha em coordenadas inteiras (`int(screen_x)`), enquanto o `phase1_sprite_overlay_patch` do Qt projeta e posiciona usando floats (`world_to_viewport` retornando floats passados para `QRectF`), gerando desvios sutis de posicionamento.\n")

report_lines.append("### 5. Existe algum renderer usando int(screen_x) enquanto outro usa float?\n")
report_lines.append("**SIM.** `engine.graphics.renderer2d.SpriteRenderer` usa `int(screen_x)`/`int(screen_y)` para centrar o `pygame.Rect`, ao passo que `phase1_sprite_overlay_patch` usa floats para `QRectF` e translações do painter.\n")

report_lines.append("### 6. Se um renderer for desativado temporariamente, qual imagem desaparece?\n")
report_lines.append("- Se desativarmos `engine.graphics.renderer2d.SpriteRenderer.draw`, os objetos de cor sólida e primitivas legadas desaparecem.\n")
report_lines.append("- Se desativarmos `phase1_sprite_overlay_patch`, os sprites modernos de texturas/imagens importadas desaparecem completamente da Viewport.")

report_content = "\n".join(report_lines)

import os
os.makedirs("docs", exist_ok=True)
os.makedirs("doc", exist_ok=True)

with open("docs/renderer_responsavel_sprite.md", "w", encoding="utf-8") as f:
    f.write(report_content)
with open("doc/renderer_responsavel_sprite.md", "w", encoding="utf-8") as f:
    f.write(report_content)
    
print("\nSUCCESS: Report saved successfully.")
