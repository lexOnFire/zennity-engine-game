# UI Runtime Foundation

A Fase 22 cria a base oficial da UI Runtime da Zennity Engine.

## Componentes

Os componentes vivem em `engine.ui.runtime_components`:

* `UIElement`: base comum com `x`, `y`, `width`, `height`, `visible` e `z_order`.
* `Canvas`: agrupador obrigatório para renderizar elementos UI.
* `LabelComponent`: texto simples.
* `ImageComponent`: imagem por caminho de asset ou placeholder.
* `ButtonComponent`: botão básico.

Todos são `Component`, aparecem no `ComponentRegistry`, são serializáveis e podem ser acessados por scripts como qualquer outro componente.

## Renderização

`UIRenderer` é independente da renderização da cena. Durante Play, `RuntimeScene.draw(...)` desenha a cena primeiro e depois chama o renderer de UI.

A UI não usa a câmera da cena. Elementos de UI são tratados como tela/runtime e não como objetos visuais comuns do mundo.

## Inspector

Cada componente possui um plugin básico no Inspector Plugin System. O Inspector não conhece os tipos concretos de UI; ele consulta o `InspectorPluginRegistry`.

## Serialização

Cenas e prefabs salvam componentes UI dentro da lista de componentes do GameObject. O carregamento usa o `ComponentRegistry`, mantendo compatibilidade com cenas antigas sem componentes de UI.

## Limites

Esta fase não inclui editor visual, layout automático, temas, animações, eventos complexos ou widgets avançados.
