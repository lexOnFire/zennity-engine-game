from __future__ import annotations
from typing import Any, List, Optional


class CameraManager:
    """
    Gerenciador central de câmeras do runtime.
    Responsável por registrar, ordenar e determinar a câmera principal ativa.
    """
    _cameras: List[Any] = []

    @classmethod
    def register_camera(cls, camera: Any) -> None:
        """Registra uma câmera ativa."""
        if camera not in cls._cameras:
            cls._cameras.append(camera)
            cls.sort_cameras()

    @classmethod
    def remove_camera(cls, camera: Any) -> None:
        """Remove uma câmera previamente registrada."""
        if camera in cls._cameras:
            cls._cameras.remove(camera)

    @classmethod
    def get_all_cameras(cls) -> List[Any]:
        """Retorna a lista de todas as câmeras registradas."""
        return list(cls._cameras)

    @classmethod
    def sort_cameras(cls) -> None:
        """Ordena as câmeras por prioridade em ordem decrescente (maior prioridade primeiro)."""
        cls._cameras.sort(key=lambda c: c.priority, reverse=True)

    @classmethod
    def get_main_camera(cls) -> Optional[Any]:
        """Localiza a câmera principal ativa de maior prioridade."""
        cls.sort_cameras()
        for camera in cls._cameras:
            if camera.active:
                return camera
        return None

    @classmethod
    def set_main_camera(cls, camera: Any) -> None:
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
