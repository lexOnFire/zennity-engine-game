"""Compatibility composition for animation workspace operations."""
from editor.animation_asset_operations import AnimationAssetOperations
from editor.animation_preview_operations import AnimationPreviewOperations


class AnimationWorkspaceOperations(AnimationAssetOperations, AnimationPreviewOperations):
    """Composes animation asset and preview behavior for the official editor."""
