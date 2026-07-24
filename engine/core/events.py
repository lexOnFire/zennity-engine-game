"""Core typed events for Zennity Engine."""
from dataclasses import dataclass

@dataclass
class ServiceInitializedEvent:
    service_name: str

@dataclass
class EngineShutdownEvent:
    reason: str
