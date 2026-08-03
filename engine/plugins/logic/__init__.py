"""Metadata node and example catalog for the canonical graph framework.

The former ``LogicPlugin`` bootstrap exposed a dummy compiler and was never part
of the engine boot path. Consumers import ``nodes`` or ``example_graphs``
explicitly, so importing this package has no side effects.
"""

__all__: list[str] = []
