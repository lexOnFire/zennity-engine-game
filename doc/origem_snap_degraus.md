# Relatorio de Origem do Movimento em Degraus (Quantizacao de Coordenadas)

Gerado em: 2026-07-11 12:59:17

## 1. Quem recebe o MouseMove
O evento de arraste é disparado pelo sistema operacional, capturado pelo loop de eventos do Qt e repassado para:
*   **Arquivo:** [phase1_viewport.py](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/widgets/phase1_viewport.py#L629)
*   **Classe:** `Phase1ViewportWidget`
*   **Método:** `mouseMoveEvent(self, event: QMouseEvent)`
*(Nota: interceptado no patch de estabilidade pelo método `mouse_move_event`)*

---

## 2. Quem converte as coordenadas (Mapeamento Completo)

As conversões ocorrem nos seguintes pontos do pipeline de drag:

*   **`viewport_to_world()`** (Mapeia coordenadas de pixels em tela para unidades do mundo):
    *   [viewport_transform_stability_patch.py:L266](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/runtime/viewport_transform_stability_patch.py#L266) (Chama `self.viewport_to_world` ao arrastar).
    *   [viewport_transform_stability_patch.py:L287](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/runtime/viewport_transform_stability_patch.py#L287) (Chama `self.viewport_to_world` no clique inicial).
*   **`world_to_viewport()`** (Mapeia unidades do mundo de volta para pixels de tela para desenhar o Gizmo):
    *   [viewport_transform_stability_patch.py:L48](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/runtime/viewport_transform_stability_patch.py#L48) (Referência inicial do Gizmo).
    *   [viewport_transform_stability_patch.py:L62](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/runtime/viewport_transform_stability_patch.py#L62) (Bloqueio do eixo de movimento).
    *   [viewport_transform_stability_patch.py:L237](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/runtime/viewport_transform_stability_patch.py#L237) (Posição do Gizmo de Escala no `paintGL`).
*   **`screen_to_world()` / `world_to_screen()`**:
    *   Chamadas indiretas através dos aliases definidos em [viewport_camera.py:L102-103](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/viewport/viewport_camera.py#L102-103), onde `world_to_viewport` aponta para `world_to_screen` e `viewport_to_world` aponta para `screen_to_world`.

---

## 3. Onde a posição é modificada no Drag

A posição do objeto é modificada em apenas um ponto no pipeline do drag de movimentação:
*   **Arquivo:** [viewport_transform_stability_patch.py:L276-277](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/runtime/viewport_transform_stability_patch.py#L276-277)
*   **Atribuições:**
    ```python
    obj.transform.position[0] = float(next_position[0])
    obj.transform.position[1] = float(next_position[1])
    ```
*   **Quem chama:** `update_move_drag(self, x, y)` (disparado pelo `mouseMoveEvent`).

---

## 4. Localização de Quantizações de Coordenadas

1.  **Quantização do Mouse do Qt (A ORIGEM DO BUG):**
    *   [phase1_viewport.py:L637](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/widgets/phase1_viewport.py#L637):
        `x, y = float(event.x()), float(event.y())`
    *   [viewport_transform_stability_patch.py:L198](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/runtime/viewport_transform_stability_patch.py#L198):
        `x, y = float(event.x()), float(event.y())`
    *   **Contexto:** No PySide6, chamar `event.x()` and `event.y()` retorna coordenadas **inteiras truncadas**. Ao ler esses inteiros e convertê-los para o espaço do mundo usando `viewport_to_world`, a posição do objeto perde qualquer precisão sub-pixel e salta em degraus proporcionais a $1 / \text{zoom}$.
2.  **Grid Snap Arredondamento:**
    *   [phase1_viewport.py:L125-126](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/widgets/phase1_viewport.py#L125-L126):
        `snapped[0] = round(float(snapped[0]) / snap) * snap`
    *   **Contexto:** Arredonda a posição para múltiplos de `snap_size` quando o snap está ativado.
3.  **Collider Width/Height (Casting para Int):**
    *   [viewport_transform_stability_patch.py:L106](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/runtime/viewport_transform_stability_patch.py#L106):
        `box.width = max(1, int(abs(float(scale[0]))))`
    *   **Contexto:** Sincroniza a caixa de colisão truncando a escala para inteiros.

---

## 5. Verificação do Grid Snap

*   **O Grid Snap é consultado durante o drag?** Sim.
*   **Mesmo desligado?** Sim, a função `_apply_snap` é chamada a cada frame de arraste, mas retorna a posição original sem modificações se `_snap_enabled()` for `False` ([phase1_viewport.py:L121](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/widgets/phase1_viewport.py#L121)).
*   **Existe algum fallback usando grid_size?** Não. O snap é calculado apenas a partir de `self.editor_state.snap_size` (que possui fallback interno de `1.0` caso `editor_state` seja None).
*   **Existe arredondamento para múltiplos de grid_size?** Não.

---

## 6. Verificação de Conversões C++ / QPoint

*   **Existe conversão `QPointF` &rarr; `QPoint` ou `float` &rarr; `int` antes de aplicar ao Transform?**
    *   **SIM.** As chamadas a `event.x()` e `event.y()` descartam sub-pixels antes de passar as coordenadas `x, y` para o `viewport_to_world`. O correto para obter movimento contínuo de alta precisão (sem degraus) é utilizar modernamente `event.position().x()` e `event.position().y()`, que expõem valores float reais (`QPointF`).

---

## 7. Múltiplas Escritas no Mesmo Frame

*   **Durante um único MouseMove, `transform.position` recebe valor quantas vezes?**
    *   **Apenas 1 vez.**
    *   **Fluxo:**
        1.  `mouseMoveEvent` intercepta a coordenada inteira `(x, y)`.
        2.  Calcula a diferença em relação à posição inicial.
        3.  Grava uma única vez em `obj.transform.position[0]` e `[1]`.
        4.  Dispara o `paintGL` coalescido.

---

## 8. Verificação de Sobrescrita Posterior

*   **Alguma outra rotina (Gizmo, SelectionManager, etc.) sobrescreve a posição depois de aplicada?**
    *   **NÃO.** Nenhuma outra rotina altera `transform.position` no frame. O valor gravado pelo drag permanece intocado até o próximo evento de mouse.

---

## 9. Call Graph Completo (Do Input ao Desenho)

```
MouseMove Event (OS)
    ↓
QApplication Event Loop
    ↓
Phase1ViewportWidget.mouseMoveEvent(event)
    [x, y = float(event.x()), float(event.y())]  <-- QUANTISED HERE! (Discard sub-pixels)
    ↓
Phase1ViewportWidget._update_move_drag(x, y)
    ↓
Phase1ViewportWidget.viewport_to_world((x, y))
    ↓
Camera2D.screen_to_world((x, y))
    ↓
next_position = start_position + delta
    ↓
next_position = _apply_snap(next_position)  [If disabled, return next_position]
    ↓
obj.transform.position[0] = float(next_position[0])
obj.transform.position[1] = float(next_position[1])
    ↓
_emit_transform_changed(viewport, obj)
    ↓
viewport.update() (Coalesced / QWidget.update)
    ↓
paintGL()
    ↓
LegacySceneAdapter.draw() / SpriteRenderer.draw()
    ↓
pygame.image.tostring() -> QImage -> QPainter.drawImage()
```
