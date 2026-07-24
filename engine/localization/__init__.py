from .manager import LocalizationManager, tr
try:
    from .keys import LocaleKeys
except ImportError:
    # Keys not generated yet
    class LocaleKeys: pass

__all__ = ["LocalizationManager", "tr", "LocaleKeys"]
