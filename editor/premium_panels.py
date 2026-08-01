import warnings
from editor.premium_hierarchy_panel import RealHierarchyPanel
from editor.premium_inspector_panel import RealInspectorPanel

warnings.warn(
    "editor.premium_panels está deprecado (legado embutido).",
    DeprecationWarning,
    stacklevel=2,
)


__all__ = ["RealHierarchyPanel", "RealInspectorPanel"]
