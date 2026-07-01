from __future__ import annotations
"""
engine/physics/tilemap_collider.py
────────────────────────────────────

TilemapCollider — integra o sistema de TileMap com BoxCollider + RigidBody.

Como usar
─────────
    # Na sua Scene.start():
    from engine.physics.tilemap_collider import TilemapCollider

    self.tilemap = ...  # seu TileMap já configurado
    tilemap_col  = TilemapCollider(self.tilemap, layer_name="collision")

    # Para cada GameObject que tem BoxCollider + RigidBody:
    TilemapCollider.resolve(tilemap_col, game_object)

    # Ou resolva vários de uma vez na Scene.update():
    tilemap_col.resolve_all([player, enemy1, enemy2])

Arquitetura
───────────
  A resolução é feita em dois passos por frame:

  1. RigidBody.update(dt) move o transform (já acontece automaticamente).
  2. TilemapCollider.resolve_all() testa overlap AABB contra tiles sólidos
     e empurra o transform para fora + zera a componente de velocidade
     relevante no RigidBody.

  Esse padrão preserva o sistema de colisão objeto↔objeto existente
  (BoxCollider.check_all) e adiciona a colisão objeto↔tilemap por cima.
"""

from typing import List, Optional, TYPE_CHECKING
import pygame

from engine.component import Component

if TYPE_CHECKING:
    from engine.tilemap.tilemap import TileMap
    from engine.game_object import GameObject


class TilemapCollider:
    """
    Resolvedor de colisões entre GameObjects e um TileMap.

    Não é um Component — é um objeto de sistema que vive na Scene.
    Isso evita duplicar lógica do ciclo de vida e permite controle
    explícito da ordem de resolução (depois do RigidBody, antes do draw).

    Parameters
    ----------
    tilemap       : TileMap – O mapa a ser usado para colisão.
    layer_name    : str     – Nome da camada de colisão (padrão: "collision").
    max_iter      : int     – Máximo de iterações de resolução por frame
                              (evita loop infinito em cantos apertados).
    """

    def __init__(
        self,
        tilemap,
        layer_name: str = "collision",
        max_iter:   int = 4,
    ) -> None:
        self.tilemap    = tilemap
        self.layer_name = layer_name
        self.max_iter   = max_iter

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def resolve_all(self, game_objects: List["GameObject"]) -> None:
        """
        Resolve colisões de tilemap para uma lista de GameObjects.
        Chame na Scene.update() após atualizar todos os objetos.
        """
        for go in game_objects:
            if go.active:
                self.resolve(go)

    def resolve(self, game_object: "GameObject") -> None:
        """
        Resolve colisões de tilemap para um único GameObject.
        O objeto precisa ter um BoxCollider para que a resolução aconteça.
        RigidBody é opcional — sem ele o transform ainda é corrigido mas
        a velocidade não é zerada.
        """
        from engine.physics.collider  import BoxCollider
        from engine.physics.rigidbody import RigidBody

        col = game_object.get_component(BoxCollider)
        if col is None or col.is_trigger:
            return

        rb  = game_object.get_component(RigidBody)
        if rb:
            rb.grounded = False
        tr  = game_object.transform

        for _ in range(self.max_iter):
            rect = col.rect
            solid_rects = self.tilemap.get_solid_rects_in_region(
                rect.x, rect.y, rect.width, rect.height,
                layer_name=self.layer_name,
            )
            if not solid_rects:
                break

            # Resolve o rect sólido com maior overlap primeiro
            resolved_any = False
            for tile_rect in solid_rects:
                overlap = rect.clip(tile_rect)
                if overlap.width == 0 or overlap.height == 0:
                    continue

                ox, oy = overlap.width, overlap.height

                if ox < oy:
                    # Resolução horizontal
                    if rect.centerx < tile_rect.centerx:
                        tr.x -= ox          # empurra para a esquerda
                        if rb and not rb.is_kinematic:
                            rb.velocity[0] = min(rb.velocity[0], 0.0)
                    else:
                        tr.x += ox          # empurra para a direita
                        if rb and not rb.is_kinematic:
                            rb.velocity[0] = max(rb.velocity[0], 0.0)
                else:
                    # Resolução vertical
                    if rect.centery < tile_rect.centery:
                        tr.y -= oy          # empurra para cima (pousa no chão)
                        if rb and not rb.is_kinematic:
                            rb.velocity[1] = min(rb.velocity[1], 0.0)
                            rb.grounded     = True
                    else:
                        tr.y += oy          # empurra para baixo (teto)
                        if rb and not rb.is_kinematic:
                            rb.velocity[1] = max(rb.velocity[1], 0.0)

                resolved_any = True
                break   # recalcula rect após cada resolução

            if not resolved_any:
                break

    # ------------------------------------------------------------------
    # One-way platform helper
    # ------------------------------------------------------------------

    def resolve_one_way(
        self,
        game_object: "GameObject",
        prev_bottom: float,
    ) -> None:
        """
        Resolve plataformas one-way (passáveis por baixo).
        Só bloqueia se o bottom do objeto estava ACIMA do topo do tile
        no frame anterior.

        Parameters
        ----------
        game_object : GameObject – Objeto a resolver.
        prev_bottom : float      – Borda inferior do collider no frame anterior.
        """
        from engine.physics.collider  import BoxCollider
        from engine.physics.rigidbody import RigidBody

        col = game_object.get_component(BoxCollider)
        if col is None:
            return

        rb  = game_object.get_component(RigidBody)
        tr  = game_object.transform
        rect = col.rect
        tw   = self.tilemap.tile_width
        th   = self.tilemap.tile_height

        layer = self.tilemap.get_layer(self.layer_name)
        if layer is None:
            return

        col_start = max(0, rect.left  // tw)
        col_end   = min(layer.width  - 1, rect.right  // tw)
        row_start = max(0, rect.top   // th)
        row_end   = min(layer.height - 1, rect.bottom // th)

        for row in range(row_start, row_end + 1):
            for col_idx in range(col_start, col_end + 1):
                gid = layer.get_gid(col_idx, row)
                if gid <= 0:
                    continue
                ts = self.tilemap._resolve_tileset(gid)
                if ts is None or not ts.is_one_way(gid):
                    continue

                tile_top = row * th
                if prev_bottom <= tile_top and rect.bottom > tile_top:
                    penetration = rect.bottom - tile_top
                    tr.y -= penetration
                    if rb and not rb.is_kinematic:
                        rb.velocity[1] = min(rb.velocity[1], 0.0)
                        rb.grounded     = True
