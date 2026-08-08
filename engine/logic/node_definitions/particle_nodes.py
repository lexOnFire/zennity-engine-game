"""Definições de nós de partículas para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class CreateParticleSystemNode(NodeDefinition):
    """Cria um sistema de partículas."""

    __node_definition__ = NodeDefinition(
        id="create_particle_system",
        title_key="Criar Sistema de Partículas",
        category_key="Particles",
        description_key="Cria um novo sistema de partículas em uma posição",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("x", "X", "FLOAT", default_value=0.0),
            PinDefinition("y", "Y", "FLOAT", default_value=0.0),
            PinDefinition("particle_type", "Tipo", "STRING", default_value="spark"),
            PinDefinition("quantity", "Quantidade", "INT", default_value=10),
            PinDefinition("lifetime", "Tempo de Vida (s)", "FLOAT", default_value=1.0),
            PinDefinition("speed", "Velocidade", "FLOAT", default_value=100.0),
        ],
        outputs=[
            PinDefinition("exec_created", "Criado", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("system_id", "ID do Sistema", "STRING"),
        ]
    )


class EmitParticlesNode(NodeDefinition):
    """Emite partículas de um sistema."""

    __node_definition__ = NodeDefinition(
        id="emit_particles",
        title_key="Emitir Partículas",
        category_key="Particles",
        description_key="Emite partículas de um sistema existente",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("system_id", "ID do Sistema", "STRING", default_value=""),
            PinDefinition("quantity", "Quantidade", "INT", default_value=10),
        ],
        outputs=[
            PinDefinition("exec_emitting", "Emitindo", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class StopParticlesNode(NodeDefinition):
    """Para a emissão de partículas."""

    __node_definition__ = NodeDefinition(
        id="stop_particles",
        title_key="Parar Partículas",
        category_key="Particles",
        description_key="Para a emissão de partículas (opcionalmente destruir imediatamente)",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("system_id", "ID do Sistema", "STRING", default_value=""),
            PinDefinition("destroy", "Destruir Imediatamente?", "BOOL", default_value=False),
        ],
        outputs=[
            PinDefinition("exec_stopped", "Parado", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )
