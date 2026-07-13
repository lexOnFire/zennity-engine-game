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
- Preparação do frame e chamadas antigas da Phase1 Viewport foram movidas para
  delegates privados usados pelos passes.

## Redução de `paintGL()`

- `Phase1ViewportWidget.paintGL()`: de 66 para 9 linhas, redução de 57 linhas.
- `ViewportWidget.paintGL()`: de 31 para 8 linhas, redução de 23 linhas.

## Acoplamentos preservados por compatibilidade

- `BackgroundPass` agora limpa o framebuffer para Scene 2D, Scene 3D e
  `RuntimeScene`, preservando respectivamente `(28, 29, 36)` e o
  `Camera.clear_color`/fallback `(30, 30, 30)`.
- Cenas desconhecidas continuam usando `draw()` integral como fallback, sem
  perda de compatibilidade.
- Sprites continuam tendo o framebuffer Pygame como fonte única; o overlay Qt
  moderno permanece desativado para evitar renderização duplicada.
- Gizmos de componentes do `GizmoRegistry` ainda são desenhados pelo caminho
  legado antes da apresentação do framebuffer.
- Gizmos Qt de transformação permanecem junto ao delegate final de overlays
  para conservar sua ordem visual histórica sobre HUD e outlines.
- `ViewportRenderer` continua coordenando selection outline, bounding box e HUD.
- A captura/restauração da visibilidade do grid ainda depende da estrutura das
  cenas legadas e de `RuntimeScene`.

## Próximos candidatos à migração

1. Migrar fundos infinitos, que continuam pertencendo ao conteúdo da cena.
2. Criar uma apresentação explícita do framebuffer para liberar a migração dos
   gizmos de componentes para `GizmoPass` sem mudar a ordem visual.
3. Migrar selection outline e bounding box para unidades independentes do
   `OverlayPass`.
4. Conectar o SpriteRenderer moderno ao `SpriteOverlayPass` somente depois de
   remover, com testes visuais, a fonte equivalente no caminho legado.
5. Substituir os delegates temporários por adapters tipados por componente.
