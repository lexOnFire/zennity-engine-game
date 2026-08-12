"""Definições canônicas dos nós de cena, aplicação e UI global.

Phase 9.5B Stage 1.

Estes tipos executavam mas não tinham definição, então eram invisíveis na
paleta.  Cada um tinha ainda várias grafias registradas no mesmo executor
(``scene.load_scene`` / ``scene.load`` / ``scene_load`` / ``open_scene`` /
``load_scene``).  Aqui existe **um id canônico por ação**; as grafias antigas
continuam funcionando via ``engine.logic.port_aliases.NODE_ID_ALIASES``, mas
não ganham entrada na paleta -- caso contrário o autor veria cinco nós
idênticos e não saberia qual funciona.

A grafia pontuada é a canônica porque é a que os assets do projeto já usam.
"""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class SceneLoadSceneNode:
    """Carrega outra cena."""

    __node_definition__ = NodeDefinition(
        id="scene.load_scene",
        title_key="Carregar Cena",
        category_key="Scene",
        description_key="Carrega a cena indicada por caminho",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="scene_path", label_key="Cena", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Pronto", pin_type=PinType.EXEC),
        ],
    )


class AppQuitNode:
    """Encerra o jogo."""

    __node_definition__ = NodeDefinition(
        id="app.quit",
        title_key="Sair do Jogo",
        category_key="Scene",
        description_key="Encerra a aplicação",
        # O jogo termina aqui: o fluxo não continua, por definição.
        execution_model="terminal",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[],
    )


class UIButtonClickedNode:
    """Continua o fluxo quando o botão indicado é clicado."""

    __node_definition__ = NodeDefinition(
        id="ui.button_clicked",
        title_key="Botão Clicado",
        category_key="UI",
        description_key="Segue adiante quando o botão indicado for clicado",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="widget_name", label_key="Botão", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Clicado", pin_type=PinType.EXEC),
        ],
    )


class UISetWidgetEnabledNode:
    """Liga/desliga um widget de UI."""

    __node_definition__ = NodeDefinition(
        id="ui.set_widget_enabled",
        title_key="Habilitar Widget",
        category_key="UI",
        description_key="Habilita ou desabilita um widget de UI",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="widget_name", label_key="Widget", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="enabled", label_key="Habilitado", pin_type=PinType.BOOL, default_value=True),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Pronto", pin_type=PinType.EXEC),
        ],
    )


# ---------------------------------------------------------------- pure data
class GetPositionNode:
    """Posição de um objeto."""

    __node_definition__ = NodeDefinition(
        id="get_position",
        title_key="Obter Posição",
        category_key="Objects",
        description_key="Devolve a posição do objeto alvo",
        execution_model="pure_data",
        inputs=[
            PinDefinition(id="target", label_key="Alvo", pin_type=PinType.OBJECT),
        ],
        outputs=[
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT),
        ],
    )


class GetObjectNameNode:
    """Nome de um objeto."""

    __node_definition__ = NodeDefinition(
        id="get_object_name",
        title_key="Obter Nome do Objeto",
        category_key="Objects",
        description_key="Devolve o nome do objeto alvo",
        execution_model="pure_data",
        inputs=[
            PinDefinition(id="target", label_key="Alvo", pin_type=PinType.OBJECT),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Nome", pin_type=PinType.STRING),
        ],
    )


class SubgraphInputNode:
    """Valor de entrada declarado pelo subgrafo."""

    __node_definition__ = NodeDefinition(
        id="subgraph_input",
        title_key="Entrada do Subgrafo",
        category_key="Graphs",
        description_key="Lê um valor passado pelo grafo chamador",
        execution_model="pure_data",
        inputs=[],
        outputs=[
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.STRING),
        ],
    )


class FindNearestObjectNode:
    """Encontra o objeto mais próximo com a tag indicada."""

    __node_definition__ = NodeDefinition(
        id="find_nearest_object",
        title_key="Encontrar Mais Próximo",
        category_key="Objects",
        description_key="Procura o objeto mais próximo com a tag indicada",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="tag", label_key="Tag", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="max_distance", label_key="Distância Máx.", pin_type=PinType.FLOAT, default_value=100.0),
        ],
        outputs=[
            PinDefinition(id="exec_found", label_key="Encontrado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_none", label_key="Nenhum", pin_type=PinType.EXEC),
            PinDefinition(id="object", label_key="Objeto", pin_type=PinType.OBJECT),
            PinDefinition(id="distance", label_key="Distância", pin_type=PinType.FLOAT),
        ],
    )
