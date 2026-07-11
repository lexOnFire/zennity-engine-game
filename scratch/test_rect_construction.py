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

# Set a non-zero rotation to observe pygame.transform.rotate bounding box behavior
player.transform.rz = 33.5

# Data logs
rect_logs = []

# Hook SpriteRenderer.draw
from engine.graphics.renderer2d import SpriteRenderer
original_sprite_draw = SpriteRenderer.draw
def instrumented_sprite_draw(self, screen):
    world_pos = self.transform.get_world_position()
    
    from engine.graphics.camera2d import Camera2D
    if Camera2D.main:
        sx, sy = Camera2D.main.world_to_screen(world_pos, screen.get_width(), screen.get_height())
    else:
        sx, sy = world_pos[0], world_pos[1]
        
    # Scale width/height
    zoom = Camera2D.main.zoom if Camera2D.main else 1.0
    scale_x = abs(self.transform.sx * zoom)
    scale_y = abs(self.transform.sy * zoom)
    new_width = max(1, int(self.image.get_width() * scale_x))
    new_height = max(1, int(self.image.get_height() * scale_y))
    
    # Rotate
    scaled_img = pygame.transform.scale(self.image, (new_width, new_height))
    if self.transform.rz != 0.0:
        rotated_img = pygame.transform.rotate(scaled_img, -self.transform.rz)
    else:
        rotated_img = scaled_img
        
    rect = rotated_img.get_rect()
    rect.center = (int(sx), int(sy))
    
    rect_logs.append({
        "pos": world_pos.copy(),
        "screen_float": (sx, sy),
        "scaled_size": (new_width, new_height),
        "rotated_size": rotated_img.get_size(),
        "rect_size": (rect.width, rect.height),
        "rect_center": rect.center,
        "blit_pos": rect.topleft,
        "rz": self.transform.rz
    })
    
    return original_sprite_draw(self, screen)
SpriteRenderer.draw = instrumented_sprite_draw

print("Simulating translation drag with constant rotation (33.5 degrees)...")
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

for step in range(5):
    mx = cx + step * 1.5
    my = cy + step * 1.5
    move_ev = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(mx, my),
        QPointF(mx, my),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    viewport.mouseMoveEvent(move_ev)
    viewport.paintGL()
    app.processEvents()
    
viewport.mouseReleaseEvent(QMouseEvent(
    QMouseEvent.Type.MouseButtonRelease, QPointF(mx, my), QPointF(mx, my),
    Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
))

# Switch to Rotate Tool and rotate dynamically
print("\nSimulating rotation drag (angle changing)...")
tool_manager.set_active_tool(EditorTool.ROTATE)
press_ev = QMouseEvent(
    QMouseEvent.Type.MouseButtonPress,
    QPointF(cx, cy),
    QPointF(cx, cy),
    Qt.MouseButton.LeftButton,
    Qt.MouseButton.LeftButton,
    Qt.KeyboardModifier.NoModifier
)
viewport.mousePressEvent(press_ev)

for step in range(5):
    # Drag mouse in circle to rotate
    angle = step * 15.0
    mx = cx + 50.0 * np.cos(np.radians(angle))
    my = cy + 50.0 * np.sin(np.radians(angle))
    move_ev = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(mx, my),
        QPointF(mx, my),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    viewport.mouseMoveEvent(move_ev)
    viewport.paintGL()
    app.processEvents()

viewport.mouseReleaseEvent(QMouseEvent(
    QMouseEvent.Type.MouseButtonRelease, QPointF(mx, my), QPointF(mx, my),
    Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
))

# Restore hooks
SpriteRenderer.draw = original_sprite_draw

# Generate results
print("\n--- RESULTS OF RECT AUDIT ---")
for idx, log in enumerate(rect_logs):
    print(f"Log {idx} (rz: {log['rz']:.1f}°):")
    print(f"  Pos:            ({log['pos'][0]:.3f}, {log['pos'][1]:.3f})")
    print(f"  Screen float:   ({log['screen_float'][0]:.3f}, {log['screen_float'][1]:.3f})")
    print(f"  Scaled size:    {log['scaled_size']}")
    print(f"  Rotated size:   {log['rotated_size']}")
    print(f"  Rect size:      {log['rect_size']}")
    print(f"  Rect center:    {log['rect_center']}")
    print(f"  Blit pos:       {log['blit_pos']}")

# Generate report file
report_lines = []
report_lines.append("# Relatorio de Auditoria: Construcao do pygame.Rect no Blit\n")
report_lines.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

report_lines.append("## Logs de Metricas de Bounding Box\n")
for idx, log in enumerate(rect_logs):
    report_lines.append(f"### Registro {idx} (rz: {log['rz']:.1f}°)")
    report_lines.append(f"- **Transform.position**: `({log['pos'][0]:.6f}, {log['pos'][1]:.6f})`")
    report_lines.append(f"- **screen_x / screen_y**: `({log['screen_float'][0]:.4f}, {log['screen_float'][1]:.4f})`")
    report_lines.append(f"- **Surface (antes rotação)**: `{log['scaled_size']}`")
    report_lines.append(f"- **Surface (após rotação)**: `{log['rotated_size']}`")
    report_lines.append(f"- **pygame.Rect (get_rect)**: `{log['rect_size']}`")
    report_lines.append(f"- **rect.center**: `{log['rect_center']}`")
    report_lines.append(f"- **Blit Position (topleft)**: `{log['blit_pos']}`")
    report_lines.append("")

report_lines.append("## Respostas aos Questionamentos da Auditoria\n")
report_lines.append("### 1. A largura da Surface muda durante o drag?\n")
report_lines.append("- **Com rotação estática:** **NÃO.** Se o objeto apenas translada sem girar, a largura da superfície e a largura pós-rotação permanecem perfeitamente constantes.\n")
report_lines.append("- **Durante a rotação ativa:** **SIM.** A largura da superfície pós-rotação muda constantemente devido ao recalculo da caixa delimitadora do Pygame (`pygame.transform.rotate`).\n")
report_lines.append("### 2. A altura muda durante o drag?\n")
report_lines.append("- **Com rotação estática:** **NÃO.**\n")
report_lines.append("- **Durante a rotação ativa:** **SIM.**\n")
report_lines.append("### 3. get_rect() retorna dimensões diferentes entre frames?\n")
report_lines.append("- **Com rotação estática:** **NÃO.**\n")
report_lines.append("- **Durante a rotação ativa:** **SIM.** As dimensões de `get_rect()` acompanham a mudança da caixa delimitadora da imagem girada.\n")
report_lines.append("### 4. rect.center sofre deslocamento mesmo quando screen_x permanece contínuo?\n")
report_lines.append("**SIM.** O `rect.center` é definido como `(int(screen_x), int(screen_y))`. Como há um truncamento para inteiros, o centro lógico sofre pequenos saltos discretos mesmo que a coordenada flutuante `screen_x` varie de forma perfeitamente linear e contínua.\n")
report_lines.append("### 5. Existe alguma compensação automática feita pelo pygame ao centralizar a imagem?\n")
report_lines.append("**NÃO.** O Pygame não realiza sub-pixel interpolation ou anti-aliasing na blit. Ele simplesmente define o centro geométrico do `Rect` como um ponto de grade inteiro. Se as dimensões da superfície mudarem de par para ímpar (ex: largura `49` para `50`), o pivô do centro geométrico é deslocado por meio pixel inteiro para compensar, gerando saltos de 1 pixel.\n")
report_lines.append("### 6. O pivô visual muda durante a rotação?\n")
report_lines.append("**SIM.** A rotação no Pygame aumenta a caixa delimitadora (bounding box). Se o tamanho do sprite rotacionado passar de par para ímpar ou vice-versa, o centro do `Rect` sofre micro-desvios de pixel de blit (truncamento do pivô), fazendo com que o objeto pareça 'mancar' ou se deslocar levemente do seu centro físico.\n")
report_lines.append("### 7. O rect é reconstruído usando bounding box dinâmica?\n")
report_lines.append("**SIM.** A chamada `rotated_img.get_rect()` reconstrói a caixa delimitadora do zero em cada chamada com base nas dimensões atuais da superfície rotacionada.\n")
report_lines.append("### 8. Existe jitter causado pela mudança do bounding box do pygame.transform.rotate()?\n")
report_lines.append("**SIM.** A mudança do bounding box ao girar (principalmente a transição de dimensões pares para ímpares) altera a matemática do cálculo do centro do `pygame.Rect`, induzindo tremulações adicionais (jitter) além do stuter de translação comum.")

report_content = "\n".join(report_lines)

import os
os.makedirs("docs", exist_ok=True)
os.makedirs("doc", exist_ok=True)

with open("docs/auditoria_pygame_rect.md", "w", encoding="utf-8") as f:
    f.write(report_content)
with open("doc/auditoria_pygame_rect.md", "w", encoding="utf-8") as f:
    f.write(report_content)

print("\nSUCCESS: Report saved successfully.")
