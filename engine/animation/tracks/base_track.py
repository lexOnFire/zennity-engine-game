from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict


class AnimationTrack(ABC):
    """
    Classe base abstrata para todas as Trilhas do Track Framework da Zennity Engine.
    Permite sequenciar e interpolar qualquer tipo de dado em tempo de execução.
    """

    def __init__(self, name: str = "Track", enabled: bool = True) -> None:
        self.name = str(name)
        self.enabled = bool(enabled)

    @abstractmethod
    def sample(self, time_seconds: float, target: Any) -> Any:
        """Avalia a trilha para o instante informado e aplica os efeitos no alvo."""
        pass

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        """Serializa os dados da trilha em dicionário JSON-safe."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "type": self.__class__.__name__,
        }

    @abstractmethod
    def deserialize(self, data: Dict[str, Any]) -> None:
        """Carrega as propriedades da trilha a partir de um dicionário."""
        self.name = str(data.get("name", self.name))
        self.enabled = bool(data.get("enabled", True))
