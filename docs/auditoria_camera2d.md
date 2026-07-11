# Relatorio de Auditoria: Componente Camera2D

Gerado em: 2026-07-11 13:31:17

## 1. Posição da Câmera Durante o Drag

*   La posição da câmera (`Camera2D.transform.position`) é representada por um array unidimensional do NumPy (`np.ndarray`) com tipo de dados `float32`.
*   **A posição da câmera possui parte fracionária?** **SIM.** Ela armazena posições contínuas de alta precisão (exemplo: `[12.456, -34.789]`) sem sofrer nenhum tipo de quantização ou truncamento em sua estrutura lógica.

---

## 2. Implementação das Funções de Conversão

Definidas em [`engine/graphics/camera2d.py`](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/engine/graphics/camera2d.py):

### `world_to_screen`
```python
    def world_to_screen(self, world_pos: np.ndarray, screen_width: int, screen_height: int) -> Tuple[float, float]:
        """Converte uma coordenada do espaço de mundo [x, y] para pixels na tela [px, py]."""
        cam_pos = self.transform.position
        screen_x = (world_pos[0] - cam_pos[0]) * self.zoom + (screen_width / 2.0)
        screen_y = (world_pos[1] - cam_pos[1]) * self.zoom + (screen_height / 2.0)
        return screen_x, screen_y
```
*   **Retorno:** Retorna tuplas de floats puros (`screen_x`, `screen_y`), preservando toda a precisão decimal.

### `screen_to_world`
```python
    def screen_to_world(self, screen_pos: Tuple[float, float], screen_width: int, screen_height: int) -> Tuple[float, float]:
        """Converte coordenadas de pixels de tela de volta para o espaço de mundo."""
        cam_pos = self.transform.position
        world_x = (screen_pos[0] - (screen_width / 2.0)) / self.zoom + cam_pos[0]
        world_y = (screen_pos[1] - (screen_height / 2.0)) / self.zoom + cam_pos[1]
        return world_x, world_y
```
*   **Retorno:** Retorna floats puros (`world_x`, `world_y`), mantendo a precisão flutuante nas conversões de entrada de mouse.

---

## 3. Presença de Funções de Conversão / Arredondamento

Analisei toda a extensão do arquivo [`engine/graphics/camera2d.py`](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/engine/graphics/camera2d.py):

*   `int()`: **Não ocorre**
*   `round()`: **Não ocorre**
*   `floor()`: **Não ocorre**
*   `ceil()`: **Não ocorre**
*   `QPoint`: **Não ocorre** (não importa nem consome tipos do PySide/Qt)
*   `QRect`: **Não ocorre**
*   `pygame.Rect`: **Não ocorre**

---

## 4. Conclusão da Auditoria da Câmera

A classe `Camera2D` trabalha de forma 100% linear em ponto flutuante e **não é a responsável** por introduzir nenhuma perda de precisão ou efeito de snap nos objetos da viewport.
