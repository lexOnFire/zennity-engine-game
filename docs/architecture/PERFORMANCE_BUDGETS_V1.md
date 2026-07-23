# Budgets de performance da v1

Os gates usam janelas aquecidas e métricas agregadas; inicialização, importação
inicial de assets e compilação de shaders/scripts são medidas separadamente.

| Métrica | Runtime 60 FPS | Editor interativo |
|---|---:|---:|
| frame p95 | 16,67 ms | 20 ms |
| frame máximo | 33,33 ms | 50 ms |
| draw calls p95 | 1.000 | 1.500 |
| repaints por frame | 1 | 1 |
| invalidations por frame | 32 | 64 |
| cache hit ratio mínimo | 90% | 85% |

A fonte executável do contrato é `engine.performance.budgets`. Qualquer mudança
nos limites exige nova versão do perfil, evidência antes/depois e atualização
deste documento. O avaliador retorna todas as violações de uma janela para que
o release gate não esconda regressões secundárias.

## Protocolo de medição

- descartar os primeiros 120 frames;
- medir pelo menos 1.000 frames em cena de referência;
- registrar p95 e máximo de tempo, p95 de draw calls e médias de repaint e
  invalidation;
- contabilizar hit/miss apenas em caches consultados;
- falhar o gate se qualquer limite do perfil for excedido.
