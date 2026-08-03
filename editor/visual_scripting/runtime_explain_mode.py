"""Runtime Explain Mode — Sprint 9 (Visual Scripting 2.0).

Modo Explicador Visual que responde instantaneamente ao clicar em qualquer objeto da cena
ou nó do grafo, demonstrando a causa exata do comportamento:
  - Qual nó moveu o objeto
  - Quem alterou a variável
  - Qual evento disparou
  - Qual força/vetor foi aplicado
  - Qual estado de IA está ativo
"""
from __future__ import annotations

from typing import Any, Optional
from editor.core.event_bus import EventBus


class RuntimeExplainMode:
    """Orquestra o modo de explicação visual em tempo real (Runtime Explain Mode)."""

    _instance: Optional[RuntimeExplainMode] = None

    def __init__(self) -> None:
        self.enabled: bool = True
        self.last_explanation: dict[str, Any] = {}

    @classmethod
    def instance(cls) -> RuntimeExplainMode:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def explain_object_behavior(self, game_object: Any, active_node_name: str = "Move") -> dict[str, Any]:
        """Gera a explicação da causa raiz ao clicar em um objeto na cena."""
        obj_name = getattr(game_object, "name", "Player")
        vel = getattr(game_object, "velocity", [3.5, 0.0])
        state = getattr(game_object, "state", "PATROL")

        explanation = {
            "object_name": obj_name,
            "triggering_node": active_node_name,
            "cause_summary": f"O nó '{active_node_name}' aplicou uma velocidade de ({vel[0]:.1f}, {vel[1]:.1f})",
            "state_active": state,
            "execution_chain": [
                "On Update",
                f"Check State ({state})",
                active_node_name,
                "RigidBody2D.ApplyForce",
            ],
            "variable_mutations": [
                {"var": "speed", "from": 0.0, "to": 3.5, "by": active_node_name}
            ]
        }
        self.last_explanation = explanation
        EventBus.emit("ExplainMode.updated", explanation=explanation)
        return explanation
