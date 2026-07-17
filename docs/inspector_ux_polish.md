# Inspector UX Polish - Fase 28

A Fase 28 melhora a experiencia de uso do Inspector sem alterar o InspectorPluginSystem nem o ComponentSystem.

## Objetivo

O Inspector continua sendo apenas um host de plugins. As melhorias desta fase adicionam recursos de produtividade ao painel:

- filtro de componentes por nome ou tipo;
- menu de contexto por componente;
- reset de componente;
- copy/paste de valores de componente;
- mover componente para cima ou baixo;
- remover componente opcional;
- comandos reversiveis para propriedades do cabecalho do objeto.

## Fluxo oficial

GameObject.components -> InspectorPluginRegistry.plugin_for(component) -> InspectorPlugin.create_widget(...) -> InspectorDock aplica UX generica em volta do widget.

O InspectorDock nao conhece widgets concretos de componentes. Ele hospeda o widget retornado pelo plugin e adiciona acoes genericas quando possivel.

## Menu de contexto

Cada widget de componente recebe um menu com acoes:

- Reset Component
- Copy Component
- Paste Component Values
- Move Up
- Move Down
- Remove Component

A remocao e bloqueada para Transform e componentes required = True.

## Copy / Paste Values

O Inspector copia apenas dados serializaveis: type, enabled e properties.

O id do componente nao e copiado. Isso preserva a identidade do componente de destino.

## Reset Component

O reset cria uma instancia padrao do mesmo tipo de componente e aplica seus dados serializaveis ao componente atual. Caso o componente nao possa ser instanciado sem argumentos, o reset e ignorado de forma segura.

## Undo / Redo

As acoes de UX usam CommandManager quando disponivel:

- paste values;
- reset;
- mover componente;
- remover componente;
- alterar active, is_static, tag e layer no cabecalho do Inspector.

Isso mantem o comportamento consistente com Hierarchy, Project Browser e demais sistemas do editor.

## Limites

Esta fase nao implementa:

- multi-selecao no Inspector;
- drag and drop visual completo entre componentes;
- presets de componentes;
- editor avancado por tipo;
- alteracoes no Runtime.
