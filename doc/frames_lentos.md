# Relatorio de Diagnostico de Frames Lentos (>10ms)

Gerado em: 2026-07-11 12:57:14

## Analise da Etapa Dominante

A etapa que mais aumentou de tempo durante os frames lentos foi: **LegacySceneAdapter**.

## TOP 20 Frames Mais Lentos

| Rank | Frame | Tempo Total | LegacySceneAdapter | SpriteRenderer | GridRenderer | pygame.image.tostring | QImage | QPainter | drawImage | GizmoRegistry | SelectionManager |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Frame 0 | 70.61 ms | 48.01 ms | 42.27 ms | 0.95 ms | 1.53 ms | 0.05 ms | 0.26 ms | 0.01 ms | 0.36 ms | 0.00 ms |
| 2 | Frame 2 | 43.22 ms | 40.71 ms | 35.87 ms | 0.29 ms | 0.96 ms | 0.02 ms | 0.08 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 3 | Frame 56 | 40.50 ms | 37.94 ms | 33.13 ms | 0.31 ms | 0.96 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 4 | Frame 1 | 40.40 ms | 37.73 ms | 33.00 ms | 0.31 ms | 0.98 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 5 | Frame 3 | 40.36 ms | 37.78 ms | 33.17 ms | 0.30 ms | 0.96 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 6 | Frame 79 | 39.97 ms | 37.36 ms | 32.71 ms | 0.29 ms | 0.97 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 7 | Frame 85 | 39.89 ms | 37.29 ms | 32.81 ms | 0.29 ms | 0.99 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 8 | Frame 95 | 39.89 ms | 37.12 ms | 32.62 ms | 0.34 ms | 1.10 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.15 ms | 0.00 ms |
| 9 | Frame 28 | 39.87 ms | 36.81 ms | 32.17 ms | 0.35 ms | 1.08 ms | 0.02 ms | 0.11 ms | 0.00 ms | 0.15 ms | 0.00 ms |
| 10 | Frame 31 | 39.82 ms | 37.25 ms | 32.80 ms | 0.29 ms | 0.98 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.14 ms | 0.00 ms |
| 11 | Frame 30 | 39.81 ms | 36.99 ms | 32.55 ms | 0.30 ms | 1.22 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 12 | Frame 94 | 39.67 ms | 36.82 ms | 32.32 ms | 0.30 ms | 0.95 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.15 ms | 0.00 ms |
| 13 | Frame 27 | 39.51 ms | 36.74 ms | 32.31 ms | 0.40 ms | 0.98 ms | 0.04 ms | 0.10 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 14 | Frame 11 | 39.46 ms | 36.83 ms | 32.31 ms | 0.30 ms | 1.01 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.14 ms | 0.00 ms |
| 15 | Frame 93 | 39.44 ms | 36.89 ms | 32.45 ms | 0.29 ms | 0.98 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 16 | Frame 20 | 39.39 ms | 36.84 ms | 32.34 ms | 0.29 ms | 0.98 ms | 0.02 ms | 0.08 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 17 | Frame 32 | 39.38 ms | 36.80 ms | 32.51 ms | 0.29 ms | 0.97 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 18 | Frame 33 | 39.34 ms | 36.74 ms | 32.31 ms | 0.29 ms | 0.96 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 19 | Frame 70 | 39.28 ms | 36.66 ms | 32.27 ms | 0.30 ms | 1.03 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.12 ms | 0.00 ms |
| 20 | Frame 54 | 39.23 ms | 36.72 ms | 32.21 ms | 0.29 ms | 0.93 ms | 0.02 ms | 0.09 ms | 0.00 ms | 0.12 ms | 0.00 ms |

## Conclusao

Conforme esperado com a inserção de 1500 sprites na cena, a etapa **LegacySceneAdapter** escala linearmente de tempo com o número de objetos ativos, ultrapassando facilmente a barreira de 10ms e se tornando o novo principal limitador de desempenho (gargalo de CPU da lógica de desenho do Pygame).