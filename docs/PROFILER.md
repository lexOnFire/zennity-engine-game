# Runtime Profiler

Zennity uses one bounded profiler model for the engine runtime, isolated editor
viewport and exported development builds.

## Metrics

Each sample records:

- frame time and calculated FPS;
- CPU time spent processing the frame;
- rolling average, P95 and maximum frame time;
- process memory when `psutil` is available;
- active object and physics-body counts;
- CPU time by subsystem.

The engine runtime exposes `scripts`, `physics`, `late_update`, `scene` and
`render`. The isolated viewport exposes `commands`, `events`, `simulation`,
`physics`, `render` and `frame_limit`.

## Memory bound

`RuntimeProfiler` retains at most 240 frames by default using a bounded deque.
Process memory is sampled every 30 frames instead of every frame. Calling
`reset()` releases all retained samples without affecting Play Mode.

## Runtime API

```python
summary = runtime_scene.profiler.summary(window=120)
print(summary.fps)
print(summary.p95_frame_ms)
print(summary.subsystems_ms)
```

Custom systems can be measured without coupling to the editor:

```python
with runtime_scene.profiler.measure("pathfinding"):
    update_pathfinding()
```

Profiling can be disabled by setting `runtime_scene.profiler.enabled = False`.
The disabled path does not read the clock, memory or append samples.

## Editor

The Profiler panel displays real samples from the active runtime. The isolated
viewport sends its rolling summary through the existing statistics event,
including memory, physics and subsystem timings. If no profiler is connected,
the dock keeps placeholder values instead of estimating an artificial FPS.

The standalone profiler module is included in development exports so the same
metrics remain available outside the editor.
