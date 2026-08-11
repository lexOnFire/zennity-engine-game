"""Definições de nós para auto-binding de UI widgets a variáveis."""
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


BindUIToVariableNode_def = NodeDefinition(
    id="bind_ui_to_variable",
    title_key="Vincular UI → Variável",
    category_key="UI",
    description_key="Sincroniza valor de um widget para uma variável (uma vez)",

    inputs=[
        PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        PinDefinition(id="widget_name", label_key="Nome Widget", pin_type=PinType.STRING, default_value="comida"),
        PinDefinition(id="variable_name", label_key="Nome Variável", pin_type=PinType.STRING, default_value="comida"),
        PinDefinition(id="property", label_key="Propriedade", pin_type=PinType.STRING, default_value="value"),
    ],
    outputs=[
        PinDefinition(id="next", label_key="Sucesso", pin_type=PinType.EXEC),
        PinDefinition(id="exec_not_found", label_key="Não Encontrado", pin_type=PinType.EXEC),
        PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        PinDefinition(id="value", label_key="Valor", pin_type=PinType.STRING),
        ]
)


UpdateUIBindingNode_def = NodeDefinition(
    id="update_ui_binding",
    title_key="Atualizar Binding UI",
    category_key="UI",
    description_key="Sincroniza valor de widget para variável (chame a cada frame)",

    inputs=[
        PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        PinDefinition(id="widget_name", label_key="Nome Widget", pin_type=PinType.STRING, default_value="comida"),
        PinDefinition(id="variable_name", label_key="Nome Variável", pin_type=PinType.STRING, default_value="comida"),
        PinDefinition(id="property", label_key="Propriedade", pin_type=PinType.STRING, default_value="value"),
    ],
    outputs=[
        PinDefinition(id="next", label_key="Sucesso", pin_type=PinType.EXEC),
        PinDefinition(id="exec_not_found", label_key="Não Encontrado", pin_type=PinType.EXEC),
        PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        PinDefinition(id="value", label_key="Valor", pin_type=PinType.STRING),
        ]
)
