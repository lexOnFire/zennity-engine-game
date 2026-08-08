"""Phase 6B.3: Animation Events & Owner Routing - Core Tests."""
import pytest
import pygame

from engine.core import Scene, GameObject
from engine.animation import Animator, AnimationClip
from engine.graphics.renderer import SpriteRenderer
from engine.logic.animation_event_dispatch import (
    register_animation_event_handler,
    unregister_animation_event_handler,
    dispatch_animation_event,
    dispatch_animation_finished,
)


@pytest.fixture
def scene_with_animators():
    """Create a scene with two GameObjects that have Animators."""
    scene = Scene("TestScene")

    # Player
    player = GameObject("Player")
    scene.add_game_object(player)
    sr1 = player.add_component(SpriteRenderer())
    anim1 = player.add_component(Animator(default_clip="idle"))

    frames = [pygame.Surface((16, 16)) for _ in range(3)]
    for f in frames:
        f.fill((255, 0, 0))

    frames_attack = [pygame.Surface((16, 16)) for _ in range(2)]
    for f in frames_attack:
        f.fill((255, 100, 0))

    anim1.add_clip(AnimationClip("idle", frames, fps=10, loop=True))
    anim1.add_clip(AnimationClip("attack", frames_attack, fps=10, loop=False))

    # Enemy
    enemy = GameObject("Enemy")
    scene.add_game_object(enemy)
    sr2 = enemy.add_component(SpriteRenderer())
    anim2 = enemy.add_component(Animator(default_clip="idle"))

    enemy_frames = [pygame.Surface((16, 16)) for _ in range(2)]
    for f in enemy_frames:
        f.fill((0, 255, 0))

    anim2.add_clip(AnimationClip("idle", enemy_frames, fps=8, loop=True))

    return scene, player, anim1, enemy, anim2


class TestAnimationEventDispatch:
    """Tests for animation event dispatch mechanism."""

    def test_dispatch_animation_event(self, scene_with_animators):
        """Test basic animation event dispatch."""
        scene, player, anim1, enemy, anim2 = scene_with_animators

        received_events = []

        def handler(owner, anim_name, event_name, frame_idx, elapsed):
            received_events.append({
                "owner_name": owner.name if owner else None,
                "animation_name": anim_name,
                "event_name": event_name,
                "frame_index": frame_idx,
                "elapsed_time": elapsed,
            })

        register_animation_event_handler(handler)

        # Dispatch an animation event
        dispatch_animation_event(
            owner_object=player,
            animation_name="idle",
            event_name="step",
            frame_index=1,
            elapsed_time=0.1,
        )

        assert len(received_events) == 1
        assert received_events[0]["owner_name"] == "Player"
        assert received_events[0]["animation_name"] == "idle"
        assert received_events[0]["event_name"] == "step"

        unregister_animation_event_handler(handler)

    def test_dispatch_animation_finished(self, scene_with_animators):
        """Test animation finished event dispatch."""
        scene, player, anim1, enemy, anim2 = scene_with_animators

        received_events = []

        def handler(owner, anim_name, event_name, frame_idx, elapsed):
            received_events.append({
                "owner_name": owner.name if owner else None,
                "animation_name": anim_name,
                "event_name": event_name,
            })

        register_animation_event_handler(handler)

        dispatch_animation_finished(
            owner_object=enemy,
            animation_name="attack",
            elapsed_time=0.2,
        )

        assert len(received_events) == 1
        assert received_events[0]["owner_name"] == "Enemy"
        assert received_events[0]["event_name"] == "finished"

        unregister_animation_event_handler(handler)

    def test_multiple_handlers(self, scene_with_animators):
        """Test multiple registered handlers receive events."""
        scene, player, anim1, enemy, anim2 = scene_with_animators

        calls_handler1 = []
        calls_handler2 = []

        def handler1(owner, anim_name, event_name, frame_idx, elapsed):
            calls_handler1.append(event_name)

        def handler2(owner, anim_name, event_name, frame_idx, elapsed):
            calls_handler2.append(event_name)

        register_animation_event_handler(handler1)
        register_animation_event_handler(handler2)

        dispatch_animation_event(player, "idle", "step", 0, 0.0)

        assert len(calls_handler1) == 1
        assert len(calls_handler2) == 1

        unregister_animation_event_handler(handler1)
        unregister_animation_event_handler(handler2)

    def test_handler_exception_isolation(self, scene_with_animators):
        """Test that handler exception doesn't prevent other handlers."""
        scene, player, anim1, enemy, anim2 = scene_with_animators

        calls = []

        def failing_handler(owner, anim_name, event_name, frame_idx, elapsed):
            raise RuntimeError("Handler failed")

        def good_handler(owner, anim_name, event_name, frame_idx, elapsed):
            calls.append(event_name)

        register_animation_event_handler(failing_handler)
        register_animation_event_handler(good_handler)

        # Should not raise, but good_handler should still be called
        dispatch_animation_event(player, "idle", "step", 0, 0.0)

        assert len(calls) == 1

        unregister_animation_event_handler(failing_handler)
        unregister_animation_event_handler(good_handler)

    def test_unregister_handler(self, scene_with_animators):
        """Test unregistering a handler."""
        scene, player, anim1, enemy, anim2 = scene_with_animators

        calls = []

        def handler(owner, anim_name, event_name, frame_idx, elapsed):
            calls.append(event_name)

        register_animation_event_handler(handler)
        dispatch_animation_event(player, "idle", "step", 0, 0.0)
        assert len(calls) == 1

        unregister_animation_event_handler(handler)
        dispatch_animation_event(player, "idle", "step", 0, 0.0)
        assert len(calls) == 1  # Not called after unregister


class TestAnimatorEventEmission:
    """Tests for Animator emitting events via animation_event_dispatch."""

    def test_animator_fires_event_via_dispatch(self, scene_with_animators):
        """Test that Animator fires events through animation_event_dispatch."""
        scene, player, anim1, enemy, anim2 = scene_with_animators

        received_events = []

        def handler(owner, anim_name, event_name, frame_idx, elapsed):
            received_events.append((anim_name, event_name))

        register_animation_event_handler(handler)

        # Create a clip with an event
        frames = [pygame.Surface((16, 16)) for _ in range(3)]
        clip = AnimationClip("test", frames, fps=10)

        # Add event to clip
        def test_callback():
            pass

        test_callback.__name__ = "hit"
        from engine.animation.clip import AnimationEvent
        clip._events.append(AnimationEvent(frame_index=1, callback=test_callback))

        anim1.add_clip(clip)
        anim1.play("test")

        # Advance to frame 1 to trigger event
        anim1._advance(0.15)

        # Check if event was dispatched
        assert any(e[0] == "test" and "hit" in e[1] for e in received_events), \
            f"Expected event with 'hit' in name, got {received_events}"

        unregister_animation_event_handler(handler)

    def test_animator_finished_event(self, scene_with_animators):
        """Test that Animator dispatches finished event for non-loop clips."""
        scene, player, anim1, enemy, anim2 = scene_with_animators

        received_events = []

        def handler(owner, anim_name, event_name, frame_idx, elapsed):
            if event_name == "finished":
                received_events.append(anim_name)

        register_animation_event_handler(handler)

        anim1.play("attack")  # Non-loop clip

        # Advance until finished
        for _ in range(10):
            anim1._advance(0.2)

        assert "attack" in received_events, \
            f"Expected 'attack' finished event, got {received_events}"

        unregister_animation_event_handler(handler)


class TestOwnerRouting:
    """Tests for owner-based event routing."""

    def test_player_receives_player_event_only(self, scene_with_animators):
        """Test that Player events go to Player, not Enemy."""
        scene, player, anim1, enemy, anim2 = scene_with_animators

        player_events = []
        enemy_events = []

        def player_handler(owner, anim_name, event_name, frame_idx, elapsed):
            if getattr(owner, "name", None) == "Player":
                player_events.append(event_name)

        def enemy_handler(owner, anim_name, event_name, frame_idx, elapsed):
            if getattr(owner, "name", None) == "Enemy":
                enemy_events.append(event_name)

        register_animation_event_handler(player_handler)
        register_animation_event_handler(enemy_handler)

        # Dispatch only to Player
        dispatch_animation_event(player, "idle", "step", 0, 0.0)

        assert len(player_events) == 1
        assert len(enemy_events) == 0

        unregister_animation_event_handler(player_handler)
        unregister_animation_event_handler(enemy_handler)

    def test_both_animators_emit_independently(self, scene_with_animators):
        """Test that Player and Enemy animations emit independently."""
        scene, player, anim1, enemy, anim2 = scene_with_animators

        all_events = []

        def handler(owner, anim_name, event_name, frame_idx, elapsed):
            all_events.append((owner.name if owner else None, anim_name, event_name))

        register_animation_event_handler(handler)

        # Emit from Player
        dispatch_animation_event(player, "idle", "step1", 0, 0.0)

        # Emit from Enemy
        dispatch_animation_event(enemy, "idle", "step2", 0, 0.0)

        assert ("Player", "idle", "step1") in all_events
        assert ("Enemy", "idle", "step2") in all_events

        unregister_animation_event_handler(handler)
