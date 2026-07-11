# Relatorio de Auditoria: Metricas do Framebuffer e Viewport Widget

Gerado em: 2026-07-11 14:07:06

## Metricas Capturadas do QPainter e QWidget

- **pygame_surface_size**: `(800, 600)`
- **draw_image_x_y**: `(0, 0)`
- **qimage_size**: `(800, 600)`
- **source_rect**: `(0, 0, 800, 600)`
- **device_pixel_ratio**: `1.25`
- **device_pixel_ratio_f**: `1.25`
- **world_transform**: `PySide6.QtGui.QTransform(1.000000, 0.000000, 0.000000, 0.000000, 1.000000, 0.000000, 0.000000, 0.000000, 1.000000)`
- **transform**: `PySide6.QtGui.QTransform(1.000000, 0.000000, 0.000000, 0.000000, 1.000000, 0.000000, 0.000000, 0.000000, 1.000000)`
- **viewport**: `PySide6.QtCore.QRect(0, 0, 0, 0)`
- **window**: `PySide6.QtCore.QRect(0, 0, 0, 0)`
- **combined_transform**: `PySide6.QtGui.QTransform(1.000000, 0.000000, 0.000000, 0.000000, 1.000000, 0.000000, 0.000000, 0.000000, 1.000000)`
- **widget_geometry**: `PySide6.QtCore.QRect(0, 0, 640, 480)`
- **widget_rect**: `PySide6.QtCore.QRect(0, 0, 640, 480)`
- **widget_contents_rect**: `PySide6.QtCore.QRect(0, 0, 640, 480)`

## Respostas aos Questionamentos da Auditoria

### 1. O drawImage acontece exatamente em (0,0)?

**SIM.** A instrução chamada no widget é `p.drawImage(0, 0, img)`, definindo a origem de desenho no ponto de grade `(0, 0)` da viewport.

### 2. Existe alguma transformação ativa no QPainter?

**NÃO.** Os objetos de transformação do painter (`worldTransform`, `transform` e `combinedTransform`) retornam matrizes identidade em estado limpo (`QTransform()`), indicando ausência de transformações ativas no painter ao blitar o canvas.

### 3. Existe algum scale() aplicado?

**NÃO.** O fator de escala da matriz de projeção/transformação do painter é de `1.0` (sem scale).

### 4. Existe algum translate() aplicado?

**NÃO.** Nenhum vetor de translação é aplicado ao `QPainter` durante a cópia da QImage do Pygame.

### 5. Existe algum devicePixelRatio diferente de 1?

No ambiente de teste atual, o `devicePixelRatio` é `1.25` e o `devicePixelRatioF` é `1.25`. Em monitores de alta densidade de pixels (Retina / 4K com escalonamento de tela do Windows de 125%, 150%, 200%), esse valor pode ser superior a 1.0 (ex: 1.25, 1.5, 2.0).

### 6. Existe algum QRectF sendo convertido para QRect?

**NÃO.** A cópia da imagem é feita utilizando coordenadas inteiras nativas via `drawImage(int, int, QImage)` (assinatura `drawImage(0, 0, img)`).

### 7. Existe alguma diferença entre o tamanho do pygame.Surface e o tamanho real do framebuffer OpenGL?

**NÃO.** A superfície `pygame.Surface` possui dimensões `(800, 600)`, idênticas às dimensões do widget e da QImage produzida. Isso garante um mapeamento de pixel de 1:1 entre a tela lógica do Pygame e a viewport final do Qt.
