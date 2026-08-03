from pathlib import Path

from engine.graphics.material_graph import MaterialGraph, load_material_graph


DEMO = Path("Assets/Demos/PortalStation/PortalGlow.zmat")


def test_material_graph_cpu_backend_evaluates_demo_properties():
    result = MaterialGraph(load_material_graph(DEMO)).evaluate_cpu()
    assert result["backend"] == "cpu"
    assert result["base_color"] == [0.1, 0.65, 1.0, 1.0]
    assert result["emissive"] == [0.1, 0.65, 1.0, 1.0]
    assert result["metallic"] == 0.25


def test_material_graph_glsl_backend_compiles_fragment_shader():
    compiled = MaterialGraph(load_material_graph(DEMO)).compile_glsl()
    assert compiled["backend"] == "opengl"
    assert "#version 330 core" in compiled["fragment"]
    assert "fragColor" in compiled["fragment"]
    assert "vec4(0.1, 0.65, 1, 1)" in compiled["fragment"]


def test_texture_material_declares_sampler_for_opengl_and_path_for_cpu():
    graph = {
        "format": "zennity.generic_graph",
        "category": "Material",
        "nodes": [
            {"id": "tex-1", "type": "material.texture_sample", "inputs": {"texture": "Assets/a.png"}},
            {"id": "out", "type": "material.pbr_output"},
        ],
        "edges": [
            {
                "source_node": "tex-1", "source_port": "rgb",
                "target_node": "out", "target_port": "base_color",
            }
        ],
    }
    material = MaterialGraph(graph)
    assert material.evaluate_cpu()["texture"] == "Assets/a.png"
    assert material.compile_glsl()["uniforms"] == {"u_tex_1": "sampler2D"}
