"""Collision layer and mask constants for bitmask-based collision filtering."""
from __future__ import annotations

# Phase 5B.4: Bitmask collision filtering
# Layers are bit positions; masks are bitsets.
# Two colliders interact if: (a.mask & b.layer) != 0 AND (b.mask & a.layer) != 0

# Default layer assignment (bit position)
DEFAULT_LAYER = 1 << 0  # Bit 0: Default layer (legacy assets)
PLAYER_LAYER = 1 << 1   # Bit 1: Player
ENEMY_LAYER = 1 << 2    # Bit 2: Enemy
WORLD_LAYER = 1 << 3    # Bit 3: World/Static
PROJECTILE_LAYER = 1 << 4  # Bit 4: Projectile/Bullet
PICKUP_LAYER = 1 << 5   # Bit 5: Pickup/Collectible
TRIGGER_LAYER = 1 << 6  # Bit 6: Trigger/Special
RESERVED_7 = 1 << 7
RESERVED_8 = 1 << 8
RESERVED_9 = 1 << 9
RESERVED_10 = 1 << 10
RESERVED_11 = 1 << 11
RESERVED_12 = 1 << 12
RESERVED_13 = 1 << 13
RESERVED_14 = 1 << 14
RESERVED_15 = 1 << 15
RESERVED_16 = 1 << 16
RESERVED_17 = 1 << 17
RESERVED_18 = 1 << 18
RESERVED_19 = 1 << 19
RESERVED_20 = 1 << 20
RESERVED_21 = 1 << 21
RESERVED_22 = 1 << 22
RESERVED_23 = 1 << 23
RESERVED_24 = 1 << 24
RESERVED_25 = 1 << 25
RESERVED_26 = 1 << 26
RESERVED_27 = 1 << 27
RESERVED_28 = 1 << 28
RESERVED_29 = 1 << 29
RESERVED_30 = 1 << 30
RESERVED_31 = 1 << 31

# Alias masks for common patterns
ALL_LAYERS = 0xFFFFFFFF  # All bits set (compatibility for legacy assets)


def can_collide(a_layer: int, a_mask: int, b_layer: int, b_mask: int) -> bool:
    """
    Determine if two colliders can interact based on layer/mask.

    Canonical collision rule:
    - a.mask accepts b's layer AND
    - b.mask accepts a's layer

    Both conditions must be true (bidirectional filtering).
    """
    return (a_mask & b_layer) != 0 and (b_mask & a_layer) != 0


def validate_layer(layer: int) -> int:
    """Validate and normalize layer value. Must be a power of 2."""
    if not isinstance(layer, int) or layer < 0:
        return DEFAULT_LAYER
    if layer == 0:
        return DEFAULT_LAYER
    return layer


def validate_mask(mask: int) -> int:
    """Validate and normalize mask value. Can be any non-negative int."""
    if not isinstance(mask, int) or mask < 0:
        return ALL_LAYERS
    return mask
