"""
engine/core
────────────────────────────────────────────────────────────────
Pacote core da Zennity Engine (FASE 1).

Este pacote será o lar definitivo de:
  Application, Engine, Scene, GameObject, Component,
  System, Time, EventBus, Logger, AssetManager

Por ora serve como módulo stub que será populado
ao longo da Sprint 1.1, commit a commit.

Migração planejada:
  engine/application.py  →  engine/core/application.py
  engine/time.py         →  engine/core/time.py
  engine/event_bus.py    →  engine/core/event_bus.py
  engine/core.py         →  engine/core/engine.py
  (novos)                   engine/core/logger.py
                            engine/core/system.py

Ate a migração acontecer, engine/application.py é o
ponto de entrada oficial.
"""
