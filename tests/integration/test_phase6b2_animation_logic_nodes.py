"""Phase 6B.2: Animation Logic Graph Core Nodes - Complete Test Suite."""
import pytest
import pygame

from engine.core import Scene, GameObject
from engine.animation import Animator, AnimationClip
from engine.graphics.renderer import SpriteRenderer
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.runtime.registry import registry


@pytest.fixture
def scene_with_animator():
    """Create a scene with a player GameObject that has Animator and SpriteRenderer."""
    scene = Scene("TestScene")
    scene.physics_enabled = False

    # Create player GameObject
    player = GameObject("Player")
    scene.add_game_object(player)

    # Add SpriteRenderer
    sr = player.add_component(SpriteRenderer())
    sr.enabled = True

    # Add Animator with default clip
    animator = player.add_component(Animator(default_clip="idle"))

    # Create test animation frames (simple colored surfaces)
    frames_idle = [
        pygame.Surface((16, 16)),
        pygame.Surface((16, 16)),
        pygame.Surface((16, 16)),
    ]
    for i, f in enumerate(frames_idle):
        f.fill((255, 0 + i * 50, 0))

    frames_run = [
        pygame.Surface((16, 16)),
        pygame.Surface((16, 16)),
        pygame.Surface((16, 16)),
        pygame.Surface((16, 16)),
    ]
    for i, f in enumerate(frames_run):
        f.fill((0, 255, 0 + i * 40))

    # Add clips
    animator.add_clip(AnimationClip("idle", frames_idle, fps=10, loop=True))
    animator.add_clip(AnimationClip("run", frames_run, fps=12, loop=True))


    # Create game mock
    class GameMock:
        def __init__(self):
            self.name = "Game"
            self.physics_world = None
            self.scenes = [scene]
            self.current_scene = scene

        def find_object(self, name: str):
            return scene.find(name)

    game = GameMock()
    return scene, player, animator, game, sr


class TestPlayAnimationNode:
    """Tests for play_animation node."""

    def test_play_animation_success(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        # Manually call executor (simulating Logic Graph runtime)
        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
                'animation_name': 'run',
                'force': False,
            }
        }

        # Create a mock runtime
        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_play_animation
        result = execute_play_animation(runtime, node, game, 0.016)

        assert result == ["next"]
        assert animator.current_clip == "run"

    def test_play_animation_missing_animator_failure(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        # Try to play on non-existent object
        node = {
            'id': 'node_1',
            'properties': {
                'target': 'NonExistent',
                'animation_name': 'idle',
                'force': False,
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_play_animation
        result = execute_play_animation(runtime, node, game, 0.016)

        assert result == ["exec_failure"]

    def test_play_animation_empty_target_failure(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        node = {
            'id': 'node_1',
            'properties': {
                'target': '',
                'animation_name': 'idle',
                'force': False,
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_play_animation
        result = execute_play_animation(runtime, node, game, 0.016)

        assert result == ["exec_failure"]

    def test_play_animation_with_force(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        # Play same animation with force=True
        animator.play("run")
        current_frame_before = animator.current_frame

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
                'animation_name': 'run',
                'force': True,
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_play_animation
        result = execute_play_animation(runtime, node, game, 0.016)

        assert result == ["next"]
        assert animator.current_frame == 0  # Reset to frame 0 with force


class TestPauseAnimationNode:
    """Tests for pause_animation node."""

    def test_pause_animation_success(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        animator.play("run")
        animator._playing = True
        animator._paused = False

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_pause_animation
        result = execute_pause_animation(runtime, node, game, 0.016)

        assert result == ["exec_success"]
        assert animator._paused is True

    def test_pause_animation_missing_animator_failure(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'NonExistent',
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_pause_animation
        result = execute_pause_animation(runtime, node, game, 0.016)

        assert result == ["exec_failure"]


class TestStopAnimationNode:
    """Tests for stop_animation node."""

    def test_stop_animation_success(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        animator.play("run")
        assert animator.current_clip == "run"

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_stop_animation
        result = execute_stop_animation(runtime, node, game, 0.016)

        assert result == ["next"]
        assert animator.current_clip is None

    def test_stop_animation_missing_animator_failure(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'NonExistent',
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_stop_animation
        result = execute_stop_animation(runtime, node, game, 0.016)

        assert result == ["exec_failure"]


class TestGetCurrentAnimationNode:
    """Tests for get_current_animation pure node."""

    def test_get_current_animation_when_playing(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        animator.play("run")

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_current_animation
        result = evaluate_get_current_animation(None, "node_1", "value", node, game, 0.016, set())

        assert result == "run"

    def test_get_current_animation_when_stopped(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        animator.stop()

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_current_animation
        result = evaluate_get_current_animation(None, "node_1", "value", node, game, 0.016, set())

        assert result == ""

    def test_get_current_animation_missing_animator(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'NonExistent',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_current_animation
        result = evaluate_get_current_animation(None, "node_1", "value", node, game, 0.016, set())

        assert result == ""


class TestGetCurrentFrameNode:
    """Tests for get_current_frame pure node."""

    def test_get_current_frame_at_start(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        animator.play("run")

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_current_frame
        result = evaluate_get_current_frame(None, "node_1", "value", node, game, 0.016, set())

        assert result == 0

    def test_get_current_frame_after_advance(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        animator.play("run")
        animator._advance(0.15)  # Advance enough to change frame at 12 fps

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_current_frame
        result = evaluate_get_current_frame(None, "node_1", "value", node, game, 0.016, set())

        assert result > 0

    def test_get_current_frame_missing_animator(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'NonExistent',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_current_frame
        result = evaluate_get_current_frame(None, "node_1", "value", node, game, 0.016, set())

        assert result == 0


class TestGetAnimationTimeNode:
    """Tests for get_animation_time pure node."""

    def test_get_animation_time_at_start(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        animator.play("run")

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_animation_time
        result = evaluate_get_animation_time(None, "node_1", "value", node, game, 0.016, set())

        assert result == pytest.approx(0.0)

    def test_get_animation_time_after_advance(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        animator.play("run")
        # Note: _clip_time only advances if clip has keyframes
        # For frame-based animation without keyframes, _clip_time stays 0
        animator._advance(0.3)

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_animation_time
        result = evaluate_get_animation_time(None, "node_1", "value", node, game, 0.016, set())

        # _clip_time is 0 for frame-based animations without keyframes
        assert result == pytest.approx(0.0)


class TestGetIsPlayingNode:
    """Tests for get_is_playing pure node."""

    def test_get_is_playing_when_playing(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        animator.play("run")

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_is_playing
        result = evaluate_get_is_playing(None, "node_1", "value", node, game, 0.016, set())

        assert result is True

    def test_get_is_playing_when_paused(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        animator.play("run")
        animator.pause()

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_is_playing
        result = evaluate_get_is_playing(None, "node_1", "value", node, game, 0.016, set())

        assert result is False

    def test_get_is_playing_when_stopped(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        animator.play("run")
        animator.stop()

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_is_playing
        result = evaluate_get_is_playing(None, "node_1", "value", node, game, 0.016, set())

        assert result is False

    def test_get_is_playing_missing_animator(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'NonExistent',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_is_playing
        result = evaluate_get_is_playing(None, "node_1", "value", node, game, 0.016, set())

        assert result is False


class TestAnimatorParameterNode:
    """Tests for animator_parameter node."""

    def test_animator_parameter_float(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
                'parameter_name': 'speed',
                'parameter_type': 'float',
                'value': '2.5',
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_animator_parameter
        result = execute_animator_parameter(runtime, node, game, 0.016)

        assert result == ["exec_success"]

    def test_animator_parameter_bool(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
                'parameter_name': 'can_jump',
                'parameter_type': 'bool',
                'value': 'true',
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_animator_parameter
        result = execute_animator_parameter(runtime, node, game, 0.016)

        assert result == ["exec_success"]

    def test_animator_parameter_int(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
                'parameter_name': 'attack_count',
                'parameter_type': 'int',
                'value': '3',
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_animator_parameter
        result = execute_animator_parameter(runtime, node, game, 0.016)

        assert result == ["exec_success"]

    def test_animator_parameter_missing_animator_failure(self, scene_with_animator):
        scene, player, animator, game, sr = scene_with_animator

        node = {
            'id': 'node_1',
            'properties': {
                'target': 'NonExistent',
                'parameter_name': 'speed',
                'parameter_type': 'float',
                'value': '1.0',
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_animator_parameter
        result = execute_animator_parameter(runtime, node, game, 0.016)

        assert result == ["exec_failure"]


class TestAnimationSpriteIntegration:
    """Tests for Logic Graph animation nodes updating SpriteRenderer visually."""

    def test_play_animation_updates_sprite(self, scene_with_animator):
        """Verify play_animation updates SpriteRenderer.surface."""
        scene, player, animator, game, sr = scene_with_animator

        # Play animation
        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
                'animation_name': 'run',
                'force': False,
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_play_animation
        result = execute_play_animation(runtime, node, game, 0.016)

        assert result == ["next"]

        # Advance animation
        animator._advance(0.016)

        # Verify surface updated
        assert sr.surface is not None

    def test_pause_animation_freezes_sprite(self, scene_with_animator):
        """Verify pause_animation freezes the sprite."""
        scene, player, animator, game, sr = scene_with_animator

        animator.play("run")
        animator._advance(0.1)
        frame_before_pause = animator.current_frame
        surface_before_pause = sr.surface

        # Pause
        node = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_pause_animation
        execute_pause_animation(runtime, node, game, 0.016)

        # Advance time
        animator._advance(0.2)
        frame_after_pause = animator.current_frame

        # Frame should not have changed
        assert frame_before_pause == frame_after_pause

    def test_multiple_animators_no_crosstalk(self, scene_with_animator):
        """Verify multiple Animators on different objects don't interfere."""
        scene, player1, animator1, game, sr1 = scene_with_animator

        # Create second player
        player2 = GameObject("Enemy")
        scene.add_game_object(player2)

        sr2 = player2.add_component(SpriteRenderer())
        animator2 = player2.add_component(Animator(default_clip="idle"))

        frames = [pygame.Surface((16, 16)) for _ in range(3)]
        for f in frames:
            f.fill((100, 100, 100))

        animator2.add_clip(AnimationClip("idle", frames, fps=10, loop=True))

        # Play different animations
        node1 = {
            'id': 'node_1',
            'properties': {
                'target': 'Player',
                'animation_name': 'run',
                'force': False,
            }
        }

        node2 = {
            'id': 'node_2',
            'properties': {
                'target': 'Enemy',
                'animation_name': 'idle',
                'force': False,
            }
        }

        class RuntimeMock:
            def __init__(self):
                self.values = {}

            def _store(self, key, subkey, value):
                self.values[(key, subkey)] = value

            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        runtime = RuntimeMock()
        from engine.logic.runtime.nodes.animation_nodes import execute_play_animation

        execute_play_animation(runtime, node1, game, 0.016)
        execute_play_animation(runtime, node2, game, 0.016)

        assert animator1.current_clip == "run"
        assert animator2.current_clip == "idle"

        # Get animations through getters
        node_get1 = {
            'id': 'node_g1',
            'properties': {
                'target': 'Player',
            }
        }

        node_get2 = {
            'id': 'node_g2',
            'properties': {
                'target': 'Enemy',
            }
        }

        from engine.logic.runtime.nodes.animation_nodes import evaluate_get_current_animation

        result1 = evaluate_get_current_animation(None, "node_g1", "value", node_get1, game, 0.016, set())
        result2 = evaluate_get_current_animation(None, "node_g2", "value", node_get2, game, 0.016, set())

        assert result1 == "run"
        assert result2 == "idle"
