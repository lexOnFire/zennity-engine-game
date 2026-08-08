"""Phase 6B.4: Animator Controller & Parameter Integration - Tests."""
import pytest
import pygame

from engine.core import Scene, GameObject
from engine.animation import Animator, AnimationClip
from engine.animation.animation_controller import AnimationController
from engine.graphics.renderer import SpriteRenderer
from engine.logic.runtime.nodes.animation_nodes import (
    execute_animator_parameter,
    execute_animator_set_trigger,
    evaluate_animator_get_parameter,
    evaluate_get_animator_state,
)


@pytest.fixture
def scene_with_controller():
    """Create a scene with a GameObject that has AnimationController."""
    scene = Scene("TestScene")

    player = GameObject("Player")
    scene.add_game_object(player)

    # Add SpriteRenderer
    sr = player.add_component(SpriteRenderer())

    # Add Animator
    animator = player.add_component(Animator())

    # Add AnimationController
    controller = player.add_component(AnimationController(default_state="idle"))

    # Create animation frames
    frames_idle = [pygame.Surface((16, 16)) for _ in range(2)]
    for f in frames_idle:
        f.fill((255, 0, 0))

    frames_run = [pygame.Surface((16, 16)) for _ in range(3)]
    for f in frames_run:
        f.fill((0, 255, 0))

    frames_attack = [pygame.Surface((16, 16)) for _ in range(2)]
    for f in frames_attack:
        f.fill((0, 0, 255))

    # Add clips to animator
    animator.add_clip(AnimationClip("idle", frames_idle, fps=10, loop=True))
    animator.add_clip(AnimationClip("run", frames_run, fps=12, loop=True))
    animator.add_clip(AnimationClip("attack", frames_attack, fps=10, loop=False))

    # Configure controller states
    controller.add_state("idle", "idle")
    controller.add_state("run", "run")
    controller.add_state("attack", "attack")

    # Configure controller transitions
    controller.add_transition(
        "idle",
        "run",
        condition=lambda p: p.get("speed", 0) > 0.5,
    )
    controller.add_transition(
        "run",
        "idle",
        condition=lambda p: p.get("speed", 0) <= 0.5,
    )
    controller.add_transition(
        "run",
        "attack",
        condition=lambda p: p.get("attack_trigger", False),
    )
    controller.add_transition(
        "attack",
        "idle",
        condition=lambda p: p.get("finished", False),
    )

    # Initialize controller
    player.scene = scene
    controller.start()

    # Create game mock
    class GameMock:
        def __init__(self):
            self.name = "Game"
            self.physics_world = None

        def find_object(self, name: str):
            return scene.find(name)

    game = GameMock()
    return scene, player, animator, controller, game, sr


class TestControllerParameterIntegration:
    """Tests for Animator Controller parameter integration with Logic Graph."""

    def test_set_float_parameter(self, scene_with_controller):
        scene, player, animator, controller, game, sr = scene_with_controller

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

        runtime = RuntimeMock()

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
                'parameter_name': 'speed',
                'value': '2.5',
            }
        }

        result = execute_animator_parameter(runtime, node, game, 0.016)

        assert result == ["success"]
        assert controller.get_parameter("speed") == 2.5

    def test_set_bool_parameter(self, scene_with_controller):
        scene, player, animator, controller, game, sr = scene_with_controller

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

        runtime = RuntimeMock()

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
                'parameter_name': 'can_jump',
                'value': 'true',
            }
        }

        result = execute_animator_parameter(runtime, node, game, 0.016)

        assert result == ["success"]
        assert controller.get_parameter("can_jump") is True

    def test_parameter_triggers_transition(self, scene_with_controller):
        scene, player, animator, controller, game, sr = scene_with_controller

        # Start in idle
        assert controller.get_current_state() == "idle"

        # Set speed to trigger transition
        controller.set_parameter("speed", 1.0)

        # Evaluate transitions
        controller.update(0.016)

        # Should now be in run state
        assert controller.get_current_state() == "run"
        assert animator.current_clip == "run"

    def test_set_trigger(self, scene_with_controller):
        scene, player, animator, controller, game, sr = scene_with_controller

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

        runtime = RuntimeMock()

        # Start in run state
        controller.set_parameter("speed", 1.0)
        controller.update(0.016)

        assert controller.get_current_state() == "run"

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
                'trigger_name': 'attack_trigger',
            }
        }

        result = execute_animator_set_trigger(runtime, node, game, 0.016)

        assert result == ["success"]
        assert controller.get_parameter("attack_trigger") is True

    def test_trigger_fires_transition(self, scene_with_controller):
        scene, player, animator, controller, game, sr = scene_with_controller

        # Go to run state
        controller.set_parameter("speed", 1.0)
        controller.update(0.016)

        # Set attack trigger
        controller.set_parameter("attack_trigger", True)

        # Evaluate transitions
        controller.update(0.016)

        # Should now be in attack state
        assert controller.get_current_state() == "attack"
        assert animator.current_clip == "attack"

    def test_get_parameter_pure(self, scene_with_controller):
        scene, player, animator, controller, game, sr = scene_with_controller

        # Set a parameter
        controller.set_parameter("speed", 3.5)

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
                'parameter_name': 'speed',
            }
        }

        result = evaluate_animator_get_parameter(None, "node_1", "value", node, game, 0.016, set())

        assert result == 3.5

    def test_get_animator_state_pure(self, scene_with_controller):
        scene, player, animator, controller, game, sr = scene_with_controller

        # Set parameter to go to run state
        controller.set_parameter("speed", 1.0)
        controller.update(0.016)

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        result = evaluate_get_animator_state(None, "node_1", "value", node, game, 0.016, set())

        assert result == "run"

    def test_missing_controller_failure(self, scene_with_controller):
        scene, player, animator, controller, game, sr = scene_with_controller

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

        runtime = RuntimeMock()

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'NonExistent',
                'parameter_name': 'speed',
                'value': '1.0',
            }
        }

        result = execute_animator_parameter(runtime, node, game, 0.016)

        assert result == ["failure"]

    def test_multiple_controllers_independent(self):
        """Test that Player and Enemy controllers don't interfere."""
        scene = Scene("TestScene")

        # Player
        player = GameObject("Player")
        scene.add_game_object(player)
        player_sr = player.add_component(SpriteRenderer())
        player_anim = player.add_component(Animator())
        player_ctrl = player.add_component(AnimationController(default_state="idle"))

        # Enemy
        enemy = GameObject("Enemy")
        scene.add_game_object(enemy)
        enemy_sr = enemy.add_component(SpriteRenderer())
        enemy_anim = enemy.add_component(Animator())
        enemy_ctrl = enemy.add_component(AnimationController(default_state="idle"))

        # Setup animations for both
        for go, ctrl in [(player, player_ctrl), (enemy, enemy_ctrl)]:
            frames = [pygame.Surface((16, 16)) for _ in range(2)]
            anim = go.get_component(Animator)
            anim.add_clip(AnimationClip("idle", frames, fps=10, loop=True))
            frames_run = [pygame.Surface((16, 16)) for _ in range(2)]
            anim.add_clip(AnimationClip("run", frames_run, fps=10, loop=True))

            ctrl.add_state("idle", "idle")
            ctrl.add_state("run", "run")
            ctrl.add_transition("idle", "run", lambda p: p.get("speed", 0) > 0.5)

            go.scene = scene
            ctrl.start()

        class GameMock:
            def find_object(self, name: str):
                return scene.find(name)

        game = GameMock()

        # Set different speeds
        player_ctrl.set_parameter("speed", 1.0)
        enemy_ctrl.set_parameter("speed", 0.0)

        player_ctrl.update(0.016)
        enemy_ctrl.update(0.016)

        # Verify independent states
        assert player_ctrl.get_current_state() == "run"
        assert enemy_ctrl.get_current_state() == "idle"

    def test_play_stop_play_resets_controller(self, scene_with_controller):
        """Test that Play/Stop/Play cycle properly resets controller."""
        scene, player, animator, controller, game, sr = scene_with_controller

        # Play 1: Set parameter and transition
        controller.set_parameter("speed", 1.0)
        controller.update(0.016)
        assert controller.get_current_state() == "run"

        # Stop: Reset everything
        controller._current_state = "idle"
        controller.set_parameter("speed", 0.0)
        controller.set_parameter("attack_trigger", False)

        # Play 2: Verify clean state
        assert controller.get_current_state() == "idle"
        assert controller.get_parameter("speed") == 0.0
        assert controller.get_parameter("attack_trigger") is False

    def test_animator_clip_matches_controller_state(self, scene_with_controller):
        """Test that animator clip always matches controller state."""
        scene, player, animator, controller, game, sr = scene_with_controller

        # Verify invariant at each state
        controller.set_parameter("speed", 1.0)
        controller.update(0.016)
        assert controller.get_current_state() == "run"
        assert animator.current_clip == "run"

        controller.set_parameter("speed", 0.0)
        controller.update(0.016)
        assert controller.get_current_state() == "idle"
        assert animator.current_clip == "idle"
