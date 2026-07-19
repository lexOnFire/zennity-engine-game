# Migração arquitetural segura — 19/07/2026

## Objetivo

Criar as fronteiras necessárias para modernizar a Zennity sem reescrever a
engine, sem alterar seu comportamento visual e sem remover compatibilidade.

## Entregas

### Baseline e proteção

- `editor.phase1_main` foi declarado como único entrypoint oficial.
- Entry points históricos foram catalogados como compatibilidade/deprecated.
- Foi adicionado teste real de caracterização do shell oficial, executado onde
  Qt headless está disponível.
- O CI ganhou um orçamento arquitetural que impede aumentar classes/métodos
  gigantes, arquivos acima de 500 linhas e ciclos de import.
- O orçamento reduziu os ciclos detectados de quatro para três ao remover o
  ciclo tipado entre `Camera` e `CameraManager`.

### Estado editável

- `SceneDocument` tornou-se o modelo tipado do documento editável.
- Preserva campos desconhecidos para compatibilidade futura.
- Valida IDs e nomes duplicados.
- Mantém índices por UUID e nome.
- O editor isolado já usa `SceneDocument` ao criar, carregar, salvar, exportar
  e mostrar uma cena.

### Editor e viewport

- `ViewportProcessController` encapsula processo, filas, coalescing, eventos,
  estatísticas e shutdown.
- O shell oficial passou a usar o controller sem alterar o protocolo IPC.
- `PlayModeController` encapsula o estado e a restauração Edit/Play/Pause/Stop.
- `IsolatedEditorWindow` deixou de controlar diretamente as transições internas
  de `EditorPlaySession`.

### Extensões e compatibilidade

- `EditorExtensionRegistry` define instalação explícita e idempotente.
- Os patches necessários somente ao shell Phase 1 embutido foram isolados em
  `phase1_compatibility_extensions()`.
- O caminho oficial isolado não instala esses patches.

### Lifecycle

- `RuntimeLifecycleScheduler` fornece fases Start, FixedUpdate, Update,
  LateUpdate e Stop.
- Registro e remoção durante dispatch são adiados com segurança.
- RuntimeScene usa o scheduler para componentes sem mudar a ordem histórica do
  update e da física.
- `ScriptBehaviour` e `ScriptRuntime` receberam FixedUpdate e LateUpdate.
- Componentes receberam hooks equivalentes.

### Logic Graph

- `LogicNodeHandlerRegistry` permite adicionar nós sem editar o dispatcher.
- Os primeiros nós comuns foram migrados para handlers.
- O runtime exportado inclui o registry e continua autocontido.

### Cena e física

- `SceneIndex` indexa objetos e filhos por UUID, nome e Tag.
- A API mantém o comportamento histórico de retornar o primeiro nome igual.
- Renomes diretos legados são recuperados automaticamente pelo rebuild.
- PhysicsWorld ganhou broad phase sweep-and-prune.
- A ordem histórica dos pares foi preservada.
- Cenas com objetos distantes deixam de executar comparações narrow phase O(n²).
- A resolução de contatos encerrados deixou de recriar o mapa de IDs para cada
  contato.

### Assets e serialização

- `AssetReference` usa GUID com fallback de path.
- AssetDatabase cria referências estáveis e grava `.meta` atomicamente.
- Bytecode `.pyc/.pyo` e `__pycache__` não entram mais no banco de assets.
- `SerializationRegistry` fornece codecs versionados e escrita JSON atômica.

## Compatibilidade

- Nenhum formato antigo foi removido.
- Paths continuam aceitos onde GUID ainda não existe.
- O runtime exportado recebeu a dependência nova do Logic Graph.
- O Render Pipeline e a aparência não foram modificados.
- A imagem local modificada pelo usuário em `Assets/Materials` não faz parte
  desta mudança.

## Métricas finais

- testes executados no ambiente: **1.813 passed, 1 skipped**;
- lint crítico dos arquivos alterados: **zero ocorrências**;
- ciclos de import: **4 → 3**;
- maior classe: **3.258 linhas**, abaixo do baseline de 3.261;
- maior método: **1.540 linhas**, sem regressão;
- arquivos acima de 500 linhas: **18**, sem regressão;
- teste de broad phase com 50 colliders distantes: **zero candidatos** em vez
  de 1.225 pares possíveis.

## Limites deliberados

Esta migração cria as fronteiras e move o caminho oficial para elas. Ela não
remove ainda os módulos antigos porque isso quebraria a regra de compatibilidade.
As classes gigantes não foram divididas mecanicamente apenas para reduzir
linhas: as próximas extrações deverão mover responsabilidades para os
controllers agora testados e medir a redução de acoplamento.

## Próxima sequência segura

1. Mover Asset/Animation/Logic workspaces da janela para controllers próprios.
2. Mover o loop de comandos de `run_viewport` para handlers registrados.
3. Migrar mais tipos de nó para `LogicNodeHandlerRegistry`.
4. Fazer `SceneDocument` substituir snapshots crus no histórico Undo/Redo.
5. Adotar `SerializationRegistry` em todos os formatos modernos.
6. Migrar referências serializadas para GUID com fallback.
7. Remover cada patch somente após teste de caracterização equivalente.
