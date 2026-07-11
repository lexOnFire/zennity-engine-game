# Relatorio de Instrumentacao do Pipeline de Drag

Gerado em: 2026-07-11 12:18:15

## Contadores Gerais

- **QWidget.update() chamados**: 365
- **paintGL() executados**: 354
- **object_transform_changed emitidos**: 1063
- **update() chamados dentro de mouseMoveEvent**: 161

## Tabela de Metricas do Pipeline

| Funcao | Chamadas | Tempo Medio (ms) | Tempo Minimo (ms) | Tempo Maximo (ms) | % do Frame (16.6ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Gizmo update | 708 | 0.0212 ms | 0.0128 ms | 0.0548 ms | 0.13% |
| LegacySceneAdapter.draw | 354 | 0.1942 ms | 0.1560 ms | 0.3332 ms | 1.17% |
| QImage | 354 | 0.0097 ms | 0.0059 ms | 0.0250 ms | 0.06% |
| QPainter | 2056 | 0.0338 ms | 0.0025 ms | 0.2745 ms | 0.20% |
| SelectionManager | 204 | 0.0039 ms | 0.0027 ms | 0.0074 ms | 0.02% |
| SpriteRenderer.draw | 1416 | 0.0307 ms | 0.0125 ms | 0.1613 ms | 0.18% |
| _emit_transform_changed | 1063 | 0.0564 ms | 0.0321 ms | 0.2699 ms | 0.34% |
| _sync_collider_size | 1063 | 0.0176 ms | 0.0110 ms | 0.0524 ms | 0.11% |
| _update_move_drag | 1063 | 0.0749 ms | 0.0433 ms | 0.2865 ms | 0.45% |
| mouseMoveEvent | 1063 | 0.0934 ms | 0.0547 ms | 0.3042 ms | 0.56% |
| paintGL | 354 | 3.4085 ms | 2.9981 ms | 3.8012 ms | 20.53% |
| pygame.image.tostring | 354 | 0.7307 ms | 0.6930 ms | 0.8690 ms | 4.40% |