"""Constants for the Zennity .zscene JSON format."""

# CONSOLIDATION (unificação de scene serialization): a constante ficava em 1,
# mas o editor real (editor/scene_persistence.py) sempre grava format_version
# 2 há muito tempo -- 14 das 15 cenas .zscene reais do projeto já são
# format_version 2. A constante estava simplesmente desatualizada em relação
# ao formato que está de fato em produção. Ver engine/scene/scene_serializer.py
# para o que muda entre as duas versões (layer como string, visual.texture,
# components.camera/audio sempre gravados, blackboard/editor_data preservados).
SCENE_FORMAT_VERSION = 2
ENGINE_VERSION = "0.1.0"

DEFAULT_SCENE_NAME = "Untitled"
DEFAULT_LAYER = "Default"
