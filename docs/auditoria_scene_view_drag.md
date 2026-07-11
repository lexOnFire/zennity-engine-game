# Auditoria Técnica: Desempenho da Scene View no Editor Phase1

Este documento apresenta a análise técnica detalhada do pipeline de atualização da **Scene View** durante operações de arraste (drag) no editor Phase1. O objetivo é mapear o fluxo de execução, identificar possíveis gargalos e classificar cada etapa de acordo com sua frequência e custo de processamento.

---

## 1. Mapeamento do Pipeline de Arraste (Drag)

Abaixo está o fluxo sequencial detalhado executado a cada movimento do mouse (`MouseMove`) durante a edição de um objeto:

```mermaid
flowchart TD
    A[MouseMove (OS Input)] --> B[ViewportWidget.mouseMoveEvent]
    B --> C[ToolManager (Verifica Ferramenta / Snap / Locks)]
    C --> D[Transform (Atualiza coordenadas em tempo real)]
    D --> E[Gizmo (Sincroniza Collider / Desenha no paintGL)]
    E --> F[QWidget.update / viewport.update (Agenda Repaint)]
    F --> G[paintGL (Chamado pelo ciclo do Qt)]
    G --> H[LegacySceneAdapter (Renderiza a cena Pygame)]
    H --> I[SpriteRenderer (Desenha cada Sprite no Pygame)]
    I --> J[pygame.Surface (Cópia da GPU para RAM via tostring)]
    J --> K[QPainter (Cria QImage e desenha na tela via OpenGL)]
```

---

## 2. Análise Detalhada das Etapas

### 1. MouseMove (OS Input)
*   **Frequência por frame:** Várias (depende da taxa de pooling do mouse do usuário, de 125Hz a 1000Hz).
*   **Custo provável:** Baixo no nível do SO, mas alto em Python se processado sem limites.
*   **Alocação:** Não (SO).
*   **Chamadas repetidas:** Sim.
*   **Outros impactos:** Nenhum.
*   **Classificação:** **C** (Executa durante todo o MouseMove).

### 2. ViewportWidget.mouseMoveEvent()
*   **Frequência por frame:** Várias (1 por evento do mouse).
*   **Custo provável:** Baixo.
*   **Alocação:** Sim (tupla de coordenadas `x, y` convertida para `float`).
*   **Chamadas repetidas:** Sim.
*   **Outros impactos:** Delega para o método de arraste específico (`_update_move_drag`).
*   **Classificação:** **C** (Executa durante todo o MouseMove).

### 3. ToolManager
*   **Frequência por frame:** Várias (1 por evento do mouse).
*   **Custo provável:** Baixo.
*   **Alocação:** Não.
*   **Chamadas repetidas:** Não.
*   **Outros impactos:** Valida o estado atual das ferramentas (`EditorTool.MOVE`, etc.).
*   **Classificação:** **C** (Executa durante todo o MouseMove).

### 4. SelectionManager
*   **Frequência por frame:** 1 por Frame (via `_tick`).
*   **Custo provável:** Baixo durante o drag (a seleção não muda durante o arraste).
*   **Alocação:** Não.
*   **Chamadas repetidas:** Não.
*   **Outros impactos:** Executa a sincronização `_sync_selection_to_model` apenas quando o QTimer de 16ms dispara.
*   **Classificação:** **A** (Executa uma vez por frame).

### 5. Gizmo
*   **Frequência por frame:** Várias (atualiza colisor no move e recalcula posições dos handles no repaint).
*   **Custo provável:** Médio.
*   **Alocação:** Sim (cria listas de coordenadas de tela, tuplas de retângulos/círculos para desenho).
*   **Chamadas repetidas:** Sim (a cada chamada de `_emit_transform_changed` e `paintGL`).
*   **Outros impactos:** Faz lookups de componentes e atualizações matemáticas.
*   **Classificação:** **C** (Executa durante todo o MouseMove).

### 6. Transform
*   **Frequência por frame:** Várias (1 por evento do mouse).
*   **Custo provável:** Baixo.
*   **Alocação:** Sim (arrays do Numpy para a nova posição temporária e snap).
*   **Chamadas repetidas:** Sim.
*   **Outros impactos:** Modifica diretamente a posição do objeto selecionado (`obj.transform.position`).
*   **Classificação:** **C** (Executa durante todo o MouseMove).

### 7. CommandManager
*   **Frequência por frame:** Zero durante o arraste. Executa **uma única vez** no `_end_move_drag` (quando solta o botão do mouse).
*   **Custo provável:** Baixo.
*   **Alocação:** Sim (instancia um `FunctionCommand` e cria closures de `_do` e `_undo`).
*   **Chamadas repetidas:** Não.
*   **Classificação:** **A** (Executa uma vez no fim do arraste).

### 8. LegacySceneAdapter
*   **Frequência por frame:** 1 por Repaint (uma vez por frame renderizado).
*   **Custo provável:** Médio.
*   **Alocação:** Não.
*   **Chamadas repetidas:** Não.
*   **Outros impactos:** Varre os objetos da cena.
*   **Classificação:** **A** (Executa uma vez por frame).

### 9. SpriteRenderer
*   **Frequência por frame:** 1 por Repaint para cada objeto que possui o componente.
*   **Custo provável:** Médio/Alto.
*   **Alocação:** Não.
*   **Chamadas repetidas:** Não.
*   **Outros impactos:** Realiza o cálculo de coordenadas de mundo para coordenadas de tela (`world_to_screen`) com base na câmera e renderiza na superfície de desenho.
*   **Classificação:** **A** (Executa uma vez por frame).

### 10. paintGL
*   **Frequência por frame:** 1 por Repaint.
*   **Custo provável:** Muito Alto.
*   **Alocação:** **Sim** (cria um buffer de bytes gigante via `pygame.image.tostring()` e instancia a classe `QImage` a cada frame).
*   **Chamadas repetidas:** Não (agendado pelo ciclo de eventos do Qt).
*   **Classificação:** **A** (Executa uma vez por frame renderizado).

### 11. QPainter
*   **Frequência por frame:** 1 por Repaint.
*   **Custo provável:** Médio.
*   **Alocação:** Sim (instancia o `QPainter(self)`).
*   **Chamadas repetidas:** Não.
*   **Outros impactos:** Realiza o blit final da `QImage` no widget OpenGL do Qt.
*   **Classificação:** **A** (Executa uma vez por frame).

### 12. pygame.Surface
*   **Frequência por frame:** 1 por Repaint por objeto desenhado.
*   **Custo provável:** Baixo/Médio (renderização nativa em C do SDL).
*   **Alocação:** Não (reutiliza a superfície interna e as texturas das imagens carregadas).
*   **Classificação:** **A** (Executa uma vez por frame).

### 13. QWidget.update() / viewport.update()
*   **Frequência por frame:** Várias antes do throttle (uma por evento do mouse); agora limitada a 1 por frame (60 FPS) devido ao limitador de tempo.
*   **Custo provável:** Baixo (apenas agenda um evento de pintura no loop do Qt), mas seu efeito colateral (chamar `paintGL`) é extremamente caro.
*   **Classificação:** **C** (Invocado durante o MouseMove).

---

## 3. Respostas às Questões Específicas

| Pergunta | Componente Responsável | Frequência / Gatilho |
| :--- | :--- | :--- |
| **1) Quem chama QWidget.update()?** | 1. `ViewportWidget._tick()` (QTimer a cada 16ms)<br>2. `_emit_transform_changed` (a cada MouseMove) | **60 FPS** pelo timer + **taxa do mouse** durante o arraste. |
| **2) Quem chama repaint()?** | `asset_direct_drop_patch.py` | Apenas ao arrastar um asset diretamente para a viewport. **Nunca no drag de objeto**. |
| **3) Quem chama processEvents()?** | Apenas arquivos de **testes unitários** (`test_*.py`) | **Zero** durante a execução real da engine. |
| **4) Quem chama viewport.update()?** | Mesmos de `QWidget.update()`. | Equivalente ao item 1. |
| **5) Quem chama paintGL()?** | Loop interno de eventos visuais do **PySide6** | Chamado automaticamente após pedidos de `update()` ou `repaint()`. |
| **6) Quem chama SpriteRenderer.draw()?** | `Scene.draw()` via `LegacySceneAdapter.draw()` | **Uma vez por frame** por objeto visível. |
| **7) Quem chama LegacySceneAdapter.draw()?** | `ViewportWidget.paintGL()` | **Uma vez por frame** no render loop da Scene View. |
| **8) Quem chama SceneViewModel.refresh()?** | **Código Morto / Inexistente** | Não é chamado (o método não existe no ViewModel). |
| **9) Quem chama hierarchy_changed()?** | **Código Morto / Inexistente** | Não é chamado (o sinal correto é `hierarchy_updated` ou `object_structure_changed`). |
| **10) Quem chama inspector.refresh()?** | **Código Morto / Inexistente** | Não existe (o método correto é `inspector.load_object()`). |

---

## 4. Classificação das Operações no Drag

*   **Recria QImage:** **Sim (C)** — A cada frame em `paintGL()`.
*   **Recria QPixmap:** **Não (D)** — A renderização desenha a `QImage` diretamente via `QPainter.drawImage`, sem converter para `QPixmap`.
*   **Chama pygame.transform.scale() / rotate():** **Não (D)** — A escala e rotação são tratadas na renderização do `SpriteRenderer` calculando a área de desenho final do retângulo ou delegando para a conversão de matrizes, sem recriar superfícies rotacionadas a cada movimento.
*   **Faz lookup de componentes:** **Sim (C)** — A cada movimento do mouse via `_sync_collider_size` que faz lookups de `BoxCollider` e `CircleCollider`.
*   **Faz de sinais Qt:** **Sim (C)** — O sinal `object_transform_changed` é emitido a cada movimento do mouse.
*   **Faz refresh do Outliner (Hierarchy):** **Não (A)** — O Outliner não reconstrói sua árvore durante o drag; apenas atualiza o item quando a seleção muda.
*   **Faz refresh do Inspector / Property Grid:** **Não (A)** — Graças à nossa última alteração, a atualização pesada do Inspector foi adiada para ocorrer **apenas no término do arraste** (quando o botão do mouse é solto).
*   **Recalcula gizmos:** **Sim (C)** — A posição dos manipuladores e colisores é recalculada a cada frame de desenho.
*   **Sincroniza SelectionManager / RuntimeManager:** **Sim (A)** — Sincroniza via `_sync_selection_to_model` no timer síncrono de 16ms do `_tick()`.

---

## 5. TOP 10 Gargalos Técnicos Mais Prováveis (Ordenados por Impacto)

1.  **`pygame.image.tostring(..., "RGBA")` (PaintGL):**
    *   *Impacto:* **Crítico**. Transfere megabytes de dados de pixel da memória de vídeo/SDL para a memória RAM do sistema em Python a cada renderização. É o maior limitador de desempenho gráfico da integração Pygame-PySide.
2.  **Alocação de nova `QImage` com dados brutos (PaintGL):**
    *   *Impacto:* **Muito Alto**. Instancia uma nova estrutura de imagem C++ no PySide a cada frame de pintura, gerando lixo na memória RAM e chamadas frequentes ao Garbage Collector do Python.
3.  **Uso de `QPainter` para desenhar a imagem (PaintGL):**
    *   *Impacto:* **Alto**. A pintura da `QImage` via software em cima da tela do `QOpenGLWidget` quebra a aceleração de hardware nativa do OpenGL do Qt.
4.  **Lookup de Componentes repetitivos no Drag (`_sync_collider_size`):**
    *   *Impacto:* **Médio/Alto**. A cada pixel movido, a engine busca componentes como `BoxCollider` e `CircleCollider` usando buscas lineares de strings ou tipos, o que consome ciclos de CPU valiosos durante o movimento.
5.  **Criação de novos Arrays Numpy (`Transform`):**
    *   *Impacto:* **Médio**. Toda atualização de posição faz alocação de novos arrays de coordenadas Numpy de 3 dimensões (float32) em Python para calcular deltas e snaps.
6.  **Cálculo repetitivo dos Gizmos de Escala/Movimento (`_scale_handle_positions`):**
    *   *Impacto:* **Médio**. Recalcula as fórmulas matemáticas de projeção de tela de todos os manipuladores e eixos do Gizmo a cada frame de pintura.
7.  **Iteração contínua sobre a lista de `editable_objects`:**
    *   *Impacto:* **Médio/Baixo**. Durante o desenho e o processamento de cliques, a Scene View varre a lista inteira de objetos editáveis sequencialmente. Em cenas populosas, isso cresce de forma linear (\(O(N)\)).
8.  **Cálculo inútil do Zoom Suave da Câmera no Repaint:**
    *   *Impacto:* **Baixo**. A cada frame, `self.camera.update(dt)` é chamado para atualizar a interpolação suave do zoom, recalculando limites mesmo quando o usuário não está alterando o zoom.
9.  **Alocação de Comando de Histórico (`FunctionCommand`):**
    *   *Impacto:* **Baixo** (ocorre apenas no fim do arraste). Cria as closures necessárias para guardar os estados de `Undo` e `Redo`.
10. **Sincronização de Seleção do Viewmodel (`_sync_selection_to_model`):**
    *   *Impacto:* **Muito Baixo**. Executa buscas de índices apenas a cada 16ms no timer de tick.
