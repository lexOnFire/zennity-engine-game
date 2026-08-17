"""Testes de contrato e execução para a ferramenta de benchmark (Phase 11 - Item 11.7)."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import pytest


def test_simulation_benchmark_cli_quick_mode():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tools", "benchmark_simulation.py"))

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        json_path = tf.name

    try:
        cmd = [sys.executable, script_path, "--quick", "--json-output", json_path]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        assert proc.returncode == 0
        assert "BENCHMARK SUMMARY" in proc.stdout
        assert "Leak Test: PASS" in proc.stdout

        # Valida JSON gerado
        assert os.path.exists(json_path)
        with open(json_path, "r", encoding="utf-8") as f:
            import json
            data = json.load(f)

        assert data["format"] == "zennity.simulation_benchmark"
        assert data["version"] == 1
        assert "bench_a_entity_pool" in data
        assert "bench_b_scheduler" in data
        assert "bench_c_spatial_hash" in data
        assert "bench_d_astar" in data
        assert "bench_e_flow_field" in data
        assert "bench_f_renderer" in data
        assert "bench_g_integrated" in data
        assert data["leak_test"]["passed"] is True
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)
