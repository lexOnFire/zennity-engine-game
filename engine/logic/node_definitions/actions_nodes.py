"""Definições de nós de ação para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class PlayAnimationNode(NodeDefinition):
    """Reproduz animação por nome."""

    __node_definition__ = NodeDefinition(
        id="play_animation",
        title_key="Tocar Animação",
        category_key="Actions",
        description_key="Reproduz uma animação pelo nome do estado",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("state", "Estado", "STRING", default_value="Idle"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("path", "Caminho", "STRING", default_value=""),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("path", "Caminho", "STRING", default_value=""),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("path", "Caminho", "STRING", default_value=""),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("path", "Caminho", "STRING", default_value=""),
            PinDefinition("speed_x", "Velocidade X", "FLOAT", default_value=0.0),
            PinDefinition("speed_y", "Velocidade Y", "FLOAT", default_value=80.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("x", "X", "FLOAT", default_value=0.0),
            PinDefinition("y", "Y", "FLOAT", default_value=0.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("degrees", "Graus", "FLOAT", default_value=90.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("active", "Ativo", "BOOL", default_value=True),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("seconds", "Segundos", "FLOAT", default_value=1.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("message", "Mensagem", "STRING", default_value=""),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("path", "Caminho", "STRING", default_value=""),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )
