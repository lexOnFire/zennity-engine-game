"""Typed events for the Localization System."""
from dataclasses import dataclass

@dataclass
class LocalizationChangedEvent:
    locale: str
    previous_locale: str
