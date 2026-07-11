# Experimento: Sincronizacao de Rasterizacao (Gizmo Snapped to Integer)

Gerado em: 2026-07-11 13:33:38

## Verificacao das Coordenadas de Tela no Drag

- **Frame 0**: Sprite Center `(400, 420)` | Gizmo Center `(400, 420)` &rarr; **Alinhados**: `True`
- **Frame 1**: Sprite Center `(400, 300)` | Gizmo Center `(400, 300)` &rarr; **Alinhados**: `True`
- **Frame 2**: Sprite Center `(400, 420)` | Gizmo Center `(400, 420)` &rarr; **Alinhados**: `True`
- **Frame 3**: Sprite Center `(400, 300)` | Gizmo Center `(400, 300)` &rarr; **Alinhados**: `True`
- **Frame 4**: Sprite Center `(400, 420)` | Gizmo Center `(400, 420)` &rarr; **Alinhados**: `True`
- **Frame 5**: Sprite Center `(404, 304)` | Gizmo Center `(404, 304)` &rarr; **Alinhados**: `True`
- **Frame 6**: Sprite Center `(400, 420)` | Gizmo Center `(400, 420)` &rarr; **Alinhados**: `True`
- **Frame 7**: Sprite Center `(404, 304)` | Gizmo Center `(404, 304)` &rarr; **Alinhados**: `True`
- **Frame 8**: Sprite Center `(400, 420)` | Gizmo Center `(400, 420)` &rarr; **Alinhados**: `True`
- **Frame 9**: Sprite Center `(408, 308)` | Gizmo Center `(408, 308)` &rarr; **Alinhados**: `True`
- **Frame 10**: Sprite Center `(400, 420)` | Gizmo Center `(400, 420)` &rarr; **Alinhados**: `True`
- **Frame 11**: Sprite Center `(408, 308)` | Gizmo Center `(408, 308)` &rarr; **Alinhados**: `True`
- **Frame 12**: Sprite Center `(400, 420)` | Gizmo Center `(400, 420)` &rarr; **Alinhados**: `True`
- **Frame 13**: Sprite Center `(412, 312)` | Gizmo Center `(412, 312)` &rarr; **Alinhados**: `True`
- **Frame 14**: Sprite Center `(400, 420)` | Gizmo Center `(400, 420)` &rarr; **Alinhados**: `True`
- **Frame 15**: Sprite Center `(412, 312)` | Gizmo Center `(412, 312)` &rarr; **Alinhados**: `True`
- **Frame 16**: Sprite Center `(400, 420)` | Gizmo Center `(400, 420)` &rarr; **Alinhados**: `True`
- **Frame 17**: Sprite Center `(417, 317)` | Gizmo Center `(417, 317)` &rarr; **Alinhados**: `True`
- **Frame 18**: Sprite Center `(400, 420)` | Gizmo Center `(400, 420)` &rarr; **Alinhados**: `True`
- **Frame 19**: Sprite Center `(417, 317)` | Gizmo Center `(417, 317)` &rarr; **Alinhados**: `True`

## Respostas aos Questionamentos do Experimento

### O movimento visual ficou mais suave?

**NÃO.**
O movimento em si não fica mais suave, pois ambos (Gizmo e Sprite) agora pulam juntos de pixel em pixel (movimento quantizado de 1 em 1 pixel de tela). A pixelização e o 'snap' de movimento continuam presentes.

### O desalinhamento entre gizmo e sprite desapareceu?

**SIM.**
Como o Gizmo e a borda de seleção são forçados a seguir a mesma matemática de rasterização inteira do `SpriteRenderer`, o desalinhamento dinâmico (jitter/tremulação) entre eles é completamente eliminado. O Gizmo e o Sprite movem-se em perfeita sincronia temporal e espacial, eliminando o efeito óptico de vibração entre os dois elementos.