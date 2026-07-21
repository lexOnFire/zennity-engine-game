from engine.runtime.runtime_world import RuntimeWorld


def test_runtime_world_pool_has_a_hard_memory_bound() -> None:
    objects = {}
    world = RuntimeWorld(objects)
    created = [
        world.create_object(name=f"Projectile_{index}", pool_key="projectile")
        for index in range(RuntimeWorld.MAX_POOLED_PER_PREFAB * 3)
    ]

    for obj in created:
        world.destroy_object(obj)

    assert world.stats()["pooled"] == RuntimeWorld.MAX_POOLED_PER_PREFAB
    world.reset_session()
    assert world.stats()["pooled"] == 0
