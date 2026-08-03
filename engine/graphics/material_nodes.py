"""Nós de Material Graph integrados ao Graph Framework e MetadataManager da Zennity Engine."""
from __future__ import annotations
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class TextureSampleNode:
    """Nó de Amostragem de Textura 2D (Texture Sample)."""

    __node_definition__ = NodeDefinition(
        id="material.texture_sample",
        title_key="node.material.texture_sample",
        category_key="Material/Texture",
        inputs=[
            PinDefinition(id="texture", pin_type=PinType.STRING),
            PinDefinition(id="uv", pin_type=PinType.VECTOR2),
        ],
        outputs=[
            PinDefinition(id="rgb", pin_type=PinType.COLOR),
            PinDefinition(id="r", pin_type=PinType.FLOAT),
            PinDefinition(id="g", pin_type=PinType.FLOAT),
            PinDefinition(id="b", pin_type=PinType.FLOAT),
            PinDefinition(id="a", pin_type=PinType.FLOAT),
        ],
    )


class ColorConstantNode:
    """Nó de Constante de Cor RGBA."""

    __node_definition__ = NodeDefinition(
        id="material.color_constant",
        title_key="node.material.color_constant",
        category_key="Material/Constant",
        inputs=[
            PinDefinition(id="color", pin_type=PinType.COLOR, default_value=[1.0, 1.0, 1.0, 1.0]),
        ],
        outputs=[
            PinDefinition(id="rgba", pin_type=PinType.COLOR),
            PinDefinition(id="alpha", pin_type=PinType.FLOAT),
        ],
    )


class FloatConstantNode:
    """Nó de Constante Escalar (Float)."""

    __node_definition__ = NodeDefinition(
        id="material.float_constant",
        title_key="node.material.float_constant",
        category_key="Material/Constant",
        inputs=[
            PinDefinition(id="value", pin_type=PinType.FLOAT, default_value=0.0),
        ],
        outputs=[
            PinDefinition(id="out", pin_type=PinType.FLOAT),
        ],
    )


class VectorMathNode:
    """Nó de Operação Matemática (Add, Multiply)."""

    __node_definition__ = NodeDefinition(
        id="material.vector_math",
        title_key="node.material.vector_math",
        category_key="Material/Math",
        inputs=[
            PinDefinition(id="a", pin_type=PinType.COLOR),
            PinDefinition(id="b", pin_type=PinType.COLOR),
            PinDefinition(id="operation", pin_type=PinType.STRING, default_value="Multiply"),
        ],
        outputs=[
            PinDefinition(id="result", pin_type=PinType.COLOR),
        ],
    )


class PBRMaterialOutputNode:
    """Nó Final de Saída do Material PBR (Base Color, Metallic, Roughness, Normal, Emissive)."""

    __node_definition__ = NodeDefinition(
        id="material.pbr_output",
        title_key="node.material.pbr_output",
        category_key="Material/Output",
        inputs=[
            PinDefinition(id="base_color", pin_type=PinType.COLOR),
            PinDefinition(id="metallic", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="roughness", pin_type=PinType.FLOAT, default_value=0.5),
            PinDefinition(id="normal", pin_type=PinType.VECTOR3),
            PinDefinition(id="emissive", pin_type=PinType.COLOR),
            PinDefinition(id="alpha", pin_type=PinType.FLOAT, default_value=1.0),
        ],
        outputs=[],
    )
