"""Definições de nós de audio avançado para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class PlaySoundFadeNode(NodeDefinition):
    """Toca som com fade in/out."""

    __node_definition__ = NodeDefinition(
        id="play_sound_fade",
        title_key="Tocar Som com Fade",
        category_key="Audio",
        description_key="Toca um som com fade in e fade out",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="path", label_key="Arquivo", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="fade_in", label_key="Fade In (s)", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="fade_out", label_key="Fade Out (s)", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="volume", label_key="Volume", pin_type=PinType.FLOAT, default_value=1.0),
        ],
        outputs=[
            PinDefinition(id="exec_playing", label_key="Tocando", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )


class SetVolumeNode(NodeDefinition):
    """Define volume de um canal."""

    __node_definition__ = NodeDefinition(
        id="set_volume",
        title_key="Definir Volume",
        category_key="Audio",
        description_key="Define o volume de um canal de audio (master, sfx, music)",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="volume", label_key="Volume", pin_type=PinType.FLOAT, default_value=1.0),
            PinDefinition(id="channel", label_key="Canal", pin_type=PinType.STRING, default_value="master"),  # master, sfx, music
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="current_volume", label_key="Volume Atual", pin_type=PinType.FLOAT),
        ]
    )


class SetPitchNode(NodeDefinition):
    """Define pitch (velocidade) de um som."""

    __node_definition__ = NodeDefinition(
        id="set_pitch",
        title_key="Definir Pitch",
        category_key="Audio",
        description_key="Define a velocidade/pitch de um som (1.0 = normal, 2.0 = dobrado)",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="pitch", label_key="Pitch", pin_type=PinType.FLOAT, default_value=1.0),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="current_pitch", label_key="Pitch Atual", pin_type=PinType.FLOAT),
        ]
    )


class StopAllSoundsNode(NodeDefinition):
    """Para todos os sons."""

    __node_definition__ = NodeDefinition(
        id="stop_all_sounds",
        title_key="Parar Todos os Sons",
        category_key="Audio",
        description_key="Para todos os sons tocando",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )
