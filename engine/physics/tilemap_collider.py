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

from engine.core import Component

if TYPE_CHECKING:
    from engine.tilemap.tilemap import TileMap
    from engine.game_object import GameObject


class LegacyTilemapCollisionAdapter:
    """
    Adapta engine.graphics.tilemap.Tilemap (o componente que o editor de
    fato cria/serializa via .zscene -- dict esparso de camadas, sem nenhum
    metadado de solidez por tile) pra interface que TilemapCollider espera
    (get_solid_rects_in_region), permitindo reusar a mesma resolução de
    colisão do sistema real.

    BUG FIX: BoxCollider.check_all() só reconhecia colisão de tilemap via
    isinstance(comp, engine.tilemap.tilemap.TilemapRenderer) -- a classe do
    sistema "real". Só que component_registry.py registra exclusivamente o
    par legado (Tilemap/TilemapRenderer de engine/graphics/tilemap.py) como
    componente serializável, então TODO tilemap criado no editor nunca batia
    nesse isinstance -- nunca tinha colisão sólida em Play Mode nem no jogo
    exportado. Como o formato legado não tem flag "solid" por tile, qualquer
    tile não-vazio (id != 0) em qualquer camada é tratado como sólido --
    cobre o caso comum de chão/parede de plataforma sem exigir migração de
    formato de dados nem mudança no editor.
    """

    def __init__(self, legacy_tilemap) -> None:
        self._tilemap = legacy_tilemap
        self.tile_width = int(legacy_tilemap.tile_size)
        self.tile_height = int(legacy_tilemap.tile_size)

    def get_solid_rects_in_region(
        self, x: float, y: float, w: float, h: float, layer_name: str = "collision",
    ) -> List[pygame.Rect]:
        tw, th = self.tile_width, self.tile_height
        if tw <= 0 or th <= 0:
            return []
        col_start = int(x // tw)
        col_end = int((x + w) // tw)
        row_start = int(y // th)
        row_end = int((y + h) // th)
        rects: List[pygame.Rect] = []
        for layer in self._tilemap.layers:
            for (tx, ty), tile_id in layer.items():
                if tile_id == 0:
                    continue
                if col_start <= tx <= col_end and row_start <= ty <= row_end:
                    rects.append(pygame.Rect(tx * tw, ty * th, tw, th))
        return rects


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
    ground_probe  : float   – Altura (px) da faixa testada logo abaixo do
                              collider para decidir ``RigidBody.grounded``.
    """

    def __init__(
        self,
        tilemap,
        layer_name: str = "collision",
        max_iter:   int = 4,
        ground_probe: float = 2.0,
    ) -> None:
        self.tilemap    = tilemap
        self.layer_name = layer_name
        self.max_iter   = max_iter
        self.ground_probe = float(ground_probe)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    @staticmethod
    def _box_collider(game_object):
        """Resolve a box collider structurally without importing its concrete module."""
        return next(
            (
                component for component in getattr(game_object, "components", ())
                if getattr(component, "component_type", "") == "BoxCollider"
            ),
            None,
        )

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
        from engine.physics.rigidbody import RigidBody

        col = self._box_collider(game_object)
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

        if rb is not None:
            rb.grounded = rb.grounded or self.is_on_ground(col)

    def is_on_ground(self, box_collider) -> bool:
        """
        Testa uma faixa fina logo ABAIXO do collider e diz se há chão sólido.

        BUG FIX: ``grounded`` era ligado apenas no frame em que a resolução
        vertical empurrava o objeto para fora de um tile. Um objeto apenas
        APOIADO no chão não penetra nada (a resolução do frame anterior já o
        alinhou à borda) e, como ``RigidBody.update()`` zera ``grounded`` todo
        frame, a flag oscilava entre True/False em repouso -- medido em ~43%
        dos frames com o objeto parado no chão. Isso fazia o nó "Is Grounded"
        do Logic Graph recusar a maioria dos comandos de pulo, deixando o
        controle do jogador visivelmente truncado.

        A sondagem não depende de penetração, então é estável em repouso.
        """
        rect = box_collider.rect
        probe = self.tilemap.get_solid_rects_in_region(
            rect.x, rect.bottom, rect.width, self.ground_probe,
            layer_name=self.layer_name,
        )
        # get_solid_rects_in_region trabalha em células inteiras, então pode
        # devolver o próprio tile em que o objeto está encostado lateralmente;
        # só conta como chão o tile cujo topo está abaixo da base do collider.
        return any(tile.top >= rect.bottom for tile in probe)

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
        from engine.physics.rigidbody import RigidBody

        col = self._box_collider(game_object)
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

        import math
        col_start = max(0, rect.left  // tw)
        col_end   = min(layer.width  - 1, math.ceil(rect.right / tw))
        row_start = max(0, rect.top   // th)
        row_end   = min(layer.height - 1, math.ceil(rect.bottom / th))

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
