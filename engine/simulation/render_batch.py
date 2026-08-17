"""engine/simulation/render_batch.py
────────────────────────────────────────────────────────────────
Pipeline de renderização em lote para entidades de simulação leves (2D).

Oferece:
  - SimulationRenderBuffer (SoA linear compacto: position, sprite_id, layer, entity_id)
  - Direct / Contiguous buffer synchronization a partir de SimulationEntityPool
  - BatchedSimulationRenderer (Culling em lote O(N), transformação de câmera canônica inlinada,
    cache interno de dimensões de sprite, submissão em lote acelerada via Surface.blits)
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

    def _ensure_capacity(self, min_capacity: int) -> None:
        if min_capacity <= self._capacity:
            return
        new_cap = max(self._capacity * 2, min_capacity)
        additional = new_cap - self._capacity
        self.position_x.extend([0.0] * additional)
        self.position_y.extend([0.0] * additional)
        self.sprite_ids.extend([0] * additional)
        self.layers.extend([0] * additional)
        self.entity_indices.extend([-1] * additional)
        self._capacity = new_cap

    def _grow(self) -> None:
        self._ensure_capacity(self._capacity * 2)

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
        Sincroniza o render buffer diretamente a partir dos arrays de um SimulationEntityPool
        com escrita contígua direta de alta velocidade sem overhead de submit individual.
        """
        alive_count = pool.count if hasattr(pool, "count") else len(pool.iter_alive_indices())
        self._ensure_capacity(alive_count)

        self.count = 0
        px_src = pool.position_x
        py_src = pool.position_y

        px_dst = self.position_x
        py_dst = self.position_y
        s_dst = self.sprite_ids
        l_dst = self.layers
        e_dst = self.entity_indices

        cnt = 0
        int_layer = int(layer)
        default_s_id = int(sprite_id)

        if visual_map:
            for idx in pool.iter_alive_indices():
                px_dst[cnt] = float(px_src[idx])
                py_dst[cnt] = float(py_src[idx])
                s_dst[cnt] = int(visual_map.get(idx, default_s_id))
                l_dst[cnt] = int_layer
                e_dst[cnt] = idx
                cnt += 1
        else:
            for idx in pool.iter_alive_indices():
                px_dst[cnt] = float(px_src[idx])
                py_dst[cnt] = float(py_src[idx])
                s_dst[cnt] = default_s_id
                l_dst[cnt] = int_layer
                e_dst[cnt] = idx
                cnt += 1

        self.count = cnt


class BatchedSimulationRenderer:
    """
    Renderizador em lote que executa culling centralizado e submissão contígua rápida ao Pygame Surface.
    """

    def __init__(self) -> None:
        self.last_stats: Dict[str, Any] = {}
        self._sprite_meta_cache: Dict[int, Tuple[Any, float, float]] = {}
        self._command_buffer: List[Tuple[Any, Tuple[int, int]]] = []

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

    def _update_sprite_cache(self, sprite_registry: Dict[int, Any]) -> Dict[int, Tuple[Any, float, float]]:
        """Atualiza e valida o cache de dimensões e metadados de sprites."""
        cache = self._sprite_meta_cache
        for s_id, surf in sprite_registry.items():
            entry = cache.get(s_id)
            if entry is None or entry[0] is not surf:
                w = surf.get_width() if surf is not None else 16.0
                h = surf.get_height() if surf is not None else 16.0
                cache[s_id] = (surf, w / 2.0, h / 2.0)
        return cache

    def render(
        self,
        buffer: SimulationRenderBuffer,
        camera: Any,
        target_surface: Any,
        sprite_registry: Dict[int, Any],
        default_sprite_size: Tuple[int, int] = (16, 16),
        use_blits: bool = True,
    ) -> Dict[str, Any]:
        """
        Executa culling, screen transform e submissão ao target_surface com aceleração por Surface.blits.
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
                "backend_submit_calls": 0,
                "culling_s": 0.0,
                "sorting_s": 0.0,
                "draw_s": 0.0,
                "total_s": 0.0,
            }
            self.last_stats = stats
            return stats

        # Resolve parâmetros de câmera
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
        half_screen_w = screen_w / 2.0
        half_screen_h = screen_h / 2.0

        # Atualiza cache de metadados das sprites
        sprite_meta = self._update_sprite_cache(sprite_registry)

        # 1. Culling bounds em coordenadas de mundo
        half_view_w = half_screen_w / zoom
        half_view_h = half_screen_h / zoom

        margin_x = default_sprite_size[0] / 2.0
        margin_y = default_sprite_size[1] / 2.0

        min_world_x = cam_x - half_view_w - margin_x
        max_world_x = cam_x + half_view_w + margin_x
        min_world_y = cam_y - half_view_h - margin_y
        max_world_y = cam_y + half_view_h + margin_y

        t_cull_start = time.perf_counter()

        # 2. Culling centralizado O(N) com local bindings
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
            e_indices = buffer.entity_indices
            visible_indices.sort(key=lambda idx: (layers[idx], e_indices[idx]))

        t_sort_end = time.perf_counter()

        # 4. Submissão ao backend (Acelerada via Surface.blits ou fallback individual)
        t_draw_start = time.perf_counter()
        draw_ops = visible_count
        backend_submits = 0
        sprite_ids = buffer.sprite_ids

        can_blits = use_blits and (pygame is not None) and hasattr(target_surface, "blits")

        if can_blits:
            commands = self._command_buffer
            commands.clear()

            for i in visible_indices:
                wx = px[i]
                wy = py[i]
                # Inlining exato de world_to_screen_canonical
                sx = (wx - cam_x) * zoom + half_screen_w
                sy = (wy - cam_y) * zoom + half_screen_h

                s_id = sprite_ids[i]
                meta = sprite_meta.get(s_id)
                if meta is not None:
                    surf, half_w, half_h = meta
                    if surf is not None:
                        commands.append((surf, (int(sx - half_w), int(sy - half_h))))

            if commands:
                target_surface.blits(commands, doreturn=False)
                backend_submits = 1
        else:
            # Fallback individual blit loop
            blit_fn = target_surface.blit if hasattr(target_surface, "blit") else None
            for i in visible_indices:
                wx = px[i]
                wy = py[i]
                sx = (wx - cam_x) * zoom + half_screen_w
                sy = (wy - cam_y) * zoom + half_screen_h

                s_id = sprite_ids[i]
                meta = sprite_meta.get(s_id)
                if meta is not None and blit_fn is not None:
                    surf, half_w, half_h = meta
                    if surf is not None:
                        blit_fn(surf, (int(sx - half_w), int(sy - half_h)))
                        backend_submits += 1

        t_draw_end = time.perf_counter()

        stats = {
            "submitted_instances": submitted,
            "visible_instances": visible_count,
            "culled_instances": culled_count,
            "draw_operations": draw_ops,
            "backend_submit_calls": backend_submits,
            "culling_s": t_cull_end - t_cull_start,
            "sorting_s": t_sort_end - t_sort_start,
            "draw_s": t_draw_end - t_draw_start,
            "total_s": time.perf_counter() - t_start,
        }
        self.last_stats = stats
        return stats
