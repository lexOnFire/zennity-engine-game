# Script reload

During Play Mode, Zennity watches every active `ScriptComponent` source using
its modification timestamp and size. When a source changes, the runtime:

1. reads and compiles the current source bytes without using stale `.pyc` data;
2. resolves and constructs the replacement `ScriptBehaviour`;
3. copies public instance state to the replacement;
4. binds the same runtime GameObject, scene and runtime services;
5. invokes `on_reload(previous_state)`;
6. swaps the behaviour only after every previous step succeeds.

The scheduler entry and runtime GameObject are not recreated. Transform,
components and scene state therefore remain intact.

## Failure recovery

Syntax errors, failed imports, invalid behaviour classes and migration errors
leave the previous behaviour active. The component is not disabled. A given
broken source revision is reported once, and the runtime retries only after the
file changes again. Deleted scripts behave the same way and reload when
restored.

Errors remain available in `ScriptRuntime.errors` with the `reload` phase.

## Optional migration hooks

```python
from engine.runtime import ScriptBehaviour


class PlayerScript(ScriptBehaviour):
    def on_before_reload(self):
        return {"checkpoint": self.current_checkpoint}

    def on_reload(self, previous_state):
        self.current_checkpoint = previous_state.get("checkpoint", 0)
```

Public attributes are already preserved automatically. `on_before_reload`
may return extra state as a dictionary, and `on_reload` may normalize migrated
values for a new script version. Neither `on_awake` nor `on_start` runs again.
