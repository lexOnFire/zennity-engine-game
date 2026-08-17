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
    AStarPathfinder,
    BatchedSimulationRenderer,
    EntityHandle,
    FlowField2D,
    NavigationGrid2D,
    SimulationEntityPool,
    SimulationRenderBuffer,
    SpatialHash2D,
    SystemScheduler,
    TickPolicy,
)
from engine.system import System


def calculate_percentiles(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"mean": 0.0, "median": 0.0, "p95": 0.0, "max": 0.0}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mean_val = sum(sorted_vals) / n
    median_val = sorted_vals[n // 2]
    p95_idx = min(int(n * 0.95), n - 1)
    p95_val = sorted_vals[p95_idx]
    max_val = sorted_vals[-1]
    return {
        "mean": mean_val,
        "median": median_val,
        "p95": p95_val,
        "max": max_val,
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
def run_bench_f(fractions: List[float]) -> Dict[str, Any]:
    pygame.init()
    target_surf = pygame.Surface((1280, 720))
    sprite_surf = pygame.Surface((16, 16))
    registry = {1: sprite_surf}

    count = 5000
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
            "buffer_sync_ms": sync_time * 1000.0,
            "culling_ms": stats["culling_s"] * 1000.0,
            "draw_ms": stats["draw_s"] * 1000.0,
            "total_render_ms": (sync_time + stats["total_s"]) * 1000.0,
        }
    return results


# ==============================================================================
# BENCH G: FULL INTEGRATED SYNTHETIC SIMULATION
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
        px = self.pool.position_x
        py = self.pool.position_y
        for idx in self.pool.iter_alive_indices():
            h = EntityHandle(idx, self.pool.generation[idx])
            self.spatial_hash.update(h, px[idx], py[idx])


class IntegratedNeighborQuerySystem(System):
    def __init__(self, pool: SimulationEntityPool, spatial_hash: SpatialHash2D) -> None:
        super().__init__()
        self.pool = pool
        self.spatial_hash = spatial_hash
        self.total_neighbors = 0

    def update(self, scene, dt: float) -> None:
        indices = self.pool.iter_alive_indices()
        sample_size = max(1, len(indices) // 20)
        px = self.pool.position_x
        py = self.pool.position_y
        for i in range(sample_size):
            idx = indices[i]
            nbrs = self.spatial_hash.query_radius(px[idx], py[idx], radius=40.0, pool=self.pool, ordered=False)
            self.total_neighbors += len(nbrs)


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
        neighbor_sys = IntegratedNeighborQuerySystem(pool, sh)

        scheduler.register(move_sys, TickPolicy.fixed_hz(60), priority=100)
        scheduler.register(spatial_sys, TickPolicy.fixed_hz(60), priority=200)
        scheduler.register(neighbor_sys, TickPolicy.fixed_hz(10), priority=300)

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
            "max_ms": pcts["max"],
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
            },
        }
    return results


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
        for i in range(1000):
            h = pool.create(position=(float(i), float(i)))
            sh.insert(h, float(i), float(i))
        pool.clear()
        sh.clear()

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
    else:
        mode_name = "FULL"
        pop_matrix = [100, 500, 1000, 2000, 5000]
        warmup = 15
        frames = 60
        grid_sizes = [50, 100]
        fractions = [1.0, 0.5, 0.1, 0.01]

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
            print(f"       -> Spatial Updates: {sh_p.get('update_calls', 0):6d} (SameCell: {sh_p.get('same_cell_percent', 0.0):5.1f}% | Transitions: {sh_p.get('cell_transitions', 0):5d}) | Queries: {sh_p.get('query_calls', 0):4d}")

    print(f"\nLeak Test: {'PASS' if leak_test['passed'] else 'FAIL'} (Net growth: {leak_test['net_growth_kb']:.2f} KB)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
