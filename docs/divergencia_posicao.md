# Relatorio de Auditoria: Divergencia Visual de Posicoes

Gerado em: 2026-07-11 13:23:42

## Dados Coletados por Frame (Posicoes Relativas)

### Frame 0
- **Mouse (world)**: `(0.000000, 0.000000)` | **Screen (mouse)**: `(400.00, 300.00)`
- **Transform.position**: `(0.000000, 0.000000)`
- **SpriteRenderer (world)**: `(0.000000, 0.000000)` | **Screen (draw)**: `(400.00, 300.00)`
- **Gizmo (world)**: `(0.000000, 0.000000)` | **Screen (draw)**: `(400.00, 300.00)`

### Frame 1
- **Mouse (world)**: `(5.500000, 5.500000)` | **Screen (mouse)**: `(405.50, 305.50)`
- **Transform.position**: `(5.500000, 5.500000)`
- **SpriteRenderer (world)**: `(5.500000, 5.500000)` | **Screen (draw)**: `(405.50, 305.50)`
- **Gizmo (world)**: `(5.500000, 5.500000)` | **Screen (draw)**: `(405.50, 305.50)`

### Frame 2
- **Mouse (world)**: `(11.000000, 11.000000)` | **Screen (mouse)**: `(411.00, 311.00)`
- **Transform.position**: `(11.000000, 11.000000)`
- **SpriteRenderer (world)**: `(11.000000, 11.000000)` | **Screen (draw)**: `(411.00, 311.00)`
- **Gizmo (world)**: `(11.000000, 11.000000)` | **Screen (draw)**: `(411.00, 311.00)`

### Frame 3
- **Mouse (world)**: `(16.500000, 16.500000)` | **Screen (mouse)**: `(416.50, 316.50)`
- **Transform.position**: `(16.500000, 16.500000)`
- **SpriteRenderer (world)**: `(16.500000, 16.500000)` | **Screen (draw)**: `(416.50, 316.50)`
- **Gizmo (world)**: `(16.500000, 16.500000)` | **Screen (draw)**: `(416.50, 316.50)`

### Frame 4
- **Mouse (world)**: `(22.000000, 22.000000)` | **Screen (mouse)**: `(422.00, 322.00)`
- **Transform.position**: `(22.000000, 22.000000)`
- **SpriteRenderer (world)**: `(22.000000, 22.000000)` | **Screen (draw)**: `(422.00, 322.00)`
- **Gizmo (world)**: `(22.000000, 22.000000)` | **Screen (draw)**: `(422.00, 322.00)`

## Analise da Divergencia Encontrada

### Posições Lógicas no Mundo são Idênticas!
Todas as posições lógicas no espaço do mundo (`Transform.position`, `SpriteRenderer_world`, `Gizmo_world`) são **exatamente iguais**.

### Divergência nas Coordenadas de Tela (Screen coordinates)!
Embora as posições lógicas no mundo sejam iguais, as **coordenadas de tela** usadas para desenhar divergem:
1. **Gizmo**: Usa `world_to_viewport` do editor (`viewport.world_to_viewport()`), que mapeia as coordenadas usando a câmera da Viewport.
2. **SpriteRenderer**: Usa `Camera2D.main.world_to_screen()`, que mapeia usando a câmera global do motor de jogo.
Se a sincronização entre a Câmera do Editor e a Câmera da Engine falhar durante o drag, as coordenadas de tela calculadas divergem. E como o SpriteRenderer converte a coordenada final para inteiros (`int(screen_x)`), a imagem desenhada do sprite sofre de serrilhamento visual, enquanto o Gizmo é desenhado em float com antialiasing, causando o efeito visual de 'deslocamento/stutter' entre o objeto e a sseta do Gizmo.