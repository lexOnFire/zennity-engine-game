from editor.runtime.viewport_systems import AudioPlaybackSystem, AnimationPlaybackSystem, FixedStepScheduler, HudRuntimeSystem


def test_fixed_step_scheduler_caps_late_frames_and_resets() -> None:
    scheduler = FixedStepScheduler(0.1, maximum_steps=3)
    assert scheduler.consume(1.0) == 3
    assert scheduler.consume(0.05) == 0
    scheduler.reset()
    assert scheduler.accumulator == 0.0


def test_animation_playback_reports_crossed_frames_deterministically() -> None:
    result = AnimationPlaybackSystem.advance(0.0, -1, 0.35, 4, 10.0, True)
    assert result.raw_frame == 3
    assert result.frame == 3
    assert result.crossed_frames == (0, 1, 2, 3)


def test_hud_runtime_groups_entries_and_removes_them() -> None:
    hud = HudRuntimeSystem()
    hud.set_entry({"key": "score", "text": "10", "position": "top-right"})
    hud.set_entry({"key": "life", "text": "3", "position": "top-right"})
    assert len(hud.grouped()["top-right"]) == 2
    hud.remove_entry("score")
    assert set(hud) == {"life"}



class _FakeChannel:
    def __init__(self) -> None:
        self.stopped = 0

    def stop(self) -> None:
        self.stopped += 1


class _FakeMusic:
    def stop(self) -> None:
        return None


class _FakeMixer:
    def __init__(self) -> None:
        self.initialized = True
        self.music = _FakeMusic()
        self.stopped = 0
        self.quit_calls = 0

    def get_init(self):
        return self.initialized

    def stop(self) -> None:
        self.stopped += 1

    def quit(self) -> None:
        self.quit_calls += 1
        self.initialized = False


class _FakePygame:
    error = RuntimeError

    def __init__(self) -> None:
        self.mixer = _FakeMixer()


def test_audio_shutdown_releases_channels_sounds_and_mixer(tmp_path) -> None:
    pygame = _FakePygame()
    system = AudioPlaybackSystem(pygame, tmp_path, lambda *_args: None)
    channel = _FakeChannel()
    system.channels["music"] = channel
    system.sounds["music"] = object()

    system.shutdown()
    system.shutdown()

    assert channel.stopped == 1
    assert system.channels == {}
    assert system.sounds == {}
    assert pygame.mixer.quit_calls == 1
