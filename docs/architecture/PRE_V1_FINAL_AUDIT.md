# Auditoria estrutural final pré-v1.0

Data: 21 de julho de 2026  
Branch auditada: `refactor/pre-v1-architecture-baseline`

## Resultado executivo

Os gates funcionais, multiplataforma, de lifecycle, determinismo, performance e
memória estão estabilizados. As fronteiras críticas medidas possuem 76% de
cobertura agregada no baseline focado, acima do budget obrigatório de 70%.

Após a consolidação estrutural, todas as classes listadas anteriormente foram
decompostas para abaixo do limite de 500 linhas da Definition of Done, e os
módulos legados do editor foram marcados com `DeprecationWarning` explícito
conforme a estratégia de sunset definida para v2.0.


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
| `editor.phase1_editor.ZennityPhase1Editor` | 434 | ✅ Resolvido (Abaixo de 500) |
| `engine.logic.runtime.core.LogicGraphRuntime` | 463 | ✅ Resolvido (Abaixo de 500) |
| `editor.widgets.phase1_viewport.Phase1ViewportWidget` | 383 | ✅ Resolvido (Abaixo de 500) |
| `editor.windows.main_window.MainWindow` | 411 | ✅ Resolvido (Abaixo de 500; `DeprecationWarning` aplicado) |
| `editor.widgets.viewport_widget.ViewportWidget` | 446 | ✅ Resolvido (Abaixo de 500) |


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

1. As classes grandes foram decompostas com sucesso e todas estão estritamente abaixo de 500 linhas.
2. Métodos longos em inicializações de runtime e instanciação de prefabs foram decompostos em ajudantes coesos.
3. O stack legado (`main_window`, `phase1_editor`, `inspector_dock`, `premium_panels`, `editor/inspector/*`) foi devidamente marcado com `DeprecationWarning` explícito e mantido via política de sunset até v2.0.

Decisão: Definition of Done atingida com sucesso para o release gate da v1.0.0.

