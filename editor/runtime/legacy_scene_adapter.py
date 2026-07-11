from typing import Any
import pygame

class LegacySceneAdapter:
    """
    Adapter para encapsular e isolar chamadas de métodos da cena legada.
    Impede que o ViewportWidget (e outros sistemas) invoquem diretamente
    métodos que variam entre Editor2DScene e cenas antigas.
    """

    @staticmethod
    def draw(scene: Any, surface: pygame.Surface) -> None:
        # Pinta o fundo primeiro
        if hasattr(scene, "_layout") and not hasattr(scene, "_lay"):
            surface.fill((28, 29, 36))
        else:
            surface.fill((30, 30, 30))
            
        if hasattr(scene, "draw"):
            scene.draw(surface)
            
        # Fallback de geometria legacy 2D
        if hasattr(scene, "_layout") and not hasattr(scene, "_lay"):
            lay = scene._layout()
            if hasattr(scene, "_draw_viewport"):
                scene._draw_viewport(surface, lay)
                return
            # O loop de desenho legado duplicado foi desativado temporariamente para o experimento
            # for idx, obj in enumerate(getattr(scene, "game_objects", [])):
            #     if obj is getattr(scene, "cam_obj", None):
            #         continue
            #     if hasattr(scene, "_draw_object"):
            #         scene._draw_object(surface, obj, idx, 1.0, lay)
            #     elif hasattr(obj, "draw"):
            #         obj.draw(surface)

    @staticmethod
    def handle_event(scene: Any, event: pygame.event.Event) -> None:
        if hasattr(scene, "handle_event"):
            scene.handle_event(event)

    @staticmethod
    def spawn_object(scene: Any, shape: str) -> None:
        if hasattr(scene, "spawn_object"):
            scene.spawn_object(shape)

    @staticmethod
    def delete_selected(scene: Any) -> None:
        if hasattr(scene, "delete_selected"):
            scene.delete_selected()

    @staticmethod
    def duplicate_selected(scene: Any) -> None:
        if hasattr(scene, "duplicate_selected"):
            scene.duplicate_selected()
