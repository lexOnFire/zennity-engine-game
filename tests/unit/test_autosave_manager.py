"""Testes unitários para AutosaveManager."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from editor.autosave_manager import AutosaveManager


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    return tmp_path


def make_manager(tmp_project: Path, snapshot=None, interval: int = 300) -> AutosaveManager:
    if snapshot is None:
        snapshot = {"scene": "TestScene", "objects": []}
    return AutosaveManager(
        project_root=tmp_project,
        snapshot_fn=lambda: snapshot,
        interval_seconds=interval,
    )


class TestAutosaveManagerLifecycle:
    def test_start_creates_lockfile(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        mgr.start()
        assert (tmp_project / AutosaveManager.LOCK_FILENAME).is_file()
        mgr.stop()

    def test_stop_removes_lockfile(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        mgr.start()
        mgr.stop()
        assert not (tmp_project / AutosaveManager.LOCK_FILENAME).is_file()

    def test_stop_creates_recovery_file(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        mgr.start()
        mgr.stop()
        assert (tmp_project / AutosaveManager.RECOVERY_FILENAME).is_file()

    def test_double_start_is_idempotent(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        mgr.start()
        mgr.start()
        assert mgr._running
        mgr.stop()

    def test_stop_without_start_is_safe(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        mgr.stop()  # Não deve lançar exceção


class TestFlushAndRecovery:
    def test_flush_creates_recovery_file(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        mgr.start()
        ok = mgr.flush()
        assert ok
        assert (tmp_project / AutosaveManager.RECOVERY_FILENAME).is_file()
        mgr.stop()

    def test_flush_increments_save_count(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        mgr.start()
        mgr.flush()
        mgr.flush()
        assert mgr.save_count == 2
        mgr.stop()

    def test_load_recovery_returns_snapshot(self, tmp_project: Path):
        snapshot = {"scene": "Main", "objects": [{"name": "Player"}]}
        mgr = make_manager(tmp_project, snapshot=snapshot)
        mgr.start()
        mgr.flush()
        payload = mgr.load_recovery()
        assert payload is not None
        assert payload.get("snapshot") == snapshot
        mgr.stop()

    def test_load_recovery_contains_meta(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        mgr.start()
        mgr.flush()
        payload = mgr.load_recovery()
        assert "_autosave_meta" in payload
        assert "saved_at" in payload["_autosave_meta"]
        mgr.stop()

    def test_clear_recovery_removes_files(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        mgr.start()
        mgr.flush()
        mgr.clear_recovery()
        assert not (tmp_project / AutosaveManager.RECOVERY_FILENAME).is_file()
        assert not (tmp_project / AutosaveManager.LOCK_FILENAME).is_file()

    def test_load_recovery_when_absent_returns_none(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        result = mgr.load_recovery()
        assert result is None


class TestCrashDetection:
    def test_check_recovery_false_when_no_lockfile(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        assert not mgr.check_recovery()

    def test_check_recovery_false_when_no_recovery_file(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        # Cria lockfile com PID morto
        lock = tmp_project / AutosaveManager.LOCK_FILENAME
        lock.write_text(json.dumps({"pid": 99999999}), encoding="utf-8")
        assert not mgr.check_recovery()

    def test_check_recovery_true_when_pid_dead_and_recovery_present(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        # Simula crash: cria lockfile + recovery com PID inexistente
        lock = tmp_project / AutosaveManager.LOCK_FILENAME
        recovery = tmp_project / AutosaveManager.RECOVERY_FILENAME
        lock.write_text(json.dumps({"pid": 99999999}), encoding="utf-8")
        recovery.write_text(json.dumps({"snapshot": {}, "_autosave_meta": {}}), encoding="utf-8")
        assert mgr.check_recovery()

    def test_check_recovery_false_when_pid_alive(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        lock = tmp_project / AutosaveManager.LOCK_FILENAME
        recovery = tmp_project / AutosaveManager.RECOVERY_FILENAME
        lock.write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")
        recovery.write_text(json.dumps({"snapshot": {}}), encoding="utf-8")
        # PID atual está vivo → não é crash
        assert not mgr.check_recovery()


class TestManifest:
    def test_manifest_written_after_flush(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        mgr.start()
        mgr.flush()
        manifest = mgr.get_manifest()
        assert "saved_at" in manifest
        assert manifest["save_count"] == 1
        mgr.stop()

    def test_manifest_empty_when_absent(self, tmp_project: Path):
        mgr = make_manager(tmp_project)
        assert mgr.get_manifest() == {}


class TestTick:
    def test_tick_saves_when_interval_elapsed(self, tmp_project: Path):
        mgr = make_manager(tmp_project, interval=1)
        mgr.start()
        # O intervalo mínimo real é 30s (max(30, 1)); forçamos ultrapassá-lo
        mgr._last_save_at = time.monotonic() - 31
        mgr.tick()
        assert mgr.save_count == 1
        mgr.stop()

    def test_tick_skips_when_not_enough_time(self, tmp_project: Path):
        mgr = make_manager(tmp_project, interval=300)
        mgr.start()
        mgr._last_save_at = time.monotonic()  # Acabou de salvar
        mgr.tick()
        assert mgr.save_count == 0
        mgr.stop()

    def test_tick_noop_when_not_running(self, tmp_project: Path):
        mgr = make_manager(tmp_project, interval=1)
        mgr._last_save_at = 0.0  # Intervalo "vencido"
        mgr.tick()  # Não deve salvar — não foi iniciado
        assert mgr.save_count == 0


class TestSnapshotFnFailure:
    def test_flush_returns_false_on_snapshot_error(self, tmp_project: Path):
        def bad_snapshot():
            raise RuntimeError("simulação de falha")
        mgr = AutosaveManager(
            project_root=tmp_project,
            snapshot_fn=bad_snapshot,
        )
        mgr.start()
        result = mgr.flush()
        assert result is False
        mgr.stop()
