from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.graphics.camera import Camera


class CameraManager:
    """
    Gerenciador central de câmeras do runtime.
    Responsável por registrar, ordenar e determinar a câmera principal ativa.
    """
    _cameras: List[Camera] = []

    @classmethod
    def register_camera(cls, camera: Camera) -> None:
        """Registra uma câmera ativa."""
        if camera not in cls._cameras:
            cls._cameras.append(camera)
            cls.sort_cameras()

    @classmethod
    def remove_camera(cls, camera: Camera) -> None:
        """Remove uma câmera previamente registrada."""
        if camera in cls._cameras:
            cls._cameras.remove(camera)

    @classmethod
    def get_all_cameras(cls) -> List[Camera]:
        """Retorna a lista de todas as câmeras registradas."""
        return list(cls._cameras)

    @classmethod
    def sort_cameras(cls) -> None:
        """Ordena as câmeras por prioridade em ordem decrescente (maior prioridade primeiro)."""
        cls._cameras.sort(key=lambda c: c.priority, reverse=True)

    @classmethod
    def get_main_camera(cls) -> Optional[Camera]:
        """Localiza a câmera principal ativa de maior prioridade."""
        cls.sort_cameras()
        for camera in cls._cameras:
            if camera.active:
                return camera
        return None

    @classmethod
    def set_main_camera(cls, camera: Camera) -> None:
        """Define a câmera principal e desativa as demais."""
        for c in cls._cameras:
            if c is camera:
                c.active = True
            else:
                c.active = False
        cls.sort_cameras()

    @classmethod
    def clear(cls) -> None:
        """Limpa o registro de câmeras."""
        cls._cameras.clear()
