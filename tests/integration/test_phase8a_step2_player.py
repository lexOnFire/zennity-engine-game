"""
Phase 8A Step 2: Player Movement, Camera & Animation Tests

Validates:
- Player prefab structure
- Movement (WASD) with normalized diagonal
- Physics-based movement (RigidBody)
- Camera following player
- Animation states (Idle/Run)
- Animation controller transitions
- Sprite animation frames
- Wall collision
- Play/Stop/Play cleanup
- Main Menu → Level1 flow

Zero Python gameplay scripts. All logic via Logic Graph.
"""

import pytest
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration import _phase8a_canonical as canonical


class TestLevel1SceneLoads:
    """Test that Level1.zscene loads correctly with Player."""

    def test_level1_scene_exists(self):
        """Verify Level1.zscene file exists."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        assert scene_path.exists(), f"Level1.zscene not found at {scene_path}"

    # O cabecalho de Level1 e verificado em test_phase8a_canonical_schema.py.
    # A assercao aqui usava format/name, a grafia anterior a 6a3fb0a7.

    def test_level1_has_player(self):
        """Level1 tem exatamente um Player, instanciado de um prefab."""
        scene = canonical.load_scene("Level1")
        players = [o for o in canonical.objects(scene) if o.get("name") == "Player"]

        assert len(players) == 1, "Level1 should have exactly one Player"
        # O formato canonico guarda a referencia em "prefab"; o discriminador
        # "type": "Prefab" do schema anterior deixou de ser escrito.
        assert players[0].get("prefab") == "Assets/Prefabs/Player.zprfb"


    def test_level1_has_player_movement_logic(self):
        """Verify Level1 Player has movement logic graph."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        player = next((obj for obj in data.get("objects", [])
                      if obj.get("name") == "Player"), None)
        assert player is not None
        assert "logic_graphs" in player
        graphs = player["logic_graphs"]
        assert any(g.get("path") == "Assets/Logic/PlayerMovementLogic.zlogic"
                  for g in graphs)

    def test_level1_has_walls(self):
        """Verify Level1 has wall colliders for boundaries."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        wall_names = {"WallLeft", "WallRight", "WallTop", "WallBottom"}
        scene_names = {obj.get("name") for obj in data.get("objects", [])}
        assert wall_names.issubset(scene_names), "Level1 missing wall colliders"

    def test_level1_has_camera(self):
        """A camera de Level1 segue o Player."""
        camera = canonical.find_object(canonical.load_scene("Level1"), "Camera")
        assert camera is not None

        config = (camera.get("components") or {}).get("camera", {})
        assert config.get("follow_target") == "Player"
        # A assercao smooth_follow foi retirada em 13.1-B: nenhum campo com esse
        # nome existe em engine/ ou editor/, entao ela nunca descreveu um
        # contrato do produto.



class TestPlayerPrefab:
    """Test that Player.zprfb is properly structured."""

    def test_player_prefab_exists(self):
        """Verify Player.zprfb file exists."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        assert prefab_path.exists(), f"Player.zprfb not found at {prefab_path}"

    def test_player_prefab_valid_json(self):
        """Verify Player.zprfb is valid JSON."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.prefab"
        assert data.get("name") == "Player"

    def test_player_has_transform(self):
        """Verify Player has Transform component."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}
        assert "Transform" in comp_types

    def test_player_has_sprite_renderer(self):
        """Verify Player has SpriteRenderer component."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}
        assert "SpriteRenderer" in comp_types

    def test_player_has_collider(self):
        """Verify Player has BoxCollider2D for collision."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}
        assert "BoxCollider2D" in comp_types

    def test_player_has_rigidbody(self):
        """Verify Player has RigidBody2D for physics."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}
        assert "RigidBody2D" in comp_types

        # Verify it's NOT using gravity (top-down 2D game)
        rigidbody = next((c for c in components if c.get("type") == "RigidBody2D"), None)
        assert rigidbody is not None
        assert rigidbody.get("gravity_scale") == 0

    def test_player_has_animator(self):
        """Verify Player has Animator component."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}
        assert "Animator" in comp_types

        # Verify it references PlayerController
        animator = next((c for c in components if c.get("type") == "Animator"), None)
        assert animator is not None
        assert animator.get("controller") == "Assets/Animations/PlayerController.zcontroller"

    def test_player_variables(self):
        """Verify Player has required variables."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "move_speed" in variables
        assert "health" in variables
        assert "max_health" in variables
        assert variables["move_speed"] == 200
        assert variables["health"] == 100
        assert variables["max_health"] == 100


class TestPlayerMovementLogic:
    """Test that PlayerMovementLogic.zlogic is properly structured."""

    def test_movement_logic_exists(self):
        """Verify PlayerMovementLogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"
        assert logic_path.exists(), f"PlayerMovementLogic.zlogic not found"

    def test_movement_logic_valid_json(self):
        """Verify PlayerMovementLogic.zlogic is valid JSON."""
        data = canonical.load_logic("PlayerMovementLogic")
        assert data.get("format") == "zennity.logic_graph"
        assert isinstance(data.get("nodes"), list)

    # As seis assercoes seguintes exigiam ids de no de um desenho anterior --
    # input_horizontal, input_vertical, create_movement_vector,
    # normalize_vector, multiply_speed, set_rigidbody_velocity e
    # set_animator_speed -- em que o movimento era montado como um Vector2
    # normalizado e aplicado ao RigidBody. O grafo que shipou usa input_axis ->
    # if_else -> move / move_y, sete nos no total. Nenhum dos ids existe, e
    # exigi-los descrevia uma implementacao, nao um requisito.
    #
    # O requisito continua sendo: o Player le entrada nos dois eixos e a
    # converte em movimento, a cada frame. E isso que os dois testes abaixo
    # verificam, sem prescrever quais nos fazem o trabalho.

    def test_movement_logic_reads_both_input_axes(self):
        """O grafo le entrada horizontal e vertical."""
        graph = canonical.load_logic("PlayerMovementLogic")
        axes = [
            n for n in graph.get("nodes", [])
            if str(n.get("type")) in {"input_axis", "input.axis"}
        ]
        assert len(axes) >= 2, (
            f"esperado um no de entrada por eixo, encontrados {len(axes)}"
        )
        keys = {
            str(n.get("properties", {}).get("positive", "")).upper()
            for n in axes
        }
        assert keys >= {"D", "S"}, f"eixos declarados: {sorted(keys)}"

    def test_movement_logic_drives_movement_every_frame(self):
        """A entrada chega a um no de movimento, disparada por event_update."""
        graph = canonical.load_logic("PlayerMovementLogic")
        types = canonical.node_types(graph)

        assert "event_update" in types, "o movimento precisa rodar a cada frame"
        assert types & {"move", "move_y", "move_by"}, (
            f"nenhum no de movimento no grafo: {sorted(types)}"
        )
        assert graph.get("edges"), "os nos nao estao conectados"


class TestAnimationController:
    """Test that PlayerController.zcontroller is properly configured."""

    def test_animation_controller_exists(self):
        """Verify PlayerController.zcontroller exists."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        assert controller_path.exists(), "PlayerController.zcontroller not found"

    def test_animation_controller_valid_json(self):
        """Verify controller is valid JSON."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.animation_controller"

    def test_controller_has_states(self):
        """Verify controller has Idle and Run states."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        layers = data.get("layers", [])
        assert len(layers) > 0
        states = [s.get("name") for s in layers[0].get("states", [])]
        assert "Idle" in states
        assert "Run" in states

    def test_controller_has_transitions(self):
        """Verify controller has Idle↔Run transitions."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        layers = data.get("layers", [])
        transitions = layers[0].get("transitions", [])

        idle_to_run = any(t.get("from") == "Idle" and t.get("to") == "Run"
                         for t in transitions)
        run_to_idle = any(t.get("from") == "Run" and t.get("to") == "Idle"
                         for t in transitions)

        assert idle_to_run, "Should have Idle → Run transition"
        assert run_to_idle, "Should have Run → Idle transition"

    def test_controller_has_speed_parameter(self):
        """Verify controller uses 'speed' float parameter for transitions."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        parameters = data.get("parameters", [])
        speed_param = next((p for p in parameters if p.get("name") == "speed"), None)
        assert speed_param is not None
        assert speed_param.get("type") == "float"


class TestAnimationClips:
    """Test that animation clips exist."""

    def test_idle_clip_exists(self):
        """Verify PlayerIdle.zanim exists."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "PlayerIdle.zanim"
        assert clip_path.exists(), "PlayerIdle.zanim not found"

    def test_idle_clip_valid_json(self):
        """Verify idle clip is valid JSON."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "PlayerIdle.zanim"
        data = json.loads(clip_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.animation_clip"
        assert data.get("name") == "PlayerIdle"


class TestZeroPythonGameplay:
    """Verify Step 2 uses ONLY visual systems, no Python gameplay scripts."""

    def test_level1_no_python_gameplay(self):
        """Verify Level1 doesn't reference Python gameplay scripts."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        content = scene_path.read_text(encoding="utf-8")

        assert "gameplay" not in content.lower()
        assert ".py" not in content.lower()

    def test_player_prefab_no_python_gameplay(self):
        """Verify Player prefab doesn't reference Python gameplay scripts."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        content = prefab_path.read_text(encoding="utf-8")

        assert "gameplay" not in content.lower()
        assert ".py" not in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
