from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class AssetHandle:
    """Identificador imutável e estável para recursos da Zennity Engine."""
    guid: str = ""

    def is_valid(self) -> bool:
        return bool(self.guid and self.guid.strip())

    def __str__(self) -> str:
        return self.guid

    def __bool__(self) -> bool:
        return self.is_valid()
