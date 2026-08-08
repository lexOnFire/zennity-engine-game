"""Definições de nós de partículas para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class CreateParticleSystemNode(NodeDefinition):
    """Cria um sistema de partículas."""

    __node_definition__ = NodeDefinition(
        id="create_particle_system",
        title_key="Criar Sistema de Partículas",
        category_key="Particles",
        description_key="Cria um novo sistema de partículas em uma posição",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="particle_type", label_key="Tipo", pin_type=PinType.STRING, default_value="spark"),
            PinDefinition(id="quantity", label_key="Quantidade", pin_type=PinType.INT, default_value=10),
            PinDefinition(id="lifetime", label_key="Tempo de Vida (s)", pin_type=PinType.FLOAT, default_value=1.0),
            PinDefinition(id="speed", label_key="Velocidade", pin_type=PinType.FLOAT, default_value=100.0),
        ],
        outputs=[
            PinDefinition(id="exec_created", label_key="Criado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="system_id", label_key="ID do Sistema", pin_type=PinType.STRING),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="system_id", label_key="ID do Sistema", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="quantity", label_key="Quantidade", pin_type=PinType.INT, default_value=10),
        ],
        outputs=[
            PinDefinition(id="exec_emitting", label_key="Emitindo", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="system_id", label_key="ID do Sistema", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="destroy", label_key="Destruir Imediatamente?", pin_type=PinType.BOOL, default_value=False),
        ],
        outputs=[
            PinDefinition(id="exec_stopped", label_key="Parado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )
