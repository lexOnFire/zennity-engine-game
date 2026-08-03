"""EngineProvider oficial da Plataforma de UI da Zennity Engine."""
from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata.asset import AssetTypeDefinition, PreviewDefinition
from engine.ui.metadata import WidgetDefinition
from engine.ui.preview_provider import UIPreviewProvider


class UIProvider(EngineProvider):
    """Provedor de infraestrutura, metadados e preview da Plataforma de UI."""

    def register_services(self, context: EngineContext) -> None:
        pass

    def boot(self, context: EngineContext) -> None:
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return

        # 1. Registro dos Assets de UI (Fase 1)
        manager.register(AssetTypeDefinition(id="ui_layout", title_key="asset.ui_layout", extensions=[".zui"]))
        manager.register(AssetTypeDefinition(id="ui_prefab", title_key="asset.ui_prefab", extensions=[".zuiprefab"]))
        manager.register(AssetTypeDefinition(id="ui_theme", title_key="asset.ui_theme", extensions=[".theme"]))
        manager.register(AssetTypeDefinition(id="ui_style", title_key="asset.ui_style", extensions=[".style"]))

        # 2. Registro dos Metadados dos Widgets (Fase 3)
        manager.register(WidgetDefinition(id="ui.canvas", widget_type="Canvas", category="UI Container"))
        manager.register(WidgetDefinition(id="ui.panel", widget_type="Panel", category="UI Container"))
        manager.register(WidgetDefinition(id="ui.button", widget_type="Button", category="UI Controls"))
        manager.register(WidgetDefinition(id="ui.label", widget_type="Label", category="UI Text"))
        manager.register(WidgetDefinition(id="ui.image", widget_type="Image", category="UI Graphics"))
        manager.register(WidgetDefinition(id="ui.scrollview", widget_type="ScrollView", category="UI Container"))
        manager.register(WidgetDefinition(id="ui.input", widget_type="Input", category="UI Controls"))

        # 3. Registro do Preview Provider de UI (Fase 4)
        manager.register(PreviewDefinition(id="ui_preview", provider_class=UIPreviewProvider))
