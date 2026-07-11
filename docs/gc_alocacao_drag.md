# Relatorio de Instrumentacao de GC e Alocacao no Drag

Gerado em: 2026-07-11 12:48:31

## Ocorrencia de Coleta de Lixo (Garbage Collection)

**SIM**, ocorreu coleta de lixo durante o arraste!
- **Quantidade de coletas**: 1
  - Coleta 1: Geracao 0 aos 0.01s

## Estatisticas do GC (gc.get_stats())

### GC Stats Antes:
- Geracao 0: {'collections': 77, 'collected': 202, 'uncollectable': 0}
- Geracao 1: {'collections': 7, 'collected': 11, 'uncollectable': 0}
- Geracao 2: {'collections': 1, 'collected': 9, 'uncollectable': 0}
### GC Stats Depois:
- Geracao 0: {'collections': 78, 'collected': 202, 'uncollectable': 0}
- Geracao 1: {'collections': 7, 'collected': 11, 'uncollectable': 0}
- Geracao 2: {'collections': 1, 'collected': 9, 'uncollectable': 0}

## Contagem de GC (gc.get_count())

- **Contagem Antes**: (1, 0, 0)
- **Contagem Depois**: (370, 1, 0)

## Metricas de Alocacao por Frame

- **Total de frames de drag executados**: 261
- **Objetos (rastreados por GC) no inicio**: 35663
- **Objetos (rastreados por GC) no final**: 36372
- **Estimativa de objetos Python criados por frame**: 1.39 objetos/frame

### Alocacao de Classes Especificas (Total / Media por Frame):
- **pygame.Surface**: 1044 total | 4.00 por frame
- **QImage**: 261 total | 1.00 por frame
- **QRect/QRectF**: 1044 total (0 QRect, 1044 QRectF) | 4.00 por frame
- **QPoint/QPointF**: 26361 total (0 QPoint, 26361 QPointF) | 101.00 por frame

## Conclusao Tecnica

1. **QImage e QRect/QPoint**: Há uma criação sistemática de novas instâncias de `QImage` e estruturas de `QPoint/QRect` a cada frame. O maior destaque é o número elevado de alocações de `QPointF` (~100 por frame) causadas pelas chamadas matemáticas de conversão do mouse/tela.
2. **pygame.Surface**: São alocadas exatamente 4 novas instâncias de `pygame.Surface` por frame. Isso ocorre devido à criação de buffers temporários internos (textos/gizmos), mas eles são corretamente liberados e limpos imediatamente, não gerando vazamentos.