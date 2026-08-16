"""engine/simulation/render_batch.py
────────────────────────────────────────────────────────────────
Pipeline de renderização em lote para entidades de simulação leves (2D).

Oferece:
  - SimulationRenderBuffer (SoA linear compacto: position, sprite_id, layer, entity_id)
  - BatchedSimulationRenderer (Culling em lote O(N), transformação de câmera canônica, ordenação determinística e submissão contígua rápida no Pygame)
  - Zero criação de GameObject, Transform, Component, LogicGraph ou UUID por entidade
  - 100% testável em modo headless sem janelas do sistema operacional.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import pygame
except ImportError:
    pygame = None  # type: ignore


class SimulationRenderBuffer:
    """
    Buffer de instâncias visuais para simulações massivas baseado em Structure of Arrays (SoA).
    """

    def __init__(self, initial_capacity: int = 1024) -> None:
        self._capacity: int = max(initial_capacity, 16)
        self.count: int = 0

        # Arrays SoA contíguos
        self.position_x: List[float] = [0.0] * self._capacity
        self.position_y: List[float] = [0.0] * self._capacity
        self.sprite_ids: List[int] = [0] * self._capacity
        self.layers: List[int] = [0] * self._capacity
        self.entity_indices: List[int] = [-1] * self._capacity

    def clear(self) -> None:
        """Limpa o buffer para o próximo frame sem desalocar memória."""
        self.count = 0

    def _grow(self) -> None:
        new_cap = self._capacity * 2
        additional = new_cap - self._capacity
        self.position_x.extend([0.0] * additional)
        self.position_y.extend([0.0] * additional)
        self.sprite_ids.extend([0] * additional)
        self.layers.extend([0] * additional)
        self.entity_indices.extend([-1] * additional)
        self._capacity = new_cap

    def submit(self, x: float, y: float, sprite_id: int = 0, layer: int = 0, entity_index: int = -1) -> None:
        """Submete uma instância visual ao buffer em O(1) amortizado."""
        if self.count >= self._capacity:
            self._grow()

        idx = self.count
        self.position_x[idx] = float(x)
        self.position_y[idx] = float(y)
        self.sprite_ids[idx] = int(sprite_id)
        self.layers[idx] = int(layer)
        self.entity_indices[idx] = int(entity_index)
        self.count += 1

    def sync_from_pool(
        self,
        pool: Any,
        sprite_id: int = 0,
        layer: int = 0,
        visual_map: Optional[Dict[int, int]] = None,
    ) -> None:
        """
        Sincroniza o render buffer diretamente a partir dos arrays de um SimulationEntityPool.
        """
        self.clear()
        px = pool.position_x
        py = pool.position_y

        for idx in pool.iter_alive_indices():
            s_id = visual_map.get(idx, sprite_id) if visual_map else sprite_id
            self.submit(px[idx], py[idx], sprite_id=s_id, layer=layer, entity_index=idx)


class BatchedSimulationRenderer:
    """
    Renderizador em lote que executa culling centralizado e submissão contígua ao Pygame Surface.
    """

    def __init__(self) -> None:
        self.last_stats: Dict[str, Any] = {}

    @staticmethod
    def world_to_screen_canonical(
        world_x: float,
        world_y: float,
        cam_x: float,
        cam_y: float,
        zoom: float,
        screen_w: int,
        screen_h: int,
    ) -> Tuple[float, float]:
        """
        Transformação canônica de câmera 100% idêntica ao contrato de Camera.world_to_screen()
        quando viewport_rect = (0, 0, 1, 1).
        """
        screen_x = (world_x - cam_x) * zoom + (screen_w / 2.0)
        screen_y = (world_y - cam_y) * zoom + (screen_h / 2.0)
        return screen_x, screen_y

    def render(
        self,
        buffer: SimulationRenderBuffer,
        camera: Any,
        target_surface: Any,
        sprite_registry: Dict[int, Any],
        default_sprite_size: Tuple[int, int] = (16, 16),
    ) -> Dict[str, Any]:
        """
        Executa culling, screen transform e submissão ao target_surface.
        Retorna estatísticas detalhadas do frame de render.
        """
        t_start = time.perf_counter()

        submitted = buffer.count
        if submitted == 0 or target_surface is None:
            stats = {
                "submitted_instances": submitted,
                "visible_instances": 0,
                "culled_instances": 0,
                "draw_operations": 0,
                "buffer_build_s": 0.0,
                "culling_s": 0.0,
                "sorting_s": 0.0,
                "draw_s": 0.0,
                "total_s": 0.0,
            }
            self.last_stats = stats
            return stats

        # Resolve câmera
        if hasattr(camera, "game_object") and camera.game_object is not None:
            cam_pos = camera.game_object.transform.position
            cam_x, cam_y = float(cam_pos[0]), float(cam_pos[1])
        elif isinstance(camera, (tuple, list)):
            cam_x, cam_y = float(camera[0]), float(camera[1])
        else:
            cam_x, cam_y = 0.0, 0.0

        zoom = float(getattr(camera, "zoom", 1.0))
        screen_w = target_surface.get_width()
        screen_h = target_surface.get_height()

        # 1. Culling bounds em coordenadas de mundo
        # Visão de mundo visível: [cam_x - half_w / zoom, cam_x + half_w / zoom]
        half_view_w = (screen_w / 2.0) / zoom
        half_view_h = (screen_h / 2.0) / zoom

        # Margem de culling baseada no tamanho da sprite
        margin_x = default_sprite_size[0] / 2.0
        margin_y = default_sprite_size[1] / 2.0

        min_world_x = cam_x - half_view_w - margin_x
        max_world_x = cam_x + half_view_w + margin_x
        min_world_y = cam_y - half_view_h - margin_y
        max_world_y = cam_y + half_view_h + margin_y

        t_cull_start = time.perf_counter()

        # 2. Culling centralizado O(N)
        visible_indices: List[int] = []
        px = buffer.position_x
        py = buffer.position_y

        for i in range(submitted):
            x = px[i]
            y = py[i]
            if min_world_x <= x <= max_world_x and min_world_y <= y <= max_world_y:
                visible_indices.append(i)

        t_cull_end = time.perf_counter()
        visible_count = len(visible_indices)
        culled_count = submitted - visible_count

        # 3. Ordenação determinística por Layer (Fast-path se todos layer 0)
        t_sort_start = time.perf_counter()
        layers = buffer.layers
        has_multiple_layers = any(layers[i] != 0 for i in visible_indices)

        if has_multiple_layers:
            visible_indices.sort(key=lambda idx: (layers[idx], buffer.entity_indices[idx]))

        t_sort_end = time.perf_counter()

        # 4. Submissão ao backend (Pygame blit)
        t_draw_start = time.perf_counter()
        draw_ops = 0
        sprite_ids = buffer.sprite_ids

        for i in visible_indices:
            wx = px[i]
            wy = py[i]
            sx, sy = self.world_to_screen_canonical(wx, wy, cam_x, cam_y, zoom, screen_w, screen_h)

            s_id = sprite_ids[i]
            surf = sprite_registry.get(s_id)
            if surf is not None and pygame is not None:
                # Centraliza o blit no pixel transformado
                target_surface.blit(surf, (int(sx - surf.get_width() / 2), int(sy - surf.get_height() / 2)))
                draw_ops += 1
            else:
                # Simulação headless ou sem Surface registrada
                draw_ops += 1

        t_draw_end = time.perf_counter()

        stats = {
            "submitted_instances": submitted,
            "visible_instances": visible_count,
            "culled_instances": culled_count,
            "draw_operations": draw_ops,
            "culling_s": t_cull_end - t_cull_start,
            "sorting_s": t_sort_end - t_sort_start,
            "draw_s": t_draw_end - t_draw_start,
            "total_s": time.perf_counter() - t_start,
        }
        self.last_stats = stats
        return stats
