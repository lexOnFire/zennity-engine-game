"""Definições de nós visuais para UI dinâmica no Logic Graph."""
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


# ════════════════════════════════════════════════════════════════════════════
# NÓS DE CRIAÇÃO DE WIDGETS DINÂMICOS
# ════════════════════════════════════════════════════════════════════════════

class CreateUILabelNode:
    """Cria um Label dinâmico na UI em runtime."""

    __node_definition__ = NodeDefinition(
        id="create_ui_label",
        title_key="Criar Label Dinâmico",
        category_key="Logic/UI Dynamic",
        description_key="Cria um novo Label na UI durante execução do jogo.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="parent", label_key="Parent (objeto)", pin_type=PinType.STRING, default_value="Panel_HUD"),
            PinDefinition(id="name", label_key="Nome do Widget", pin_type=PinType.STRING, default_value="label_dynamic"),
            PinDefinition(id="text", label_key="Texto", pin_type=PinType.STRING, default_value="Dinâmico"),
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="font_size", label_key="Tamanho Fonte", pin_type=PinType.INT, default_value=24),
        ],
        outputs=[
            PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="failure", label_key="Erro", pin_type=PinType.EXEC),
        ],
        tags=["ui", "criar", "dinâmico", "label"],
    )


class CreateUIProgressBarNode:
    """Cria uma ProgressBar dinâmica na UI em runtime."""

    __node_definition__ = NodeDefinition(
        id="create_ui_progress_bar",
        title_key="Criar ProgressBar Dinâmica",
        category_key="Logic/UI Dynamic",
        description_key="Cria uma nova ProgressBar na UI durante execução.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="parent", label_key="Parent (objeto)", pin_type=PinType.STRING, default_value="Panel_HUD"),
            PinDefinition(id="name", label_key="Nome do Widget", pin_type=PinType.STRING, default_value="progress_dynamic"),
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="width", label_key="Largura", pin_type=PinType.FLOAT, default_value=200.0),
            PinDefinition(id="height", label_key="Altura", pin_type=PinType.FLOAT, default_value=20.0),
            PinDefinition(id="value", label_key="Valor Inicial", pin_type=PinType.FLOAT, default_value=50.0),
            PinDefinition(id="max_value", label_key="Valor Max", pin_type=PinType.FLOAT, default_value=100.0),
        ],
        outputs=[
            PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="failure", label_key="Erro", pin_type=PinType.EXEC),
        ],
        tags=["ui", "criar", "dinâmico", "progress", "barra"],
    )


class CreateUIButtonNode:
    """Cria um Button dinâmico na UI em runtime."""

    __node_definition__ = NodeDefinition(
        id="create_ui_button",
        title_key="Criar Button Dinâmico",
        category_key="Logic/UI Dynamic",
        description_key="Cria um novo Button na UI durante execução.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="parent", label_key="Parent (objeto)", pin_type=PinType.STRING, default_value="Panel_HUD"),
            PinDefinition(id="name", label_key="Nome do Widget", pin_type=PinType.STRING, default_value="button_dynamic"),
            PinDefinition(id="text", label_key="Texto do Botão", pin_type=PinType.STRING, default_value="Clique Aqui"),
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="width", label_key="Largura", pin_type=PinType.FLOAT, default_value=120.0),
            PinDefinition(id="height", label_key="Altura", pin_type=PinType.FLOAT, default_value=40.0),
        ],
        outputs=[
            PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="failure", label_key="Erro", pin_type=PinType.EXEC),
        ],
        tags=["ui", "criar", "dinâmico", "botão"],
    )


class CreateUIImageNode:
    """Cria uma Image dinâmica na UI em runtime."""

    __node_definition__ = NodeDefinition(
        id="create_ui_image",
        title_key="Criar Image Dinâmica",
        category_key="Logic/UI Dynamic",
        description_key="Cria uma nova Image na UI durante execução.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="parent", label_key="Parent (objeto)", pin_type=PinType.STRING, default_value="Panel_HUD"),
            PinDefinition(id="name", label_key="Nome do Widget", pin_type=PinType.STRING, default_value="image_dynamic"),
            PinDefinition(id="texture_path", label_key="Caminho Imagem", pin_type=PinType.STRING, default_value="Assets/Sprites/icon.png"),
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="width", label_key="Largura", pin_type=PinType.FLOAT, default_value=100.0),
            PinDefinition(id="height", label_key="Altura", pin_type=PinType.FLOAT, default_value=100.0),
        ],
        outputs=[
            PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="failure", label_key="Erro", pin_type=PinType.EXEC),
        ],
        tags=["ui", "criar", "dinâmico", "imagem"],
    )


# ════════════════════════════════════════════════════════════════════════════
# NÓS DE MODIFICAÇÃO DE WIDGETS
# ════════════════════════════════════════════════════════════════════════════

class DestroyUIWidgetNode:
    """Remove um widget da UI em runtime."""

    __node_definition__ = NodeDefinition(
        id="destroy_ui_widget",
        title_key="Remover Widget",
        category_key="Logic/UI Dynamic",
        description_key="Remove um widget dinâmico da UI.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="parent", label_key="Parent (objeto)", pin_type=PinType.STRING, default_value="Panel_HUD"),
            PinDefinition(id="widget_name", label_key="Nome do Widget", pin_type=PinType.STRING, default_value="label_dynamic"),
        ],
        outputs=[
            PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="failure", label_key="Erro", pin_type=PinType.EXEC),
        ],
        tags=["ui", "remover", "dinâmico", "destruir"],
    )


class UpdateUIWidgetPropertyNode:
    """Atualiza uma propriedade de um widget dinâmico."""

    __node_definition__ = NodeDefinition(
        id="update_ui_widget_property",
        title_key="Atualizar Propriedade Widget",
        category_key="Logic/UI Dynamic",
        description_key="Modifica propriedade (text, value, visible, etc) de um widget.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="parent", label_key="Parent (objeto)", pin_type=PinType.STRING, default_value="Panel_HUD"),
            PinDefinition(id="widget_name", label_key="Nome do Widget", pin_type=PinType.STRING, default_value="label_dynamic"),
            PinDefinition(id="property", label_key="Propriedade", pin_type=PinType.STRING, default_value="text"),
            PinDefinition(id="value", label_key="Novo Valor", pin_type=PinType.STRING, default_value="Novo Texto"),
        ],
        outputs=[
            PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="failure", label_key="Erro", pin_type=PinType.EXEC),
        ],
        tags=["ui", "modificar", "dinâmico", "propriedade"],
    )


class GetUIWidgetPropertyNode:
    """Lê uma propriedade de um widget dinâmico."""

    __node_definition__ = NodeDefinition(
        id="get_ui_widget_property",
        title_key="Ler Propriedade Widget",
        category_key="Logic/UI Dynamic",
        description_key="Lê propriedade (text, value, visible, etc) de um widget e salva em variável.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="parent", label_key="Parent (objeto)", pin_type=PinType.STRING, default_value="Panel_HUD"),
            PinDefinition(id="widget_name", label_key="Nome do Widget", pin_type=PinType.STRING, default_value="label_dynamic"),
            PinDefinition(id="property", label_key="Propriedade", pin_type=PinType.STRING, default_value="text"),
        ],
        outputs=[
            PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="failure", label_key="Erro", pin_type=PinType.EXEC),
        ],
        tags=["ui", "ler", "dinâmico", "propriedade"],
    )


class GetProgressBarValueNode:
    """Lê o valor de uma ProgressBar."""

    __node_definition__ = NodeDefinition(
        id="get_progress_bar_value",
        title="Ler Valor ProgressBar",
        category="UI",
        description="Lê o valor atual de uma ProgressBar (0-100 ou 0.0-1.0)",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("widget_name", "Nome da ProgressBar", "STRING", default_value="progress"),
        ],
        pins_output=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_not_found", "Não Encontrado", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("value", "Valor", "FLOAT"),
        ]
    )
