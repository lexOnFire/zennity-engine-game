"""Nó de Behavior Tree integrados ao Graph Framework e MetadataManager da Zennity Engine."""
from __future__ import annotations
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class BTSelectorNode:
    """Nó Seletor (Fallback) da Behavior Tree."""

    __node_definition__ = NodeDefinition(
        id="bt.selector",
        title_key="Seletor (Selector)",
        category_key="Behavior Tree/Composite",
        inputs=[
            PinDefinition(id="in", label_key="In (Entrada)", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="out_1", label_key="Opção 1", pin_type=PinType.EXEC),
            PinDefinition(id="out_2", label_key="Opção 2", pin_type=PinType.EXEC),
        ],
    )


class BTSequenceNode:
    """Nó Sequência da Behavior Tree."""

    __node_definition__ = NodeDefinition(
        id="bt.sequence",
        title_key="Sequência (Sequence)",
        category_key="Behavior Tree/Composite",
        inputs=[
            PinDefinition(id="in", label_key="In (Entrada)", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="out_1", label_key="Passo 1", pin_type=PinType.EXEC),
            PinDefinition(id="out_2", label_key="Passo 2", pin_type=PinType.EXEC),
        ],
    )


class BTInverterNode:
    """Nó Decorador Inversor da Behavior Tree."""

    __node_definition__ = NodeDefinition(
        id="bt.inverter",
        title_key="Inversor (Inverter)",
        category_key="Behavior Tree/Decorator",
        inputs=[
            PinDefinition(id="in", label_key="In (Entrada)", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="child", label_key="Filho", pin_type=PinType.EXEC),
        ],
    )


class BTWaitNode:
    """Nó de Ação de Espera da Behavior Tree."""

    __node_definition__ = NodeDefinition(
        id="bt.wait",
        title_key="Esperar (Wait)",
        category_key="Behavior Tree/Action",
        inputs=[
            PinDefinition(id="in", label_key="In (Entrada)", pin_type=PinType.EXEC),
            PinDefinition(id="duration", label_key="Duração (s)", pin_type=PinType.FLOAT, default_value=1.0),
        ],
        outputs=[
            PinDefinition(id="out", label_key="Próximo", pin_type=PinType.EXEC),
        ],
    )


class BTMoveToNode:
    """Nó de Ação MoveTo da Behavior Tree."""

    __node_definition__ = NodeDefinition(
        id="bt.move_to",
        title_key="Mover Até (MoveTo)",
        category_key="Behavior Tree/Action",
        inputs=[
            PinDefinition(id="in", label_key="In (Entrada)", pin_type=PinType.EXEC),
            PinDefinition(id="target_pos", label_key="Posição Alvo", pin_type=PinType.VECTOR3),
            PinDefinition(id="speed", label_key="Velocidade", pin_type=PinType.FLOAT, default_value=5.0),
        ],
        outputs=[
            PinDefinition(id="out", label_key="Próximo", pin_type=PinType.EXEC),
        ],
    )


class BTRepeatNode:
    """Repete o filho uma quantidade definida; zero significa continuamente."""

    __node_definition__ = NodeDefinition(
        id="bt.repeat", title_key="Repetir", category_key="Behavior Tree/Decorator",
        description_key="Repete o nó filho. Use 0 para repetir continuamente.",
        inputs=[PinDefinition(id="in", pin_type=PinType.EXEC),
                PinDefinition(id="count", pin_type=PinType.INT, default_value=0)],
        outputs=[PinDefinition(id="child", pin_type=PinType.EXEC)],
        tags=["loop", "repetir", "patrulha"],
    )


class BTCooldownNode:
    """Impede nova execução do filho até o intervalo terminar."""

    __node_definition__ = NodeDefinition(
        id="bt.cooldown", title_key="Cooldown", category_key="Behavior Tree/Decorator",
        description_key="Executa o filho somente quando o tempo de recarga estiver pronto.",
        inputs=[PinDefinition(id="in", pin_type=PinType.EXEC),
                PinDefinition(id="seconds", pin_type=PinType.FLOAT, default_value=1.0)],
        outputs=[PinDefinition(id="child", pin_type=PinType.EXEC)],
        tags=["intervalo", "recarga", "ataque"],
    )


class BTTargetInRangeNode:
    """Condição de distância até um objeto identificado por tag."""

    __node_definition__ = NodeDefinition(
        id="bt.target_in_range", title_key="Alvo no alcance", category_key="Behavior Tree/Condition",
        description_key="Retorna sucesso quando o alvo existe e está dentro da distância.",
        inputs=[PinDefinition(id="in", pin_type=PinType.EXEC),
                PinDefinition(id="target", pin_type=PinType.STRING, default_value="Player"),
                PinDefinition(id="distance", pin_type=PinType.FLOAT, default_value=150.0)],
        outputs=[PinDefinition(id="out", pin_type=PinType.EXEC)],
        tags=["distância", "visão", "alcance", "jogador"],
    )


class BTParameterConditionNode:
    """Condição sobre um parâmetro do Behavior Tree."""

    __node_definition__ = NodeDefinition(
        id="bt.parameter_condition", title_key="Condição de parâmetro", category_key="Behavior Tree/Condition",
        description_key="Compara um parâmetro com um valor usando ==, !=, >, >=, < ou <=.",
        inputs=[PinDefinition(id="in", pin_type=PinType.EXEC),
                PinDefinition(id="parameter", pin_type=PinType.STRING, default_value="alert"),
                PinDefinition(id="operator", pin_type=PinType.STRING, default_value="=="),
                PinDefinition(id="value", pin_type=PinType.STRING, default_value="true")],
        outputs=[PinDefinition(id="out", pin_type=PinType.EXEC)],
        tags=["variável", "condição", "estado"],
    )


class BTChaseNode:
    """Persegue um objeto até atingir a distância de parada."""

    __node_definition__ = NodeDefinition(
        id="bt.chase", title_key="Perseguir alvo", category_key="Behavior Tree/Action",
        description_key="Move em direção ao alvo e termina ao alcançar a distância de parada.",
        inputs=[PinDefinition(id="in", pin_type=PinType.EXEC),
                PinDefinition(id="target", pin_type=PinType.STRING, default_value="Player"),
                PinDefinition(id="speed", pin_type=PinType.FLOAT, default_value=120.0),
                PinDefinition(id="stop_distance", pin_type=PinType.FLOAT, default_value=48.0)],
        outputs=[PinDefinition(id="out", pin_type=PinType.EXEC)],
        tags=["perseguir", "inimigo", "movimento"],
    )


class BTPatrolNode:
    """Alterna continuamente entre dois pontos do cenário."""

    __node_definition__ = NodeDefinition(
        id="bt.patrol", title_key="Patrulhar", category_key="Behavior Tree/Action",
        description_key="Move continuamente entre os pontos A e B.",
        inputs=[PinDefinition(id="in", pin_type=PinType.EXEC),
                PinDefinition(id="point_a", pin_type=PinType.VECTOR2, default_value="0,0"),
                PinDefinition(id="point_b", pin_type=PinType.VECTOR2, default_value="200,0"),
                PinDefinition(id="speed", pin_type=PinType.FLOAT, default_value=80.0)],
        outputs=[PinDefinition(id="out", pin_type=PinType.EXEC)],
        tags=["patrulha", "rota", "movimento"],
    )


class BTAttackNode:
    """Aplica dano a um alvo dentro do alcance."""

    __node_definition__ = NodeDefinition(
        id="bt.attack", title_key="Atacar alvo", category_key="Behavior Tree/Action",
        description_key="Aplica dano ao campo health/vida do alvo quando estiver no alcance.",
        inputs=[PinDefinition(id="in", pin_type=PinType.EXEC),
                PinDefinition(id="target", pin_type=PinType.STRING, default_value="Player"),
                PinDefinition(id="damage", pin_type=PinType.FLOAT, default_value=10.0),
                PinDefinition(id="range", pin_type=PinType.FLOAT, default_value=64.0)],
        outputs=[PinDefinition(id="out", pin_type=PinType.EXEC)],
        tags=["ataque", "dano", "combate"],
    )


class BTPlayAnimationNode:
    """Solicita uma animação no Animator do objeto."""

    __node_definition__ = NodeDefinition(
        id="bt.play_animation", title_key="Reproduzir animação", category_key="Behavior Tree/Action",
        description_key="Ativa um estado ou clip de animação e retorna sucesso.",
        inputs=[PinDefinition(id="in", pin_type=PinType.EXEC),
                PinDefinition(id="animation", pin_type=PinType.STRING, default_value="Idle")],
        outputs=[PinDefinition(id="out", pin_type=PinType.EXEC)],
        tags=["animar", "estado", "clip"],
    )
