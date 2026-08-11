"""Shipping runtime node implementations.

Importing this package loads every module in
:data:`engine.logic.runtime.node_loader.RUNTIME_NODE_MODULES`.  It used to carry
its own hand-written list of 13 imports while ``LogicProvider.boot()`` carried a
different list of 22, so what a process could execute depended on which one ran.
Both now defer to the single loader; this package keeps no list of its own.
"""

from ..node_loader import load_runtime_node_modules

load_runtime_node_modules()
