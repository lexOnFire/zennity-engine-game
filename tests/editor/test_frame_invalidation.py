from editor.render.frame_invalidation import FrameInvalidation


def test_invalidation_coalesces_requests_until_frame_is_consumed() -> None:
    invalidation = FrameInvalidation()

    assert invalidation.invalidate("selection") is True
    assert invalidation.invalidate("property") is False
    assert invalidation.consume() == frozenset({"selection", "property"})
    assert invalidation.invalidate("camera") is True

    stats = invalidation.snapshot()
    assert stats.requested == 3
    assert stats.coalesced == 1
    assert stats.rendered == 1


def test_idle_ticks_do_not_make_frame_dirty() -> None:
    invalidation = FrameInvalidation()

    invalidation.record_idle_tick()
    invalidation.record_idle_tick()

    assert invalidation.dirty is False
    assert invalidation.snapshot().idle_ticks == 2
