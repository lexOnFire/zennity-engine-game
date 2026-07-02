"""
engine/logger.py
────────────────────────────────────────────────────────────────
Logger global da Zennity Engine.

Uso básico:

    from engine.logger import Logger

    Logger.info("Engine initialized")
    Logger.warning("Missing texture", path="hero.png")
    Logger.error("Audio device not found")
    Logger.debug("Collider registered", id="player", type="Box")

Logger com tag de módulo:

    log = Logger.tagged("Physics")
    log.warning("Overlap detected", a="player", b="wall")
    # Saída: [WARN ] [Physics] Overlap detected | a=player b=wall

Configuração:

    Logger.set_level(Logger.DEBUG)          # mostra tudo
    Logger.set_level(Logger.WARNING)        # só warnings e erros
    Logger.enable_file("zennity.log")       # também escreve em arquivo
    Logger.silence()                        # mudo (útil em testes)
    Logger.unsilence()

Níveis (do mais ao menos verbose):
    DEBUG < INFO < WARNING < ERROR
"""
from __future__ import annotations

import sys
import os
import datetime
from typing import Optional, IO


class Logger:
    """Logger global da Zennity Engine. Zero dependências externas."""

    # Níveis
    DEBUG   = 0
    INFO    = 1
    WARNING = 2
    ERROR   = 3

    _level:    int  = INFO
    _silenced: bool = False
    _file:     Optional[IO] = None

    # Suporte a cores ANSI (desabilitado no Windows sem terminal moderno)
    _use_color: bool = sys.stdout.isatty() and (
        os.name != "nt" or os.environ.get("TERM_PROGRAM") is not None
    )

    # Códigos ANSI
    _RESET  = "\033[0m"
    _COLORS = {
        DEBUG:   "\033[36m",   # ciano
        INFO:    "\033[32m",   # verde
        WARNING: "\033[33m",   # amarelo
        ERROR:   "\033[31m",   # vermelho
    }
    _LABELS = {
        DEBUG:   "DEBUG",
        INFO:    "INFO ",
        WARNING: "WARN ",
        ERROR:   "ERROR",
    }

    # ------------------------------------------------------------------ #
    # API pública                                                         #
    # ------------------------------------------------------------------ #

    @classmethod
    def debug(cls, message: str, **kwargs) -> None:
        cls._log(cls.DEBUG, message, tag=None, **kwargs)

    @classmethod
    def info(cls, message: str, **kwargs) -> None:
        cls._log(cls.INFO, message, tag=None, **kwargs)

    @classmethod
    def warning(cls, message: str, **kwargs) -> None:
        cls._log(cls.WARNING, message, tag=None, **kwargs)

    @classmethod
    def error(cls, message: str, **kwargs) -> None:
        cls._log(cls.ERROR, message, tag=None, **kwargs)

    # ------------------------------------------------------------------ #
    # Logger com tag de módulo                                            #
    # ------------------------------------------------------------------ #

    @classmethod
    def tagged(cls, tag: str) -> "_TaggedLogger":
        """
        Retorna um logger decorado com a tag do módulo.

        Exemplo:
            log = Logger.tagged("Audio")
            log.warning("Device not found")
            # [WARN ] [Audio] Device not found
        """
        return _TaggedLogger(tag)

    # ------------------------------------------------------------------ #
    # Configuração                                                        #
    # ------------------------------------------------------------------ #

    @classmethod
    def set_level(cls, level: int) -> None:
        """Define o nível mínimo de log exibido."""
        cls._level = level

    @classmethod
    def enable_file(cls, path: str) -> None:
        """Habilita escrita em arquivo. Cria ou abre em modo append."""
        if cls._file:
            cls._file.close()
        cls._file = open(path, "a", encoding="utf-8")

    @classmethod
    def disable_file(cls) -> None:
        """Fecha e desabilita o arquivo de log."""
        if cls._file:
            cls._file.close()
            cls._file = None

    @classmethod
    def silence(cls) -> None:
        """Suprime toda saída no terminal (arquivo não é afetado)."""
        cls._silenced = True

    @classmethod
    def unsilence(cls) -> None:
        cls._silenced = False

    # ------------------------------------------------------------------ #
    # Interno                                                             #
    # ------------------------------------------------------------------ #

    @classmethod
    def _log(
        cls,
        level: int,
        message: str,
        tag: Optional[str],
        **kwargs,
    ) -> None:
        if level < cls._level:
            return

        now    = datetime.datetime.now().strftime("%H:%M:%S")
        label  = cls._LABELS.get(level, "?????")
        extras = (" | " + " ".join(f"{k}={v}" for k, v in kwargs.items())) if kwargs else ""
        tag_str = f" [{tag}]" if tag else ""

        # Linha plain (arquivo / sem cor)
        plain = f"[{now}] [{label}]{tag_str} {message}{extras}"

        # Linha colorida (terminal)
        if cls._use_color:
            color  = cls._COLORS.get(level, "")
            reset  = cls._RESET
            colored = f"{color}[{now}] [{label}]{tag_str}{reset} {message}{extras}"
        else:
            colored = plain

        if not cls._silenced:
            stream = sys.stderr if level >= cls.WARNING else sys.stdout
            print(colored, file=stream)

        if cls._file:
            print(plain, file=cls._file, flush=True)


class _TaggedLogger:
    """Logger com tag de módulo fixa. Criado por Logger.tagged()."""

    __slots__ = ("_tag",)

    def __init__(self, tag: str) -> None:
        self._tag = tag

    def debug(self, message: str, **kwargs) -> None:
        Logger._log(Logger.DEBUG, message, tag=self._tag, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        Logger._log(Logger.INFO, message, tag=self._tag, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        Logger._log(Logger.WARNING, message, tag=self._tag, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        Logger._log(Logger.ERROR, message, tag=self._tag, **kwargs)

    def __repr__(self) -> str:
        return f"<Logger tag='{self._tag}'>"
