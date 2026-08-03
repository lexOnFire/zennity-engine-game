from __future__ import annotations
from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.graphics.camera import Camera
    from engine.graphics.camera2d import Camera2D


def get_active_camera() -> Optional[Union["Camera", "Camera2D"]]:
    """
    Ponto único de resolução de "qual câmera usar" para código de renderização.

    `Camera` (engine/graphics/camera.py) é a fonte de verdade oficial: é a única
    registrada no component_registry, serializada em .zscene e usada pelo pipeline
    de build/runtime. `Camera2D` (engine/graphics/camera2d.py) é legada, mantida
    para follow-target embutido usado por demos e pela câmera de viewport do editor
    (que não é um GameObject de cena). Antes desta função, o fallback
    `Camera.main or Camera2D.main` era reimplementado manualmente em 7 arquivos
    diferentes (renderer.py, particles.py, tilemap.py, renderer2d.py x2,
    ui/runtime_components.py x2) — centralizado aqui para evitar divergência.

    Vive em módulo próprio (em vez de camera_manager.py) para não criar um
    ciclo de import entre camera.py e camera_manager.py: ambos já se importam
    um ao outro de forma lazy, e o gate de arquitetura do projeto
    (tests/architecture/test_no_circular_imports.py) trata qualquer import no
    corpo do arquivo — mesmo dentro de função — como aresta do grafo.
    """
    from engine.graphics.camera import Camera
    cam = Camera.main
    if cam is not None:
        return cam
    from engine.graphics.camera2d import Camera2D
    return Camera2D.main
