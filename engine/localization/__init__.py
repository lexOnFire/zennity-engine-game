from .manager import LocalizationManager, tr
from .events import LocalizationChangedEvent
try:
    from .keys import LocaleKeys
except ImportError:
    LocaleKeys = object

__all__ = ["LocalizationManager", "tr", "LocaleKeys", "LocalizationChangedEvent"]
