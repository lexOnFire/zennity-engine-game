"""Definições de nós de audio avançado para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class PlaySoundFadeNode(NodeDefinition):
    """Toca som com fade in/out."""

    __node_definition__ = NodeDefinition(
        id="play_sound_fade",
        title_key="Tocar Som com Fade",
        category_key="Audio",
        description_key="Toca um som com fade in e fade out",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("path", "Arquivo", "STRING", default_value=""),
            PinDefinition("fade_in", "Fade In (s)", "FLOAT", default_value=0.0),
            PinDefinition("fade_out", "Fade Out (s)", "FLOAT", default_value=0.0),
            PinDefinition("volume", "Volume", "FLOAT", default_value=1.0),
        ],
        outputs=[
            PinDefinition("exec_playing", "Tocando", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("volume", "Volume", "FLOAT", default_value=1.0),
            PinDefinition("channel", "Canal", "STRING", default_value="master"),  # master, sfx, music
        ],
        outputs=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("current_volume", "Volume Atual", "FLOAT"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("pitch", "Pitch", "FLOAT", default_value=1.0),
        ],
        outputs=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("current_pitch", "Pitch Atual", "FLOAT"),
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
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )
