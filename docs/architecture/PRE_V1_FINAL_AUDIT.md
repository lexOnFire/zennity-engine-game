# Auditoria estrutural final pré-v1.0

Data da auditoria original: 21 de julho de 2026

Medição AST atualizada: 2 de agosto de 2026

Commit da medição: `77fad10`

Branch auditada: `integration/merge-audit-into-codex`

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

### Classes monitoradas pelo limite de 500 linhas

| Classe | Linhas | Margem até 500 | Situação |
|---|---:|---:|---|
| `editor.phase1_editor.ZennityPhase1Editor` | 434 | 66 | ✅ Abaixo de 500 |
| `engine.logic.runtime.core.LogicGraphRuntime` | 494 | 6 | ⚠️ Abaixo de 500; crescimento congelado |
| `editor.widgets.phase1_viewport.Phase1ViewportWidget` | 387 | 113 | ✅ Abaixo de 500 |
| `editor.windows.main_window.MainWindow` | 482 | 18 | ⚠️ Legado abaixo de 500; crescimento congelado |
| `editor.widgets.viewport_widget.ViewportWidget` | 483 | 17 | ⚠️ Abaixo de 500; extração preventiva planejada |

Contagem calculada com `ast.ClassDef.lineno/end_lineno`, incluindo a declaração
e a última linha de cada classe. A tabela deve sempre informar a data e o commit
da medição para não ser interpretada como estado permanente do código.

### Decisão preventiva para classes próximas do limite

- `LogicGraphRuntime` possui somente 6 linhas de margem. Novas responsabilidades
  não devem ser adicionadas à classe; qualquer crescimento exige extração prévia
  para os mixins ou serviços de runtime existentes.
- `MainWindow` possui 18 linhas de margem, mas pertence ao stack legado com sunset
  previsto para v2.0. A decisão é congelar funcionalidades nesse entrypoint e
  aceitar somente correções essenciais, evitando uma refatoração sem retorno.
- `ViewportWidget` possui 17 linhas de margem e `_apply_qt_shims` mede 113 linhas.
  A próxima alteração estrutural desse widget deve extrair essa compatibilidade
  Qt para um helper/mixin dedicado antes de adicionar novas funcionalidades.
- Esta atualização é apenas documental e não altera comportamento de runtime.


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

1. Todas as classes monitoradas permanecem abaixo de 500 linhas, mas `LogicGraphRuntime`, `MainWindow` e `ViewportWidget` têm margem crítica e seguem as restrições preventivas registradas acima.
2. Métodos longos em inicializações de runtime e instanciação de prefabs foram decompostos em ajudantes coesos.
3. O isolamento do teste `test_memory_leak.py` contra contaminação de mocks da suíte global foi implementado via `_reset_all_mocks()`, obtendo **2.207 de 2.207 testes passando em execução sequencial estrita** (100% de aprovação funcional, 0 falhas, 2 skipped devido a especificidades de OS/Win32).
4. Adicionado teste de regressão em `tests/editor/test_phase1_viewport_pro.py::test_tick_handles_null_active_scene_regression` cobrindo o tratamento de `active_scene=None` em `_tick()`.
5. O stack legado (`main_window`, `phase1_editor`, `inspector_dock`, `premium_panels`, `editor/inspector/*`) foi devidamente marcado com `DeprecationWarning` explícito e mantido via política de sunset até v2.0.

Decisão: Definition of Done atingida com sucesso e validada empiricamente para o release gate da v1.0.0.
