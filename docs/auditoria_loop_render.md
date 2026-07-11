# Relatorio de Auditoria: Loop de Renderizacao e Concorrencia de Timers

Gerado em: 2026-07-11 13:10:54

## 1. Mapeamento das Chamadas

### 1. Quem chama `QWidget.update()`
1.  **`Phase1ViewportWidget._tick(self)`** ([phase1_viewport.py:L715](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/widgets/phase1_viewport.py#L715)) - Chamado a cada 16ms pelo `QTimer`.
2.  **`_emit_transform_changed(viewport, obj)`** ([viewport_transform_stability_patch.py:L128](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/runtime/viewport_transform_stability_patch.py#L128)) - Chamado no drag (move e scale).
3.  **`Phase1ViewportWidget.mousePressEvent`** (no patch de estabilidade) - Chamado ao selecionar objeto no clique.
4.  **`coalesced_widget_update(self)`** (no patch de estabilidade) - Delega para o `QWidget.update(self)` original do Qt.
5.  **`Phase1ViewportWidget.resizeGL`** ([viewport_widget.py:L249](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/widgets/viewport_widget.py#L249)).

### 2. Quem chama `repaint()`
*   Ninguém no fluxo do drag (chamado apenas de forma isolada em `asset_direct_drop_patch.py` ao soltar arquivos).

### 3. Quem chama `paintGL()`
*   Chamado exclusivamente pelo **C++ interno do QOpenGLWidget** em resposta a eventos de pintura (`QPaintEvent`) agendados pelo ciclo de eventos do Qt.

---

## 2. Respostas às Perguntas de Controle

### 4. Existe algum `QTimer` chamando `update()` continuamente?
*   **SIM.** `self._timer = QTimer(self)` é criado no construtor da viewport ([viewport_widget.py:L77](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/widgets/viewport_widget.py#L77)) e roda a cada 16ms (60 FPS) chamando `_tick()`, que dispara `self.update()`.

### 5. Existe algum timer rodando a 0 ms?
*   **NÃO.** Todos os QTimers de viewport/profiler rodam com intervalos explicitamente configurados (16ms ou 100ms).

### 6. Durante UM MouseMove, quantos `paintGL` acontecem?
*   **No máximo 1.** O evento de mouse solicita o `update()`, que é enfileirado e coalescido pelo Qt.

### 7. Durante UM paintGL, quantos MouseMove aconteceram?
*   **Pode ser 1, zero ou múltiplos.** Depende inteiramente da velocidade do mouse em relação à taxa de atualização do event loop.

### 8. Existe algum `paintGL` acontecendo sem mudança de Transform?
*   **SIM.** O `QTimer` de 16ms continua chamando `_tick` &rarr; `update` &rarr; `paintGL` mesmo se o mouse estiver imóvel e o objeto parado.

### 9. Existe algum `update()` sendo disparado pelo renderizador?
*   **NÃO.** O método `paintGL` não possui chamadas recursivas para `update()`.

---

## 3. Call Graph Completo (Múltiplas Fontes de Paint)

```
MouseMove Event (OS)
    ↓
mouseMoveEvent() -> _update_move_drag()
    ↓
viewport.update()  (Solicita repaint)
    ↓
 [Qt Event Loop] ──────┐
                       ├─→ paintGL() ──→ LegacySceneAdapter.draw()
 [Qt Event Loop] ──────┘
    ↑
viewport.update()  (Solicita repaint)
    ↑
_tick()
    ↑
QTimer (Timeout a cada 16ms)
```

---

## 4. Conclusão da Auditoria

Existe renderização desacoplada do input?
**SIM**
