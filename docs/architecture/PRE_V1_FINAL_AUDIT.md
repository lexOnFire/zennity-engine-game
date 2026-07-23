# Auditoria estrutural final da v1.0

Data: 23 de julho de 2026
Branch auditada: `refactor/pre-v1-architecture-baseline`

## Resultado executivo

Os gates funcionais, estruturais, de lifecycle, determinismo, performance,
memória, persistência e exportação estão estabilizados. A branch atende à
Definition of Done arquitetural da v1.0 e pode seguir para revisão e execução da
matriz remota de CI.

A cobertura agregada das fronteiras críticas permanece em 76%, acima do budget
obrigatório de 70%.

## Gates concluídos

- nenhuma classe em `engine/` ou `editor/` acima de 500 linhas;
- nenhuma função ou método de produção acima de 100 linhas;
- gate AST global sem allowlist para impedir regressões estruturais;
- um único entrypoint público, com cinco launchers antigos reduzidos a redirects;
- `SceneDocument` e persistência lossless protegidos por round-trip;
- Play/Stop, Hot Reload e Close protegidos por testes de lifecycle e soak;
- Logic Graph normalizado, validado e executado por fronteiras menores;
- RuntimeWorld e pool de Prefabs com limite rígido de 128 objetos;
- exportação sem caches Python e com validação do build fora do editor;
- nenhum monkey patch instalado pelo bootstrap oficial;
- imports circulares bloqueados pelo CI;
- `Assets/` como raiz canônica, com compatibilidade de leitura para projetos antigos.

## Correções do checkpoint final

| Fronteira | Antes | Depois |
|---|---:|---:|
| `build_logic_graph_ui` | 328 linhas | 24 linhas |
| `validate_logic_graph` | 172 linhas | 29 linhas |
| `normalize_logic_graph` | 134 linhas | 15 linhas |
| `evaluate_output` | 129 linhas | 42 linhas |
| `_apply_qt_shims` | 113 linhas | 59 linhas |
| `RuntimeWorld.instantiate_prefab` | 111 linhas | 96 linhas |

Os builders do Inspector, plugins de Camera e Script, sessão da Viewport,
drag-and-drop de assets, grid e itens do Logic Graph também foram divididos e
ficaram abaixo do budget global.

## Validação local do checkpoint

- 101 testes focados de arquitetura, Inspector, Viewport, runtime e Logic Graph;
- 22 contratos do workspace de Logic Graph;
- 207 testes da metade final da suíte do editor;
- 497 testes de runtime, cena, física, performance, UI, unitários e Logic Graph;
- 10 testes do exportador, incluindo execução do jogo exportado com
  `main.py --validate-only`;
- `git diff --check` sem erros.

A suíte integral contém 2.210 testes. A execução monolítica local atingiu o
limite de tempo após 36%, sem falhas de comportamento; as áreas restantes foram
executadas em grupos. A matriz oficial Linux/Python 3.10–3.12 e Windows/Python
3.12 continua sendo o gate final antes do merge.

## Compatibilidade e legado

Os launchers antigos permanecem apenas como redirects com `FutureWarning`
durante a série 1.x. O modo embutido legado é diagnóstico e não faz parte da API
pública. A remoção física desses redirects está reservada para a v2.0, evitando
quebra desnecessária na v1.x.

O exportador antigo de `editor.core` permanece como adaptador documentado para a
janela legada. O caminho oficial é `engine.build.project_exporter`.

## Riscos residuais aceitos

1. Os redirects legados continuam importáveis durante a janela de depreciação.
2. O checkout de desenvolvimento pode conter assets de demonstração ausentes;
   o exportador oficial reporta referências faltantes sem corromper o build.
3. A aprovação final ainda depende da matriz remota de CI e de smoke manual do
   editor em uma máquina Windows com GPU/display reais.

## Decisão

Arquitetura e confiabilidade da v1.0 concluídas na branch de trabalho. Liberar o
merge somente após CI remoto verde e smoke manual de criar, editar, salvar,
reabrir, executar, parar e exportar um projeto de demonstração.
