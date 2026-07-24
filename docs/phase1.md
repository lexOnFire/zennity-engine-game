# Zennity Editor - Fase 1

Esta fase estabiliza a base do editor antes de adicionar Rotate e Scale.
O foco atual e funcionalidade, sincronizacao de estado e manutencao futura.

## Editor Runtime

O editor possui um runtime proprio em `editor/runtime/`.

- `EditorContext`: ponto de entrada do runtime do editor.
- `EditorState`: estado compartilhado do editor, como Play Mode e Snap.
- `SelectionManager`: fonte canonica de selecao.
- `ToolManager`: controla a ferramenta ativa.
- `CommandManager`: base para Undo/Redo via Command Pattern.

Views e widgets devem consumir esse runtime. A Viewport pode sincronizar com
campos legados da cena, como `selected_index`, mas a selecao real da Fase 1
deve passar pelo `SelectionManager`.

## SelectionManager

`SelectionManager` e a fonte real de selecao.

Hierarchy, Viewport e Inspector nao devem manter selecoes independentes. Eles
devem emitir uma intencao de selecao ou escutar os sinais do ViewModel, que por
sua vez delega para o `SelectionManager`.

## ToolManager

`ToolManager` guarda a ferramenta ativa:

- Select
- Move
- Rotate
- Scale

Na Fase 1.2, Select e Move sao funcionais. Rotate e Scale podem ser ativadas
como modo visual, mas mostram mensagem de "em desenvolvimento" e nao simulam
comportamento que ainda nao existe.

## Move Tool

Move usa a conversao correta entre tela e mundo da Viewport.

Regras atuais:

- Move so arrasta quando a ferramenta Move esta ativa.
- Select apenas seleciona.
- O objeto nao deve saltar ao iniciar o drag.
- Snap usa `EditorState.snap_enabled` e `EditorState.snap_size`.
- Drag e gizmo ficam bloqueados durante Play Mode.
- Toda mudanca de Transform deve atualizar o Inspector.

## Play/Stop

Play cria um snapshot da cena editavel. Stop restaura esse snapshot e preserva
contagem de objetos e selecao por indice/ordem da cena.

Objetos removidos durante restore precisam passar pelo ciclo de vida correto
para que componentes, colliders e estados de fisica sejam limpos.

