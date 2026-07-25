"""EngineProvider do sistema de Materiais e Shaders da Zennity Engine."""
from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata.asset import AssetTypeDefinition
from engine.graphics.material_nodes import (
    TextureSampleNode,
    ColorConstantNode,
    FloatConstantNode,
    VectorMathNode,
    PBRMaterialOutputNode,
)


class MaterialProvider(EngineProvider):
    """Provedor oficial de metadados de Materiais e Shaders."""

    def register_services(self, context: EngineContext) -> None:
        pass

    def boot(self, context: EngineContext) -> None:
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return

        # 1. Registro do Asset de Material (.zmat)
        manager.register(AssetTypeDefinition(
            id="material_graph",
            title_key="asset.material_graph",
            extensions=[".zmat"],
        ))

        # 2. Registro dos Nós de Material no Graph Framework
        manager.register(TextureSampleNode.__node_definition__)
        manager.register(ColorConstantNode.__node_definition__)
        manager.register(FloatConstantNode.__node_definition__)
        manager.register(VectorMathNode.__node_definition__)
        manager.register(PBRMaterialOutputNode.__node_definition__)
