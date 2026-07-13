# Relatório — infraestrutura do Render Pipeline da Scene View

## Escopo

Foi criada apenas a infraestrutura de orquestração. Nenhum renderizador foi
reescrito, nenhuma otimização foi aplicada e o caminho legado permanece ativo.

## Responsabilidades movidas

- Ordenação e habilitação de etapas: `RenderPipeline`.
- Contrato compartilhado do frame: `RenderContext`.
- Fronteira do desenho legado: `LegacySceneAdapter` e `LegacyScenePass`.
- Chamada do `GridRenderer.draw()`: `GridPass`.
- Pontos de extensão formais para fundo, sprites modernos, gizmos e overlays.
- Apresentação do framebuffer Pygame foi extraída do `paintGL()` base para um
  helper reutilizável com o mesmo `QPainter` da pipeline.
- `FramebufferPresentPass` tornou explícito o ponto em que o framebuffer
  Pygame concluído é copiado para o Qt.
- Gizmos registrados de componentes foram movidos para `GizmoPass`, que agora
  delega para `GizmoRegistry.draw()` antes da apresentação do framebuffer.
- Selection outline e bounding box agora são unidades explícitas do
  `OverlayPass`, separadas do desenho de HUD e coordenadas.
- Gizmos Qt de Move e Rotate foram movidos para `TransformGizmoPass`, executado
  depois do `OverlayPass` para preservar sua sobreposição visual histórica.
- Cor de limpeza e fundos infinitos agora são desenhados pelo `BackgroundPass`;
  `LegacyScenePass` recebe apenas o conteúdo das cenas que suportam separação.
- `SpriteOverlayPass` agora desenha componentes `Image` válidos na Scene View
  com o transform da câmera Qt; somente esses componentes são omitidos no
  framebuffer legado durante o mesmo frame.
- O passe de sprites é executado antes do `GridPass`, conservando a grade acima
  da imagem como acontecia quando ela integrava o framebuffer Pygame.
- Adaptadores distintos agora aceitam `Image`, `engine.graphics.renderer` e
  `engine.graphics.renderer2d`, preservando as regras atuais de escala, rotação,
  alpha e flip de cada implementação.
- `SpriteDrawCommand` normaliza sorting layer, order, tint, alpha e flip sem
  ativar semânticas que ainda divergem entre os renderizadores legados.
- Scene View e Play Mode agora compartilham `engine.graphics.sorting`, com
  camadas `Background`, `Midground`, `Default`, `Foreground` e `UI`, seguidas
  por `Order in Layer` e pela ordem original como desempate estável.
- Tint RGB multiplicativo e alpha combinado agora usam o contrato comum
  `engine.graphics.tint` no Qt, `Image` e nos dois `SpriteRenderer` Pygame.
- Background, cena legada, grid, gizmos e overlays agora passam por adaptadores
  tipados próprios; a viewport deixou de conter a implementação desses passes.
- `FramePreparationAdapter` assume criação/limpeza do contexto, câmera, grid e
  coleta de sprites; `FramebufferPresentRendererAdapter` assume a apresentação.
- `SpriteRendererAdapter` liga o passe de sprites aos comandos já preparados,
  removendo o último callback de renderização mantido pela viewport.
- `RenderPipeline` oferece métricas opt-in por passe (último, média, máximo e
  execuções), desativadas por padrão e sem alterar a ordem de desenho.
- Preparação do frame e chamadas antigas da Phase1 Viewport foram movidas para
  delegates privados usados pelos passes.

## Redução de `paintGL()`

- `Phase1ViewportWidget.paintGL()`: de 66 para 9 linhas, redução de 57 linhas.
- `ViewportWidget.paintGL()`: de 31 para 8 linhas, redução de 23 linhas.

## Acoplamentos preservados por compatibilidade

- `BackgroundPass` limpa o framebuffer para Scene 2D, Scene 3D e
  `RuntimeScene`, preservando respectivamente `(28, 29, 36)` e o
  `Camera.clear_color`/fallback `(30, 30, 30)`.
- Cenas que sobrescrevem somente `draw()` continuam usando-o integralmente, sem
  perda de compatibilidade.
- Sprites sem arquivo válido, Game View, Play Mode e renderizadores antigos
  continuam usando exclusivamente o framebuffer Pygame.
- `TransformGizmoPass` ainda delega diretamente aos overlays Qt concretos de
  Move e Rotate mantidos pela viewport, agora via `GizmoRendererAdapter`.
- `ViewportRenderer.render_qt_overlays()` permanece como wrapper de
  compatibilidade, delegando para seleção e HUD independentes.
- A captura/restauração da visibilidade do grid ainda depende da estrutura das
  cenas legadas e de `RuntimeScene`.

## Próximos candidatos à migração

1. Expor as métricas opcionais no painel Profiler sem ativá-las por padrão.
