# Relatorio de Auditoria: SpriteRenderer (Pygame) vs Overlay Qt

Gerado em: 2026-07-11 14:21:00

## 1. Cadeia de Conversão do QPixmap

```
pygame.Surface (Imagem original do sprite)
       ↓
pygame.image.tostring(surface, "RGBA") (Converte em bytes brutos na RAM)
       ↓
QImage(raw, w, h, w * 4, QImage.Format_RGBA8888) (Encapsula buffer em formato Qt)
       ↓
QPixmap.fromImage(qimg) (Upload dos pixels da RAM para a GPU/Textura Qt)
       ↓
painter.drawPixmap(local_rect, pixmap) (Renderização acelerada por GPU)
```

---

## 2. Configuracoes de Qualidade de Imagem (Hints)

No experimento e no patch de overlay do Qt, são configurados:
*   **`painter.setRenderHint(QPainter.Antialiasing, True)`** &rarr; Habilita anti-aliasing na rotação e contorno do retângulo.
*   *Nota:* O `QPainter` aplica por padrão interpolação linear (`SmoothPixmapTransform`) caso o pixmap seja rotacionado ou escalonado com antialiasing ativado no widget OpenGL.

---

## 3. Estruturas Utilizadas no Desenho

*   O `drawPixmap` utiliza **`QRectF`** (especificação de retângulo em ponto flutuante de precisão simples) para o retângulo local do Sprite:
    `local_rect = QRectF(-w / 2.0, -h / 2.0, w, h)`
*   A translação da origem do painter utiliza floats nativos do C++:
    `painter.translate(float(cx), float(cy))`

---

## 4. Analise de Arredondamento e Fracao

*   **Existe arredondamento no caminho do Qt?**
    **NÃO.** Não é executado nenhum `int()`, `round()`, `floor()` ou `ceil()` sobre as coordenadas decimais no pipeline do Qt. As coordenadas são passadas diretamente como `float`.
*   **A posição do Qt possui parte decimal?**
    **SIM.** As coordenadas de desenho do painter possuem parte decimal (ex: `400.30`, `400.60`, `400.90`), fazendo com que o pixel seja rasterizado na posição sub-pixel correspondente na tela.

---

## 5. Comparativo de Posicoes (Exemplo Pratico)

| Etapa / Posição | Valor no Frame 1 | Valor no Frame 2 | Valor no Frame 3 |
| :--- | :---: | :---: | :---: |
| **`screen_x` (float)** | `400.3000` | `400.6000` | `400.9000` |
| **Enviada ao `drawPixmap`** | `400.3000` | `400.6000` | `400.9000` |
| **Enviada ao `pygame.blit`** | `400.0000` | `400.0000` | `400.0000` |

---

## 6. Comparativo de Pipelines de Processamento

| Característica | SpriteRenderer (Pygame Legado) | Overlay Qt (QPainter Moderno) |
| :--- | :--- | :--- |
| **Espaço de Coordenadas** | Grade inteira de pixels (`int`) | Coordenadas fracionárias contínuas (`float`) |
| **Transformações de Escala** | `pygame.transform.scale` (Software, CPU) | OpenGL Scaling (Hardware, GPU) |
| **Transformações de Rotação** | `pygame.transform.rotate` (Software, CPU) | `painter.rotate` (Matriz 3x3 na GPU) |
| **Modificação de Bounding Box** | Dinâmica a cada ângulo (CPU altera tamanho da Surface) | Estática (GPU apenas rotaciona a malha 2D) |
| **Fração de Sub-pixel (Jitter)** | Ignorada (quantiza para o pixel inferior) | Preservada via interpolação de fragmentos |
| **Gargalo / Snap** | **Presente** (deslocamentos discretos em degraus) | **Inexistente** (deslocamento contínuo) |
| **Interpolação de Cor** | Padrão Nearest Neighbor (pixelizado) | Bilinear / Trilinear automática (suave) |
