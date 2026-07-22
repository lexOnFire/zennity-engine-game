# Auditoria estrutural final pré-v1.0

Data: 21 de julho de 2026  
Branch auditada: `refactor/pre-v1-architecture-baseline`

## Resultado executivo

Os gates funcionais, multiplataforma, de lifecycle, determinismo, performance e
memória estão estabilizados. As fronteiras críticas medidas possuem 76% de
cobertura agregada no baseline focado, acima do budget obrigatório de 70%.

A auditoria não recomenda promover a branch diretamente para v1.0: ainda há
classes e métodos acima dos limites definidos na Definition of Done. Essas
violações não foram escondidas por uma allowlist; estão listadas abaixo como
bloqueios de release.

## Fronteiras críticas cobertas

- `SceneDocument` e persistência lossless;
- scheduler de lifecycle e `RuntimeWorld`;
- Logic Graph Runtime, handlers e avaliação de outputs;
- Play/Stop isolado e sessão da Viewport;
- controllers de Asset Browser, Console, Hierarchy e Inspector.

O CI executa a suíte integral com `coverage.py` e falha se a cobertura agregada
dessas fronteiras cair abaixo de 70%.

## Auditoria AST

### Classes acima de 500 linhas

| Classe | Linhas | Situação |
|---|---:|---|
| `editor.phase1_editor.ZennityPhase1Editor` | 809 | bloqueio; entrypoint oficial |
| `engine.logic.runtime.core.LogicGraphRuntime` | 788 | bloqueio; runtime oficial |
| `editor.widgets.phase1_viewport.Phase1ViewportWidget` | 762 | bloqueio; viewport oficial |
| `editor.windows.main_window.MainWindow` | 600 | legado ainda importável |
| `editor.widgets.viewport_widget.ViewportWidget` | 585 | base ativa da viewport |

### Métodos acima de 100 linhas

Os maiores casos restantes são montagem visual, normalização/validação de grafo,
exportação e shims de compatibilidade. Eles devem ser extraídos por
responsabilidade, preservando os testes de caracterização existentes. Os casos
oficiais observados variam de 102 a 328 linhas.

### Dependências e lifecycle

- o gate global não detecta ciclos de import de runtime;
- nenhum monkey patch é instalado pelo bootstrap oficial;
- sinais dos controllers possuem conexão e desconexão idempotentes;
- Play/Stop, Hot Reload e Close possuem soak tests determinísticos;
- teardown limpa filas, scripts, áudio e caches de renderização;
- `Assets/` é a raiz canônica, com compatibilidade para projetos antigos.

## Métricas consolidadas

| Gate | Resultado |
|---|---|
| Cobertura crítica | 76% no baseline focado; mínimo CI 70% |
| Logic Graph handlers | até 60 linhas |
| Logic Graph orchestration | métodos abaixo de 100 linhas |
| Play/Stop memory probe | 500 ciclos dentro do budget |
| Prefab object pool | limite rígido de 128 objetos |
| Matriz suportada | Linux 3.10–3.12 e Windows 3.12 |

## Riscos residuais e decisão

1. As cinco classes grandes aumentam blast radius e custo de manutenção.
2. Builders e validadores longos dificultam testes unitários finos.
3. `MainWindow` e `ViewportWidget` continuam importáveis por consumidores
   legados, prolongando duas superfícies de editor.

Decisão: manter o PR em draft e não marcar a Definition of Done como concluída
até decompor as classes oficiais e eliminar os métodos acima do orçamento. Os
budgets de cobertura, performance, memória, imports e lifecycle permanecem
obrigatórios durante essa decomposição.
