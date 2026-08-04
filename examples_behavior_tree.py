"""Exemplos práticos de Behavior Tree — Complete e use como referência!

Esses exemplos mostram como criar árvores e integrá-las com seu jogo.
"""

import json
from engine.ai.behavior_tree_runtime import BehaviorTreeRuntime, BehaviorStatus


# ════════════════════════════════════════════════════════════════════════════
# EXEMPLO 1: Inimigo Patrulha + Persegue + Ataca
# ════════════════════════════════════════════════════════════════════════════

ENEMY_TREE_BASIC = {
    "format": "zennity.behavior_tree",
    "version": 1,
    "name": "BasicEnemy",
    "start_node": "root",
    "nodes": {
        "root": {
            "type": "bt.selector",
            "children": ["check_attack", "check_chase", "patrol"]
        },
        # Tenta atacar se alvo está muito perto
        "check_attack": {
            "type": "bt.sequence",
            "children": ["in_attack_range", "attack_action"]
        },
        "in_attack_range": {
            "type": "bt.target_in_range",
            "target": "Player",
            "distance": 60.0
        },
        "attack_action": {
            "type": "bt.attack",
            "target": "Player",
            "damage": 15.0,
            "range": 60.0
        },
        # Persegue se alvo está perto
        "check_chase": {
            "type": "bt.target_in_range",
            "target": "Player",
            "distance": 300.0
        },
        # Patrulha normalmente
        "patrol": {
            "type": "bt.patrol",
            "point_a": [100, 100],
            "point_b": [400, 100],
            "speed": 80.0
        }
    }
}


# ════════════════════════════════════════════════════════════════════════════
# EXEMPLO 2: Inimigo Inteligente (Ataca se Saudável, Foge se Ferido)
# ════════════════════════════════════════════════════════════════════════════

ENEMY_TREE_SMART = {
    "format": "zennity.behavior_tree",
    "version": 1,
    "name": "SmartEnemy",
    "start_node": "root",
    "nodes": {
        "root": {
            "type": "bt.selector",
            "children": ["behavior_attack", "behavior_flee", "patrol"]
        },
        # Persegue e ataca se saudável
        "behavior_attack": {
            "type": "bt.sequence",
            "children": ["is_healthy", "check_range_attack", "attack_with_cooldown"]
        },
        "is_healthy": {
            "type": "bt.health_check",
            "min_health": 50.0
        },
        "check_range_attack": {
            "type": "bt.target_in_range",
            "target": "Player",
            "distance": 250.0
        },
        "attack_with_cooldown": {
            "type": "bt.cooldown",
            "child": "attack",
            "seconds": 1.0  # Um ataque por segundo
        },
        "attack": {
            "type": "bt.attack",
            "target": "Player",
            "damage": 20.0,
            "range": 60.0
        },
        # Foge se ferido e alvo está perto
        "behavior_flee": {
            "type": "bt.sequence",
            "children": ["is_hurt", "check_range_flee", "run_away"]
        },
        "is_hurt": {
            "type": "bt.health_check",
            "min_health": 20.0  # Falha se health ≤ 20
        },
        "check_range_flee": {
            "type": "bt.target_in_range",
            "target": "Player",
            "distance": 300.0
        },
        "run_away": {
            "type": "bt.move_to",
            "target_pos": [0, 100],
            "speed": 150.0
        },
        # Patrulha se nada acontece
        "patrol": {
            "type": "bt.patrol",
            "point_a": [50, 50],
            "point_b": [500, 50],
            "speed": 60.0
        }
    }
}


# ════════════════════════════════════════════════════════════════════════════
# EXEMPLO 3: Bôs com Múltiplas Fases
# ════════════════════════════════════════════════════════════════════════════

BOSS_TREE = {
    "format": "zennity.behavior_tree",
    "version": 1,
    "name": "BossEnemy",
    "start_node": "root",
    "nodes": {
        "root": {
            "type": "bt.selector",
            "children": ["phase_dead", "phase_low_hp", "phase_medium_hp", "phase_high_hp"]
        },
        # Fase morto (saúde ≤ 0)
        "phase_dead": {
            "type": "bt.inverter",
            "child": "check_alive"
        },
        "check_alive": {
            "type": "bt.health_check",
            "min_health": 1.0
        },
        # Fase crítica (HP < 30)
        "phase_low_hp": {
            "type": "bt.sequence",
            "children": ["check_low_hp", "boss_desperado"]
        },
        "check_low_hp": {
            "type": "bt.health_check",
            "min_health": 30.0
        },
        "boss_desperado": {
            "type": "bt.sequence",
            "children": ["attack_rapid", "scream_anim"]
        },
        "attack_rapid": {
            "type": "bt.repeat",
            "child": "boss_attack_quick",
            "count": 3
        },
        "boss_attack_quick": {
            "type": "bt.cooldown",
            "child": "boss_attack",
            "seconds": 0.3  # Ataque rápido
        },
        "boss_attack": {
            "type": "bt.attack",
            "target": "Player",
            "damage": 30.0,
            "range": 100.0
        },
        "scream_anim": {
            "type": "bt.play_animation",
            "animation": "Roar"
        },
        # Fase média (30 <= HP < 70)
        "phase_medium_hp": {
            "type": "bt.sequence",
            "children": ["check_medium_hp", "boss_balanced"]
        },
        "check_medium_hp": {
            "type": "bt.health_check",
            "min_health": 70.0
        },
        "boss_balanced": {
            "type": "bt.selector",
            "children": ["attack_balanced", "move_around"]
        },
        "attack_balanced": {
            "type": "bt.cooldown",
            "child": "boss_attack_medium",
            "seconds": 0.7
        },
        "boss_attack_medium": {
            "type": "bt.attack",
            "target": "Player",
            "damage": 25.0,
            "range": 100.0
        },
        "move_around": {
            "type": "bt.patrol",
            "point_a": [100, 100],
            "point_b": [500, 100],
            "speed": 100.0
        },
        # Fase calmo (HP >= 70)
        "phase_high_hp": {
            "type": "bt.sequence",
            "children": ["boss_careful", "attack_passive"]
        },
        "boss_careful": {
            "type": "bt.idle",
            "duration": 0.5
        },
        "attack_passive": {
            "type": "bt.cooldown",
            "child": "boss_attack_weak",
            "seconds": 1.5
        },
        "boss_attack_weak": {
            "type": "bt.attack",
            "target": "Player",
            "damage": 15.0,
            "range": 80.0
        }
    }
}


# ════════════════════════════════════════════════════════════════════════════
# IMPLEMENTAÇÃO: Classe do Inimigo com Behavior Tree
# ════════════════════════════════════════════════════════════════════════════

class Enemy:
    """Inimigo com Behavior Tree integrada."""

    def __init__(self, x=100, y=100, tree_data=None):
        self.position = [x, y]
        self.velocity = [0, 0]
        self.health = 100
        self.max_health = 100
        self.is_dead = False

        # Integração com Behavior Tree
        if tree_data is None:
            tree_data = ENEMY_TREE_BASIC

        self.bt = MyGameBehaviorTree(tree_data, game_object=self)

    def update(self, dt=0.016):
        """Atualiza o inimigo a cada frame."""
        if self.is_dead:
            return

        # Atualizar posição
        self.position[0] += self.velocity[0] * dt
        self.position[1] += self.velocity[1] * dt

        # Executar behavior tree
        status = self.bt.update(dt)

        # Debug
        self._log_events()

    def _log_events(self):
        """Mostra eventos do behavior tree."""
        for event in self.bt.events:
            if event["type"] == "action_done":
                print(f"  → {event.get('action_type', '?')}")
            elif event["type"] == "node_failed":
                print(f"  ✗ Falha: {event.get('reason', '?')}")

    def take_damage(self, amount):
        """Recebe dano."""
        self.health -= amount
        if self.health <= 0:
            self.is_dead = True
            self.health = 0


# ════════════════════════════════════════════════════════════════════════════
# INTEGRAÇÃO COM O JOG0: Sobrescrever Métodos
# ════════════════════════════════════════════════════════════════════════════

class MyGameBehaviorTree(BehaviorTreeRuntime):
    """Behavior Tree integrada com seu jogo."""

    def _find_objects_by_tag(self, tag):
        """Encontrar objetos no jogo por tag."""
        if tag == "Player":
            return [GAME_STATE.get("player")]
        return []

    def _get_position(self, obj):
        """Pegar posição de um objeto."""
        if hasattr(obj, "position"):
            return tuple(obj.position)
        return (0.0, 0.0)

    def _get_health(self, obj):
        """Pegar saúde de um objeto."""
        return getattr(obj, "health", 100.0)

    def _move_towards_target(self, obj, target_pos, speed):
        """Mover objeto em direção ao alvo."""
        if not hasattr(obj, "position") or not hasattr(obj, "velocity"):
            return

        dx = target_pos[0] - obj.position[0]
        dy = target_pos[1] - obj.position[1]
        dist = (dx * dx + dy * dy) ** 0.5

        if dist > 0:
            obj.velocity[0] = (dx / dist) * speed
            obj.velocity[1] = (dy / dist) * speed

    def _apply_damage(self, obj, damage):
        """Aplicar dano a um objeto."""
        if hasattr(obj, "take_damage"):
            obj.take_damage(damage)

    def _play_animation(self, obj, animation):
        """Tocar uma animação."""
        print(f"  🎬 Tocar: {animation}")


# ════════════════════════════════════════════════════════════════════════════
# TESTE/DEMO
# ════════════════════════════════════════════════════════════════════════════

GAME_STATE = {
    "player": None,
    "enemies": []
}


class SimplePlayer:
    """Jogador simples para teste."""

    def __init__(self, x=700, y=100):
        self.position = [x, y]
        self.health = 100


def demo_basic_enemy():
    """Demo: Inimigo básico."""
    print("=" * 60)
    print("DEMO 1: Inimigo Básico (Patrulha + Ataca)")
    print("=" * 60)

    GAME_STATE["player"] = SimplePlayer(300, 100)

    enemy = Enemy(100, 100, ENEMY_TREE_BASIC)

    # Simular 5 segundos de jogo
    for i in range(int(5.0 / 0.016)):
        # Atualizar distância ao player
        dx = GAME_STATE["player"].position[0] - enemy.position[0]
        dy = GAME_STATE["player"].position[1] - enemy.position[1]
        dist = (dx * dx + dy * dy) ** 0.5
        enemy.bt.set_parameter("player_distance", dist)

        if i % 20 == 0:  # Print a cada 0.3s
            print(f"\nFrame {i}: pos={enemy.position}, health={enemy.health}, dist={dist:.0f}")

        enemy.update(dt=0.016)


def demo_smart_enemy():
    """Demo: Inimigo inteligente que foge."""
    print("\n" + "=" * 60)
    print("DEMO 2: Inimigo Inteligente (Ataca se Saudável, Foge se Ferido)")
    print("=" * 60)

    GAME_STATE["player"] = SimplePlayer(300, 100)

    enemy = Enemy(100, 100, ENEMY_TREE_SMART)

    # Simular: jogador vai ficando mais perto
    for i in range(int(10.0 / 0.016)):
        # Aproximar jogador
        GAME_STATE["player"].position[0] -= 0.3
        GAME_STATE["player"].position[1] = 100

        # Danificar inimigo depois de 2 segundos
        if i == 125:  # 2 segundos
            print("\n💥 JOGADOR ATACA O INIMIGO!")
            enemy.take_damage(60)

        dx = GAME_STATE["player"].position[0] - enemy.position[0]
        dy = GAME_STATE["player"].position[1] - enemy.position[1]
        dist = (dx * dx + dy * dy) ** 0.5

        if i % 20 == 0:
            print(f"\nFrame {i}: health={enemy.health}, dist={dist:.0f}")

        enemy.update(dt=0.016)


if __name__ == "__main__":
    print("🎮 Exemplos de Behavior Tree\n")

    # Descomentar para testar:
    # demo_basic_enemy()
    # demo_smart_enemy()

    print("\n✅ Exemplos criados! Descomente demo_basic_enemy() ou demo_smart_enemy() para rodar.\n")
