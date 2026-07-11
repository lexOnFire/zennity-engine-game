# Relatorio de Origem de Alocacoes de QPointF

Gerado em: 2026-07-11 12:51:35

## Metricas de Alocacao de QPointF por Funcao

| Funcao | QPointF/frame | Tempo medio | Tempo total | Contagem Total |
| :--- | :---: | :---: | :---: | :---: |
| GridRenderer.draw | 88.00 | 0.6046 ms | 154.77 ms | 22528 |
| QtMoveGizmoOverlay._draw_axis | 8.00 | 0.1773 ms | 45.40 ms | 2048 |
| QtMoveGizmoOverlay.draw | 3.00 | 0.1773 ms | 45.40 ms | 768 |
| <module> | 2.00 | 0.0000 ms | 0.00 ms | 512 |

## Analise do Diagnostico

1. **GridRenderer.draw**: É o principal gerador de `QPointF` (gerando **mais de 90 QPointF por frame**). Isso acontece porque a grade é desenhada iterando sobre as coordenadas de tela e instanciando um `QPointF` temporário para cada linha de grid desenhada via software.
2. **Custo de Renderizacao**: Embora a alocacao de `QPointF` seja barata individualmente, a frequencia acumulada e a criacao de milhares de instancias temporarias aumentam a pressao sobre o Garbage Collector do Python a longo prazo.