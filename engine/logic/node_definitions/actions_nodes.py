"""Definições de nós de ação para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class PlayAnimationNode(NodeDefinition):
    """Reproduz animação por nome."""

    __node_definition__ = NodeDefinition(
        id="play_animation",
        title_key="Tocar Animação",
        category_key="Actions",
        description_key="Reproduz uma animação pelo nome do estado",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="state", label_key="Estado", pin_type=PinType.STRING, default_value="Idle"),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class PlayAnimationAssetNode(NodeDefinition):
    """Reproduz animação de asset."""

    __node_definition__ = NodeDefinition(
        id="play_animation_asset",
        title_key="Tocar Animação (Asset)",
        category_key="Actions",
        description_key="Reproduz uma animação de um arquivo asset",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="path", label_key="Caminho", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class StopAnimationNode(NodeDefinition):
    """Para a animação atual."""

    __node_definition__ = NodeDefinition(
        id="stop_animation",
        title_key="Parar Animação",
        category_key="Actions",
        description_key="Para a animação atualmente reproduzindo",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class PlaySoundNode(NodeDefinition):
    """Reproduz som."""

    __node_definition__ = NodeDefinition(
        id="play_sound",
        title_key="Tocar Som",
        category_key="Actions",
        description_key="Reproduz um arquivo de áudio",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="path", label_key="Caminho", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class SetSpriteNode(NodeDefinition):
    """Define sprite do objeto."""

    __node_definition__ = NodeDefinition(
        id="set_sprite",
        title_key="Definir Sprite",
        category_key="Actions",
        description_key="Define a imagem/sprite do objeto",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="path", label_key="Caminho", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class StartTextureScrollNode(NodeDefinition):
    """Inicia rolagem de textura."""

    __node_definition__ = NodeDefinition(
        id="start_texture_scroll",
        title_key="Iniciar Rolagem de Textura",
        category_key="Actions",
        description_key="Inicia a rolagem da textura do objeto",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="path", label_key="Caminho", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="speed_x", label_key="Velocidade X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="speed_y", label_key="Velocidade Y", pin_type=PinType.FLOAT, default_value=80.0),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class StopTextureScrollNode(NodeDefinition):
    """Para rolagem de textura."""

    __node_definition__ = NodeDefinition(
        id="stop_texture_scroll",
        title_key="Parar Rolagem de Textura",
        category_key="Actions",
        description_key="Para a rolagem de textura do objeto",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class SetPositionNode(NodeDefinition):
    """Define posição do objeto."""

    __node_definition__ = NodeDefinition(
        id="set_position",
        title_key="Definir Posição",
        category_key="Actions",
        description_key="Define a posição X,Y do objeto",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT, default_value=0.0),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class RotateNode(NodeDefinition):
    """Rotaciona o objeto."""

    __node_definition__ = NodeDefinition(
        id="rotate",
        title_key="Rotacionar",
        category_key="Actions",
        description_key="Rotaciona o objeto em um ângulo específico",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="degrees", label_key="Graus", pin_type=PinType.FLOAT, default_value=90.0),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class SetActiveNode(NodeDefinition):
    """Ativa/desativa objeto."""

    __node_definition__ = NodeDefinition(
        id="set_active",
        title_key="Ativar/Desativar",
        category_key="Actions",
        description_key="Ativa ou desativa o objeto",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="active", label_key="Ativo", pin_type=PinType.BOOL, default_value=True),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class DestroyObjectNode(NodeDefinition):
    """Destrói o objeto."""

    __node_definition__ = NodeDefinition(
        id="destroy_object",
        title_key="Destruir Objeto",
        category_key="Actions",
        description_key="Destrói o objeto imediatamente",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class DestroyAfterTimeNode(NodeDefinition):
    """Destrói objeto após delay."""

    __node_definition__ = NodeDefinition(
        id="destroy_after_time",
        title_key="Destruir Após Tempo",
        category_key="Actions",
        description_key="Agenda a destruição do objeto após um tempo",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="seconds", label_key="Segundos", pin_type=PinType.FLOAT, default_value=1.0),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class LogMessageNode(NodeDefinition):
    """Escreve mensagem no console."""

    __node_definition__ = NodeDefinition(
        id="log_message",
        title_key="Log",
        category_key="Actions",
        description_key="Escreve uma mensagem no console para debug",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="message", label_key="Mensagem", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class StartBehaviorTreeNode(NodeDefinition):
    """Inicia uma behavior tree."""

    __node_definition__ = NodeDefinition(
        id="start_behavior_tree",
        title_key="Iniciar Behavior Tree",
        category_key="Actions",
        description_key="Inicia execução de uma behavior tree",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="path", label_key="Caminho", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )
