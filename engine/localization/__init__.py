from .manager import LocalizationManager, tr
from .events import LocalizationChangedEvent
try:
    from .keys import LocaleKeys
except ImportError:
    class LocaleKeys: pass

__all__ = ["LocalizationManager", "tr", "LocaleKeys", "LocalizationChangedEvent"]
