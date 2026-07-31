"""Compilação e fallback CPU para Material Graphs."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


def load_material_graph(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if (
        not isinstance(data, dict)
        or data.get("format") != "zennity.generic_graph"
        or str(data.get("category", "")).casefold() != "material"
    ):
        raise ValueError("Formato de Material Graph inválido.")
    return data


class MaterialGraph:
    """Uma única representação que produz parâmetros CPU e fragment shader GLSL."""

    def __init__(self, graph: Mapping[str, Any]) -> None:
        self.nodes = {
            str(node["id"]): dict(node)
            for node in graph.get("nodes", [])
            if isinstance(node, Mapping) and node.get("id")
        }
        self.links: dict[tuple[str, str], tuple[str, str]] = {}
        for edge in graph.get("edges", []):
            if isinstance(edge, Mapping):
                self.links[(str(edge.get("target_node", "")), str(edge.get("target_port", "")))] = (
                    str(edge.get("source_node", "")), str(edge.get("source_port", ""))
                )
        outputs = [node_id for node_id, node in self.nodes.items() if node.get("type") == "material.pbr_output"]
        if len(outputs) != 1:
            raise ValueError("Material Graph deve possuir exatamente um PBR Output.")
        self.output = outputs[0]

    def evaluate_cpu(self) -> dict[str, Any]:
        """Avalia propriedades portáveis usadas pelo renderer Pygame."""
        return {
            "base_color": self._cpu_input(self.output, "base_color", [1.0, 1.0, 1.0, 1.0]),
            "metallic": float(self._cpu_input(self.output, "metallic", 0.0)),
            "roughness": float(self._cpu_input(self.output, "roughness", 0.5)),
            "emissive": self._cpu_input(self.output, "emissive", [0.0, 0.0, 0.0, 1.0]),
            "alpha": float(self._cpu_input(self.output, "alpha", 1.0)),
            "texture": self._texture_path_for_output(),
            "backend": "cpu",
        }

    def compile_glsl(self, version: str = "330 core") -> dict[str, Any]:
        """Gera GLSL para o caminho OpenGL; o chamador decide se há contexto disponível."""
        uniforms: dict[str, str] = {}
        base = self._glsl_input(self.output, "base_color", "vec4(1.0)", uniforms)
        emissive = self._glsl_input(self.output, "emissive", "vec4(0.0, 0.0, 0.0, 1.0)", uniforms)
        alpha = self._glsl_input(self.output, "alpha", "1.0", uniforms)
        declarations = "\n".join(
            f"uniform {kind} {name};" for name, kind in sorted(uniforms.items())
        )
        source = (
            f"#version {version}\n"
            "in vec2 v_uv;\nout vec4 fragColor;\n"
            f"{declarations}\n"
            "void main() {\n"
            f"    vec4 base = {base};\n"
            f"    vec4 glow = {emissive};\n"
            f"    fragColor = vec4(clamp(base.rgb + glow.rgb, 0.0, 1.0), base.a * ({alpha}));\n"
            "}\n"
        )
        return {"fragment": source, "uniforms": uniforms, "backend": "opengl"}

    def _cpu_input(self, node_id: str, port: str, default: Any) -> Any:
        source = self.links.get((node_id, port))
        if source is None:
            values = self.nodes[node_id].get("inputs", {})
            return values.get(port, default) if isinstance(values, Mapping) else default
        return self._cpu_output(*source)

    def _cpu_output(self, node_id: str, port: str) -> Any:
        node, kind = self.nodes[node_id], str(self.nodes[node_id].get("type", ""))
        values = node.get("inputs", {}) if isinstance(node.get("inputs"), Mapping) else {}
        if kind == "material.color_constant":
            color = _color(values.get("color", [1, 1, 1, 1]))
            return color[3] if port == "alpha" else color
        if kind == "material.float_constant":
            return float(values.get("value", 0.0))
        if kind == "material.texture_sample":
            return 1.0 if port == "a" else ([1.0, 1.0, 1.0, 1.0] if port == "rgb" else 1.0)
        if kind == "material.vector_math":
            a = _color(self._cpu_input(node_id, "a", [0, 0, 0, 0]))
            b = _color(self._cpu_input(node_id, "b", [0, 0, 0, 0]))
            if str(values.get("operation", "Multiply")).casefold() == "add":
                return [min(1.0, x + y) for x, y in zip(a, b)]
            return [x * y for x, y in zip(a, b)]
        return 0.0

    def _glsl_input(self, node_id: str, port: str, default: str, uniforms: dict[str, str]) -> str:
        source = self.links.get((node_id, port))
        if source is None:
            value = self._cpu_input(node_id, port, None)
            return _glsl_literal(value) if value is not None else default
        return self._glsl_output(*source, uniforms)

    def _glsl_output(self, node_id: str, port: str, uniforms: dict[str, str]) -> str:
        node, kind = self.nodes[node_id], str(self.nodes[node_id].get("type", ""))
        values = node.get("inputs", {}) if isinstance(node.get("inputs"), Mapping) else {}
        if kind == "material.color_constant":
            color = _color(values.get("color", [1, 1, 1, 1]))
            return _glsl_literal(color[3] if port == "alpha" else color)
        if kind == "material.float_constant":
            return _glsl_literal(float(values.get("value", 0.0)))
        if kind == "material.texture_sample":
            name = "u_" + re.sub(r"[^a-zA-Z0-9_]", "_", node_id)
            uniforms[name] = "sampler2D"
            sample = f"texture({name}, v_uv)"
            return sample if port == "rgb" else f"{sample}.{port}"
        if kind == "material.vector_math":
            a = self._glsl_input(node_id, "a", "vec4(0.0)", uniforms)
            b = self._glsl_input(node_id, "b", "vec4(0.0)", uniforms)
            operator = "+" if str(values.get("operation", "Multiply")).casefold() == "add" else "*"
            return f"({a} {operator} {b})"
        return "0.0"

    def _texture_path_for_output(self) -> str:
        visited: set[str] = set()
        pending = [source[0] for key, source in self.links.items() if key[0] == self.output]
        while pending:
            node_id = pending.pop()
            if node_id in visited:
                continue
            visited.add(node_id)
            node = self.nodes.get(node_id, {})
            if node.get("type") == "material.texture_sample":
                values = node.get("inputs", {})
                return str(values.get("texture", "")) if isinstance(values, Mapping) else ""
            pending.extend(source[0] for key, source in self.links.items() if key[0] == node_id)
        return ""


def _color(value: Any) -> list[float]:
    if isinstance(value, str):
        raw = value.strip().lstrip("#")
        if len(raw) in {6, 8}:
            channels = [int(raw[index:index + 2], 16) / 255.0 for index in range(0, len(raw), 2)]
            return channels + ([1.0] if len(channels) == 3 else [])
    if isinstance(value, (list, tuple)):
        channels = [max(0.0, min(1.0, float(channel))) for channel in value[:4]]
        return channels + [1.0] * (4 - len(channels))
    return [1.0, 1.0, 1.0, 1.0]


def _glsl_literal(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        values = ", ".join(f"{float(item):.6g}" for item in value)
        return f"vec{len(value)}({values})"
    if isinstance(value, bool):
        return "true" if value else "false"
    return f"{float(value):.6g}"
