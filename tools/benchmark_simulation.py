"""tools/benchmark_simulation.py
────────────────────────────────────────────────────────────────
Ferramenta CLI genérica de benchmark para simulações massivas na Zennity Engine.

Executa diagnósticos de desempenho de:
  - BENCH A: SimulationEntityPool (create, iterate, destroy, reuse, memory)
  - BENCH B: SystemScheduler (dispatch multi-taxa 60Hz/10Hz/1Hz)
  - BENCH C: SpatialHash2D vs Brute Force (Uniform, Clustered, Hotspot)
  - BENCH D: AStarPathfinder (pesquisa de rotas em grids e saturação)
  - BENCH E: FlowField2D vs N A* (destinos compartilhados e frequência de rebuild)
  - BENCH F: SimulationRenderBuffer + BatchedSimulationRenderer (frações de visibilidade)
  - BENCH G: Simulação Sintética Integrada (Pipeline Completo: Scheduler + Pool + SpatialHash + FlowField + RenderBuffer + Renderer)
  - BENCH H: Simulation LOD (Classificação O(N), tiers de frequência e redução de expensive updates)
  - BENCH I: Spatial Update Optimization & Transitions (Same-cell vs Transitions vs Bulk sync)
  - BENCH J: Batch Renderer Optimization (Individual Blit vs Surface.blits por contagem visível)
  - BENCH K: Temporal Query Smoothing (Burst 10Hz vs Distributed Temporal Smoothing)
  - SCALE GATE: Validação de escalabilidade para 10k, 15k e 25k entidades
  - Testes de Lifecycle Reset e Memory Leak.
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import os
import platform
import random
import sys
import time
import tracemalloc
from typing import Any, Dict, List, Optional, Tuple

# Garante path para importar engine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
from engine.simulation import (
    LOD_HIGH,
    LOD_LOW,
    LOD_MEDIUM,
    LOD_SLEEP,
    AStarPathfinder,
    BatchedSimulationRenderer,
    EntityHandle,
    FlowField2D,
    NavigationGrid2D,
    SimulationEntityPool,
    SimulationFocus,
    SimulationLODConfig,
    SimulationLODManager,
    SimulationRenderBuffer,
    SpatialHash2D,
    SystemScheduler,
    TemporalWorkDistributor,
    TickPolicy,
)
from engine.system import System


def calculate_percentiles(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"mean": 0.0, "median": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0, "stddev": 0.0}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mean_val = sum(sorted_vals) / n
    median_val = sorted_vals[n // 2]
    p95_idx = min(int(n * 0.95), n - 1)
    p95_val = sorted_vals[p95_idx]
    p99_idx = min(int(n * 0.99), n - 1)
    p99_val = sorted_vals[p99_idx]
    max_val = sorted_vals[-1]
    variance = sum((x - mean_val) ** 2 for x in sorted_vals) / n
    stddev_val = math.sqrt(variance)
    return {
        "mean": mean_val,
        "median": median_val,
        "p95": p95_val,
        "p99": p99_val,
        "max": max_val,
        "stddev": stddev_val,
    }


# ==============================================================================
# BENCH A: ENTITY POOL
# ==============================================================================
def run_bench_a(populations: List[int], rng: random.Random) -> Dict[str, Any]:
    results = {}
    for count in populations:
        gc.collect()
        tracemalloc.start()
        t0 = time.perf_counter()
        pool = SimulationEntityPool(initial_capacity=count)
        handles = [pool.create(position=(rng.uniform(-100, 100), rng.uniform(-100, 100)), velocity=(1.0, 1.0)) for _ in range(count)]
        create_s = time.perf_counter() - t0

        t0 = time.perf_counter()
        px = pool.position_x
        py = pool.position_y
        vx = pool.velocity_x
        vy = pool.velocity_y
        dt = 0.016
        for _ in range(60):
            for idx in pool.iter_alive_indices():
                px[idx] += vx[idx] * dt
                py[idx] += vy[idx] * dt
        move_60_frames_s = time.perf_counter() - t0

        t0 = time.perf_counter()
        for h in handles[:count // 2]:
            pool.destroy(h)
        destroy_half_s = time.perf_counter() - t0

        t0 = time.perf_counter()
        reused_handles = [pool.create(position=(0.0, 0.0)) for _ in range(count // 2)]
        reuse_s = time.perf_counter() - t0

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        results[str(count)] = {
            "create_ms": create_s * 1000.0,
            "move_60_frames_ms": move_60_frames_s * 1000.0,
            "move_per_frame_ms": (move_60_frames_s / 60.0) * 1000.0,
            "destroy_half_ms": destroy_half_s * 1000.0,
            "reuse_half_ms": reuse_s * 1000.0,
            "approx_memory_kb": peak_mem / 1024.0,
        }
    return results


# ==============================================================================
# BENCH B: SCHEDULER
# ==============================================================================
class SyntheticMoveSys(System):
    def __init__(self, pool: SimulationEntityPool) -> None:
        super().__init__()
        self.pool = pool
        self.calls = 0

    def update(self, scene, dt: float) -> None:
        self.calls += 1
        px = self.pool.position_x
        py = self.pool.position_y
        vx = self.pool.velocity_x
        vy = self.pool.velocity_y
        for idx in self.pool.iter_alive_indices():
            px[idx] += vx[idx] * dt
            py[idx] += vy[idx] * dt


class SyntheticDecisionSys(System):
    def __init__(self, pool: SimulationEntityPool) -> None:
        super().__init__()
        self.pool = pool
        self.calls = 0

    def update(self, scene, dt: float) -> None:
        self.calls += 1
        states = self.pool.state
        for idx in self.pool.iter_alive_indices():
            states[idx] = (states[idx] + 1) % 10


def run_bench_b(populations: List[int]) -> Dict[str, Any]:
    results = {}
    for count in populations:
        pool = SimulationEntityPool(initial_capacity=count)
        for _ in range(count):
            pool.create(position=(0.0, 0.0), velocity=(1.0, 1.0))

        scheduler = SystemScheduler()
        move_sys = SyntheticMoveSys(pool)
        dec_sys = SyntheticDecisionSys(pool)

        scheduler.register(move_sys, TickPolicy.fixed_hz(60), priority=100)
        scheduler.register(dec_sys, TickPolicy.fixed_hz(10), priority=200)

        t0 = time.perf_counter()
        for _ in range(60):
            scheduler.update(None, 0.016)
        total_s = time.perf_counter() - t0

        results[str(count)] = {
            "total_60_frames_ms": total_s * 1000.0,
            "avg_frame_ms": (total_s / 60.0) * 1000.0,
            "move_calls": move_sys.calls,
            "decision_calls": dec_sys.calls,
        }
    return results


# ==============================================================================
# BENCH C: SPATIAL HASH
# ==============================================================================
def run_bench_c(populations: List[int], rng: random.Random) -> Dict[str, Any]:
    results = {}
    for count in populations:
        pool = SimulationEntityPool(initial_capacity=count)
        sh = SpatialHash2D(cell_size=64.0)

        # 1. Uniform
        handles = []
        for _ in range(count):
            x = rng.uniform(-1000.0, 1000.0)
            y = rng.uniform(-1000.0, 1000.0)
            h = pool.create(position=(x, y))
            handles.append(h)
            sh.insert(h, x, y)

        t0 = time.perf_counter()
        sh_results = []
        for _ in range(50):
            qx = rng.uniform(-800.0, 800.0)
            qy = rng.uniform(-800.0, 800.0)
            res = sh.query_radius(qx, qy, radius=64.0, pool=pool)
            sh_results.append(len(res))
        sh_time = time.perf_counter() - t0

        t0 = time.perf_counter()
        r2 = 64.0 * 64.0
        for _ in range(50):
            qx = rng.uniform(-800.0, 800.0)
            qy = rng.uniform(-800.0, 800.0)
            bf_res = []
            for h in handles:
                idx = h.index
                dx = pool.position_x[idx] - qx
                dy = pool.position_y[idx] - qy
                if (dx * dx + dy * dy) <= r2:
                    bf_res.append(h)
        bf_time = time.perf_counter() - t0

        # 2. Hotspot (Worst Case: todas na mesma célula)
        sh_hotspot = SpatialHash2D(cell_size=64.0)
        for h in handles:
            sh_hotspot.insert(h, 10.0, 10.0)
        t0 = time.perf_counter()
        for _ in range(50):
            _ = sh_hotspot.query_radius(10.0, 10.0, radius=64.0, pool=pool)
        hotspot_time = time.perf_counter() - t0

        results[str(count)] = {
            "spatial_hash_uniform_50_queries_ms": sh_time * 1000.0,
            "brute_force_uniform_50_queries_ms": bf_time * 1000.0,
            "speedup_uniform": (bf_time / sh_time) if sh_time > 0 else 1.0,
            "spatial_hash_hotspot_50_queries_ms": hotspot_time * 1000.0,
            "avg_candidates_found": sum(sh_results) / len(sh_results) if sh_results else 0,
        }
    return results


# ==============================================================================
# BENCH D: ASTAR
# ==============================================================================
def run_bench_d(grid_sizes: List[int], rng: random.Random) -> Dict[str, Any]:
    results = {}
    for size in grid_sizes:
        grid = NavigationGrid2D(width=size, height=size)
        for y in range(size // 4, 3 * size // 4):
            grid.set_walkable(size // 2, y, False)

        requests = 50
        t0 = time.perf_counter()
        found = 0
        for _ in range(requests):
            sx = rng.randint(0, size // 4)
            sy = rng.randint(0, size - 1)
            gx = rng.randint(3 * size // 4, size - 1)
            gy = rng.randint(0, size - 1)
            path = AStarPathfinder.find_path(grid, (sx, sy), (gx, gy))
            if path:
                found += 1
        duration_s = time.perf_counter() - t0

        avg_req_ms = (duration_s / requests) * 1000.0
        max_in_16ms = int(16.67 / avg_req_ms) if avg_req_ms > 0 else requests

        results[f"{size}x{size}"] = {
            "requests": requests,
            "total_ms": duration_s * 1000.0,
            "avg_request_ms": avg_req_ms,
            "success_rate": found / requests,
            "est_max_requests_per_16ms_frame": max_in_16ms,
        }
    return results


# ==============================================================================
# BENCH E: FLOWFIELD
# ==============================================================================
def run_bench_e(populations: List[int], rng: random.Random) -> Dict[str, Any]:
    grid = NavigationGrid2D(width=50, height=50)
    for y in range(10, 40):
        grid.set_walkable(25, y, False)

    goal = (45, 45)
    results = {}

    for count in populations:
        starts = [(rng.randint(0, 20), rng.randint(0, 45)) for _ in range(count)]

        # 1. FlowField
        t0 = time.perf_counter()
        flow = FlowField2D(grid)
        flow.build(goal)
        build_s = time.perf_counter() - t0

        t0 = time.perf_counter()
        for s in starts:
            _ = flow.get_direction(s[0], s[1])
        lookup_s = time.perf_counter() - t0
        flow_total_s = build_s + lookup_s

        # 2. A*
        t0 = time.perf_counter()
        for s in starts:
            _ = AStarPathfinder.find_path(grid, s, goal)
        astar_total_s = time.perf_counter() - t0

        results[str(count)] = {
            "flow_build_ms": build_s * 1000.0,
            "flow_lookups_ms": lookup_s * 1000.0,
            "flow_total_ms": flow_total_s * 1000.0,
            "astar_total_ms": astar_total_s * 1000.0,
            "speedup": (astar_total_s / flow_total_s) if flow_total_s > 0 else 1.0,
        }
    return results


# ==============================================================================
# BENCH F: RENDERER & VISIBLE FRACTIONS
# ==============================================================================
def run_bench_f(fractions: List[float], count: int = 5000) -> Dict[str, Any]:
    pygame.init()
    target_surf = pygame.Surface((1280, 720))
    sprite_surf = pygame.Surface((16, 16))
    registry = {1: sprite_surf}

    results = {}

    for frac in fractions:
        vis_count = int(count * frac)
        pool = SimulationEntityPool(initial_capacity=count)
        for i in range(count):
            if i < vis_count:
                x = float((i % 25) * 40 - 500)
                y = float((i // 25) * 30 - 250)
            else:
                x = float(2000.0 + i)
                y = float(2000.0 + i)
            pool.create(position=(x, y))

        buf = SimulationRenderBuffer(initial_capacity=count)
        renderer = BatchedSimulationRenderer()

        t0 = time.perf_counter()
        buf.sync_from_pool(pool, sprite_id=1)
        sync_time = time.perf_counter() - t0

        stats = renderer.render(buf, camera=(0.0, 0.0), target_surface=target_surf, sprite_registry=registry)

        results[f"{int(frac * 100)}%"] = {
            "submitted": stats["submitted_instances"],
            "visible": stats["visible_instances"],
            "culled": stats["culled_instances"],
            "draw_operations": stats["draw_operations"],
            "backend_submit_calls": stats.get("backend_submit_calls", 0),
            "buffer_sync_ms": sync_time * 1000.0,
            "culling_ms": stats["culling_s"] * 1000.0,
            "draw_ms": stats["draw_s"] * 1000.0,
            "total_render_ms": (sync_time + stats["total_s"]) * 1000.0,
        }
    return results


# ==============================================================================
# BENCH G: FULL INTEGRATED SYNTHETIC SIMULATION (WITH TEMPORAL SMOOTHING)
# ==============================================================================
class IntegratedAgentMovementSystem(System):
    def __init__(self, pool: SimulationEntityPool, flow: FlowField2D, speed: float = 50.0) -> None:
        super().__init__()
        self.pool = pool
        self.flow = flow
        self.speed = speed

    def update(self, scene, dt: float) -> None:
        px = self.pool.position_x
        py = self.pool.position_y
        vx = self.pool.velocity_x
        vy = self.pool.velocity_y
        for idx in self.pool.iter_alive_indices():
            dx, dy = self.flow.get_direction_world(px[idx], py[idx])
            vx[idx] = dx * self.speed
            vy[idx] = dy * self.speed
            px[idx] += vx[idx] * dt
            py[idx] += vy[idx] * dt


class IntegratedSpatialSyncSystem(System):
    def __init__(self, pool: SimulationEntityPool, spatial_hash: SpatialHash2D) -> None:
        super().__init__()
        self.pool = pool
        self.spatial_hash = spatial_hash

    def update(self, scene, dt: float) -> None:
        # Usa sync_from_pool bulk otimizado
        self.spatial_hash.sync_from_pool(self.pool)


class IntegratedSmoothNeighborQuerySystem(System):
    def __init__(self, pool: SimulationEntityPool, spatial_hash: SpatialHash2D, distributor: TemporalWorkDistributor) -> None:
        super().__init__()
        self.pool = pool
        self.spatial_hash = spatial_hash
        self.distributor = distributor
        self.total_neighbors = 0

    def update(self, scene, dt: float) -> None:
        indices = self.pool.iter_alive_indices()
        sample_size = max(1, len(indices) // 20)
        active_sample = indices[:sample_size]

        # Distribuição temporal determinística em 6 fases
        batch = self.distributor.select(active_sample)
        px = self.pool.position_x
        py = self.pool.position_y
        for idx in batch:
            nbrs = self.spatial_hash.query_radius(px[idx], py[idx], radius=40.0, pool=self.pool, ordered=False)
            self.total_neighbors += len(nbrs)
        self.distributor.advance()


def run_bench_g(populations: List[int], warmup_frames: int, measured_frames: int, rng: random.Random) -> Dict[str, Any]:
    pygame.init()
    target_surf = pygame.Surface((1280, 720))
    sprite_surf = pygame.Surface((16, 16))
    registry = {1: sprite_surf}

    grid = NavigationGrid2D(width=80, height=80, cell_size=32.0)
    for y in range(20, 60):
        grid.set_walkable(40, y, False)

    goal = (70, 70)
    flow = FlowField2D(grid)
    flow.build(goal)

    results = {}

    for count in populations:
        pool = SimulationEntityPool(initial_capacity=count)
        sh = SpatialHash2D(cell_size=64.0)

        for i in range(count):
            wx = rng.uniform(32.0, 500.0)
            wy = rng.uniform(32.0, 500.0)
            h = pool.create(position=(wx, wy), velocity=(1.0, 1.0))
            sh.insert(h, wx, wy)

        buf = SimulationRenderBuffer(initial_capacity=count)
        renderer = BatchedSimulationRenderer()

        scheduler = SystemScheduler()
        move_sys = IntegratedAgentMovementSystem(pool, flow)
        spatial_sys = IntegratedSpatialSyncSystem(pool, sh)
        distributor = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)
        neighbor_sys = IntegratedSmoothNeighborQuerySystem(pool, sh, distributor)

        scheduler.register(move_sys, TickPolicy.fixed_hz(60), priority=100)
        scheduler.register(spatial_sys, TickPolicy.fixed_hz(60), priority=200)
        # Registrado at every_frame para distribuição suave contínua
        scheduler.register(neighbor_sys, TickPolicy.every_frame(), priority=300)

        # Warmup
        dt = 1.0 / 60.0
        for _ in range(warmup_frames):
            scheduler.update(None, dt)
            buf.sync_from_pool(pool, sprite_id=1)
            renderer.render(buf, camera=(250.0, 250.0), target_surface=target_surf, sprite_registry=registry)

        # Reseta métricas do SpatialHash após o warmup para isolar os frames medidos
        sh.reset_profiling_stats()

        # Measured frames
        frame_times = []
        breakdown_movement = []
        breakdown_spatial = []
        breakdown_render = []

        for _ in range(measured_frames):
            t_frame_start = time.perf_counter()

            # Scheduler update
            t0 = time.perf_counter()
            scheduler.update(None, dt)
            t_sched = time.perf_counter() - t0

            # Render sync + draw
            t0 = time.perf_counter()
            buf.sync_from_pool(pool, sprite_id=1)
            renderer.render(buf, camera=(250.0, 250.0), target_surface=target_surf, sprite_registry=registry)
            t_render = time.perf_counter() - t0

            total_frame = time.perf_counter() - t_frame_start
            frame_times.append(total_frame * 1000.0)
            breakdown_movement.append(t_sched * 1000.0)
            breakdown_render.append(t_render * 1000.0)

        pcts = calculate_percentiles(frame_times)
        mean_ms = pcts["mean"]
        est_fps = (1000.0 / mean_ms) if mean_ms > 0 else 0.0

        avg_sched = sum(breakdown_movement) / len(breakdown_movement)
        avg_render = sum(breakdown_render) / len(breakdown_render)

        if avg_render > avg_sched:
            p_bot = "Batched Renderer (Culling + Blit)"
            s_bot = "Simulation Scheduler / Spatial Sync"
        else:
            p_bot = "Simulation Scheduler / Spatial Sync"
            s_bot = "Batched Renderer (Culling + Blit)"

        sh_stats = sh.get_profiling_stats()
        tot_up = sh_stats["update_calls"]
        same_cell = sh_stats["same_cell_updates"]
        transitions = sh_stats["cell_transitions"]
        same_cell_pct = (same_cell / tot_up * 100.0) if tot_up > 0 else 0.0

        results[str(count)] = {
            "mean_ms": pcts["mean"],
            "median_ms": pcts["median"],
            "p95_ms": pcts["p95"],
            "p99_ms": pcts.get("p99", pcts["p95"]),
            "max_ms": pcts["max"],
            "stddev_ms": pcts.get("stddev", 0.0),
            "estimated_fps": est_fps,
            "avg_scheduler_sim_ms": avg_sched,
            "avg_render_pass_ms": avg_render,
            "primary_bottleneck": p_bot,
            "secondary_bottleneck": s_bot,
            "spatial_profiling": {
                "update_calls": tot_up,
                "same_cell_updates": same_cell,
                "cell_transitions": transitions,
                "same_cell_percent": same_cell_pct,
                "query_calls": sh_stats["query_calls"],
                "candidate_entities_evaluated": sh_stats["candidate_entities_evaluated"],
                "bucket_mutations": sh_stats["bucket_mutations"],
                "bulk_sync_calls": sh_stats["bulk_sync_calls"],
            },
        }
    return results


# ==============================================================================
# BENCH H: SIMULATION LOD
# ==============================================================================
class SyntheticLODDecisionSystem(System):
    def __init__(self, pool: SimulationEntityPool, lod_mgr: SimulationLODManager, tier: int) -> None:
        super().__init__()
        self.pool = pool
        self.lod_mgr = lod_mgr
        self.tier = tier
        self.expensive_updates = 0

    def update(self, scene, dt: float) -> None:
        states = self.pool.state
        for idx in self.lod_mgr.iter_tier(self.tier):
            # Trabalho sintético pesado idêntico em baseline e LOD
            for _ in range(10):
                states[idx] = (states[idx] * 3 + 7) % 1000
            self.expensive_updates += 1


class SyntheticBaselineDecisionSystem(System):
    def __init__(self, pool: SimulationEntityPool) -> None:
        super().__init__()
        self.pool = pool
        self.expensive_updates = 0

    def update(self, scene, dt: float) -> None:
        states = self.pool.state
        for idx in self.pool.iter_alive_indices():
            for _ in range(10):
                states[idx] = (states[idx] * 3 + 7) % 1000
            self.expensive_updates += 1


def run_bench_h(populations: List[int], rng: random.Random) -> Dict[str, Any]:
    results = {}
    for count in populations:
        # Distribui entidades espacialmente ao redor da origem (0, 0)
        pool_base = SimulationEntityPool(initial_capacity=count)
        pool_lod = SimulationEntityPool(initial_capacity=count)

        for _ in range(count):
            # Distribuição radial determinística
            dist = rng.uniform(50.0, 2000.0)
            angle = rng.uniform(0.0, 6.28318)
            x = dist * math.cos(angle)
            y = dist * math.sin(angle)
            pool_base.create(position=(x, y))
            pool_lod.create(position=(x, y))

        focus = SimulationFocus(0.0, 0.0, enabled=True)
        cfg = SimulationLODConfig(high_distance=300.0, medium_distance=800.0, low_distance=1500.0, hysteresis_margin=50.0)
        lod_mgr = SimulationLODManager(config=cfg, initial_capacity=count)

        # 1. Mede custo puro de classificação O(N)
        t0 = time.perf_counter()
        for _ in range(60):
            lod_mgr.classify(pool_lod, focus)
        class_time_60_s = time.perf_counter() - t0
        class_per_frame_ms = (class_time_60_s / 60.0) * 1000.0

        # 2. Baseline sem LOD (60Hz para 100% das entidades em full simulation rate)
        sched_base = SystemScheduler()
        base_dec = SyntheticBaselineDecisionSystem(pool_base)
        sched_base.register(base_dec, TickPolicy.fixed_hz(60), priority=100)

        t0 = time.perf_counter()
        for _ in range(60):
            sched_base.update(None, 1.0 / 60.0)
        base_dur_ms = (time.perf_counter() - t0) * 1000.0

        # 3. Com LOD (High=60Hz, Medium=20Hz, Low=5Hz, Sleep=0Hz, Classifier=10Hz)
        sched_lod = SystemScheduler()
        lod_high = SyntheticLODDecisionSystem(pool_lod, lod_mgr, LOD_HIGH)
        lod_med = SyntheticLODDecisionSystem(pool_lod, lod_mgr, LOD_MEDIUM)
        lod_low = SyntheticLODDecisionSystem(pool_lod, lod_mgr, LOD_LOW)

        sched_lod.register(lod_high, TickPolicy.fixed_hz(60), priority=100)
        sched_lod.register(lod_med, TickPolicy.fixed_hz(20), priority=200)
        sched_lod.register(lod_low, TickPolicy.fixed_hz(5), priority=300)

        t0 = time.perf_counter()
        for frame_idx in range(60):
            if frame_idx % 6 == 0:  # Classificação a 10Hz
                lod_mgr.classify(pool_lod, focus)
            sched_lod.update(None, 1.0 / 60.0)
        lod_dur_ms = (time.perf_counter() - t0) * 1000.0

        stats = lod_mgr.get_stats()
        tot_lod_updates = lod_high.expensive_updates + lod_med.expensive_updates + lod_low.expensive_updates
        tot_base_updates = base_dec.expensive_updates
        reduction_pct = ((tot_base_updates - tot_lod_updates) / tot_base_updates * 100.0) if tot_base_updates > 0 else 0.0

        results[str(count)] = {
            "classification_ms_per_call": class_per_frame_ms,
            "tier_counts": stats["tier_counts"],
            "baseline_expensive_updates_60f": tot_base_updates,
            "lod_expensive_updates_60f": tot_lod_updates,
            "work_reduction_percent": reduction_pct,
            "baseline_60f_ms": base_dur_ms,
            "lod_60f_ms": lod_dur_ms,
        }
    return results


# ==============================================================================
# BENCH I: SPATIAL UPDATE OPTIMIZATION & TRANSITIONS
# ==============================================================================
def run_bench_i(populations: List[int], rng: random.Random) -> Dict[str, Any]:
    results = {}
    for count in populations:
        pool = SimulationEntityPool(initial_capacity=count)
        handles = []
        for _ in range(count):
            x = rng.uniform(-1000.0, 1000.0)
            y = rng.uniform(-1000.0, 1000.0)
            h = pool.create(position=(x, y))
            handles.append(h)

        # 1. Same-Cell Updates (100% permanência)
        sh_same = SpatialHash2D(cell_size=64.0)
        for h in handles:
            idx = h.index
            sh_same.insert(h, pool.position_x[idx], pool.position_y[idx])

        t0 = time.perf_counter()
        for _ in range(60):
            for h in handles:
                idx = h.index
                # Pequeno deslocamento que mantém na mesma célula
                sh_same.update(h, pool.position_x[idx] + 0.1, pool.position_y[idx] + 0.1)
        same_cell_60_ms = (time.perf_counter() - t0) * 1000.0

        # 2. Bulk Sync Same-Cell
        sh_bulk_same = SpatialHash2D(cell_size=64.0)
        for h in handles:
            idx = h.index
            sh_bulk_same.insert(h, pool.position_x[idx], pool.position_y[idx])

        t0 = time.perf_counter()
        for _ in range(60):
            sh_bulk_same.sync_from_pool(pool)
        bulk_same_cell_60_ms = (time.perf_counter() - t0) * 1000.0

        # 3. Transitions (100% mudança de célula)
        sh_trans = SpatialHash2D(cell_size=64.0)
        for h in handles:
            idx = h.index
            sh_trans.insert(h, pool.position_x[idx], pool.position_y[idx])

        t0 = time.perf_counter()
        for f in range(60):
            offset = (f + 1) * 70.0
            for h in handles:
                idx = h.index
                sh_trans.update(h, pool.position_x[idx] + offset, pool.position_y[idx] + offset)
        trans_60_ms = (time.perf_counter() - t0) * 1000.0

        # 4. Realistic Mix (~98.7% same-cell / 1.3% transitions)
        sh_mix = SpatialHash2D(cell_size=64.0)
        for h in handles:
            idx = h.index
            sh_mix.insert(h, pool.position_x[idx], pool.position_y[idx])

        t0 = time.perf_counter()
        for f in range(60):
            for i, h in enumerate(handles):
                idx = h.index
                # 1.3% das entidades saltam para fora da célula
                step = 80.0 if (i % 75 == 0) else 0.5
                sh_mix.update(h, pool.position_x[idx] + step, pool.position_y[idx] + step)
        mix_60_ms = (time.perf_counter() - t0) * 1000.0

        results[str(count)] = {
            "same_cell_individual_per_frame_ms": same_cell_60_ms / 60.0,
            "same_cell_bulk_per_frame_ms": bulk_same_cell_60_ms / 60.0,
            "bulk_speedup_over_individual": (same_cell_60_ms / bulk_same_cell_60_ms) if bulk_same_cell_60_ms > 0 else 1.0,
            "realistic_mix_per_frame_ms": mix_60_ms / 60.0,
            "full_transitions_per_frame_ms": trans_60_ms / 60.0,
        }
    return results


# ==============================================================================
# BENCH J: BATCH RENDERER (BLIT VS BLITS)
# ==============================================================================
def run_bench_j(visible_counts: List[int]) -> Dict[str, Any]:
    pygame.init()
    target_indiv = pygame.Surface((1280, 720))
    target_blits = pygame.Surface((1280, 720))
    sprite_surf = pygame.Surface((16, 16))
    registry = {1: sprite_surf}

    results = {}
    renderer = BatchedSimulationRenderer()

    for count in visible_counts:
        buf = SimulationRenderBuffer(initial_capacity=count)
        for i in range(count):
            x = float((i % 50) * 20 - 450)
            y = float((i // 50) * 15 - 250)
            buf.submit(x, y, sprite_id=1)

        # 1. Individual Blit
        t0 = time.perf_counter()
        for _ in range(60):
            renderer.render(buf, camera=(0.0, 0.0), target_surface=target_indiv, sprite_registry=registry, use_blits=False)
        indiv_ms = (time.perf_counter() - t0) * 1000.0 / 60.0

        # 2. Batch Surface.blits
        t0 = time.perf_counter()
        for _ in range(60):
            renderer.render(buf, camera=(0.0, 0.0), target_surface=target_blits, sprite_registry=registry, use_blits=True)
        blits_ms = (time.perf_counter() - t0) * 1000.0 / 60.0

        results[str(count)] = {
            "individual_blit_per_frame_ms": indiv_ms,
            "batch_blits_per_frame_ms": blits_ms,
            "blits_speedup": (indiv_ms / blits_ms) if blits_ms > 0 else 1.0,
        }
    return results


# ==============================================================================
# BENCH K: TEMPORAL QUERY SMOOTHING (BURST VS DISTRIBUTED)
# ==============================================================================
def run_bench_k(populations: List[int], rng: random.Random) -> Dict[str, Any]:
    results = {}
    for count in populations:
        pool = SimulationEntityPool(initial_capacity=count)
        sh = SpatialHash2D(cell_size=64.0)
        handles = []
        for _ in range(count):
            x = rng.uniform(-500.0, 500.0)
            y = rng.uniform(-500.0, 500.0)
            h = pool.create(position=(x, y))
            handles.append(h)
            sh.insert(h, x, y)

        sample_size = max(1, count // 20)
        sample_indices = [h.index for h in handles[:sample_size]]

        # 1. Burst Mode (10Hz Scheduler tick -> executa tudo a cada 6 frames)
        burst_frame_times = []
        for f in range(60):
            t0 = time.perf_counter()
            if f % 6 == 0:
                for idx in sample_indices:
                    _ = sh.query_radius(pool.position_x[idx], pool.position_y[idx], radius=40.0, pool=pool, ordered=False)
            burst_frame_times.append((time.perf_counter() - t0) * 1000.0)

        # 2. Distributed Mode (60Hz base com 6 fases -> executa 1/6 a cada frame)
        distributor = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)
        dist_frame_times = []
        for _ in range(60):
            t0 = time.perf_counter()
            batch = distributor.select(sample_indices)
            for idx in batch:
                _ = sh.query_radius(pool.position_x[idx], pool.position_y[idx], radius=40.0, pool=pool, ordered=False)
            distributor.advance()
            dist_frame_times.append((time.perf_counter() - t0) * 1000.0)

        p_burst = calculate_percentiles(burst_frame_times)
        p_dist = calculate_percentiles(dist_frame_times)

        results[str(count)] = {
            "burst_mean_ms": p_burst["mean"],
            "burst_p95_ms": p_burst["p95"],
            "burst_max_ms": p_burst["max"],
            "dist_mean_ms": p_dist["mean"],
            "dist_p95_ms": p_dist["p95"],
            "dist_max_ms": p_dist["max"],
            "p95_reduction_percent": ((p_burst["p95"] - p_dist["p95"]) / p_burst["p95"] * 100.0) if p_burst["p95"] > 0 else 0.0,
            "max_reduction_percent": ((p_burst["max"] - p_dist["max"]) / p_burst["max"] * 100.0) if p_burst["max"] > 0 else 0.0,
        }
    return results


# ==============================================================================
# SCALE GATE (10K / 15K / 25K)
# ==============================================================================
def run_scale_gate(rng: random.Random) -> Dict[str, Any]:
    pygame.init()
    target_surf = pygame.Surface((1280, 720))
    sprite_surf = pygame.Surface((16, 16))
    registry = {1: sprite_surf}
    scale_results = {}
    counts = [10000, 15000, 25000]

    for count in counts:
        gc.collect()
        tracemalloc.start()

        pool = SimulationEntityPool(initial_capacity=count)
        sh = SpatialHash2D(cell_size=64.0)

        # Mundo dimensionado para manter densidade e visibilidade realistas de ~10-20%
        world_size = 1000.0 * math.sqrt(count / 1000.0)
        half_world = world_size / 2.0

        grid = NavigationGrid2D(width=80, height=80, cell_size=32.0)
        for y in range(20, 60):
            grid.set_walkable(40, y, False)

        goal = (70, 70)
        flow = FlowField2D(grid)
        flow.build(goal)

        for i in range(count):
            wx = rng.uniform(32.0, world_size - 32.0)
            wy = rng.uniform(32.0, world_size - 32.0)
            h = pool.create(position=(wx, wy), velocity=(1.0, 1.0))
            sh.insert(h, wx, wy)

        buf = SimulationRenderBuffer(initial_capacity=count)
        renderer = BatchedSimulationRenderer()

        scheduler = SystemScheduler()
        move_sys = IntegratedAgentMovementSystem(pool, flow)
        spatial_sys = IntegratedSpatialSyncSystem(pool, sh)
        distributor = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)
        neighbor_sys = IntegratedSmoothNeighborQuerySystem(pool, sh, distributor)

        scheduler.register(move_sys, TickPolicy.fixed_hz(60), priority=100)
        scheduler.register(spatial_sys, TickPolicy.fixed_hz(60), priority=200)
        scheduler.register(neighbor_sys, TickPolicy.every_frame(), priority=300)

        dt = 1.0 / 60.0

        # Warmup
        for _ in range(10):
            scheduler.update(None, dt)
            buf.sync_from_pool(pool, sprite_id=1)
            renderer.render(buf, camera=(half_world, half_world), target_surface=target_surf, sprite_registry=registry)

        cur_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        frame_times = []
        breakdown_movement = []
        breakdown_render = []

        # Medição de 30 frames
        for _ in range(30):
            t_frame_start = time.perf_counter()

            # Scheduler update
            t0 = time.perf_counter()
            scheduler.update(None, dt)
            t_sched = time.perf_counter() - t0

            # Render sync + draw (realistic ~10% visibility via camera framing)
            t0 = time.perf_counter()
            buf.sync_from_pool(pool, sprite_id=1)
            renderer.render(buf, camera=(half_world, half_world), target_surface=target_surf, sprite_registry=registry)
            t_render = time.perf_counter() - t0

            total_frame = time.perf_counter() - t_frame_start
            frame_times.append(total_frame * 1000.0)
            breakdown_movement.append(t_sched * 1000.0)
            breakdown_render.append(t_render * 1000.0)

        pcts = calculate_percentiles(frame_times)

        scale_results[str(count)] = {
            "mean_ms": pcts["mean"],
            "median_ms": pcts["median"],
            "p95_ms": pcts["p95"],
            "p99_ms": pcts["p99"],
            "max_ms": pcts["max"],
            "stddev_ms": pcts["stddev"],
            "estimated_fps": (1000.0 / pcts["mean"]) if pcts["mean"] > 0 else 0.0,
            "avg_scheduler_ms": sum(breakdown_movement) / len(breakdown_movement),
            "avg_render_ms": sum(breakdown_render) / len(breakdown_render),
            "peak_memory_mb": peak_mem / (1024.0 * 1024.0),
        }
    return scale_results


# ==============================================================================
# LEAK TEST
# ==============================================================================
def run_leak_test() -> Dict[str, Any]:
    # Warmup allocation
    pool_warmup = SimulationEntityPool(initial_capacity=100)
    pool_warmup.clear()

    gc.collect()
    tracemalloc.start()
    snap_start = tracemalloc.take_snapshot()

    for _ in range(10):
        pool = SimulationEntityPool(initial_capacity=1000)
        sh = SpatialHash2D(cell_size=64.0)
        mgr = SimulationLODManager(initial_capacity=1000)
        buf = SimulationRenderBuffer(initial_capacity=1000)
        dist = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)
        focus = SimulationFocus(0.0, 0.0)
        for i in range(1000):
            h = pool.create(position=(float(i), float(i)))
            sh.insert(h, float(i), float(i))
        mgr.classify(pool, focus)
        sh.sync_from_pool(pool)
        buf.sync_from_pool(pool, sprite_id=1)
        dist.select(pool.iter_alive_indices())
        dist.advance()
        pool.clear()
        sh.clear()
        mgr.clear()
        buf.clear()

    gc.collect()
    snap_end = tracemalloc.take_snapshot()
    stats = snap_end.compare_to(snap_start, "lineno")
    total_diff = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
    tracemalloc.stop()

    passed = total_diff < 500 * 1024  # Tolerância segura para alocações Python em ciclo
    return {
        "passed": passed,
        "net_growth_kb": total_diff / 1024.0,
    }


def main():
    parser = argparse.ArgumentParser(description="Zennity Engine Large-Scale Simulation Benchmark")
    parser.add_argument("--quick", action="store_true", help="Executa versão rápida para CI")
    parser.add_argument("--full", action="store_true", help="Executa matriz completa de benchmarks")
    parser.add_argument("--scale-gate", action="store_true", help="Executa validação formal de 10k, 15k e 25k entidades")
    parser.add_argument("--entities", type=int, default=None, help="Número customizado de entidades")
    parser.add_argument("--frames", type=int, default=None, help="Número customizado de frames medidos")
    parser.add_argument("--json-output", type=str, default=None, help="Salva relatório em formato JSON")
    parser.add_argument("--seed", type=int, default=12345, help="Seed determinística")

    args = parser.parse_args()
    rng = random.Random(args.seed)

    if args.quick:
        mode_name = "QUICK"
        pop_matrix = [100, 500, 1000]
        warmup = 5
        frames = 20
        grid_sizes = [25, 50]
        fractions = [1.0, 0.1]
        vis_matrix = [100, 500, 1000]
    else:
        mode_name = "FULL"
        pop_matrix = [100, 500, 1000, 2000, 5000]
        warmup = 15
        frames = 60
        grid_sizes = [50, 100]
        fractions = [1.0, 0.5, 0.1, 0.01]
        vis_matrix = [100, 500, 2500, 5000]

    if args.entities is not None:
        pop_matrix = [args.entities]
    if args.frames is not None:
        frames = args.frames

    print(f"============================================================")
    print(f"ZENNITY SIMULATION BENCHMARK [{mode_name} MODE] (Seed: {args.seed})")
    print(f"Platform: {platform.platform()} | Python: {platform.python_version()}")
    print(f"============================================================")

    # Executa cenários
    print("Running Bench A (EntityPool)...")
    bench_a = run_bench_a(pop_matrix, rng)

    print("Running Bench B (Scheduler)...")
    bench_b = run_bench_b(pop_matrix)

    print("Running Bench C (SpatialHash)...")
    bench_c = run_bench_c(pop_matrix, rng)

    print("Running Bench D (AStar)...")
    bench_d = run_bench_d(grid_sizes, rng)

    print("Running Bench E (FlowField)...")
    bench_e = run_bench_e(pop_matrix, rng)

    print("Running Bench F (Renderer Fractions)...")
    bench_f = run_bench_f(fractions)

    print("Running Bench G (Integrated Simulation)...")
    bench_g = run_bench_g(pop_matrix, warmup, frames, rng)

    print("Running Bench H (Simulation LOD)...")
    bench_h = run_bench_h(pop_matrix, rng)

    print("Running Bench I (Spatial Update Optimization)...")
    bench_i = run_bench_i(pop_matrix, rng)

    print("Running Bench J (Batch Renderer Optimization)...")
    bench_j = run_bench_j(vis_matrix)

    print("Running Bench K (Temporal Query Smoothing)...")
    bench_k = run_bench_k(pop_matrix, rng)

    scale_gate = {}
    if args.scale_gate or args.full:
        print("Running Scale Gate (10K / 15K / 25K)...")
        scale_gate = run_scale_gate(rng)

    print("Running Leak Test...")
    leak_test = run_leak_test()

    report = {
        "format": "zennity.simulation_benchmark",
        "version": 1,
        "metadata": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "mode": mode_name,
            "seed": args.seed,
            "render_target": "1280x720 (Offscreen)",
            "warmup_frames": warmup,
            "measured_frames": frames,
        },
        "bench_a_entity_pool": bench_a,
        "bench_b_scheduler": bench_b,
        "bench_c_spatial_hash": bench_c,
        "bench_d_astar": bench_d,
        "bench_e_flow_field": bench_e,
        "bench_f_renderer": bench_f,
        "bench_g_integrated": bench_g,
        "bench_h_lod": bench_h,
        "bench_i_spatial_optimization": bench_i,
        "bench_j_batch_renderer": bench_j,
        "bench_k_temporal_smoothing": bench_k,
        "scale_gate": scale_gate,
        "leak_test": leak_test,
    }

    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport written to: {args.json_output}")

    # Resumo
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY (INTEGRATED FULL PASS)")
    print("=" * 60)
    for pop, data in bench_g.items():
        sh_p = data.get("spatial_profiling", {})
        print(f"Pop: {pop:5s} | Avg: {data['mean_ms']:6.2f}ms | P95: {data['p95_ms']:6.2f}ms | Est FPS: {data['estimated_fps']:6.1f} | Top: {data['primary_bottleneck']}")
        if sh_p:
            print(f"       -> Spatial Updates: {sh_p.get('update_calls', 0):6d} (SameCell: {sh_p.get('same_cell_percent', 0.0):5.1f}% | Transitions: {sh_p.get('cell_transitions', 0):5d}) | Mutations: {sh_p.get('bucket_mutations', 0):5d}")

    print("\n" + "=" * 60)
    print("SIMULATION LOD SUMMARY")
    print("=" * 60)
    for pop, data in bench_h.items():
        tc = data.get("tier_counts", {})
        print(f"Pop: {pop:5s} | Classify: {data['classification_ms_per_call']:5.3f}ms | Work Reduction: {data['work_reduction_percent']:5.1f}% | Tiers: [H:{tc.get('high', 0)} M:{tc.get('medium', 0)} L:{tc.get('low', 0)} S:{tc.get('sleep', 0)}]")

    print("\n" + "=" * 60)
    print("SPATIAL OPTIMIZATION SUMMARY (BENCH I)")
    print("=" * 60)
    for pop, data in bench_i.items():
        print(f"Pop: {pop:5s} | SameCell Indiv: {data['same_cell_individual_per_frame_ms']:5.3f}ms | SameCell Bulk: {data['same_cell_bulk_per_frame_ms']:5.3f}ms | Bulk Speedup: {data['bulk_speedup_over_individual']:4.2f}x | Realistic Mix: {data['realistic_mix_per_frame_ms']:5.3f}ms")

    print("\n" + "=" * 60)
    print("BATCH RENDERER OPTIMIZATION SUMMARY (BENCH J)")
    print("=" * 60)
    for count, data in bench_j.items():
        print(f"Vis: {count:5s} | Indiv Blit: {data['individual_blit_per_frame_ms']:5.3f}ms | Batch Blits: {data['batch_blits_per_frame_ms']:5.3f}ms | Blits Speedup: {data['blits_speedup']:4.2f}x")

    print("\n" + "=" * 60)
    print("TEMPORAL QUERY SMOOTHING SUMMARY (BENCH K)")
    print("=" * 60)
    for pop, data in bench_k.items():
        print(f"Pop: {pop:5s} | Burst P95: {data['burst_p95_ms']:5.3f}ms | Dist P95: {data['dist_p95_ms']:5.3f}ms | P95 Drop: {data['p95_reduction_percent']:5.1f}% | Max Drop: {data['max_reduction_percent']:5.1f}%")

    if scale_gate:
        print("\n" + "=" * 60)
        print("SCALE GATE SUMMARY (10K / 15K / 25K)")
        print("=" * 60)
        for count, data in scale_gate.items():
            print(f"Pop: {count:5s} | Mean: {data['mean_ms']:6.2f}ms | P95: {data['p95_ms']:6.2f}ms | Est FPS: {data['estimated_fps']:6.1f} | Peak Mem: {data['peak_memory_mb']:5.2f}MB")

    print(f"\nLeak Test: {'PASS' if leak_test['passed'] else 'FAIL'} (Net growth: {leak_test['net_growth_kb']:.2f} KB)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
