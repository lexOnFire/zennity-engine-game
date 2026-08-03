"""AutosaveManager — Salvamento automático e recuperação de sessão da Zennity Engine.

Responsabilidades:
  - Salvar um snapshot temporário da cena em intervalos regulares (padrão: 5 min).
  - Detectar crash na inicialização: se o arquivo de lock existir sem o editor ter fechado
    normalmente, o recovery file está disponível.
  - Oferecer API simples: start() / stop() / flush() / check_recovery() / clear_recovery().
  - Funciona com qualquer serializador JSON; não depende de PySide.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AutosaveManager:
    """Gerencia autosave periódico e detecção de crash (lockfile protocol).

    Uso básico::

        manager = AutosaveManager(
            project_root=Path.cwd(),
            snapshot_fn=lambda: editor.get_current_snapshot(),
            interval_seconds=300,
        )
        manager.start()           # abre lockfile, agenda timer
        manager.flush()           # salva imediatamente (ex: antes de fechar)
        manager.stop()            # salva + remove lockfile (saída normal)

    Na próxima abertura::

        if manager.check_recovery():
            payload = manager.load_recovery()
            # perguntar ao usuário se quer restaurar
            manager.clear_recovery()
    """

    LOCK_FILENAME     = ".zennity_session.lock"
    RECOVERY_FILENAME = ".zennity_autosave.json"
    MANIFEST_FILENAME = ".zennity_autosave_manifest.json"

    def __init__(
        self,
        project_root: str | Path,
        snapshot_fn: Callable[[], Any],
        interval_seconds: int = 300,
    ) -> None:
        self._root         = Path(project_root).resolve()
        self._snapshot_fn  = snapshot_fn
        self._interval     = max(30, int(interval_seconds))
        self._running      = False
        self._last_save_at = 0.0
        self._save_count   = 0

        # Paths
        self._lock_path     = self._root / self.LOCK_FILENAME
        self._recovery_path = self._root / self.RECOVERY_FILENAME
        self._manifest_path = self._root / self.MANIFEST_FILENAME

        # Timer opcional (PySide); configurado externamente se necessário
        self._qt_timer: Any = None

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def start(self) -> None:
        """Inicia o autosave: cria lockfile e agenda o primeiro ciclo."""
        if self._running:
            return
        self._running = True
        self._write_lockfile()
        logger.info("AutosaveManager iniciado (intervalo: %ds).", self._interval)

    def stop(self) -> None:
        """Para o autosave, salva uma última vez e remove o lockfile (saída normal)."""
        if not self._running:
            return
        self.flush()
        self._running = False
        self._remove_lockfile()
        if self._qt_timer is not None:
            try:
                self._qt_timer.stop()
            except Exception:  # noqa: BLE001
                logger.debug(
                    "AutosaveManager: falha ao interromper o QTimer durante shutdown.",
                    exc_info=True,
                )
        logger.info("AutosaveManager encerrado normalmente.")

    def flush(self) -> bool:
        """Salva o snapshot atual imediatamente. Retorna True em caso de sucesso."""
        try:
            snapshot = self._snapshot_fn()
        except Exception as exc:  # noqa: BLE001
            logger.warning("AutosaveManager: snapshot_fn falhou: %s", exc)
            return False
        return self._write_recovery(snapshot)

    def tick(self) -> None:
        """Deve ser chamado periodicamente (pelo QTimer ou qualquer loop).
        Salva automaticamente se o intervalo configurado tiver passado.
        """
        if not self._running:
            return
        now = time.monotonic()
        if now - self._last_save_at >= self._interval:
            self.flush()

    def attach_qt_timer(self, parent_widget: Any) -> None:
        """Cria e inicia um QTimer ligado ao tick(). Chame após start()."""
        try:
            from PySide6.QtCore import QTimer
            timer = QTimer(parent_widget)
            timer.setInterval(self._interval * 1000)
            timer.timeout.connect(self.tick)
            timer.start()
            self._qt_timer = timer
            logger.debug("AutosaveManager: QTimer anexado (%dms).", timer.interval())
        except ImportError:
            logger.debug("AutosaveManager: PySide6 não disponível — use tick() manualmente.")

    # ── Recovery ───────────────────────────────────────────────────────────

    def check_recovery(self) -> bool:
        """Retorna True se um arquivo de recovery estiver disponível (indica crash anterior).

        A heurística é: lockfile existe mas o processo que o criou não está mais ativo
        (verificado via PID registrado no lock).
        """
        if not self._lock_path.is_file():
            return False
        if not self._recovery_path.is_file():
            return False
        # Verifica se o PID ainda está ativo
        pid = self._read_lockfile_pid()
        if pid is not None and _pid_alive(pid):
            # Outra instância ainda está rodando — não é um crash
            return False
        return True

    def load_recovery(self) -> dict[str, Any] | None:
        """Lê e retorna o snapshot do arquivo de recovery, ou None se inválido."""
        if not self._recovery_path.is_file():
            return None
        try:
            payload = json.loads(self._recovery_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else None
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("AutosaveManager: falha ao ler recovery: %s", exc)
            return None

    def clear_recovery(self) -> None:
        """Remove os arquivos de recovery e lock (após o usuário decidir o que fazer)."""
        for path in (self._recovery_path, self._lock_path, self._manifest_path):
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                logger.warning("AutosaveManager: falha ao remover %s: %s", path.name, exc)

    # ── Metadata / Manifest ────────────────────────────────────────────────

    def get_manifest(self) -> dict[str, Any]:
        """Retorna metadados da última sessão autosalvada."""
        if not self._manifest_path.is_file():
            return {}
        try:
            return json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    @property
    def save_count(self) -> int:
        """Número de autosaves realizados na sessão atual."""
        return self._save_count

    @property
    def last_save_time(self) -> float:
        """Timestamp UNIX do último autosave (0 se nunca salvou)."""
        return self._last_save_at

    # ── Internos ───────────────────────────────────────────────────────────

    def _write_lockfile(self) -> None:
        try:
            self._lock_path.write_text(
                json.dumps({"pid": os.getpid(), "started": time.time()}, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("AutosaveManager: falha ao criar lockfile: %s", exc)

    def _remove_lockfile(self) -> None:
        try:
            self._lock_path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("AutosaveManager: falha ao remover lockfile: %s", exc)

    def _read_lockfile_pid(self) -> int | None:
        try:
            data = json.loads(self._lock_path.read_text(encoding="utf-8"))
            return int(data["pid"]) if "pid" in data else None
        except (OSError, json.JSONDecodeError, KeyError, ValueError):
            return None

    def _write_recovery(self, snapshot: Any) -> bool:
        now = time.time()
        payload = {
            "_autosave_meta": {
                "saved_at": now,
                "save_count": self._save_count + 1,
                "pid": os.getpid(),
            },
            "snapshot": snapshot,
        }
        manifest = {
            "saved_at": now,
            "save_count": self._save_count + 1,
            "pid": os.getpid(),
        }
        try:
            self._recovery_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self._manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self._save_count += 1
            self._last_save_at = time.monotonic()
            logger.debug("AutosaveManager: snapshot salvo (#%d).", self._save_count)
            return True
        except OSError as exc:
            logger.warning("AutosaveManager: falha ao salvar recovery: %s", exc)
            return False


def _pid_alive(pid: int) -> bool:
    """Verifica se o processo com o PID informado ainda está ativo."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
    except OSError:
        return False
