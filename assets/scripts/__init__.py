"""
assets/scripts/__init__.py

Importa todos os scripts para garantir que sejam registrados
no ComponentRegistry ao importar o pacote.
"""
from assets.scripts.player_controller import PlayerController
from assets.scripts.enemy_ai import EnemyAI
from assets.scripts.health import Health
from assets.scripts.collectible import Collectible
from assets.scripts.camera_follow import CameraFollow
from assets.scripts.timer_component import TimerComponent
from assets.scripts.animator import Animator
from assets.scripts.projectile import Projectile

__all__ = [
    "PlayerController",
    "EnemyAI",
    "Health",
    "Collectible",
    "CameraFollow",
    "TimerComponent",
    "Animator",
    "Projectile",
]
