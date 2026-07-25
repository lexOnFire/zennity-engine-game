"""Declarative Node definitions for Logic Plugin (Visual Scripting Core Completion).

Extensa biblioteca de nós com suporte a categorias completas e busca por sinonímia (PT-BR e EN):
  - Eventos (Start, Update, FixedUpdate, Collision, KeyPress, MouseClick)
  - Fluxo (Branch, Sequence, ForLoop, WhileLoop, Switch, Delay, Timer, Gate, DoOnce, FlipFlop)
  - Variáveis (GetVariable, SetVariable, LocalVariable, GlobalVariable)
  - Matemática (Add, Subtract, Multiply, Divide, Clamp, Lerp, Distance, Normalize)
  - Vetores (Vector2, Vector3, AddVector, RotateVector, Magnitude, Direction)
  - Transform (GetPosition, SetPosition, Translate, Rotate, Scale, LookAt)
  - Física (AddForce, SetVelocity, GetVelocity, Raycast, Overlap, RigidBody)
  - Objetos (Instantiate, Destroy, FindObject, GetComponent, AddComponent)
  - Áudio (PlayAudio, StopAudio, PauseAudio, SetVolume)
  - UI (SetUIText, SetUIImage, OnButtonClick, SetProgressBar)
  - IA (MoveTo, FollowTarget, Patrol, Chase, Attack)
  - Animação (PlayAnimation, StopAnimation, BlendAnimation, SetTransition)
  - Cena (LoadScene, UnloadScene, SpawnObject)
"""
from engine.graphs.registry import register_node
from engine.core.metadata.pin import PinDefinition, PinType

# ── 1. EVENTOS ─────────────────────────────────────────────────────────────
@register_node(
    id="logic.events.start",
    name="On Start",
    category="Events",
    description="Triggered when the object enters the scene or game starts.",
    tags=["start", "inicio", "começo", "onstart", "init"],
    color="#e74c3c",
    outputs=[PinDefinition("exec", PinType.EXEC, hide_label=True)]
)
class LogicStartEventNode: pass

@register_node(
    id="logic.events.update",
    name="On Update",
    category="Events",
    description="Triggered every frame.",
    tags=["update", "frame", "loop", "tick", "onupdate", "atualizar"],
    color="#e74c3c",
    outputs=[
        PinDefinition("exec", PinType.EXEC, hide_label=True),
        PinDefinition("dt", PinType.FLOAT, "Delta Time")
    ]
)
class LogicUpdateEventNode: pass

@register_node(
    id="logic.events.fixed_update",
    name="On Fixed Update",
    category="Events",
    description="Triggered on fixed physics step.",
    tags=["fixedupdate", "physics", "fisica", "tick"],
    color="#e74c3c",
    outputs=[PinDefinition("exec", PinType.EXEC, hide_label=True)]
)
class LogicFixedUpdateEventNode: pass

@register_node(
    id="logic.events.collision_enter",
    name="On Collision Enter",
    category="Events",
    description="Triggered when a collision starts.",
    tags=["collision", "colisao", "hit", "impacto", "touch"],
    color="#e74c3c",
    outputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("other", PinType.OBJECT, "Other Object")
    ]
)
class LogicCollisionEnterNode: pass

@register_node(
    id="logic.events.key_press",
    name="On Key Press",
    category="Events",
    description="Triggered when a key is pressed.",
    tags=["key", "tecla", "input", "keyboard", "teclado", "button"],
    color="#e74c3c",
    inputs=[PinDefinition("key_name", PinType.STRING, default_value="Space")],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicKeyPressNode: pass


# ── 2. FLUXO ───────────────────────────────────────────────────────────────
@register_node(
    id="logic.flow.branch",
    name="Branch / If-Else",
    category="Flow",
    description="Branches execution flow based on condition.",
    tags=["if", "else", "branch", "se", "condicao", "condition"],
    color="#f39c12",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("condition", PinType.BOOL, default_value=True)
    ],
    outputs=[
        PinDefinition("true", PinType.EXEC, "True"),
        PinDefinition("false", PinType.EXEC, "False")
    ]
)
class LogicBranchNode: pass

@register_node(
    id="logic.flow.sequence",
    name="Sequence",
    category="Flow",
    description="Executes outputs in sequential order.",
    tags=["sequence", "sequencia", "ordem", "then"],
    color="#f39c12",
    inputs=[PinDefinition("exec", PinType.EXEC)],
    outputs=[
        PinDefinition("then_0", PinType.EXEC, "Then 0"),
        PinDefinition("then_1", PinType.EXEC, "Then 1"),
        PinDefinition("then_2", PinType.EXEC, "Then 2")
    ]
)
class LogicSequenceNode: pass

@register_node(
    id="logic.flow.for_loop",
    name="For Loop",
    category="Flow",
    description="Loops through a range of integer values.",
    tags=["for", "loop", "repeat", "repetir", "para"],
    color="#f39c12",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("start", PinType.INT, default_value=0),
        PinDefinition("end", PinType.INT, default_value=10)
    ],
    outputs=[
        PinDefinition("loop_body", PinType.EXEC, "Loop Body"),
        PinDefinition("index", PinType.INT, "Index"),
        PinDefinition("completed", PinType.EXEC, "Completed")
    ]
)
class LogicForLoopNode: pass

@register_node(
    id="logic.flow.delay",
    name="Delay / Wait",
    category="Flow",
    description="Delays execution for specified duration in seconds.",
    tags=["delay", "wait", "esperar", "tempo", "timer", "cooldown"],
    color="#f39c12",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("duration", PinType.FLOAT, default_value=1.0)
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicDelayNode: pass


# ── 3. VARIÁVEIS ───────────────────────────────────────────────────────────
@register_node(
    id="logic.variables.get",
    name="Get Variable",
    category="Variables",
    description="Reads a variable value by name.",
    tags=["get", "variable", "variavel", "obter", "read", "ler"],
    color="#1abc9c",
    inputs=[PinDefinition("var_name", PinType.STRING, default_value="speed")],
    outputs=[PinDefinition("value", PinType.OBJECT)]
)
class LogicGetVariableNode: pass

@register_node(
    id="logic.variables.set",
    name="Set Variable",
    category="Variables",
    description="Writes a variable value by name.",
    tags=["set", "variable", "variavel", "definir", "write", "salvar"],
    color="#1abc9c",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("var_name", PinType.STRING, default_value="speed"),
        PinDefinition("value", PinType.OBJECT)
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicSetVariableNode: pass


# ── 4. MOVIMENTO & TRANSFORM ───────────────────────────────────────────────
@register_node(
    id="logic.movement.move",
    name="Move Object",
    category="Movement",
    description="Moves the object in the given direction.",
    tags=["move", "mover", "andar", "caminhar", "translate", "velocity", "movimento", "posicao"],
    color="#3498db",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("direction", PinType.VECTOR2),
        PinDefinition("speed", PinType.FLOAT, default_value=5.0)
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicMoveNode: pass

@register_node(
    id="logic.transform.set_position",
    name="Set Position",
    category="Transform",
    description="Sets object position in world space.",
    tags=["position", "posicao", "teleport", "setposition", "mover", "transform"],
    color="#3498db",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("position", PinType.VECTOR2)
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicSetPositionNode: pass

@register_node(
    id="logic.transform.rotate",
    name="Rotate Object",
    category="Transform",
    description="Rotates object by angle degrees.",
    tags=["rotate", "rotacionar", "giar", "angulo", "rotation"],
    color="#3498db",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("angle", PinType.FLOAT, default_value=90.0)
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicRotateNode: pass


# ── 5. FÍSICA ──────────────────────────────────────────────────────────────
@register_node(
    id="logic.physics.add_force",
    name="Add Force / Impulse",
    category="Physics",
    description="Applies impulse or force to RigidBody.",
    tags=["force", "forca", "pulo", "jump", "impulse", "impulso", "rigidbody", "physics", "fisica"],
    color="#9b59b6",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("force", PinType.VECTOR2)
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicAddForceNode: pass

@register_node(
    id="logic.physics.raycast",
    name="Raycast 2D",
    category="Physics",
    description="Casts a ray to detect colliders.",
    tags=["raycast", "raio", "detect", "colisao", "hit", "groundcheck"],
    color="#9b59b6",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("origin", PinType.VECTOR2),
        PinDefinition("direction", PinType.VECTOR2),
        PinDefinition("distance", PinType.FLOAT, default_value=10.0)
    ],
    outputs=[
        PinDefinition("hit", PinType.BOOL, "Did Hit"),
        PinDefinition("hit_object", PinType.OBJECT, "Hit Object")
    ]
)
class LogicRaycastNode: pass


# ── 6. MATEMÁTICA ──────────────────────────────────────────────────────────
@register_node(
    id="logic.math.add",
    name="Add (+)",
    category="Math",
    description="Adds two numbers.",
    tags=["add", "soma", "somar", "+", "math", "adicao"],
    color="#27ae60",
    inputs=[
        PinDefinition("a", PinType.FLOAT, default_value=0.0),
        PinDefinition("b", PinType.FLOAT, default_value=0.0)
    ],
    outputs=[PinDefinition("result", PinType.FLOAT)]
)
class LogicMathAddNode: pass

@register_node(
    id="logic.math.clamp",
    name="Clamp Value",
    category="Math",
    description="Clamps value between min and max.",
    tags=["clamp", "limite", "min", "max", "math", "restringir"],
    color="#27ae60",
    inputs=[
        PinDefinition("value", PinType.FLOAT, default_value=0.0),
        PinDefinition("min", PinType.FLOAT, default_value=0.0),
        PinDefinition("max", PinType.FLOAT, default_value=100.0)
    ],
    outputs=[PinDefinition("result", PinType.FLOAT)]
)
class LogicMathClampNode: pass


# ── 7. IA & NAVEGAÇÃO ──────────────────────────────────────────────────────
@register_node(
    id="logic.ai.move_to",
    name="AI Move To Target",
    category="AI",
    description="Moves AI character to target destination.",
    tags=["ai", "ia", "moveto", "chase", "perseguir", "patrol", "patrulha", "target", "pathfinding"],
    color="#8e44ad",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("target_position", PinType.VECTOR2),
        PinDefinition("speed", PinType.FLOAT, default_value=3.5)
    ],
    outputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("reached", PinType.EXEC, "On Reached Target")
    ]
)
class LogicAIMoveToNode: pass


# ── 8. ANIMAÇÃO ────────────────────────────────────────────────────────────
@register_node(
    id="logic.animation.play",
    name="Play Animation",
    category="Animation",
    description="Plays an animation clip by name.",
    tags=["animation", "animacao", "play", "tocar", "anim", "clip", "sprite"],
    color="#2ecc71",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("clip_name", PinType.STRING, default_value="Run")
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicPlayAnimationNode: pass


# ── 9. ÁUDIO ───────────────────────────────────────────────────────────────
@register_node(
    id="logic.audio.play",
    name="Play Sound Effect",
    category="Audio",
    description="Plays sound asset by name.",
    tags=["audio", "sound", "som", "musica", "sfx", "play", "tocar"],
    color="#e67e22",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("sound_name", PinType.STRING, default_value="jump.wav")
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicPlayAudioNode: pass


# ── 10. OBJETOS & CENA ─────────────────────────────────────────────────────
@register_node(
    id="logic.objects.instantiate",
    name="Instantiate Prefab / Spawn",
    category="Objects",
    description="Creates a new object instance in scene.",
    tags=["instantiate", "spawn", "criar", "gerar", "prefab", "object", "clone"],
    color="#16a085",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("prefab_name", PinType.STRING, default_value="Bullet"),
        PinDefinition("position", PinType.VECTOR2)
    ],
    outputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("spawned_object", PinType.OBJECT)
    ]
)
class LogicInstantiateNode: pass

@register_node(
    id="logic.objects.destroy",
    name="Destroy Object",
    category="Objects",
    description="Destroys target object.",
    tags=["destroy", "destruir", "remover", "kill", "delete", "eliminar"],
    color="#16a085",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("target_object", PinType.OBJECT)
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicDestroyNode: pass


# ── 11. UI & HUD ───────────────────────────────────────────────────────────
@register_node(
    id="logic.ui.set_text",
    name="Set UI Text",
    category="UI",
    description="Sets text of a UI Label element.",
    tags=["ui", "text", "texto", "hud", "label", "pontos", "score"],
    color="#d35400",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("element_id", PinType.STRING, default_value="ScoreText"),
        PinDefinition("text_value", PinType.STRING, default_value="100")
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicSetUITextNode: pass
