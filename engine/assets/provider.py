from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata.asset import AssetTypeDefinition, ImporterDefinition
from engine.assets.asset_database import AssetDatabase
from engine.assets.runtime_asset_manager import RuntimeAssetManager
from engine.assets.asset_importer import TextureImporter, AudioImporter, ScriptImporter, TilemapImporter


class AssetProvider(EngineProvider):
    """Provides core asset types metadata and registers AssetDatabase & RuntimeAssetManager services."""
    
    def register_services(self, context: EngineContext) -> None:
        db = AssetDatabase()
        context.services.register(AssetDatabase, db)
        runtime_mgr = RuntimeAssetManager()
        context.services.register(RuntimeAssetManager, runtime_mgr)
        
    def boot(self, context: EngineContext) -> None:
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return
            
        manager.register(AssetTypeDefinition(
            id="scene", title_key="asset.scene", extensions=[".zscene"], icon="🎬 "
        ))
        manager.register(AssetTypeDefinition(
            id="image", title_key="asset.image", extensions=[".png", ".jpg", ".jpeg", ".bmp", ".webp"], icon="🖼️ "
        ))
        manager.register(AssetTypeDefinition(
            id="audio", title_key="asset.audio", extensions=[".wav", ".ogg", ".mp3"], icon="🔊 "
        ))
        manager.register(AssetTypeDefinition(
            id="script", title_key="asset.script", extensions=[".py"], icon="🐍 "
        ))
        manager.register(AssetTypeDefinition(
            id="font", title_key="asset.font", extensions=[".ttf", ".otf"], icon="🔤 "
        ))
        manager.register(AssetTypeDefinition(
            id="material", title_key="asset.material", extensions=[".zmat"], icon="🎨 "
        ))
        manager.register(AssetTypeDefinition(
            id="prefab", title_key="asset.prefab", extensions=[".zprefab"], icon="📦 "
        ))
        manager.register(AssetTypeDefinition(
            id="animation", title_key="asset.animation", extensions=[".zanim"], icon="🎞 "
        ))
        manager.register(AssetTypeDefinition(
            id="animator", title_key="asset.animator", extensions=[".zanimator"], icon="◉ "
        ))
        manager.register(AssetTypeDefinition(
            id="logic_graph", title_key="asset.logic_graph", extensions=[".zlogic"], icon="◇ "
        ))
        manager.register(AssetTypeDefinition(
            id="blackboard", title_key="asset.blackboard", extensions=[".zblackboard"], icon="▦ "
        ))
        manager.register(AssetTypeDefinition(
            id="tilemap", title_key="asset.tilemap", extensions=[".tmx"], icon="🗺️ "
        ))
        manager.register(AssetTypeDefinition(
            id="behavior_tree", title_key="asset.behavior_tree", extensions=[".zbehavior"], icon="🌳 "
        ))
        manager.register(AssetTypeDefinition(
            id="dialogue", title_key="asset.dialogue", extensions=[".zdialogue"], icon="💬 "
        ))
        manager.register(AssetTypeDefinition(
            id="ui_layout", title_key="asset.ui_layout", extensions=[".zui"], icon="🖥️ "
        ))
        
        manager.register(ImporterDefinition(
            id="texture_importer",
            extensions=TextureImporter.get_supported_extensions(),
            importer_class=TextureImporter
        ))
        manager.register(ImporterDefinition(
            id="audio_importer",
            extensions=AudioImporter.get_supported_extensions(),
            importer_class=AudioImporter
        ))
        manager.register(ImporterDefinition(
            id="script_importer",
            extensions=ScriptImporter.get_supported_extensions(),
            importer_class=ScriptImporter
        ))
        manager.register(ImporterDefinition(
            id="tilemap_importer",
            extensions=TilemapImporter.get_supported_extensions(),
            importer_class=TilemapImporter
        ))
