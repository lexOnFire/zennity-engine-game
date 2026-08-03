"""EngineProvider oficial da Extension Platform da Zennity Engine."""
from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata.asset import AssetTypeDefinition
from engine.extension.metadata import ExtensionPackageDefinition, ExtensionType


class ExtensionProvider(EngineProvider):
    """Provedor oficial do ecossistema de extensões e plugins."""

    def register_services(self, context: EngineContext) -> None:
        pass

    def boot(self, context: EngineContext) -> None:
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return

        # 1. Registro de tipos de assets (.zext e .zplugin)
        manager.register(AssetTypeDefinition(id="extension_package", title_key="asset.extension_package", extensions=[".zext", ".zplugin"]))

        # 2. Registro de Extensões Nativas no Ecossistema
        manager.register(ExtensionPackageDefinition(id="ext.2d_physics", name="Physics 2D Engine", extension_type=ExtensionType.PLUGIN.value))
        manager.register(ExtensionPackageDefinition(id="ext.dark_theme", name="Dark Midnight Theme", extension_type=ExtensionType.THEME.value))
        manager.register(ExtensionPackageDefinition(id="ext.rpg_nodes", name="RPG Dialogue Node Pack", extension_type=ExtensionType.NODE_PACK.value))
        manager.register(ExtensionPackageDefinition(id="ext.platformer_template", name="2D Platformer Template", extension_type=ExtensionType.TEMPLATE.value))
