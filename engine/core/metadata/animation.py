"""Metadata definitions for Animation Platform and Track Framework."""
from dataclasses import dataclass, field
from typing import Any, List, Type
from engine.metadata.core import MetadataDefinition


@dataclass
class AnimationClipDefinition(MetadataDefinition):
    """Metadata definition for animation clip assets (.zanim)."""
    extensions: List[str] = field(default_factory=lambda: [".zanim"])
    
    def __post_init__(self):
        if not self.title_key and self.id:
            self.title_key = "asset.animation"


@dataclass
class AnimatorDefinition(MetadataDefinition):
    """Metadata definition for animator controller assets (.zanimator)."""
    extensions: List[str] = field(default_factory=lambda: [".zanimator"])

    def __post_init__(self):
        if not self.title_key and self.id:
            self.title_key = "asset.animator"


@dataclass
class TrackDefinition(MetadataDefinition):
    """Metadata definition for a Track type in the Track Framework."""
    track_class: Type | None = None
    target_type: str = "GameObject"
    color: str = "#4A90E2"
    icon: str = "🎞 "


@dataclass
class CurveDefinition(MetadataDefinition):
    """Metadata definition for Animation Curves."""
    curve_type: str = "hermite"
    extrapolation_pre: str = "constant"
    extrapolation_post: str = "constant"


@dataclass
class BlendTreeDefinition(MetadataDefinition):
    """Metadata definition for Blend Trees (1D / 2D blending)."""
    blend_type: str = "1D"
    parameter_x: str = "Blend"
    parameter_y: str = ""


@dataclass
class AnimationEventDefinition(MetadataDefinition):
    """Metadata definition for Animation Keyframe Events."""
    event_type: str = "generic"
    payload_schema: dict = field(default_factory=dict)
