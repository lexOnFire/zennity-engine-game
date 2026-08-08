"""Definições de nós para auto-binding de UI widgets a variáveis."""
from engine.logic.metadata import NodeDefinition, PinDefinition


BindUIToVariableNode_def = NodeDefinition(
    id="bind_ui_to_variable",
    title="Vincular UI → Variável",
    category="UI",
    description="Sincroniza valor de um widget para uma variável (uma vez)",

    pins_input=[
        PinDefinition("exec", "Exec", "EXEC"),
        PinDefinition("widget_name", "Nome Widget", "STRING", default_value="comida"),
        PinDefinition("variable_name", "Nome Variável", "STRING", default_value="comida"),
        PinDefinition("property", "Propriedade", "STRING", default_value="value"),
    ],
    pins_output=[
        PinDefinition("exec_success", "Sucesso", "EXEC"),
        PinDefinition("exec_not_found", "Não Encontrado", "EXEC"),
        PinDefinition("exec_failure", "Falha", "EXEC"),
    ]
)


UpdateUIBindingNode_def = NodeDefinition(
    id="update_ui_binding",
    title="Atualizar Binding UI",
    category="UI",
    description="Sincroniza valor de widget para variável (chame a cada frame)",

    pins_input=[
        PinDefinition("exec", "Exec", "EXEC"),
        PinDefinition("widget_name", "Nome Widget", "STRING", default_value="comida"),
        PinDefinition("variable_name", "Nome Variável", "STRING", default_value="comida"),
        PinDefinition("property", "Propriedade", "STRING", default_value="value"),
    ],
    pins_output=[
        PinDefinition("exec_success", "Sucesso", "EXEC"),
        PinDefinition("exec_not_found", "Não Encontrado", "EXEC"),
        PinDefinition("exec_failure", "Falha", "EXEC"),
    ]
)
