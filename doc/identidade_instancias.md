# Relatorio de Auditoria: Identidade de Instancias e Objetos no Drag

Gerado em: 2026-07-11 14:36:48

## IDs (id()) de Instâncias Capturados

- **id(Phase1ViewportWidgetInstance)**: `1667760531328`
- **id(active_scene)**: `1667760224640`
- **id(editor_context.current_scene())**: `1667760224640`
- **id(runtime_scene)**: `1667760224640`
- **id(selected_object())**: `1667757469680`
- **id(GameObject arrastado)**: `1667757469680`

## Comparativo de Recebimento do GameObject nos Renderizadores

- **id recebido pelo Overlay Qt**: `1667757469680`
- **id recebido pelo SpriteRenderer**: `1667757469680`
- **id retornado por selected_object()**: `1667757469680`

## Respostas aos Questionamentos da Auditoria

### 1. Todos esses IDs são exatamente iguais?

**SIM.** Todos os IDs que se referem ao GameObject Player são rigorosamente idênticos (`1667757469680`), o que prova que os renderizadores (Pygame e Qt Overlay) e o sistema de seleção operam sobre a **mesma instância física** em memória.

### 2. Identificação da Pilha de Execução

- **paintGL executado**: `Phase1ViewportWidget.paintGL` (através da substituição pelo decorator/patch de estabilidade).

- **Widget executado**: Instância de `Phase1ViewportWidget` (ID `1667760531328`).

- **Scene executada**: Instância de `Editor2DScene` (ID `1667760224640`).

### 3. Contagem de Instâncias Simultâneas em Memória

- **Phase1ViewportWidget**: `1` instância(s) ativa(s).

- **ViewportWidget**: `1` instância(s) ativa(s).

- **Editor2DScene**: `1` instância(s) ativa(s).
