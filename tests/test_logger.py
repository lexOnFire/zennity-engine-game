"""
tests/test_logger.py
────────────────────────────────────────────────────────────────
Testes unitários de engine/logger.py.

Estratégia de isolamento:
  - Nenhum arquivo real é criado: enable_file usa io.StringIO injetado
    diretamente em Logger._file.
  - sys.stdout e sys.stderr são capturados via StringIO/pytest capsys.
  - Logger._level, _silenced, _file são resetados por fixture autouse
    após cada teste.
  - Logger._use_color é forçado a False para evitar códigos ANSI nas
    asserções de conteúdo.
"""
from __future__ import annotations

import io
import sys
from unittest.mock import patch, MagicMock

import pytest

from engine.logger import Logger, _TaggedLogger


# ── fixture de reset autouse ─────────────────────────────────────────────
@pytest.fixture(autouse=True)
def reset_logger():
    orig_level    = Logger._level
    orig_silenced = Logger._silenced
    orig_file     = Logger._file
    orig_color    = Logger._use_color
    Logger._use_color = False   # sem ANSI em testes
    Logger._level     = Logger.INFO
    Logger._silenced  = False
    Logger._file      = None
    yield
    # teardown
    if Logger._file and Logger._file is not orig_file:
        try:
            Logger._file.close()
        except Exception:
            pass
    Logger._level     = orig_level
    Logger._silenced  = orig_silenced
    Logger._file      = orig_file
    Logger._use_color = orig_color


# ── helpers ────────────────────────────────────────────────────────────────

def _inject_file():
    """Cria um StringIO e injeta como Logger._file."""
    buf = io.StringIO()
    Logger._file = buf
    return buf


# ────────────────────────────────────────────────────────────────────────────
class TestLevelConstants:
    def test_debug_is_lowest(self):
        assert Logger.DEBUG < Logger.INFO

    def test_info_less_than_warning(self):
        assert Logger.INFO < Logger.WARNING

    def test_warning_less_than_error(self):
        assert Logger.WARNING < Logger.ERROR

    def test_levels_are_ints(self):
        for lvl in (Logger.DEBUG, Logger.INFO, Logger.WARNING, Logger.ERROR):
            assert isinstance(lvl, int)


# ────────────────────────────────────────────────────────────────────────────
class TestSetLevel:
    def test_set_level_changes_level(self):
        Logger.set_level(Logger.DEBUG)
        assert Logger._level == Logger.DEBUG

    def test_set_level_to_error(self):
        Logger.set_level(Logger.ERROR)
        assert Logger._level == Logger.ERROR

    def test_debug_suppressed_at_info(self, capsys):
        Logger.set_level(Logger.INFO)
        Logger.debug("hidden")
        out = capsys.readouterr().out
        assert "hidden" not in out

    def test_debug_shown_at_debug(self, capsys):
        Logger.set_level(Logger.DEBUG)
        Logger.debug("visible")
        out = capsys.readouterr().out
        assert "visible" in out

    def test_info_suppressed_at_warning(self, capsys):
        Logger.set_level(Logger.WARNING)
        Logger.info("hidden")
        out = capsys.readouterr()
        assert "hidden" not in out.out + out.err

    def test_warning_shown_at_warning(self, capsys):
        Logger.set_level(Logger.WARNING)
        Logger.warning("visible")
        err = capsys.readouterr().err
        assert "visible" in err

    def test_error_always_shown(self, capsys):
        Logger.set_level(Logger.ERROR)
        Logger.error("critical")
        err = capsys.readouterr().err
        assert "critical" in err

    def test_error_suppressed_below_error_does_not_happen(self, capsys):
        """Erro não é suprimido mesmo com WARNING."""
        Logger.set_level(Logger.WARNING)
        Logger.error("still shown")
        err = capsys.readouterr().err
        assert "still shown" in err


# ────────────────────────────────────────────────────────────────────────────
class TestMessageFormat:
    def test_label_debug_in_output(self, capsys):
        Logger.set_level(Logger.DEBUG)
        Logger.debug("msg")
        assert "DEBUG" in capsys.readouterr().out

    def test_label_info_in_output(self, capsys):
        Logger.info("msg")
        assert "INFO" in capsys.readouterr().out

    def test_label_warn_in_output(self, capsys):
        Logger.warning("msg")
        assert "WARN" in capsys.readouterr().err

    def test_label_error_in_output(self, capsys):
        Logger.error("msg")
        assert "ERROR" in capsys.readouterr().err

    def test_message_present_in_output(self, capsys):
        Logger.info("hello engine")
        assert "hello engine" in capsys.readouterr().out

    def test_timestamp_format_hh_mm_ss(self, capsys):
        Logger.info("ts")
        out = capsys.readouterr().out
        # formato [HH:MM:SS]
        import re
        assert re.search(r"\[\d{2}:\d{2}:\d{2}\]", out)

    def test_kwargs_appended_as_key_eq_value(self, capsys):
        Logger.info("ctx", player="hero", hp=100)
        out = capsys.readouterr().out
        assert "player=hero" in out
        assert "hp=100" in out

    def test_no_extras_when_no_kwargs(self, capsys):
        Logger.info("clean")
        out = capsys.readouterr().out
        assert "|" not in out

    def test_info_goes_to_stdout(self, capsys):
        Logger.info("stdout")
        cap = capsys.readouterr()
        assert "stdout" in cap.out
        assert "stdout" not in cap.err

    def test_warning_goes_to_stderr(self, capsys):
        Logger.warning("stderr")
        cap = capsys.readouterr()
        assert "stderr" in cap.err
        assert "stderr" not in cap.out

    def test_error_goes_to_stderr(self, capsys):
        Logger.error("err_msg")
        cap = capsys.readouterr()
        assert "err_msg" in cap.err

    def test_debug_goes_to_stdout(self, capsys):
        Logger.set_level(Logger.DEBUG)
        Logger.debug("dbg")
        cap = capsys.readouterr()
        assert "dbg" in cap.out


# ────────────────────────────────────────────────────────────────────────────
class TestSilence:
    def test_silence_suppresses_stdout(self, capsys):
        Logger.silence()
        Logger.info("muted")
        assert "muted" not in capsys.readouterr().out

    def test_silence_suppresses_stderr(self, capsys):
        Logger.silence()
        Logger.error("muted")
        assert "muted" not in capsys.readouterr().err

    def test_unsilence_restores_output(self, capsys):
        Logger.silence()
        Logger.unsilence()
        Logger.info("audible")
        assert "audible" in capsys.readouterr().out

    def test_silence_does_not_affect_file(self):
        buf = _inject_file()
        Logger.silence()
        Logger.info("to_file")
        assert "to_file" in buf.getvalue()

    def test_silence_flag_set(self):
        Logger.silence()
        assert Logger._silenced is True

    def test_unsilence_flag_clear(self):
        Logger.silence()
        Logger.unsilence()
        assert Logger._silenced is False


# ────────────────────────────────────────────────────────────────────────────
class TestFileOutput:
    def test_log_written_to_file(self):
        buf = _inject_file()
        Logger.info("to_file")
        assert "to_file" in buf.getvalue()

    def test_file_receives_plain_text(self):
        """Arquivo nunca deve conter códigos ANSI."""
        Logger._use_color = True  # força cor no terminal
        buf = _inject_file()
        Logger.info("plain")
        assert "\033[" not in buf.getvalue()

    def test_file_receives_label(self):
        buf = _inject_file()
        Logger.info("msg")
        assert "INFO" in buf.getvalue()

    def test_file_receives_kwargs(self):
        buf = _inject_file()
        Logger.info("ctx", x=1)
        assert "x=1" in buf.getvalue()

    def test_disable_file_stops_writing(self):
        buf = _inject_file()
        Logger.disable_file()
        Logger.info("after_disable")
        assert "after_disable" not in buf.getvalue()

    def test_disable_file_sets_none(self):
        _inject_file()
        Logger.disable_file()
        assert Logger._file is None

    def test_file_suppressed_below_level(self):
        Logger.set_level(Logger.WARNING)
        buf = _inject_file()
        Logger.debug("hidden")
        assert "hidden" not in buf.getvalue()

    def test_enable_file_replaces_old_file(self, tmp_path):
        """enable_file deve fechar o antigo antes de abrir o novo."""
        old = io.StringIO()
        Logger._file = old
        new_path = str(tmp_path / "test.log")
        Logger.enable_file(new_path)
        assert Logger._file is not old
        Logger.disable_file()


# ────────────────────────────────────────────────────────────────────────────
class TestTaggedLogger:
    def test_tagged_returns_tagged_logger(self):
        log = Logger.tagged("Physics")
        assert isinstance(log, _TaggedLogger)

    def test_tag_in_output(self, capsys):
        log = Logger.tagged("Audio")
        log.info("init")
        assert "[Audio]" in capsys.readouterr().out

    def test_tag_in_warning_output(self, capsys):
        log = Logger.tagged("Scene")
        log.warning("missing")
        assert "[Scene]" in capsys.readouterr().err

    def test_tag_in_error_output(self, capsys):
        log = Logger.tagged("Renderer")
        log.error("crash")
        assert "[Renderer]" in capsys.readouterr().err

    def test_tagged_debug_respects_level(self, capsys):
        Logger.set_level(Logger.INFO)
        log = Logger.tagged("X")
        log.debug("hidden")
        assert "hidden" not in capsys.readouterr().out

    def test_tagged_debug_shown_at_debug_level(self, capsys):
        Logger.set_level(Logger.DEBUG)
        log = Logger.tagged("X")
        log.debug("visible")
        assert "visible" in capsys.readouterr().out

    def test_tagged_respects_silence(self, capsys):
        Logger.silence()
        log = Logger.tagged("Y")
        log.info("muted")
        assert "muted" not in capsys.readouterr().out

    def test_tagged_writes_to_file(self):
        buf = _inject_file()
        log = Logger.tagged("Z")
        log.info("file_entry")
        assert "file_entry" in buf.getvalue()
        assert "[Z]" in buf.getvalue()

    def test_tagged_kwargs_in_output(self, capsys):
        log = Logger.tagged("T")
        log.info("ctx", a=1, b=2)
        out = capsys.readouterr().out
        assert "a=1" in out and "b=2" in out

    def test_repr_contains_tag(self):
        log = Logger.tagged("MyTag")
        assert "MyTag" in repr(log)
