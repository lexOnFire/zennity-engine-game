# Zennity Architecture Report

## Assets\Scripts\__init__.py

## Assets\Scripts\animator.py

### Classes
- Animator

## Assets\Scripts\builtin_destroy_on_collision.py

### Functions
- start
- update

## Assets\Scripts\builtin_follow_player.py

### Functions
- start
- update

## Assets\Scripts\builtin_jump.py

### Functions
- start
- update

## Assets\Scripts\builtin_rotate.py

### Functions
- start
- update

## Assets\Scripts\builtin_wasd.py

### Functions
- start
- update

## Assets\Scripts\camera_follow.py

### Classes
- CameraFollow

## Assets\Scripts\collectible.py

### Classes
- Collectible

## Assets\Scripts\enemy_ai.py

### Classes
- EnemyAI

## Assets\Scripts\health.py

### Classes
- Health

## Assets\Scripts\oscillate.py

### Functions
- update

## Assets\Scripts\player.py

### Classes
- PlayerController

## Assets\Scripts\player_controller.py

### Classes
- PlayerController

## Assets\Scripts\projectile.py

### Classes
- Projectile

## Assets\Scripts\pulse.py

### Functions
- update

## Assets\Scripts\rotate.py

### Functions
- update

## Assets\Scripts\timer_component.py

### Classes
- TimerComponent

## __init__.py

## conftest.py

### Functions
- _pygame_init
- screen
- empty_scene
- simple_go

## demos\demo_2d.py

### Classes
- PlayerController
- CameraFollow2D
- Game2DScene

### Functions
- create_player_surface
- create_platform_surface

## demos\demo_3d.py

### Classes
- Spinner3D
- FreeCameraController3D
- Game3DScene

### Functions
- ensure_pyramid_obj

## demos\demo_animator.py

### Classes
- AnimatorDemoScene

### Functions
- _draw_player_frame
- _make_spritesheet
- _make_extra_frames
- _make_tile_surface
- _build_tilemap

## demos\demo_particles.py

### Classes
- ParticlesDemoScene

## demos\demo_physics.py

### Classes
- DemoScene

## demos\demo_platformer.py

### Classes
- RectSprite
- PlayerSprite
- CoinComponent
- PlatformerScene

### Functions
- _make_tileset
- _make_tilemap

## demos\demo_scene_manager.py

### Classes
- SplashScene
- TitleScene
- PauseScene
- GameScene
- GameOverScene

### Functions
- _font
- _center_text

## demos\demo_tilemap.py

### Classes
- TilemapDemoScene

### Functions
- _cleanup_tmp_tileset
- _make_procedural_tileset
- _build_map

## demos\demo_tilemap_physics.py

### Classes
- PhysicsDemoScene

### Functions
- _make_tileset
- _build_map

## demos\demo_ui.py

### Classes
- UIDemoScene

## demos\editor_3d.py

## editor\__init__.py

## editor\assets\__init__.py

## editor\assets\asset_browser_model.py

### Classes
- AssetBrowserItem
- AssetBrowserModel

## editor\assets\asset_browser_viewmodel.py

### Classes
- AssetBrowserViewModel

## editor\assets\project_browser.py

### Classes
- ProjectBrowserSession
- ProjectBrowserService

### Functions
- thumbnail_key_for
- _safe_name
- _unique_path
- _normalize_rel_path

## editor\core\editor_mvp.py

### Functions
- install_editor_mvp
- _set_status
- _sync
- _scene
- _center_2d
- _select_last
- _add_2d_go
- _create_empty_2d
- _create_camera_2d
- _create_preset
- _clear_editable
- _create_template
- _create_topdown_scene

## editor\core\event_bus.py

## editor\core\exporter.py

### Functions
- export_project

## editor\core\script_manager.py

### Classes
- ScriptManager

## editor\core\serializer.py

### Functions
- serialize_game_object
- deserialize_game_object
- save_scene_to_file
- load_scene_from_file

## editor\fixed_studio_main.py

### Functions
- load_stylesheet
- main

## editor\gizmos\__init__.py

## editor\gizmos\gizmo_registry.py

### Classes
- GizmoRegistry

### Functions
- _get_screen_pos
- _get_zoom
- draw_camera_gizmo
- draw_box_collider_gizmo
- draw_circle_collider_gizmo
- draw_audio_source_gizmo
- draw_audio_listener_gizmo

## editor\gizmos\gizmo_runtime.py

### Functions
- install_gizmo_runtime

## editor\gizmos\move_gizmo.py

### Classes
- MoveGizmo

## editor\gizmos\qt_gizmo_overlay.py

### Classes
- QtMoveGizmoOverlay

## editor\gizmos\rotate_gizmo.py

### Classes
- QtRotateGizmoOverlay

## editor\inspector\__init__.py

## editor\inspector\asset_component_plugins.py

### Classes
- AssetAwareImageInspectorPlugin
- AssetAwareAnimatorInspectorPlugin

### Functions
- _project_relative
- _available_sprite_paths
- register_asset_component_plugins

## editor\inspector\default_plugins.py

### Classes
- TransformInspectorPlugin
- RigidBodyInspectorPlugin
- ColliderInspectorPlugin
- ScriptInspectorPlugin
- CameraInspectorPlugin
- AudioSourceInspectorPlugin
- AudioListenerInspectorPlugin
- AnimatorInspectorPlugin
- CanvasInspectorPlugin
- LabelInspectorPlugin
- ImageInspectorPlugin
- ButtonInspectorPlugin
- TilemapInspectorPlugin
- TilemapRendererInspectorPlugin
- AssetInspectorPlugin
- PackageInspectorPlugin

### Functions
- _section
- _float_field
- _axis_row
- _property_row
- _project_relative
- _available_script_paths
- _script_template
- _safe_script_name
- _safe_class_name
- register_default_inspector_plugins

## editor\inspector\infinite_background_plugin.py

### Classes
- InfiniteBackgroundInspectorPlugin

### Functions
- _project_relative
- _available_sprite_paths
- register_infinite_background_plugin

## editor\inspector\plugin.py

### Classes
- InspectorPlugin

## editor\inspector\plugin_registry.py

### Classes
- InspectorPluginRegistry

## editor\main.py

### Functions
- patch_logger
- load_stylesheet
- main

## editor\models\asset_model.py

### Classes
- AssetModel

## editor\models\scene_model.py

### Classes
- SceneModel

## editor\mvp_main.py

### Functions
- load_stylesheet
- main

## editor\phase1_editor.py

### Classes
- ZennityPhase1Editor

## editor\phase1_main.py

## editor\premium_editor.py

### Classes
- Panel
- HierarchyPanel
- ResourcesPanel
- CreatePanel
- PrefabsPanel
- InspectorPanel
- ConsolePanel
- SimplePanel
- AssetPreviewPanel
- ZennityPremiumEditor

### Functions
- run

## editor\premium_main.py

## editor\premium_panels.py

### Classes
- RealHierarchyPanel
- RealInspectorPanel

## editor\premium_theme.py

## editor\runtime\__init__.py

## editor\runtime\asset_direct_drop_patch.py

### Functions
- _event_pos
- _asset_path
- _supported
- _selected
- _object_at
- _apply
- _patch_asset_tree
- _patch_target
- apply_asset_direct_drop_patch
- _scan
- patch_asset_direct_drop_runtime

## editor\runtime\asset_drag_drop_patch.py

### Classes
- _AssetDragFilter
- _ViewportDropFilter
- _HierarchyDropFilter
- _InspectorDropFilter

### Functions
- _event_pos
- _asset_path_from_mime
- _is_asset_mime
- _asset_path_from_item
- _is_image
- _is_script
- _is_supported
- _apply_asset_with_undo
- _post_apply
- apply_asset_drag_drop_patch

## editor\runtime\assets_panel_polish_patch.py

### Classes
- _AssetsPanelFilter

### Functions
- _item_path
- _walk_items
- _expanded_paths
- _restore_expanded_paths
- _find_item_by_path
- _mark_item_flags
- _image_icon_for
- _request_refresh
- _install_assets_watcher
- _sync_watcher_paths
- apply_assets_panel_polish
- _scan_and_apply_assets_panel_polish
- install_assets_panel_polish_runtime_watch

## editor\runtime\command_manager.py

### Classes
- Command
- FunctionCommand
- BatchCommand
- CommandManager

## editor\runtime\component_commands.py

### Classes
- AddComponentCommand
- RemoveComponentCommand

## editor\runtime\editor2d_sprite_no_border_patch.py

### Functions
- _image_component
- _load_surface
- apply_editor2d_sprite_no_border_patch

## editor\runtime\editor2d_sprite_patch.py

### Functions
- apply_editor2d_sprite_patch

## editor\runtime\editor_context.py

### Classes
- EditorContext

## editor\runtime\editor_state.py

### Classes
- EditorState

## editor\runtime\hierarchy_commands.py

### Classes
- ReparentGameObjectCommand
- DuplicateGameObjectCommand
- DeleteGameObjectCommand
- RenameGameObjectCommand

### Functions
- root_objects
- is_descendant
- can_reparent
- _editable
- _scene_add
- _scene_remove
- _detach_from_parent
- _attach_to_parent
- _move_in_list
- clone_game_object

## editor\runtime\phase1_sprite_overlay_patch.py

### Functions
- _candidate_roots
- _resolve_sprite_path
- _cached_pixmap
- _image_component
- _call_or_value
- _selected_object
- _is_rect_visible
- _patch_sprite_selection_overlay
- apply_phase1_sprite_overlay_patch

## editor\runtime\rotated_scale_gizmo_patch.py

### Functions
- _rotated_scale_handle_positions
- apply_rotated_scale_gizmo_patch

## editor\runtime\selection_manager.py

### Classes
- SelectionManager

## editor\runtime\sprite_selection_overlay_patch.py

### Functions
- _has_image_sprite
- apply_sprite_selection_overlay_patch

## editor\runtime\tool_manager.py

### Classes
- EditorTool
- ToolManager

## editor\runtime\tool_selection_stability_patch.py

### Functions
- _current_scene_object
- _current_runtime_object
- _sync_object_selection
- apply_tool_selection_stability_patch

## editor\runtime\undo_redo_feedback_patch.py

### Functions
- _current_selected
- _refresh_viewport
- _refresh_editor
- _subscribe_refresh_callbacks
- _safe_disconnect
- _install_instance_shortcuts
- _scan_and_install_instances
- apply_undo_redo_feedback_patch

## editor\runtime\viewport_transform_stability_patch.py

### Functions
- _sync_camera_to_engine
- _selected_or_scene_object
- _activate_gizmo_reference
- _move_axis_at
- _sync_collider_size
- _emit_transform_changed
- apply_viewport_transform_stability_patch

## editor\selection_runtime.py

### Functions
- install_viewport_selection_api

## editor\studio_main.py

### Functions
- load_stylesheet
- main

## editor\viewmodels\asset_viewmodel.py

### Classes
- AssetViewModel

## editor\viewmodels\scene_viewmodel.py

### Classes
- SceneViewModel

## editor\viewport\__init__.py

## editor\viewport\bounding_box.py

### Classes
- BoundingBoxRenderer

### Functions
- get_object_bounds
- get_handle_positions
- hit_test_handle

## editor\viewport\grid_renderer.py

### Classes
- GridRenderer

## editor\viewport\scene_view_polish.py

### Classes
- SceneViewPolishState

### Functions
- focus_selected_camera_position

## editor\viewport\selection_outline.py

### Classes
- SelectionOutlineRenderer

### Functions
- _has_visible_sprite

## editor\viewport\viewport_camera.py

### Classes
- ViewportCamera

## editor\viewport\viewport_overlay.py

### Classes
- ViewportOverlay

## editor\viewport\viewport_renderer.py

### Classes
- ViewportRenderer

## editor\widgets\asset_browser_dock.py

### Classes
- AssetBrowserDock

## editor\widgets\code_editor_dock.py

### Classes
- CodeEditorDock

## editor\widgets\collapsible_section.py

### Classes
- CollapsibleSection

## editor\widgets\component_widgets.py

### Classes
- TransformComponentWidget
- MeshRendererComponentWidget
- SpriteRendererComponentWidget
- ImageComponentWidget
- AnimatorComponentWidget
- RigidBodyComponentWidget
- ColliderComponentWidget
- ScriptComponentWidget

### Functions
- create_spin_box
- validate_and_get_value
- _create_xyz_row

## editor\widgets\console_dock.py

### Classes
- ConsoleDock

## editor\widgets\create_dock.py

### Classes
- CreateDock

## editor\widgets\hierarchy_dock.py

### Classes
- HierarchyDock

## editor\widgets\inspector_dock.py

### Classes
- ComponentFrame
- InspectorDock
- _ScriptProxy

## editor\widgets\phase1_viewport.py

### Classes
- Phase1ViewportWidget

## editor\widgets\profiler_dock.py

### Classes
- PerformanceChartWidget
- ProfilerDock

## editor\widgets\viewport_widget.py

### Classes
- ViewportWidget

## editor\windows\fixed_studio_window.py

### Classes
- FixedStudioWindow

## editor\windows\main_window.py

### Classes
- MainWindow

## editor\windows\preferences_dialog.py

### Classes
- PreferencesDialog

## editor\windows\studio_window.py

### Classes
- StudioWindow

## editor\workspace.py

### Classes
- WorkspaceLayout
- WorkspaceManager

### Functions
- default_workspace_layout
- compact_workspace_layout
- animation_workspace_layout

## editor_legacy\__init__.py

## editor_legacy\camera_controller.py

### Classes
- OrbitCameraController

## editor_legacy\code_editor.py

### Classes
- CodeEditor

## editor_legacy\gui.py

### Classes
- GuiButton
- SectionHeader
- Divider
- Badge

## editor_legacy\history.py

### Classes
- History

### Functions
- _snap_obj
- _get_color
- _snap_scene

## editor_legacy\launcher.py

### Classes
- LauncherScene

## editor_legacy\layout.py

### Classes
- Layout

## editor_legacy\layout_constants.py

## editor_legacy\mesh_factory.py

### Functions
- create_pyramid_mesh
- create_sphere_mesh
- create_plane_mesh
- create_capsule_mesh

## editor_legacy\physics_sim.py

### Classes
- PhysicsSim

### Functions
- _half_extents
- _aabb_overlap

## editor_legacy\scene.py

### Classes
- EditorScene

### Functions
- _point_in_polygon

## editor_legacy\script_manager.py

### Classes
- ScriptManager

## editor_legacy\theme.py

### Functions
- alpha_blend
- grid_color

## editor_legacy\widgets\__init__.py

## editor_legacy\widgets\panel_base.py

### Classes
- PanelBase
- _ClipContext

## engine\__init__.py

## engine\animation\__init__.py

## engine\animation\animator.py

### Classes
- Animator

## engine\animation\clip.py

### Classes
- AnimationEvent
- Keyframe
- AnimationClip

## engine\animation\spritesheet.py

### Classes
- SpriteSheet

## engine\application.py

### Classes
- Application

## engine\assets\__init__.py

### Classes
- Mesh
- Assets

## engine\assets\asset_database.py

### Classes
- AssetDatabase

## engine\assets\asset_importer.py

### Classes
- AssetImporter
- TextureImporter
- AudioImporter
- ScriptImporter
- TilemapImporter
- GenericImporter
- ImporterRegistry

## engine\assets\asset_metadata.py

### Classes
- AssetInfo
- AssetMeta

## engine\assets\asset_types.py

### Classes
- AssetType

### Functions
- detect_asset_type

## engine\audio.py

### Classes
- AudioManager
- AudioSource
- AudioListener

## engine\build\__init__.py

## engine\build\build_config.py

### Classes
- BuildTarget
- BuildConfig

## engine\build\desktop_package.py

### Classes
- DesktopPackagePlan

### Functions
- executable_name_for
- create_desktop_package_plan
- create_plan_from_profile

## engine\build\export_profile.py

### Classes
- ExportProfile

### Functions
- debug_profile
- release_profile

## engine\build\export_profile_manager.py

### Classes
- ExportProfileManager

## engine\component.py

## engine\component_registry.py

### Classes
- ComponentRegistry

## engine\components\__init__.py

## engine\components\script_component.py

### Classes
- ScriptComponent

## engine\core.py

## engine\core\__init__.py

## engine\core\application.py

## engine\core\component.py

### Classes
- Component
- Transform

## engine\core\component_registry.py

### Classes
- ComponentRegistry

### Functions
- register_component

## engine\core\engine.py

### Classes
- Engine

### Functions
- _builtin_physics_system

## engine\core\event_bus.py

## engine\core\game_object.py

## engine\core\logger.py

## engine\core\scene.py

### Classes
- Scene

## engine\core\scene_manager.py

### Classes
- SceneManager

## engine\core\system.py

## engine\core\time.py

## engine\event_bus.py

### Classes
- EventBus

## engine\game_object.py

### Classes
- GameObject

## engine\graphics\__init__.py

## engine\graphics\camera.py

### Classes
- CameraMeta
- Camera

## engine\graphics\camera2d.py

### Classes
- Camera2D

## engine\graphics\camera_manager.py

### Classes
- CameraManager

## engine\graphics\math3d.py

### Functions
- translation_matrix
- scale_matrix
- rotation_matrix
- projection_matrix
- view_matrix
- project_vertices

## engine\graphics\particles.py

### Classes
- Particle
- ParticleSystem

## engine\graphics\renderer.py

### Classes
- SpriteRenderer

## engine\graphics\renderer2d.py

### Classes
- SpriteRenderer
- TextRenderer
- Particle
- ParticleSystem

## engine\graphics\renderer3d.py

### Classes
- Camera3D
- MeshRenderer3D

## engine\graphics\tilemap.py

### Classes
- Tileset
- Tilemap
- TilemapRenderer

## engine\input.py

### Classes
- Input

## engine\logger.py

### Classes
- Logger
- _TaggedLogger

## engine\packages\__init__.py

## engine\packages\manager.py

### Classes
- PackageManager

## engine\packages\package.py

### Classes
- Package

## engine\packages\registry.py

### Classes
- PackageRegistry

## engine\physics\__init__.py

## engine\physics\collider.py

### Classes
- CollisionInfo
- BoxCollider
- CircleCollider

## engine\physics\collision.py

### Classes
- BoxCollider2D

### Functions
- check_collision

## engine\physics\physics.py

### Classes
- Physics

## engine\physics\physics_world.py

### Classes
- PhysicsContact
- PhysicsWorld

## engine\physics\rigidbody.py

### Classes
- RigidBody

## engine\physics\rigidbody3d.py

### Classes
- RigidBody3D

## engine\physics\tilemap_collider.py

### Classes
- TilemapCollider

## engine\prefabs\__init__.py

## engine\prefabs\prefab_format.py

## engine\prefabs\prefab_loader.py

### Functions
- _resolve_project_root_from_path
- create_prefab_from_object
- instantiate_prefab

## engine\prefabs\prefab_serializer.py

### Functions
- serialize_prefab
- deserialize_prefab

## engine\runtime\__init__.py

## engine\runtime\clone.py

### Functions
- _is_runtime_resource
- _safe_copy_value
- _copy_optional_attr
- _clone_component_by_constructor
- _clone_component
- clone_game_object

## engine\runtime\input_manager.py

### Classes
- InputManager

## engine\runtime\runtime_manager.py

### Classes
- RuntimeState
- RuntimeManager

## engine\runtime\runtime_scene.py

### Classes
- RuntimeScene

## engine\runtime\script_behaviour.py

### Classes
- ScriptBehaviour

## engine\runtime\script_runtime.py

### Classes
- ScriptRuntimeInstance
- ScriptRuntime

## engine\runtime\serialization.py

### Classes
- _NumpyEncoder
- SceneSerializer
- PrefabSerializer

### Functions
- _serialize_go
- _deserialize_go
- _validate_schema

## engine\scene\__init__.py

## engine\scene\scene_format.py

## engine\scene\scene_loader.py

### Functions
- load_scene

## engine\scene\scene_serializer.py

### Functions
- _vector
- _get_scene_objects
- _portable_asset_path
- _component_by_class_name
- _serialize_collider
- _serialize_rigidbody
- _serialize_component_items
- serialize_game_object
- serialize_scene
- _deserialize_collider
- _deserialize_rigidbody
- _component_from_item
- deserialize_game_object
- deserialize_scene
- save_scene

## engine\scene_manager.py

## engine\system.py

### Classes
- SystemPriority
- System
- SystemRegistry

## engine\tilemap\__init__.py

## engine\tilemap\tilemap.py

### Classes
- TileLayer
- TileMap
- TilemapRenderer

## engine\tilemap\tilemap_loader.py

### Classes
- TileMapLoader

## engine\tilemap\tileset.py

### Classes
- TileData
- Tileset

## engine\time.py

### Classes
- Time

## engine\transitions.py

### Classes
- TransitionPhase
- Transition
- FadeTransition
- SlideDirection
- SlideTransition
- WipeTransition
- CrossfadeTransition

### Functions
- _linear
- _ease_in
- _ease_out
- _ease_in_out

## engine\ui\__init__.py

## engine\ui\base.py

### Classes
- Anchor
- Pivot
- UIElement

## engine\ui\button.py

### Classes
- Button

## engine\ui\canvas.py

### Classes
- UICanvas

## engine\ui\image.py

### Classes
- UIImage

## engine\ui\label.py

### Classes
- Label

## engine\ui\panel.py

### Classes
- Panel

## engine\ui\progress_bar.py

### Classes
- ProgressBar

## engine\ui\runtime_components.py

### Classes
- UIElement
- Canvas
- LabelComponent
- ImageComponent
- InfiniteBackground
- ButtonComponent

## engine\ui\sprite_performance_patch.py

### Functions
- _resolved_key
- _trim_cache
- _is_screen_rect_visible
- apply_sprite_performance_patch

## engine\ui\ui_manager.py

### Classes
- UIManager

## engine\ui\ui_renderer.py

### Classes
- UIRenderer

## engine\window.py

### Classes
- Window

## examples\GettingStarted\Assets\Scripts\auto_rotate.py

### Classes
- Script

## examples\GettingStarted\Assets\Scripts\click_logger.py

### Classes
- Script

## examples\GettingStarted\Assets\Scripts\ping_pong_movement.py

### Classes
- Script

## examples\GettingStarted\Assets\Scripts\player_controller.py

### Classes
- Script

## scripts\behavior_bloco_1.py

### Functions
- start
- update

## scripts\behavior_bloco_2.py

### Functions
- start
- update

## scripts\builtin_destroy_on_collision.py

### Functions
- start
- update

## scripts\builtin_follow_player.py

### Functions
- start
- update

## scripts\builtin_jump.py

### Functions
- start
- update

## scripts\builtin_rotate.py

### Functions
- start
- update

## scripts\builtin_wasd.py

### Functions
- start
- update

## scripts\oscillate.py

### Functions
- update

## scripts\pulse.py

### Functions
- update

## scripts\rotate.py

### Functions
- update

## tests\__init__.py

## tests\animation\__init__.py

## tests\animation\conftest.py

## tests\animation\test_animation.py

### Classes
- TestAnimationEvent
- TestAnimationClip
- TestAnimatorInit
- TestAnimatorUpdate
- TestAnimatorEvents
- TestAnimatorTransitions
- TestAnimatorPushFrame
- TestAnimatorState

### Functions
- make_surface
- make_frames
- make_animator

## tests\animation\test_animation_runtime_foundation.py

### Functions
- _empty_editor_scene
- _move_clip
- setup_function
- teardown_function
- test_keyframe_creation_and_serialization
- test_animation_clip_samples_interpolated_properties
- test_animator_play_pause_and_stop
- test_animator_loop_wraps_clip_time
- test_animator_uses_official_time_delta_time
- test_animator_changes_runtime_transform_and_preserves_editor_world
- test_animator_component_serializes_and_deserializes
- test_scene_serialization_preserves_animator_component

## tests\animation\test_animator.py

### Classes
- TestInit
- TestAddClip
- TestPlay
- TestStart
- TestUpdateFrameAdvance
- TestOnFinish
- TestTransitions
- TestAnimationEvents
- TestStateQueries

### Functions
- _frames
- _clip
- _animator_with_go
- _animator

## tests\animation\test_clip.py

### Classes
- TestAnimationEvent
- TestAnimationClipInit
- TestFlipH
- TestFrameCount
- TestDuration
- TestAddEvent
- TestRepr

### Functions
- reset_flip
- _frames
- _clip

## tests\assets\test_asset_database.py

### Functions
- _write
- test_scan_creates_assets_folder
- test_scan_recognizes_types_and_creates_meta
- test_meta_uuid_is_stable_across_refresh
- test_list_assets_by_type_and_lookup
- test_scan_ignores_meta_as_primary_asset
- test_remove_missing_assets_deletes_orphan_meta
- test_asset_paths_are_project_relative
- test_zscene_uses_relative_asset_reference

## tests\assets\test_asset_importer.py

### Functions
- test_asset_importer_recognizes_supported_types
- test_asset_importer_unknown_type

## tests\beta\test_beta_stabilization.py

### Functions
- _empty_editor_scene
- _add_to_scene
- _write_beta_script
- _read_events
- test_beta_complete_project_flow_keeps_editor_world_intact
- test_beta_old_scene_and_prefab_formats_remain_compatible
- test_getting_started_example_scene_is_loadable
- instantiate_prefab_from_data

## tests\components\test_component_management.py

### Functions
- qapp
- test_add_component_command_adds_component
- test_remove_component_command_removes_component
- test_undo_and_redo_add_component
- test_undo_and_redo_remove_component_restores_same_instance_and_order
- test_cannot_remove_transform
- test_cannot_add_duplicate_unique_component
- test_inspector_adds_and_removes_components_with_undo_redo
- test_inspector_blocks_transform_removal
- test_inspector_available_components_respects_unique_components
- test_serialization_reflects_added_and_removed_components
- test_prefab_serialization_keeps_component_changes

## tests\components\test_component_system.py

### Functions
- qapp
- test_component_has_identity_type_enabled_and_serializes
- test_component_registry_registers_and_creates_component
- test_game_object_add_remove_find_components_and_prevent_unique_duplicates
- test_game_object_transform_is_required
- test_builtin_components_are_registered
- test_component_serialization_round_trip
- test_old_scene_component_format_still_loads
- test_old_prefab_format_still_loads
- test_prefab_serializes_component_items
- test_inspector_lists_components_and_edits_with_undo_redo

## tests\components\test_inspector_plugin_system.py

### Classes
- DummyPlugin

### Functions
- qapp
- test_inspector_plugin_registry_registers_and_resolves_plugin
- test_default_plugins_resolve_builtin_components
- test_inspector_hosts_plugins_for_multiple_components
- test_inspector_handles_missing_plugin
- test_plugin_edit_uses_undo_redo
- test_inspector_switches_selection_and_rebuilds_plugins
- test_new_component_and_plugin_appear_without_inspector_change
- test_inspector_dock_does_not_import_concrete_component_widgets

## tests\conftest.py

### Functions
- _remove_fake_engine_modules
- pytest_collect_file
- reset_global_input_state

## tests\core\__init__.py

## tests\core\test_application.py

### Classes
- TestSingleton
- TestServiceLocator
- TestBuiltins
- TestRepr
- TestConvenienceProperties

### Functions
- reset_application
- _make_app
- _stop_patches

## tests\core\test_component.py

### Classes
- TestComponentInit
- TestComponentLifecycle
- TestComponentProperties
- TestTransformInit
- TestTransformSetters
- TestTransformTranslate
- TestTransformRotate
- TestTransformModelMatrix
- TestTransformRepr

## tests\core\test_event_bus.py

### Classes
- TestSubscribe
- TestUnsubscribe
- TestEmit
- TestOnce
- TestEmitDeferred
- TestClear
- TestInspection
- TestInstanceAlias
- TestEdgeCases

### Functions
- reset_bus

## tests\core\test_game_object.py

### Classes
- TestIdentity
- TestTransform
- TestAddComponent
- TestGetComponent
- TestRemoveComponent
- TestHierarchy
- TestUpdate
- TestDraw
- TestDestroy
- TestScenePropagation

### Functions
- make_component
- fake_scene

## tests\core\test_input.py

### Classes
- TestGetKey
- TestGetKeyDown
- TestGetKeyUp
- TestMousePosition
- TestMouseButton
- TestAxes
- TestUpdate

### Functions
- _make_keys

## tests\core\test_scene.py

### Classes
- TestSceneInit
- TestAddGameObject
- TestRemoveGameObject
- TestFind
- TestUpdate
- TestDraw
- TestLifecycleHooks
- TestEngineRef

### Functions
- make_go
- make_tracked_go

## tests\core\test_scene_manager.py

### Classes
- _FakePhase
- _FakeScene
- _FakeTransition
- TestSingleton
- TestBind
- TestLoad
- TestPush
- TestPop
- TestUpdate
- TestDraw
- TestHandleEvent
- TestCallbacks
- TestRepr

### Functions
- restore_sys_modules_after_test_module
- clean_sm
- sm
- fake_engine

## tests\core\test_time.py

### Classes
- TestDefaults
- TestTick
- TestDtCap
- TestScale
- TestPaused
- TestElapsed
- TestSlowMo
- TestAliases
- TestCurrent
- TestRepr

### Functions
- make_time

## tests\core\test_transform.py

### Classes
- TestTransformSetters
- TestTransformMethods
- TestTransformRepr
- TestComponentLifecycle

## tests\core\test_ui_runtime_components.py

### Classes
- GameplayMarker

### Functions
- test_pure_ui_owner_is_hidden_from_world_draw
- test_mixed_gameplay_owner_stays_visible_with_ui_component
- test_all_pure_ui_components_are_hidden_from_world_draw

## tests\core\test_window.py

### Classes
- TestDefaults
- TestSetTitle
- TestOnResize
- TestToggleFullscreen
- TestFlip
- TestResolutionClamping

### Functions
- _make_surface
- _make_display_info
- make_window

## tests\editor\test_asset_component_inspector_plugins.py

### Functions
- qapp
- test_image_inspector_has_sprite_selector
- test_image_sprite_selector_updates_component
- test_animator_inspector_exposes_default_clip_and_speed
- test_animator_speed_field_updates_component

## tests\editor\test_desktop_package.py

### Functions
- test_desktop_package_plan_for_windows
- test_desktop_package_plan_for_linux
- test_desktop_package_plan_for_macos
- test_desktop_package_plan_includes_entry_scene
- test_desktop_package_plan_can_skip_assets
- test_desktop_package_plan_roundtrip
- test_desktop_package_plan_from_profile

## tests\editor\test_export_config.py

### Functions
- test_config_defaults_are_valid
- test_config_output_path_contains_target_and_project
- test_config_roundtrip
- test_config_rejects_invalid_entry_scene_extension

## tests\editor\test_export_profiles.py

### Functions
- test_export_profile_defaults_are_valid
- test_export_profile_roundtrip_preserves_config
- test_default_profiles_have_expected_modes
- test_export_profile_manager_register_get_remove
- test_export_profile_manager_enabled_profiles
- test_export_profile_manager_dict_roundtrip
- test_export_profile_manager_file_roundtrip

## tests\editor\test_hierarchy_improvements.py

### Functions
- qapp
- editor
- _clear_scene
- _add
- _item_for
- test_hierarchy_reparent_valid
- test_hierarchy_prevents_cycles
- test_hierarchy_move_to_root
- test_hierarchy_reorders_siblings
- test_hierarchy_duplicate_object
- test_hierarchy_duplicate_with_children
- test_hierarchy_delete
- test_hierarchy_rename_valid
- test_hierarchy_rename_empty_rejected
- test_hierarchy_filter_keeps_matching_parents_visible

## tests\editor\test_inspector_ux_polish.py

### Classes
- _ViewModel

### Functions
- _app
- test_inspector_component_filter_keeps_matching_components
- test_inspector_copy_paste_component_values_uses_command_manager
- test_inspector_reset_component_is_reversible
- test_inspector_move_component_is_reversible
- test_inspector_object_property_command_is_reversible

## tests\editor\test_phase1_editor_context.py

### Classes
- _MousePress

### Functions
- qapp
- phase1_editor
- _hierarchy_item_for
- _scene_registered_colliders
- _scene_attached_colliders
- _assert_scene_collider_registry_is_current
- test_phase1_editor_owns_editor_context
- test_phase1_toolbar_tools_update_tool_manager
- test_phase1_file_menu_has_scene_actions
- test_phase1_save_scene_uses_current_scene_path
- test_phase1_apply_scene_data_replaces_scene_and_selection
- test_phase1_toolbar_active_tool_is_visually_checked
- test_phase1_snap_toolbar_toggle_updates_editor_state
- test_phase1_play_controls_reflect_simulation_state
- test_phase1_editor_has_scene_and_game_view_tabs
- test_phase1_stop_restores_scene_and_reselects_restored_object
- test_phase1_play_cycles_start_from_same_physics_state
- test_phase1_play_stop_preserves_objects_and_selection
- test_phase1_play_mode_switches_viewport_and_inspector_to_runtime_scene
- test_phase1_game_view_hides_runtime_inner_scene_grid
- test_phase1_camera_2d_creation_adds_real_camera_component
- test_phase1_runtime_fallback_objects_are_hidden_from_game_draw
- test_phase1_rotate_reports_active_and_scale_reports_unimplemented
- test_phase1_selection_uses_editor_context
- test_phase1_hierarchy_selection_updates_selection_manager
- test_phase1_viewport_selection_updates_selection_manager
- test_phase1_selection_manager_syncs_viewport_hierarchy_and_inspector
- test_phase1_hierarchy_refreshes_after_viewport_delete
- test_phase1_viewport_move_tool_moves_selected_object_and_updates_inspector
- test_phase1_viewmodel_transform_change_refreshes_inspector
- test_phase1_move_tool_does_not_jump_when_drag_starts_off_center
- test_phase1_move_tool_does_not_drag_from_empty_viewport_space
- test_phase1_move_tool_snap_disabled_moves_freely
- test_phase1_move_tool_snap_enabled_snaps_drag_position
- test_phase1_move_tool_does_not_drag_while_playing
- test_phase1_gizmo_is_hidden_while_playing
- test_phase1_select_tool_does_not_start_move_drag
- test_phase1_world_to_viewport_uses_scene_camera_transform
- test_phase1_viewport_has_command_manager_injected
- test_phase1_move_tool_registers_undo_command
- test_phase1_move_tool_undo_restores_position
- test_phase1_move_tool_redo_reapplies_position
- test_phase1_move_tool_no_command_when_no_movement
- test_phase1_snap_applied_over_absolute_position
- test_phase1_snap_disabled_delta_zero_preserves_position

## tests\editor\test_phase1_inspector.py

### Functions
- qapp
- editor_context
- scene_model
- scene_viewmodel
- inspector
- test_inspector_empty_state_without_selection
- test_inspector_populates_fields_on_selection
- test_inspector_interactive_update_no_command
- test_inspector_commit_creates_undo_command
- test_inspector_commit_identical_value_no_command
- test_inspector_selection_switch_updates_fields
- test_inspector_deleted_object_does_not_crash
- test_inspector_invalid_input_handling
- test_inspector_empty_input_reverts_to_original
- test_rigidbody_properties_undo_redo
- test_collider_properties_undo_redo_sync
- test_script_property_undo_redo
- test_script_inspector_lists_assets_scripts_and_uses_buttons
- test_script_inspector_create_button_creates_script_template

## tests\editor\test_phase1_rotate_tool.py

### Functions
- qapp
- phase1_editor
- _selected
- _set_rotate_tool
- test_rotate_gizmo_overlay_exists_on_viewport
- test_editor_state_has_snap_angle
- test_rotate_tool_status_message
- test_rotate_gizmo_hit_test_detects_ring
- test_rotate_gizmo_hit_test_detects_center
- test_rotate_gizmo_hit_test_rejects_far_point
- test_rotate_tool_begin_drag_returns_true_on_valid_object
- test_rotate_tool_begin_drag_returns_false_for_select_tool
- test_rotate_tool_drag_changes_rz
- test_rotate_tool_drag_does_not_move_position
- test_rotate_tool_registers_undo_command
- test_rotate_tool_undo_restores_rz
- test_rotate_tool_redo_reapplies_rz
- test_rotate_tool_no_command_when_no_rotation
- test_rotate_tool_snap_enabled_snaps_to_angle
- test_rotate_tool_snap_disabled_allows_free_rotation
- test_rotate_tool_blocked_during_play_mode
- test_rotate_drag_does_not_interfere_with_move_drag
- test_viewport_rotate_drag_cleans_up_after_end
- test_undo_redo_toolbar_actions_enabled_state

## tests\editor\test_phase1_scale_tool.py

### Functions
- qapp
- phase1_editor
- _selected
- test_scale_tool_begin_drag_returns_true_on_valid_object
- test_scale_tool_begin_drag_returns_false_for_wrong_tool
- test_scale_tool_drag_changes_scale_right_center
- test_scale_tool_snap_enabled
- test_scale_tool_registers_undo_command
- test_scale_tool_blocked_during_play_mode

## tests\editor\test_phase1_viewport_pro.py

### Functions
- qapp
- phase1_editor
- test_viewport_camera_pan
- test_viewport_camera_zoom_boundaries
- test_viewport_camera_coordinates_roundtrip
- test_viewport_camera_zoom_to_mouse_preserves_anchor
- test_bounding_box_eight_handles_rotation
- test_bounding_box_can_hide_scale_handles
- test_viewport_renderer_shows_handles_only_for_scale_tool
- test_viewport_renderer_hides_handles_during_play_mode
- test_phase1_viewport_syncs_legacy_scale_handles_by_active_tool
- test_grid_renderer_opacity_fading
- test_viewport_public_coordinate_api
- test_bounding_box_apis_rectangular_bounds
- test_bounding_box_apis_circular_bounds
- test_bounding_box_apis_eight_handle_positions
- test_bounding_box_apis_hit_test_handle
- test_bounding_box_draw_no_selection_no_crash

## tests\editor\test_project_browser_improvements.py

### Functions
- _write_asset
- test_project_browser_thumbnail_keys
- test_project_browser_search_by_name_extension_and_type
- test_project_browser_rename_preserves_guid_and_refreshes_database
- test_project_browser_move_preserves_guid_and_refreshes_database
- test_project_browser_duplicate_creates_new_guid
- test_project_browser_delete_removes_asset_and_meta
- test_project_browser_create_folder_uses_unique_name
- test_project_browser_session_tracks_view_mode_and_favorites

## tests\editor\test_reference_scripts.py

### Functions
- test_reference_scripts_define_runtime_behaviour
- test_reference_scripts_use_explicit_script_class

## tests\editor\test_runtime.py

### Functions
- test_selection_manager_notifies_only_on_change
- test_tool_manager_tracks_active_tool
- test_command_manager_executes_undo_and_redo
- test_editor_context_resets_scene_state

## tests\editor\test_scene_view_polish.py

### Classes
- _Transform
- _Object

### Functions
- test_scene_view_polish_toolbar_state_defaults
- test_scene_view_polish_toggles_are_explicit
- test_scene_view_polish_gizmos_hidden_in_play_and_game_view
- test_scene_view_polish_can_hide_gizmo_by_type
- test_focus_selected_camera_position_is_safe

## tests\editor\test_selection_integration.py

### Functions
- test_viewmodel_selection_setter_delegates_to_selection_manager
- test_selection_manager_updates_viewmodel_signal
- test_viewmodel_keeps_event_bus_compatibility

## tests\editor\test_workspace.py

### Functions
- test_workspace_layout_roundtrip
- test_default_workspace_contains_core_panels
- test_compact_workspace_hides_secondary_panels
- test_animation_workspace_keeps_preview_visible
- test_workspace_manager_applies_and_resets
- test_workspace_manager_falls_back_to_default

## tests\graphics\__init__.py

## tests\graphics\test_camera2d.py

### Classes
- TestInit
- TestMakeMain
- TestUpdateFollow
- TestBounds
- TestWorldToScreen
- TestScreenToWorld

### Functions
- _make_go
- _make_cam
- reset_main

## tests\graphics\test_renderer.py

### Classes
- _FakeSurface
- TestInit
- TestSurfaceProperty
- TestDrawNoCam
- TestDrawWithCam

### Functions
- _make_surface
- reset_camera
- _make_go
- _renderer

## tests\integration\test_gameplay_foundation.py

### Functions
- test_full_gameplay_foundation_integration

## tests\integration\test_tilemap_integration.py

### Functions
- runtime_scene
- test_tilemap_integration

## tests\integration\test_v030_stabilization.py

### Functions
- temp_dir
- test_v030_stabilization_end_to_end

## tests\physics\test_collider.py

### Classes
- TestCollisionInfo
- TestBoxColliderInit
- TestBoxColliderLifecycle
- TestBoxColliderRect
- TestBoxCheckAllBasic
- TestBoxCheckAllTrigger
- TestBoxResolve
- TestCircleCollider

### Functions
- _make_transform
- _make_rb
- _make_go
- _box
- _circle
- _clean_registries

## tests\physics\test_rigidbody.py

### Classes
- TestRigidBodyInit
- TestAddForce
- TestAddImpulse
- TestSetVelocityStop
- TestUpdateGravity
- TestUpdateExternalForces
- TestUpdateDrag
- TestUpdateKinematic
- TestGrounded

### Functions
- _make_transform
- _make_go
- _rb

## tests\prefabs\test_prefab_loader.py

### Functions
- test_prefab_lifecycle_and_db_integration
- test_create_prefab_outside_project_raises_error
- test_instantiate_prefab_no_duplication

## tests\prefabs\test_prefab_serializer.py

### Functions
- test_serialize_and_deserialize_simple_object

## tests\runtime\test_input_system.py

### Functions
- _empty_editor_scene
- _add_script_object
- _write_input_script
- _read_events
- test_key_pressed_down_and_released_states_last_one_frame
- test_mouse_pressed_down_released_position_and_delta
- test_multiple_keys_can_be_held_simultaneously
- test_input_api_is_inactive_outside_play
- test_runtime_manager_updates_input_before_scripts
- test_runtime_manager_clears_input_after_stop
- test_runtime_manager_ignores_input_events_when_not_playing

## tests\runtime\test_physics_runtime.py

### Classes
- TriggerProbe

### Functions
- _empty_editor_scene
- _add_object
- setup_function
- teardown_function
- test_physics_world_registers_and_unregisters_rigidbody
- test_physics_world_registers_and_unregisters_collider
- test_physics_world_detects_box_box_collision
- test_physics_world_detects_circle_circle_collision
- test_physics_world_detects_box_circle_collision
- test_trigger_enter_and_exit_are_emitted
- test_runtime_builds_physics_world_from_runtime_scene_and_cleans_on_stop
- test_runtime_physics_uses_fixed_delta_time_and_does_not_modify_editor_world
- test_runtime_physics_detects_trigger_contacts_between_clones_only

## tests\runtime\test_play_mode_foundation.py

### Functions
- _editor_scene_with_object
- test_clone_game_object_is_deep_and_independent
- test_runtime_scene_clones_editor_scene_and_maps_selection
- test_runtime_manager_start_stop_lifecycle

## tests\runtime\test_runtime_lifecycle.py

### Classes
- LifecycleProbe

### Functions
- _empty_editor_scene
- _add_probe_object
- setup_function
- test_tick_without_play_does_nothing
- test_start_calls_runtime_start_once_and_play_twice_does_not_duplicate
- test_tick_calls_runtime_update_only_while_playing
- test_stop_calls_runtime_stop_and_destroys_scene
- test_stop_twice_is_safe
- test_disabled_components_do_not_receive_lifecycle
- test_inactive_game_objects_do_not_receive_lifecycle
- test_inactive_parent_blocks_child_lifecycle
- test_multiple_components_receive_update
- test_editor_scene_is_not_modified_by_runtime_lifecycle
- test_play_tick_stop_sequence_is_safe

## tests\runtime\test_script_runtime.py

### Functions
- _empty_editor_scene
- _add_script_object
- _write_script
- _read_events
- test_script_runtime_loads_script_and_binds_runtime_context
- test_script_lifecycle_awake_start_update_destroy
- test_multiple_game_objects_get_separate_script_instances
- test_script_update_error_disables_only_failed_component
- test_script_instances_are_cleared_on_stop
- test_scripts_do_not_execute_outside_play
- test_scripts_modify_only_runtime_world

## tests\runtime\test_time_system.py

### Classes
- TimeProbe

### Functions
- _empty_editor_scene
- _add_probe_object
- _write_script
- _read_events
- setup_function
- teardown_function
- test_time_defaults_and_fixed_delta_time
- test_tick_without_play_does_not_advance_time
- test_runtime_tick_updates_scaled_and_unscaled_time
- test_multiple_ticks_accumulate_time_and_frames
- test_time_scale_zero_pauses_scaled_delta_but_runtime_still_ticks
- test_time_scale_above_one_speeds_scaled_time
- test_time_scale_below_one_slows_scaled_time
- test_stop_resets_runtime_time_state
- test_new_play_session_starts_with_clean_time_state
- test_script_behaviour_can_read_time_api

## tests\scene\test_scene_serialization.py

### Functions
- _component_by_class_name
- test_serialize_and_load_empty_scene
- test_serialize_scene_with_object_transform
- test_deserialize_game_object_restores_transform_and_identity
- test_serialize_and_deserialize_collider_and_rigidbody
- test_circle_collider_round_trip

## tests\test_assets.py

### Classes
- _FakeSurface
- TestMeshInit
- TestGetImage
- TestLoadSpriteSheet
- TestGetSound
- TestPlayMusic
- TestGetFont
- TestGetMesh
- TestCreateCubeMesh

### Functions
- clean_cache

## tests\test_audio.py

### Classes
- _FakeMusic
- _FakeSound
- TestInit
- TestPlayMusic
- TestStopMusic
- TestPauseResumeMusic
- TestMusicVolume
- TestSfx
- TestMasterVolume
- TestGlobalControl
- TestUnloadCache

### Functions
- cleanup_pygame_mixer
- _build_mixer_stub
- reset_audio
- exists_true
- exists_false

## tests\test_event_bus.py

### Classes
- TestSubscribe
- TestUnsubscribe
- TestEmit
- TestOnce
- TestEmitDeferred
- TestClear
- TestRetrocompatInstance
- TestEdgeCases

### Functions
- bus

## tests\test_game_object.py

### Classes
- _Counter
- _Crasher
- _TypeA
- _TypeB
- TestInit
- TestComponents
- TestLifecycle
- TestHierarchy
- TestRepr

### Functions
- _go
- _screen

## tests\test_input.py

### Classes
- _FakeKeys
- TestGetKey
- TestGetKeyDown
- TestGetKeyUp
- TestMouse
- TestAxes
- TestUpdate

### Functions
- _build_pygame_stub
- reset_input
- _press
- _release

## tests\test_logger.py

### Classes
- TestLevelConstants
- TestSetLevel
- TestMessageFormat
- TestSilence
- TestFileOutput
- TestTaggedLogger

### Functions
- reset_logger
- _inject_file

## tests\test_runtime_lifecycle.py

### Classes
- _FakeScene
- TestCloneGameObject
- TestRuntimeManagerLifecycle
- TestEditorContextReset
- TestSceneSerializerRoundTrip
- TestPrefabSerializerRoundTrip

## tests\test_tilemap.py

### Functions
- dummy_surface
- test_tileset_initialization
- test_tilemap_component
- test_tilemap_serialization
- test_tilemap_renderer

## tests\test_time.py

### Classes
- _FakeClock
- TestInit
- TestTick
- TestScaledDelta
- TestElapsed
- TestPauseUnpause
- TestDtCap
- TestCurrent
- TestRepr

### Functions
- _build_pygame_stub
- reset_current
- t
- _tick

## tests\test_transitions.py

### Classes
- _FakeSurface
- TestEasing
- TestTransitionBase
- TestFadeTransition
- TestSlideTransition
- TestWipeTransition
- TestCrossfadeTransition
- TestPhaseLifecycle

### Functions
- _build_pygame_stub
- _advance
- _run_to_swap
- _run_to_done
- _fake_snap
- _stub_transition_pygame

## tests\tilemap\__init__.py

## tests\tilemap\conftest.py

## tests\tilemap\test_tilemap.py

### Classes
- _FakeSurface
- _FakeRect
- _StubTileset
- TestTileLayerInit
- TestTileLayerGetSetGid
- TestTileMapInit
- TestTileMapTilesets
- TestTileMapLayers
- TestCoordinates
- TestIsSolidAt
- TestGetSolidRectsInRegion
- TestBakeAndInvalidate
- TestDraw
- TestTilemapRenderer

### Functions
- _layer
- _map
- _tileset

## tests\ui\__init__.py

## tests\ui\test_button.py

### Classes
- _FakeRect
- _FakeTextSurf
- _FakeFont
- _FakeSurface
- TestButtonInit
- TestNaturalSize
- TestHandleEventMouseMotion
- TestHandleEventMouseDown
- TestHandleEventMouseUp
- TestUpdate
- TestLerpColor
- TestDrawSelf

### Functions
- reset_draw
- _screen
- _btn
- _event

## tests\ui\test_label.py

### Classes
- _FakeSurf
- _FakeFont
- _FakeScreen
- TestLabelInit
- TestSetText
- TestRebuild
- TestNaturalSize
- TestDrawSelf

### Functions
- reset_font_mock
- _screen
- _lbl

## tests\ui\test_progress_bar.py

### Classes
- _FakeRect
- _FakeSurf
- _FakeFont
- _FakeScreen
- TestInit
- TestRatio
- TestSetValue
- TestUpdate
- TestDrawSelf

### Functions
- reset_mocks
- _screen
- _bar

## tests\ui\test_ui_base.py

### Classes
- _FakeRect
- _FakeSurface
- TestAnchorEnum
- TestPivotEnum
- TestUIElementInit
- TestHierarchy
- TestGetRect
- TestContainsPoint
- TestVisibility
- TestHandleEvent
- TestUpdate
- TestRepr

### Functions
- _screen
- _elem

## tests\ui\test_ui_runtime_foundation.py

### Functions
- _empty_editor_scene
- _add
- test_canvas_component_creation
- test_label_and_button_component_creation
- test_ui_renderer_draws_label_after_canvas_exists
- test_ui_renderer_draws_image_placeholder_and_button
- test_ui_components_serialize_and_deserialize
- test_runtime_ui_is_isolated_and_hidden_from_world_draw

## tests\unit\test_asset_pipeline.py

### Functions
- test_importer_registry_resolves_correctly
- test_texture_importer_creates_meta
- test_importer_preserves_uuid_and_updates_settings
- test_audio_importer_creates_meta

## tests\unit\test_audio_system.py

### Functions
- mock_pygame_mixer
- clean_audio_manager
- test_audio_components_initialization
- test_audio_registration_and_removal
- test_audio_playback_controls
- test_audio_serialization_deserialization
- test_runtime_isolation_and_fallback
- test_runtime_listener_registry_ignores_stale_editor_listener

## tests\unit\test_camera_system.py

### Functions
- clean_camera_manager
- test_camera_component_initialization
- test_camera_registration_and_removal
- test_main_camera_static_shortcut
- test_camera_manager_set_main_camera
- test_camera_serialization_deserialization
- test_runtime_scene_camera_isolation_and_fallback

## tests\unit\test_game_object.py

### Classes
- DummyComponent

### Functions
- go
- child_go
- test_go_has_unique_id
- test_go_short_id_is_8_chars
- test_go_name
- test_go_tag_default
- test_go_tag_custom
- test_go_active_by_default
- test_go_repr
- test_go_has_transform_on_creation
- test_go_transform_default_position
- test_add_component_returns_component
- test_get_component_returns_correct_type
- test_get_component_returns_none_when_missing
- test_get_components_returns_all_of_type
- test_remove_component
- test_added_component_knows_its_game_object
- test_add_child
- test_remove_child
- test_reparenting_removes_from_old_parent
- test_update_calls_component_update
- test_inactive_go_skips_update
- test_destroy_deactivates_and_clears

## tests\unit\test_gizmo_system.py

### Functions
- test_gizmo_registry_and_resolution
- test_camera_gizmo_rendering
- test_box_collider_gizmo_rendering
- test_circle_collider_gizmo_rendering
- test_audio_gizmos_rendering

## tests\unit\test_package_manager.py

### Functions
- temp_project_dir
- create_dummy_package
- test_package_load_and_validate_success
- test_package_invalid_json
- test_package_missing_fields
- test_package_manager_install_uninstall
- test_package_manager_update

## tests\unit\test_transform.py

### Functions
- go_with_transform
- test_transform_default_position
- test_transform_default_rotation
- test_transform_default_scale
- test_transform_set_x
- test_transform_set_y
- test_transform_set_position_array
- test_transform_set_rz
- test_transform_set_rotation_array
- test_transform_set_sx
- test_transform_set_scale_array
- test_transform_translate_2d
- test_transform_translate_preserves_z
- test_transform_rotate
- test_transform_rotate_accumulates
- test_transform_position_is_float32
- test_transform_scale_is_float32
- test_world_position_no_parent
- test_world_position_with_parent
- test_transform_repr_contains_go_name

## tools\ai_bundle.py

## tools\analyze_project.py

## tools\architecture_report.py

## tools\dashboard.py

## tools\dependency_graph.py

## tools\generate_ai_context.py

### Functions
- run
- save

## venv\Lib\site-packages\PySide6\QtAsyncio\__init__.py

### Functions
- run

## venv\Lib\site-packages\PySide6\QtAsyncio\events.py

### Classes
- QAsyncioExecutorWrapper
- QAsyncioEventLoopPolicy
- QAsyncioEventLoop
- QAsyncioHandle
- QAsyncioTimerHandle

## venv\Lib\site-packages\PySide6\QtAsyncio\futures.py

### Classes
- QAsyncioFuture

## venv\Lib\site-packages\PySide6\QtAsyncio\tasks.py

### Classes
- QAsyncioTask

## venv\Lib\site-packages\PySide6\__init__.py

### Classes
- ModuleDict
- SubModule

### Functions
- _additional_dll_directories
- _setupQtDirectories
- _find_all_qt_modules
- __getattr__

## venv\Lib\site-packages\PySide6\_config.py

## venv\Lib\site-packages\PySide6\_git_pyside_version.py

## venv\Lib\site-packages\PySide6\scripts\__init__.py

## venv\Lib\site-packages\PySide6\scripts\deploy.py

### Functions
- main

## venv\Lib\site-packages\PySide6\scripts\deploy_lib\__init__.py

### Functions
- get_all_pyside_modules

## venv\Lib\site-packages\PySide6\scripts\deploy_lib\commands.py

### Functions
- run_command
- run_qmlimportscanner

## venv\Lib\site-packages\PySide6\scripts\deploy_lib\config.py

### Classes
- BaseConfig
- Config
- DesktopConfig

## venv\Lib\site-packages\PySide6\scripts\deploy_lib\dependency_util.py

### Classes
- QtDependencyReader

### Functions
- get_py_files
- get_ast
- find_permission_categories
- find_pyside_modules

## venv\Lib\site-packages\PySide6\scripts\deploy_lib\deploy_util.py

### Functions
- config_option_exists
- cleanup
- create_config_file
- finalize

## venv\Lib\site-packages\PySide6\scripts\deploy_lib\nuitka_helper.py

### Classes
- Nuitka

## venv\Lib\site-packages\PySide6\scripts\deploy_lib\python_helper.py

### Classes
- PythonExecutable

## venv\Lib\site-packages\PySide6\scripts\metaobjectdump.py

### Classes
- VisitorContext
- MetaObjectDumpVisitor

### Functions
- _decorator
- _attribute
- _name
- _func_name
- _python_to_cpp_type
- _parse_property_kwargs
- _parse_assignment
- _parse_pyside_type
- _parse_call_args
- _parse_slot
- create_arg_parser
- parse_file

## venv\Lib\site-packages\PySide6\scripts\project.py

### Classes
- Project

### Functions
- _sort_sources
- main

## venv\Lib\site-packages\PySide6\scripts\project_lib\__init__.py

### Classes
- Singleton
- ClOptions

## venv\Lib\site-packages\PySide6\scripts\project_lib\design_studio_project.py

### Classes
- DesignStudioProject

## venv\Lib\site-packages\PySide6\scripts\project_lib\newproject.py

### Classes
- NewProjectType
- NewProjectTypes

### Functions
- _write_project
- _widget_project
- _ui_form_project
- _qml_project
- new_project

## venv\Lib\site-packages\PySide6\scripts\project_lib\project_data.py

### Classes
- ProjectData
- QmlProjectData

### Functions
- is_python_file
- _has_qml_decorated_class
- check_qml_decorators

## venv\Lib\site-packages\PySide6\scripts\project_lib\pyproject_json.py

### Functions
- write_pyproject_json
- parse_pyproject_json

## venv\Lib\site-packages\PySide6\scripts\project_lib\pyproject_parse_result.py

### Classes
- PyProjectParseResult

## venv\Lib\site-packages\PySide6\scripts\project_lib\pyproject_toml.py

### Functions
- _write_base_toml_content
- parse_pyproject_toml
- write_pyproject_toml
- robust_relative_to_posix
- migrate_pyproject

## venv\Lib\site-packages\PySide6\scripts\project_lib\utils.py

### Functions
- run_command
- qrc_file_requires_rebuild
- requires_rebuild
- _remove_path_recursion
- remove_path
- package_dir
- qtpaths
- qt_metatype_json_dir
- resolve_valid_project_file

## venv\Lib\site-packages\PySide6\scripts\pyside_tool.py

### Functions
- is_pyenv_python
- is_virtual_env
- init_virtual_env
- main
- qt_tool_wrapper
- pyside_script_wrapper
- ui_tool_binary
- lrelease
- lupdate
- uic
- rcc
- qmltyperegistrar
- qmlimportscanner
- qmlcachegen
- qmllint
- qmlformat
- qmlls
- assistant
- _extend_path_var
- designer
- linguist
- genpyi
- metaobjectdump
- _check_requirements
- project
- qml
- qtpy2cpp
- deploy
- android_deploy
- qsb
- balsam
- balsamui
- svgtoqml

## venv\Lib\site-packages\PySide6\scripts\qml.py

### Functions
- import_qml_modules
- print_configurations

## venv\Lib\site-packages\PySide6\scripts\qtpy2cpp.py

### Functions
- create_arg_parser

## venv\Lib\site-packages\PySide6\scripts\qtpy2cpp_lib\astdump.py

### Classes
- NodeType
- DumpVisitor

### Functions
- first_non_space
- get_node_type
- parse_ast
- create_arg_parser

## venv\Lib\site-packages\PySide6\scripts\qtpy2cpp_lib\formatter.py

### Classes
- Indenter
- CppFormatter

### Functions
- _fix_function_argument_type
- to_string
- format_inheritance
- format_for_target
- format_for_loop
- format_name_constant
- format_literal
- format_literal_list
- format_member
- format_reference
- format_function_def_arguments
- format_start_function_call
- write_import
- write_import_from

## venv\Lib\site-packages\PySide6\scripts\qtpy2cpp_lib\nodedump.py

### Functions
- to_string
- debug_format_node

## venv\Lib\site-packages\PySide6\scripts\qtpy2cpp_lib\qt.py

### Classes
- ClassFlag

### Functions
- qt_class_flags

## venv\Lib\site-packages\PySide6\scripts\qtpy2cpp_lib\tokenizer.py

### Functions
- format_token
- first_non_space

## venv\Lib\site-packages\PySide6\scripts\qtpy2cpp_lib\visitor.py

### Classes
- ConvertVisitor

### Functions
- _is_qt_constructor
- _is_if_main

## venv\Lib\site-packages\PySide6\support\__init__.py

## venv\Lib\site-packages\PySide6\support\deprecated.py

## venv\Lib\site-packages\PySide6\support\generate_pyi.py

### Functions
- generate_all_pyi

## venv\Lib\site-packages\_pytest\__init__.py

## venv\Lib\site-packages\_pytest\_argcomplete.py

### Classes
- FastFilesCompleter

## venv\Lib\site-packages\_pytest\_code\__init__.py

## venv\Lib\site-packages\_pytest\_code\code.py

### Classes
- Code
- Frame
- TracebackEntry
- Traceback
- ExceptionInfo
- ExceptionInfoFormatter
- TerminalRepr
- ExceptionRepr
- ExceptionChainRepr
- ReprExceptionInfo
- ReprTraceback
- ReprTracebackNative
- ReprEntryNative
- ReprEntry
- ReprFileLocation
- ReprLocals
- ReprFuncArgs

### Functions
- stringify_exception
- getfslineno
- _byte_offset_to_character_offset
- filter_traceback
- filter_excinfo_traceback

## venv\Lib\site-packages\_pytest\_code\source.py

### Classes
- Source

### Functions
- findsource
- getrawcode
- deindent
- get_statement_startend2
- getstatementrange_ast

## venv\Lib\site-packages\_pytest\_io\__init__.py

## venv\Lib\site-packages\_pytest\_io\pprint.py

### Classes
- _safe_key
- PrettyPrinter

### Functions
- _safe_tuple
- _recursion
- _wrap_bytes_repr

## venv\Lib\site-packages\_pytest\_io\saferepr.py

### Classes
- SafeRepr

### Functions
- _try_repr_or_str
- _format_repr_exception
- _ellipsize
- safeformat
- saferepr
- saferepr_unlimited

## venv\Lib\site-packages\_pytest\_io\terminalwriter.py

### Classes
- TerminalWriter

### Functions
- get_terminal_width
- should_do_markup

## venv\Lib\site-packages\_pytest\_io\wcwidth.py

### Functions
- wcwidth
- wcswidth

## venv\Lib\site-packages\_pytest\_py\__init__.py

## venv\Lib\site-packages\_pytest\_py\error.py

### Classes
- Error
- ErrorMaker

### Functions
- __getattr__

## venv\Lib\site-packages\_pytest\_py\path.py

### Classes
- Checkers
- NeverRaised
- Visitor
- FNMatcher
- Stat
- LocalPath

### Functions
- map_as_list
- getuserid
- getgroupid
- copymode
- copystat
- copychunked
- isimportable

## venv\Lib\site-packages\_pytest\_version.py

## venv\Lib\site-packages\_pytest\assertion\__init__.py

### Classes
- RewriteHook
- DummyRewriteHook
- AssertionState

### Functions
- pytest_addoption
- pytest_configure
- register_assert_rewrite
- install_importhook
- pytest_collection
- pytest_runtest_protocol
- pytest_sessionfinish
- pytest_assertrepr_compare

## venv\Lib\site-packages\_pytest\assertion\_compare_any.py

### Functions
- _compare_eq_any
- _compare_eq_cls

## venv\Lib\site-packages\_pytest\assertion\_compare_mapping.py

### Functions
- _compare_eq_mapping

## venv\Lib\site-packages\_pytest\assertion\_compare_sequence.py

### Functions
- _compare_eq_iterable
- _compare_eq_sequence

## venv\Lib\site-packages\_pytest\assertion\_compare_set.py

### Functions
- _set_one_sided_diff
- _compare_eq_set
- _compare_gte_set
- _compare_lte_set
- _compare_gt_set
- _compare_lt_set
- _both_sets_are_equal

## venv\Lib\site-packages\_pytest\assertion\_guards.py

### Functions
- issequence
- istext
- ismapping
- isset
- isnamedtuple
- isattrs
- isiterable
- has_default_eq

## venv\Lib\site-packages\_pytest\assertion\_typing.py

### Classes
- _HighlightFunc

## venv\Lib\site-packages\_pytest\assertion\compare_text.py

### Functions
- _compare_eq_text
- _diff_text_block
- _format_text_block_lines
- _diff_text
- _notin_text

## venv\Lib\site-packages\_pytest\assertion\highlight.py

### Functions
- dummy_highlighter

## venv\Lib\site-packages\_pytest\assertion\rewrite.py

### Classes
- Sentinel
- AssertionRewritingHook
- AssertionRewriter

### Functions
- _write_pyc_fp
- _write_pyc
- _rewrite_test
- _read_pyc
- rewrite_asserts
- _saferepr
- _get_maxsize_for_saferepr
- _format_assertmsg
- _should_repr_global_name
- _format_boolop
- _call_reprcompare
- _call_assertion_pass
- _check_if_assertion_pass_impl
- traverse_node
- _get_assertion_exprs
- try_makedirs
- get_cache_dir

## venv\Lib\site-packages\_pytest\assertion\truncate.py

### Functions
- truncate_if_required
- _get_truncation_parameters
- _truncate_explanation
- _truncate_by_char_count

## venv\Lib\site-packages\_pytest\assertion\util.py

### Functions
- get_assertion_text_diff_style
- validate_assertion_text_diff_style
- format_explanation
- _split_explanation
- _format_lines
- assertrepr_compare

## venv\Lib\site-packages\_pytest\cacheprovider.py

### Classes
- Cache
- LFPluginCollWrapper
- LFPluginCollSkipfiles
- LFPlugin
- NFPlugin

### Functions
- _make_cachedir
- pytest_addoption
- pytest_cmdline_main
- pytest_configure
- cache
- pytest_report_header
- cacheshow

## venv\Lib\site-packages\_pytest\capture.py

### Classes
- EncodedFile
- CaptureIO
- TeeCaptureIO
- DontReadFromInput
- CaptureBase
- NoCapture
- SysCaptureBase
- SysCaptureBinary
- SysCapture
- FDCaptureBase
- FDCaptureBinary
- FDCapture
- MultiCapture
- CaptureManager
- CaptureFixture

### Functions
- pytest_addoption
- _colorama_workaround
- _readline_workaround
- _windowsconsoleio_workaround
- pytest_load_initial_conftests
- _get_multicapture
- capsys
- capteesys
- capsysbinary
- capfd
- capfdbinary

## venv\Lib\site-packages\_pytest\compat.py

### Classes
- NotSetType
- CallableBool

### Functions
- legacy_path
- iscoroutinefunction
- is_async_function
- signature
- getlocation
- num_mock_patch_args
- getfuncargnames
- get_default_arg_names
- ascii_escaped
- get_real_func
- getimfunc
- safe_getattr
- safe_isclass
- get_user_id
- running_on_ci

## venv\Lib\site-packages\_pytest\config\__init__.py

### Classes
- ExitCode
- ConftestImportFailure
- cmdline
- PytestPluginManager
- _DeprecatedInicfgProxy
- Config

### Functions
- filter_traceback_for_conftest_import_failure
- print_conftest_import_error
- print_usage_error
- _get_prog_name
- main
- _main
- _console_main
- console_main
- filename_arg
- directory_arg
- get_config
- get_plugin_manager
- _prepareconfig
- _get_directory
- _get_legacy_hook_marks
- _get_plugin_specs_as_list
- _iter_rewritable_modules
- _assertion_supported
- create_terminal_writer
- _strtobool
- parse_warning_filter
- _resolve_warning_category
- apply_warning_filters

## venv\Lib\site-packages\_pytest\config\argparsing.py

### Classes
- Parser
- Argument
- OptionGroup
- PytestArgumentParser
- DropShorterLongHelpFormatter
- OverrideIniAction

### Functions
- get_ini_default_for_type

## venv\Lib\site-packages\_pytest\config\exceptions.py

### Classes
- UsageError
- PrintHelp

## venv\Lib\site-packages\_pytest\config\findpaths.py

### Classes
- ConfigValue

### Functions
- _parse_ini_config
- load_config_dict_from_file
- locate_config
- get_common_ancestor
- get_dirs_from_args
- parse_override_ini
- determine_setup
- is_fs_root

## venv\Lib\site-packages\_pytest\debugging.py

### Classes
- pytestPDB
- PdbInvoke
- PdbTrace

### Functions
- _validate_usepdb_cls
- pytest_addoption
- pytest_configure
- wrap_pytest_function_for_tracing
- maybe_wrap_pytest_function_for_tracing
- _enter_pdb
- _postmortem_exc_or_tb
- post_mortem

## venv\Lib\site-packages\_pytest\deprecated.py

### Functions
- check_ispytest

## venv\Lib\site-packages\_pytest\doctest.py

### Classes
- ReprFailDoctest
- MultipleDoctestFailures
- DoctestItem
- DoctestTextfile
- DoctestModule

### Functions
- pytest_addoption
- pytest_unconfigure
- pytest_collect_file
- _is_setup_py
- _is_doctest
- _is_main_py
- _init_runner_class
- _get_runner
- _get_flag_lookup
- get_optionflags
- _get_continue_on_failure
- _check_all_skipped
- _is_mocked
- _patch_unwrap_mock_aware
- _init_checker_class
- _get_checker
- _get_allow_unicode_flag
- _get_allow_bytes_flag
- _get_number_flag
- _get_report_choice
- doctest_namespace

## venv\Lib\site-packages\_pytest\faulthandler.py

### Functions
- pytest_addoption
- pytest_configure
- pytest_unconfigure
- get_stderr_fileno
- get_timeout_config_value
- get_exit_on_timeout_config_value
- pytest_runtest_protocol
- pytest_enter_pdb
- pytest_exception_interact

## venv\Lib\site-packages\_pytest\fixtures.py

### Classes
- ParamArgKey
- FuncFixtureInfo
- FixtureRequest
- TopRequest
- SubRequest
- FixtureLookupError
- FixtureLookupErrorRepr
- FixtureDef
- RequestFixtureDef
- FixtureFunctionMarker
- FixtureFunctionDefinition
- FixtureManager

### Functions
- pytest_sessionstart
- get_scope_package
- is_visibility_more_specific
- get_scope_node
- getfixturemarker
- get_param_argkeys
- reorder_items
- reorder_items_atscope
- traverse_fixture_closure
- call_fixture_func
- _teardown_yield_fixture
- _eval_scope_callable
- resolve_fixture_function
- pytest_fixture_setup
- fixture
- fixture
- fixture
- yield_fixture
- pytestconfig
- pytest_addoption
- pytest_cmdline_main
- _resolve_args_directness
- _get_direct_parametrize_args
- deduplicate_names
- show_fixtures_per_test
- _pretty_fixture_path
- _get_fixtures_per_test
- _show_fixtures_per_test
- showfixtures
- _showfixtures_main
- write_docstring
- register_fixture

## venv\Lib\site-packages\_pytest\freeze_support.py

### Functions
- freeze_includes
- _iter_all_modules

## venv\Lib\site-packages\_pytest\helpconfig.py

### Classes
- HelpAction

### Functions
- pytest_addoption
- pytest_cmdline_parse
- show_version_verbose
- pytest_cmdline_main
- showhelp
- getpluginversioninfo
- pytest_report_header

## venv\Lib\site-packages\_pytest\hookspec.py

### Functions
- pytest_addhooks
- pytest_plugin_registered
- pytest_addoption
- pytest_configure
- pytest_cmdline_parse
- pytest_load_initial_conftests
- pytest_cmdline_main
- pytest_collection
- pytest_collection_modifyitems
- pytest_collection_finish
- pytest_ignore_collect
- pytest_collect_directory
- pytest_collect_file
- pytest_collectstart
- pytest_itemcollected
- pytest_collectreport
- pytest_deselected
- pytest_make_collect_report
- pytest_pycollect_makemodule
- pytest_pycollect_makeitem
- pytest_pyfunc_call
- pytest_generate_tests
- pytest_make_parametrize_id
- pytest_runtestloop
- pytest_runtest_protocol
- pytest_runtest_logstart
- pytest_runtest_logfinish
- pytest_runtest_setup
- pytest_runtest_call
- pytest_runtest_teardown
- pytest_runtest_makereport
- pytest_runtest_logreport
- pytest_report_to_serializable
- pytest_report_from_serializable
- pytest_fixture_setup
- pytest_fixture_post_finalizer
- pytest_sessionstart
- pytest_sessionfinish
- pytest_unconfigure
- pytest_assertrepr_compare
- pytest_assertion_pass
- pytest_report_header
- pytest_report_collectionfinish
- pytest_report_teststatus
- pytest_terminal_summary
- pytest_warning_recorded
- pytest_markeval_namespace
- pytest_internalerror
- pytest_keyboard_interrupt
- pytest_exception_interact
- pytest_enter_pdb
- pytest_leave_pdb

## venv\Lib\site-packages\_pytest\junitxml.py

### Classes
- _NodeReporter
- LogXML

### Functions
- bin_xml_escape
- merge_family
- _warn_incompatibility_with_xunit2
- record_property
- record_xml_attribute
- _check_record_param_type
- record_testsuite_property
- pytest_addoption
- pytest_configure
- pytest_unconfigure
- mangle_test_address

## venv\Lib\site-packages\_pytest\legacypath.py

### Classes
- Testdir
- LegacyTestdirPlugin
- TempdirFactory
- LegacyTmpdirPlugin

### Functions
- Cache_makedir
- FixtureRequest_fspath
- TerminalReporter_startdir
- Config_invocation_dir
- Config_rootdir
- Config_inifile
- Session_startdir
- Config__getini_unknown_type
- Node_fspath
- Node_fspath_set
- pytest_load_initial_conftests
- pytest_configure
- pytest_plugin_registered

## venv\Lib\site-packages\_pytest\logging.py

### Classes
- DatetimeFormatter
- ColoredLevelFormatter
- PercentStyleMultiline
- catching_logs
- LogCaptureHandler
- LogCaptureFixture
- LoggingPlugin
- _FileHandler
- _LiveLoggingStreamHandler
- _LiveLoggingNullHandler

### Functions
- _remove_ansi_escape_sequences
- get_option_ini
- pytest_addoption
- caplog
- get_log_level_for_setting
- pytest_configure

## venv\Lib\site-packages\_pytest\main.py

### Classes
- FSHookProxy
- Interrupted
- Failed
- _bestrelpath_cache
- Dir
- Session
- CollectionArgument

### Functions
- pytest_addoption
- validate_basetemp
- wrap_session
- pytest_cmdline_main
- _main
- pytest_collection
- pytest_runtestloop
- _in_venv
- pytest_ignore_collect
- pytest_collect_directory
- pytest_collection_modifyitems
- search_pypath
- resolve_collection_argument
- is_collection_argument_subsumed_by
- normalize_collection_arguments

## venv\Lib\site-packages\_pytest\mark\__init__.py

### Classes
- KeywordMatcher
- MarkMatcher

### Functions
- param
- pytest_addoption
- pytest_cmdline_main
- deselect_by_keyword
- deselect_by_mark
- _parse_expression
- pytest_collection_modifyitems
- pytest_configure
- pytest_unconfigure

## venv\Lib\site-packages\_pytest\mark\expression.py

### Classes
- TokenType
- Token
- Scanner
- ExpressionMatcher
- MatcherNameAdapter
- MatcherAdapter
- Expression

### Functions
- expression
- expr
- and_expr
- not_expr
- single_kwarg
- all_kwargs

## venv\Lib\site-packages\_pytest\mark\structures.py

### Classes
- _HiddenParam
- ParameterSet
- Mark
- MarkDecorator
- MarkGenerator
- NodeKeywords

### Functions
- istestfunc
- get_empty_parameterset_mark
- get_unpacked_marks
- normalize_mark_list
- store_mark

## venv\Lib\site-packages\_pytest\monkeypatch.py

### Classes
- MonkeyPatch

### Functions
- monkeypatch
- resolve
- annotated_getattr
- derive_importpath

## venv\Lib\site-packages\_pytest\nodes.py

### Classes
- NodeMeta
- Node
- Collector
- FSCollector
- File
- Directory
- Item

### Functions
- norm_sep
- get_fslocation_from_item
- _check_initialpaths_for_relpath

## venv\Lib\site-packages\_pytest\outcomes.py

### Classes
- OutcomeException
- Skipped
- Failed
- Exit
- XFailed
- _Exit
- _Skip
- _Fail
- _XFail

### Functions
- importorskip

## venv\Lib\site-packages\_pytest\pastebin.py

### Functions
- pytest_addoption
- pytest_configure
- pytest_unconfigure
- create_new_paste
- pytest_terminal_summary

## venv\Lib\site-packages\_pytest\pathlib.py

### Classes
- ImportMode
- ImportPathMismatchError
- CouldNotResolvePathError

### Functions
- _ignore_error
- get_lock_path
- on_rm_rf_error
- ensure_extended_length_path
- get_extended_length_path_str
- rm_rf
- find_prefixed
- extract_suffixes
- find_suffixes
- parse_num
- _force_symlink
- make_numbered_dir
- create_cleanup_lock
- register_cleanup_lock_removal
- maybe_delete_a_numbered_dir
- ensure_deletable
- try_cleanup
- cleanup_candidates
- cleanup_dead_symlinks
- cleanup_numbered_dir
- make_numbered_dir_with_cleanup
- resolve_from_str
- fnmatch_ex
- parts
- symlink_or_skip
- import_path
- _import_module_using_spec
- spec_matches_module_path
- module_name_from_path
- insert_missing_modules
- resolve_package_path
- resolve_pkg_root_and_module_name
- is_importable
- compute_module_name
- scandir
- visit
- absolutepath
- commonpath
- bestrelpath
- safe_exists
- samefile_nofollow

## venv\Lib\site-packages\_pytest\pytester.py

### Classes
- LsofFdLeakChecker
- PytestArg
- RecordedHookCall
- HookRecorder
- RunResult
- SysModulesSnapshot
- SysPathsSnapshot
- Pytester
- LineComp
- LineMatcher

### Functions
- pytest_addoption
- pytest_configure
- _pytest
- get_public_names
- linecomp
- LineMatcher_fixture
- pytester
- _sys_snapshot
- _config_for_test

## venv\Lib\site-packages\_pytest\pytester_assertions.py

### Functions
- assertoutcome
- assert_outcomes

## venv\Lib\site-packages\_pytest\python.py

### Classes
- PyobjMixin
- _EmptyClass
- PyCollector
- Module
- Package
- Class
- IdMaker
- CallSpec2
- DirectParamFixtureDef
- Metafunc
- Function
- FunctionDefinition

### Functions
- pytest_addoption
- pytest_generate_tests
- pytest_configure
- async_fail
- pytest_pyfunc_call
- pytest_collect_directory
- pytest_collect_file
- path_matches_patterns
- pytest_pycollect_makemodule
- pytest_pycollect_makeitem
- importtestmodule
- _call_with_optional_argument
- _get_first_non_fixture_func
- hasinit
- hasnew
- get_direct_param_fixture_func
- _find_parametrized_scope
- _ascii_escaped_by_config

## venv\Lib\site-packages\_pytest\python_api.py

### Classes
- ApproxBase
- ApproxNumpy
- ApproxMapping
- ApproxSequenceLike
- ApproxScalar
- ApproxDecimal
- ApproxTimedelta

### Functions
- _compare_approx
- _recursive_sequence_map
- approx
- _is_sequence_like
- _as_numpy_array

## venv\Lib\site-packages\_pytest\raises.py

### Classes
- AbstractRaises
- RaisesExc
- RaisesGroup
- NotChecked
- ResultHolder

### Functions
- raises
- raises
- raises
- raises
- raises
- _match_pattern
- repr_callable
- backquote
- _exception_type_name
- _check_raw_type
- is_fully_escaped
- unescape
- possible_match

## venv\Lib\site-packages\_pytest\recwarn.py

### Classes
- WarningsRecorder
- WarningsChecker

### Functions
- recwarn
- deprecated_call
- deprecated_call
- deprecated_call
- warns
- warns
- warns

## venv\Lib\site-packages\_pytest\reports.py

### Classes
- BaseReport
- TestReport
- CollectReport
- CollectErrorRepr

### Functions
- getworkerinfoline
- _report_unserialization_failure
- _format_failed_longrepr
- _format_exception_group_all_skipped_longrepr
- pytest_report_to_serializable
- pytest_report_from_serializable
- _report_to_json
- _report_kwargs_from_json

## venv\Lib\site-packages\_pytest\runner.py

### Classes
- CallInfo
- SetupState

### Functions
- pytest_addoption
- pytest_terminal_summary
- pytest_sessionstart
- pytest_sessionfinish
- pytest_runtest_protocol
- runtestprotocol
- show_test_item
- pytest_runtest_setup
- pytest_runtest_call
- pytest_runtest_teardown
- _update_current_test_var
- pytest_report_teststatus
- call_and_report
- get_reraise_exceptions
- check_interactive_exception
- pytest_runtest_makereport
- pytest_make_collect_report
- collect_one_node

## venv\Lib\site-packages\_pytest\scope.py

### Classes
- Scope

## venv\Lib\site-packages\_pytest\setuponly.py

### Functions
- pytest_addoption
- pytest_fixture_setup
- pytest_fixture_post_finalizer
- _show_fixture_action
- pytest_cmdline_main

## venv\Lib\site-packages\_pytest\setupplan.py

### Functions
- pytest_addoption
- pytest_fixture_setup
- pytest_cmdline_main

## venv\Lib\site-packages\_pytest\skipping.py

### Classes
- Skip
- Xfail

### Functions
- pytest_addoption
- pytest_configure
- evaluate_condition
- evaluate_skip_marks
- evaluate_xfail_marks
- pytest_runtest_setup
- pytest_runtest_call
- pytest_runtest_makereport
- pytest_report_teststatus

## venv\Lib\site-packages\_pytest\stash.py

### Classes
- StashKey
- Stash

## venv\Lib\site-packages\_pytest\stepwise.py

### Classes
- StepwiseCacheInfo
- StepwisePlugin

### Functions
- pytest_addoption
- pytest_configure
- pytest_sessionfinish

## venv\Lib\site-packages\_pytest\subtests.py

### Classes
- SubtestContext
- SubtestReport
- Subtests
- _SubTestContextManager
- Captured
- CapturedLogs

### Functions
- pytest_addoption
- subtests
- capturing_output
- capturing_logs
- pytest_report_to_serializable
- pytest_report_from_serializable
- pytest_configure
- pytest_report_teststatus

## venv\Lib\site-packages\_pytest\terminal.py

### Classes
- MoreQuietAction
- TestShortLogReport
- WarningReport
- TerminalReporter
- TerminalProgressPlugin

### Functions
- pytest_addoption
- pytest_configure
- getreportopt
- pytest_report_teststatus
- _get_node_id_with_markup
- _format_trimmed
- _get_line_with_reprcrash_message
- _folded_skips
- pluralize
- _plugin_nameversions
- format_session_duration
- format_node_duration
- _get_raw_skip_reason

## venv\Lib\site-packages\_pytest\terminalprogress.py

### Functions
- pytest_configure

## venv\Lib\site-packages\_pytest\threadexception.py

### Classes
- ThreadExceptionMeta

### Functions
- collect_thread_exception
- cleanup
- thread_exception_hook
- pytest_configure
- pytest_runtest_setup
- pytest_runtest_call
- pytest_runtest_teardown

## venv\Lib\site-packages\_pytest\timing.py

### Classes
- Instant
- Duration
- MockTiming

## venv\Lib\site-packages\_pytest\tmpdir.py

### Classes
- TempPathFactory

### Functions
- get_user
- pytest_configure
- pytest_addoption
- tmp_path_factory
- _mk_tmp
- tmp_path
- pytest_sessionfinish
- pytest_runtest_makereport

## venv\Lib\site-packages\_pytest\tracemalloc.py

### Functions
- tracemalloc_message

## venv\Lib\site-packages\_pytest\unittest.py

### Classes
- UnitTestCase
- TestCaseFunction
- TwistedVersion

### Functions
- pytest_pycollect_makeitem
- pytest_runtest_makereport
- _is_skipped
- pytest_configure
- _get_twisted_version
- pytest_runtest_protocol
- _handle_twisted_exc_info

## venv\Lib\site-packages\_pytest\unraisableexception.py

### Classes
- UnraisableMeta

### Functions
- gc_collect_harder
- collect_unraisable
- cleanup
- unraisable_hook
- pytest_configure
- pytest_unconfigure
- pytest_runtest_setup
- pytest_runtest_call
- pytest_runtest_teardown

## venv\Lib\site-packages\_pytest\warning_types.py

### Classes
- PytestWarning
- PytestAssertRewriteWarning
- PytestCacheWarning
- PytestConfigWarning
- PytestCollectionWarning
- PytestDeprecationWarning
- PytestRemovedIn10Warning
- PytestExperimentalApiWarning
- PytestReturnNotNoneWarning
- PytestUnknownMarkWarning
- PytestUnraisableExceptionWarning
- PytestUnhandledThreadExceptionWarning
- UnformattedWarning
- PytestFDWarning

### Functions
- warn_explicit_for

## venv\Lib\site-packages\_pytest\warnings.py

### Functions
- catch_warnings_for_item
- warning_record_to_str
- pytest_runtest_protocol
- pytest_collection
- pytest_terminal_summary
- pytest_sessionfinish
- pytest_load_initial_conftests
- pytest_configure

## venv\Lib\site-packages\ast_serialize\__init__.py

## venv\Lib\site-packages\colorama\__init__.py

## venv\Lib\site-packages\colorama\ansi.py

### Classes
- AnsiCodes
- AnsiCursor
- AnsiFore
- AnsiBack
- AnsiStyle

### Functions
- code_to_chars
- set_title
- clear_screen
- clear_line

## venv\Lib\site-packages\colorama\ansitowin32.py

### Classes
- StreamWrapper
- AnsiToWin32

## venv\Lib\site-packages\colorama\initialise.py

### Functions
- _wipe_internal_state_for_tests
- reset_all
- init
- deinit
- just_fix_windows_console
- colorama_text
- reinit
- wrap_stream

## venv\Lib\site-packages\colorama\tests\__init__.py

## venv\Lib\site-packages\colorama\tests\ansi_test.py

### Classes
- AnsiTest

## venv\Lib\site-packages\colorama\tests\ansitowin32_test.py

### Classes
- StreamWrapperTest
- AnsiToWin32Test

## venv\Lib\site-packages\colorama\tests\initialise_test.py

### Classes
- InitTest
- JustFixWindowsConsoleTest

## venv\Lib\site-packages\colorama\tests\isatty_test.py

### Classes
- IsattyTest

### Functions
- is_a_tty

## venv\Lib\site-packages\colorama\tests\utils.py

### Classes
- StreamTTY
- StreamNonTTY

### Functions
- osname
- replace_by
- replace_original_by
- pycharm

## venv\Lib\site-packages\colorama\tests\winterm_test.py

### Classes
- WinTermTest

## venv\Lib\site-packages\colorama\win32.py

## venv\Lib\site-packages\colorama\winterm.py

### Classes
- WinColor
- WinStyle
- WinTerm

### Functions
- enable_vt_processing

## venv\Lib\site-packages\coverage\__init__.py

## venv\Lib\site-packages\coverage\__main__.py

## venv\Lib\site-packages\coverage\annotate.py

### Classes
- AnnotateReporter

## venv\Lib\site-packages\coverage\bytecode.py

### Classes
- ByteParser
- InstructionWalker

### Functions
- bytes_to_lines
- op_set
- branch_trails
- always_jumps

## venv\Lib\site-packages\coverage\cmdline.py

### Classes
- Opts
- CoverageOptionParser
- GlobalOptionParser
- MultiParaHelpFormatter
- CmdOptionParser
- CoverageScript

### Functions
- prep_help
- show_help
- unshell_list
- unglob_args
- main
- main_deprecated

## venv\Lib\site-packages\coverage\collector.py

### Classes
- Collector

## venv\Lib\site-packages\coverage\config.py

### Classes
- HandyConfigParser
- CoverageConfig

### Functions
- process_file_value
- abs_path_if_exists
- process_regexlist
- config_files_to_try
- read_coverage_config

## venv\Lib\site-packages\coverage\context.py

### Functions
- combine_context_switchers
- should_start_context_test_function
- qualname_from_frame

## venv\Lib\site-packages\coverage\control.py

### Classes
- Coverage

### Functions
- override_config
- process_startup
- _after_fork_in_child
- _prevent_sub_process_measurement

## venv\Lib\site-packages\coverage\core.py

### Classes
- Core

## venv\Lib\site-packages\coverage\data.py

### Classes
- DataFileClassifier

### Functions
- line_counts
- add_data_to_hash
- combinable_files
- hash_for_data_file
- combine_parallel_data
- debug_data_file
- sorted_lines

## venv\Lib\site-packages\coverage\debug.py

### Classes
- DebugControl
- NoDebugging
- DevNullDebug
- CwdTracker
- ProcessTracker
- PytestTracker
- DebugOutputFile

### Functions
- info_header
- info_formatter
- write_formatted_info
- exc_one_line
- short_filename
- short_filename
- short_filename
- file_summary
- short_stack
- dump_stack_frames
- clipped_repr
- short_id
- add_pid_and_tid
- auto_repr
- simplify
- ppformat
- pp
- filter_text
- log
- decorate_methods
- break_in_debugger
- show_calls
- relevant_environment_display

## venv\Lib\site-packages\coverage\disposition.py

### Classes
- FileDisposition

### Functions
- disposition_init
- disposition_debug_msg

## venv\Lib\site-packages\coverage\env.py

### Classes
- PYBEHAVIOR

### Functions
- debug_info

## venv\Lib\site-packages\coverage\exceptions.py

### Classes
- CoverageException
- ConfigError
- DataError
- NoDataError
- NoSource
- NoCode
- NotPython
- PluginError
- _ExceptionDuringRun
- CoverageWarning

## venv\Lib\site-packages\coverage\execfile.py

### Classes
- DummyLoader
- PyRunner

### Functions
- find_module
- run_python_module
- run_python_file
- make_code_from_py
- make_code_from_pyc

## venv\Lib\site-packages\coverage\files.py

### Classes
- Matcher
- TreeMatcher
- ModuleMatcher
- GlobMatcher
- PathAliases

### Functions
- set_relative_directory
- relative_directory
- relative_filename
- canonical_filename
- flat_rootname
- abs_file
- zip_location
- source_exists
- python_reported_file
- isabs_anywhere
- prep_patterns
- sep
- _glob_to_regex
- globs_to_regex
- find_python_files

## venv\Lib\site-packages\coverage\html.py

### Classes
- LineData
- FileData
- IndexItem
- IndexPage
- HtmlDataGeneration
- FileToReport
- HtmlReporter
- FileInfo
- IncrementalChecker

### Functions
- data_filename
- read_data
- write_html
- encode_int
- copy_with_cache_bust
- escape
- pair
- pretty_file

## venv\Lib\site-packages\coverage\inorout.py

### Classes
- DirectoryDetail
- InOrOut

### Functions
- canonical_path
- name_for_module
- module_is_namespace
- module_has_file
- file_and_path_for_module
- _add_sysconfig_paths
- _add_stdlib_paths
- _add_third_party_paths
- _add_coverage_paths
- _analyze_directory
- _dir_detail

## venv\Lib\site-packages\coverage\jsonreport.py

### Classes
- JsonReporter

### Functions
- _convert_branch_arcs

## venv\Lib\site-packages\coverage\lcovreport.py

### Classes
- LcovReporter

### Functions
- line_hash
- lcov_lines
- lcov_functions
- lcov_arcs

## venv\Lib\site-packages\coverage\misc.py

### Classes
- SysModuleSaver
- Hasher
- DefaultValue

### Functions
- isolate_module
- sys_modules_saved
- import_third_party
- nice_pair
- bool_or_none
- join_regex
- file_be_gone
- ensure_dir
- ensure_dir_for_file
- _needs_to_implement
- substitute_variables
- format_local_datetime
- import_local_file
- _human_key
- human_sorted
- human_sorted_items
- plural
- stdout_link

## venv\Lib\site-packages\coverage\multiproc.py

### Classes
- ProcessWithCoverage
- Stowaway

### Functions
- patch_multiprocessing

## venv\Lib\site-packages\coverage\numbits.py

### Functions
- nums_to_numbits
- numbits_to_nums
- numbits_union
- numbits_intersection
- numbits_any_intersection
- num_in_numbits
- register_sqlite_functions

## venv\Lib\site-packages\coverage\parser.py

### Classes
- PythonParser
- ArcStart
- TAddArcFn
- Block
- LoopBlock
- FunctionBlock
- TryBlock
- AstArcAnalyzer

### Functions
- is_constant_test_expr

## venv\Lib\site-packages\coverage\patch.py

### Functions
- apply_patches
- _patch__exit
- _patch_execv
- _patch_fork
- _patch_subprocess

## venv\Lib\site-packages\coverage\phystokens.py

### Functions
- _phys_tokens
- find_soft_key_lines
- source_token_lines
- generate_tokens
- source_encoding

## venv\Lib\site-packages\coverage\plugin.py

### Classes
- CoveragePlugin
- CoveragePluginBase
- FileTracer
- CodeRegion
- FileReporter

## venv\Lib\site-packages\coverage\plugin_support.py

### Classes
- Plugins
- LabelledDebug
- DebugPluginWrapper
- DebugFileTracerWrapper
- DebugFileReporterWrapper

## venv\Lib\site-packages\coverage\pth_file.py

## venv\Lib\site-packages\coverage\python.py

### Classes
- PythonFileReporter

### Functions
- read_python_source
- get_python_source
- get_zip_bytes
- source_for_file
- source_for_morf

## venv\Lib\site-packages\coverage\pytracer.py

### Classes
- PyTracer

## venv\Lib\site-packages\coverage\regions.py

### Classes
- Context
- RegionFinder

### Functions
- code_regions

## venv\Lib\site-packages\coverage\report.py

### Classes
- SummaryReporter

### Functions
- escape_markdown

## venv\Lib\site-packages\coverage\report_core.py

### Classes
- Reporter

### Functions
- render_report
- get_analysis_to_report

## venv\Lib\site-packages\coverage\results.py

### Classes
- Analysis
- AnalysisNarrower
- Numbers

### Functions
- analysis_from_file_reporter
- display_covered
- _line_ranges
- format_lines
- should_fail_under

## venv\Lib\site-packages\coverage\sqldata.py

### Classes
- NumbitsUnionAgg
- CoverageData

### Functions
- _locked
- filename_suffix
- filename_match
- good_filename_match

## venv\Lib\site-packages\coverage\sqlitedb.py

### Classes
- SqliteDb

## venv\Lib\site-packages\coverage\sysmon.py

### Classes
- CodeInfo
- SysMonitor

### Functions
- get_multiline_map

## venv\Lib\site-packages\coverage\templite.py

### Classes
- TempliteSyntaxError
- TempliteValueError
- CodeBuilder
- Templite

## venv\Lib\site-packages\coverage\tomlconfig.py

### Classes
- TomlDecodeError
- TomlConfigParser

## venv\Lib\site-packages\coverage\types.py

### Classes
- TTraceFn
- TFileDisposition
- Tracer
- TConfigurable
- TPluginConfig
- TWarnFn
- TDebugCtl
- TWritable

## venv\Lib\site-packages\coverage\version.py

### Functions
- _make_version

## venv\Lib\site-packages\coverage\xmlreport.py

### Classes
- PackageData
- XmlReporter

### Functions
- rate
- appendChild
- serialize_xml

## venv\Lib\site-packages\dotenv\__init__.py

### Functions
- load_ipython_extension
- get_cli_string

## venv\Lib\site-packages\dotenv\__main__.py

## venv\Lib\site-packages\dotenv\cli.py

### Functions
- enumerate_env
- cli
- stream_file
- list_values
- set_value
- get
- unset
- run
- run_command

## venv\Lib\site-packages\dotenv\ipython.py

### Classes
- IPythonDotEnv

### Functions
- load_ipython_extension

## venv\Lib\site-packages\dotenv\main.py

### Classes
- DotEnv

### Functions
- _load_dotenv_disabled
- with_warn_for_invalid_lines
- get_key
- rewrite
- set_key
- unset_key
- resolve_variables
- _walk_to_root
- find_dotenv
- load_dotenv
- dotenv_values
- _is_file_or_fifo

## venv\Lib\site-packages\dotenv\parser.py

### Classes
- Original
- Binding
- Position
- Error
- Reader

### Functions
- make_regex
- decode_escapes
- parse_key
- parse_unquoted_value
- parse_value
- parse_binding
- parse_stream

## venv\Lib\site-packages\dotenv\variables.py

### Classes
- Atom
- Literal
- Variable

### Functions
- parse_variables

## venv\Lib\site-packages\dotenv\version.py

## venv\Lib\site-packages\iniconfig\__init__.py

### Classes
- SectionWrapper
- IniConfig

## venv\Lib\site-packages\iniconfig\_parse.py

### Classes
- ParsedLine

### Functions
- parse_ini_data
- parse_lines
- _parseline
- iscommentline

## venv\Lib\site-packages\iniconfig\_version.py

## venv\Lib\site-packages\iniconfig\exceptions.py

### Classes
- ParseError

## venv\Lib\site-packages\mypy\__init__.py

## venv\Lib\site-packages\mypy\__main__.py

### Functions
- console_entry

## venv\Lib\site-packages\mypy\api.py

### Functions
- _run
- run
- run_dmypy

## venv\Lib\site-packages\mypy\applytype.py

### Classes
- PolyTranslationError
- PolyTranslator

### Functions
- get_target_type
- apply_generic_arguments
- apply_poly

## venv\Lib\site-packages\mypy\argmap.py

### Classes
- ArgTypeExpander

### Functions
- map_actuals_to_formals
- map_formals_to_actuals

## venv\Lib\site-packages\mypy\binder.py

### Classes
- CurrentType
- Frame
- FrameContext
- ConditionalTypeBinder

### Functions
- get_declaration
- collapse_variadic_union

## venv\Lib\site-packages\mypy\bogus_type.py

## venv\Lib\site-packages\mypy\build.py

### Classes
- SCC
- BuildResult
- WorkerClient
- FgDepMeta
- BuildManager
- SuppressionReason
- ModuleNotFound
- State
- NodeInfo
- AckMessage
- SccRequestMessage
- ModuleResult
- SccResponseMessage
- SourcesDataMessage
- SccsDataMessage
- GraphMessage

### Functions
- build_error
- build
- build_inner
- warn_unused_configs
- default_data_dir
- normpath
- import_priority
- load_plugins_from_config
- load_plugins
- take_module_snapshot
- find_config_file_line_number
- deps_to_json
- write_deps_cache
- invert_deps
- generate_deps_for_cache
- write_plugins_snapshot
- read_plugins_snapshot
- read_quickstart_file
- read_deps_cache
- _load_ff_file
- _load_json_file
- _cache_dir_prefix
- add_catch_all_gitignore
- exclude_from_backups
- create_metastore
- get_meta_ex_name
- get_cache_names
- options_snapshot
- find_cache_meta
- validate_meta
- compute_hash
- write_cache
- write_cache_meta
- write_cache_meta_ex
- find_module_and_diagnose
- exist_added_packages
- exist_removed_submodules
- find_module_simple
- find_module_with_reason
- in_partial_package
- module_not_found
- skipping_module
- skipping_ancestor
- log_configuration
- dispatch
- dump_timing_stats
- dump_line_checking_stats
- dump_graph
- load_graph
- order_ascc_ex
- verify_transitive_deps
- find_stale_sccs
- process_graph
- order_ascc
- process_fresh_modules
- maybe_load_deps
- process_stale_scc
- process_stale_scc_interface
- process_stale_scc_implementation
- prepare_sccs_full
- sorted_components
- sorted_components_inner
- deps_filtered
- transitive_dep_hash
- missing_stubs_file
- record_missing_stub_packages
- is_silent_import_module
- write_undocumented_ref_info

## venv\Lib\site-packages\mypy\build_worker\__init__.py

## venv\Lib\site-packages\mypy\build_worker\__main__.py

## venv\Lib\site-packages\mypy\build_worker\worker.py

### Classes
- ServerContext

### Functions
- main
- should_shutdown
- serve
- timed_send
- load_states
- setup_worker_manager
- console_entry

## venv\Lib\site-packages\mypy\cache.py

### Classes
- CacheMeta
- CacheMetaEx

### Functions
- read_literal
- write_literal
- read_int
- write_int
- read_str
- write_str
- read_bytes
- write_bytes
- read_int_opt
- write_int_opt
- read_str_opt
- write_str_opt
- read_int_list
- write_int_list
- read_str_list
- write_str_list
- read_bytes_list
- write_bytes_list
- read_str_opt_list
- write_str_opt_list
- read_json_value
- write_json_value
- read_json
- write_json
- write_errors
- read_errors

## venv\Lib\site-packages\mypy\checker.py

### Classes
- DeferredNode
- FineGrainedDeferredNode
- PartialTypeScope
- LocalTypeMap
- TypeChecker
- TypeCheckerAsSemanticAnalyzer
- CollectArgTypeVarTypes
- TypeTransformVisitor
- InvalidInferredTypes
- SetNothingToAny
- DisjointDict
- VarAssignVisitor
- EqualityDomainInfo
- EqualityValueInfo

### Functions
- conditional_types
- conditional_types
- conditional_types
- conditional_types_to_typemaps
- gen_unique_name
- is_true_literal
- is_false_literal
- is_literal_none
- is_literal_not_implemented
- _is_empty_generator_function
- builtin_item_type
- is_unreachable_map
- and_conditional_maps
- or_conditional_maps
- reduce_conditional_maps
- reduce_or_conditional_type_maps
- reduce_and_conditional_type_maps
- has_custom_eq_checks
- convert_to_typetype
- flatten
- flatten_types_if_tuple
- expand_func
- are_argument_counts_overlapping
- expand_callable_variants
- is_unsafe_overlapping_overload_signatures
- detach_callable
- overload_can_never_match
- is_more_general_arg_prefix
- is_same_arg_prefix
- infer_operator_assignment_method
- _find_inplace_method
- is_valid_inferred_type
- is_classmethod_node
- is_node_static
- group_comparison_operands
- is_typed_callable
- is_untyped_decorator
- is_static
- is_property
- is_settable_property
- is_custom_settable_property
- get_property_type
- is_subset_no_promote
- is_overlapping_types_for_overload
- is_private
- is_string_literal
- has_bool_item
- collapse_walrus
- find_last_var_assignment_line
- partition_equality_ambiguous_types
- is_equality_ambiguous_for_narrowing
- equality_value_info
- combine_equality_value_info
- is_typeddict_type_context
- is_method

## venv\Lib\site-packages\mypy\checker_shared.py

### Classes
- TypeRange
- ExpressionCheckerSharedApi
- TypeCheckerSharedApi
- CheckerScope

## venv\Lib\site-packages\mypy\checker_state.py

### Classes
- TypeCheckerState

## venv\Lib\site-packages\mypy\checkexpr.py

### Classes
- TooManyUnions
- Finished
- UseReverse
- ExpressionChecker
- HasAnyType
- ArgInferSecondPassQuery
- HasErasedComponentsQuery
- HasUninhabitedComponentsQuery
- HasAmbiguousUninhabitedComponentsQuery

### Functions
- allow_fast_container_literal
- has_any_type
- has_coroutine_decorator
- is_async_def
- is_non_empty_tuple
- is_duplicate_mapping
- replace_callable_return_type
- has_erased_component
- has_uninhabited_component
- has_ambiguous_uninhabited_component
- arg_approximate_similarity
- any_causes_overload_ambiguity
- all_same_types
- merge_typevars_in_callables_by_name
- try_getting_literal
- is_expr_literal_type
- has_bytes_component
- type_info_from_type
- is_operator_method
- get_partial_instance_type
- is_type_type_context

## venv\Lib\site-packages\mypy\checkmember.py

### Classes
- MemberContext

### Functions
- analyze_member_access
- _analyze_member_access
- may_be_awaitable_attribute
- report_missing_attribute
- analyze_instance_member_access
- validate_super_call
- analyze_type_callable_member_access
- analyze_type_type_member_access
- analyze_union_member_access
- analyze_none_member_access
- analyze_member_var_access
- check_final_member
- analyze_descriptor_access
- analyze_descriptor_assign
- is_instance_var
- analyze_var
- expand_without_binding
- expand_and_bind_callable
- expand_self_type_if_needed
- check_self_arg
- analyze_class_attribute_access
- apply_class_attr_hook
- analyze_enum_class_attribute_access
- analyze_typeddict_access
- add_class_tvars
- analyze_decorator_or_funcbase_access
- bind_self_fast
- has_operator
- instance_fallback
- meta_has_operator
- defined_in_superclass

## venv\Lib\site-packages\mypy\checkpattern.py

### Classes
- PatternType
- PatternChecker

### Functions
- get_match_arg_names
- get_var
- get_type_range
- is_uninhabited

## venv\Lib\site-packages\mypy\checkstrformat.py

### Classes
- ConversionSpecifier
- StringFormatterChecker

### Functions
- compile_format_re
- compile_new_format_re
- parse_conversion_specifiers
- parse_format_value
- find_non_escaped_targets
- has_type_component

## venv\Lib\site-packages\mypy\config_parser.py

### Classes
- VersionTypeError
- ConfigTOMLValueError

### Functions
- parse_version
- try_split
- validate_package_allow_list
- expand_path
- str_or_array_as_list
- split_and_match_files_list
- split_and_match_files
- check_follow_imports
- check_junit_format
- split_commas
- _parse_individual_file
- _find_config_file
- parse_config_file
- get_prefix
- is_toml
- destructure_overrides
- parse_section
- convert_to_boolean
- split_directive
- mypy_comments_to_config_map
- parse_mypy_comments
- get_config_module_names

## venv\Lib\site-packages\mypy\constant_fold.py

### Functions
- constant_fold_expr
- constant_fold_binary_op
- constant_fold_binary_int_op
- constant_fold_binary_float_op
- constant_fold_unary_op

## venv\Lib\site-packages\mypy\constraints.py

### Classes
- Constraint
- ConstraintBuilderVisitor

### Functions
- infer_constraints_for_callable
- infer_constraints
- _infer_constraints
- _is_type_type
- _unwrap_type_type
- infer_constraints_if_possible
- select_trivial
- merge_with_any
- handle_recursive_union
- any_constraints
- filter_satisfiable
- exclude_non_meta_vars
- is_same_constraints
- is_same_constraint
- is_similar_constraints
- _is_similar_constraints
- neg_op
- find_matching_overload_item
- find_matching_overload_items
- get_tuple_fallback_from_unpack
- repack_callable_args
- build_constraints_for_simple_unpack
- infer_directed_arg_constraints
- infer_callable_arguments_constraints
- filter_imprecise_kinds

## venv\Lib\site-packages\mypy\copytype.py

### Classes
- TypeShallowCopier

### Functions
- copy_type

## venv\Lib\site-packages\mypy\defaults.py

## venv\Lib\site-packages\mypy\dmypy\__init__.py

## venv\Lib\site-packages\mypy\dmypy\__main__.py

## venv\Lib\site-packages\mypy\dmypy\client.py

### Classes
- AugmentedHelpFormatter

### Functions
- main
- fail
- action
- do_start
- do_restart
- restart_server
- start_server
- wait_for_server
- do_run
- do_status
- do_stop
- do_kill
- do_check
- do_recheck
- do_suggest
- do_inspect
- check_output
- show_stats
- do_hang
- do_daemon
- do_help
- request
- get_status
- check_status
- is_running
- console_entry

## venv\Lib\site-packages\mypy\dmypy_os.py

### Functions
- alive
- kill

## venv\Lib\site-packages\mypy\dmypy_server.py

### Classes
- Server

### Functions
- process_start_options
- ignore_suppressed_imports
- get_meminfo
- find_all_sources_in_build
- add_all_sources_to_changed
- fix_module_deps
- filter_out_missing_top_level_packages

## venv\Lib\site-packages\mypy\dmypy_util.py

### Classes
- WriteToConn

### Functions
- receive
- send

## venv\Lib\site-packages\mypy\erasetype.py

### Classes
- EraseTypeVisitor
- TypeVarEraser
- LastKnownValueEraser

### Functions
- erase_type
- erase_typevars
- erase_meta_id
- replace_meta_vars
- remove_instance_last_known_values
- shallow_erase_type_for_equality

## venv\Lib\site-packages\mypy\error_formatter.py

### Classes
- ErrorFormatter
- JSONFormatter

## venv\Lib\site-packages\mypy\errorcodes.py

### Classes
- ErrorCode

## venv\Lib\site-packages\mypy\errors.py

### Classes
- ErrorInfo
- ErrorWatcher
- NonOverlapErrorInfo
- IterationDependentErrors
- IterationErrorWatcher
- Errors
- CompileError
- MypyError

### Functions
- remove_path_prefix
- report_internal_error
- create_errors

## venv\Lib\site-packages\mypy\evalexpr.py

### Classes
- _NodeEvaluator

### Functions
- evaluate_expression

## venv\Lib\site-packages\mypy\expandtype.py

### Classes
- HasGenericCallable
- FreshenCallableVisitor
- ExpandTypeVisitor

### Functions
- expand_type
- expand_type
- expand_type
- expand_type
- expand_type_by_instance
- expand_type_by_instance
- expand_type_by_instance
- expand_type_by_instance
- freshen_function_type_vars
- freshen_all_functions_type_vars
- expand_self_type
- expand_self_type
- expand_self_type
- remove_trivial

## venv\Lib\site-packages\mypy\exportjson.py

### Classes
- Config

### Functions
- convert_binary_cache_to_json
- convert_mypy_file_to_json
- convert_symbol_table
- convert_symbol_table_node
- convert_symbol_node
- convert_func_def
- convert_dataclass_transform_spec
- convert_overloaded_func_def
- convert_overload_part
- convert_decorator
- convert_var
- convert_type_info
- convert_class_def
- convert_type_alias
- convert_type_var_expr
- convert_param_spec_expr
- convert_type_var_tuple_expr
- convert_type
- convert_instance
- convert_extra_attrs
- convert_type_alias_type
- convert_any_type
- convert_none_type
- convert_union_type
- convert_tuple_type
- convert_literal_type
- convert_type_var_type
- convert_callable_type
- convert_overloaded
- convert_type_type
- convert_uninhabited_type
- convert_unpack_type
- convert_param_spec_type
- convert_type_var_tuple_type
- convert_parameters
- convert_typeddict_type
- convert_unbound_type
- convert_binary_cache_meta_to_json
- main

## venv\Lib\site-packages\mypy\exprtotype.py

### Classes
- TypeTranslationError

### Functions
- _extract_argument_name
- expr_to_unanalyzed_type

## venv\Lib\site-packages\mypy\fastparse.py

### Classes
- ASTConverter
- TypeConverter
- FindAttributeAssign
- FindYield

### Functions
- ast3_parse
- parse
- parse_type_ignore_tag
- parse_type_comment
- parse_type_string
- is_no_type_check_decorator
- find_disallowed_expression_in_annotation_scope
- stringify_name
- is_possible_trivial_body

## venv\Lib\site-packages\mypy\find_sources.py

### Classes
- InvalidSourceList
- SourceFinder

### Functions
- create_source_list
- keyfunc
- normalise_package_base
- get_explicit_package_bases
- module_join
- strip_py

## venv\Lib\site-packages\mypy\fixup.py

### Classes
- NodeFixer
- TypeFixer

### Functions
- lookup_fully_qualified_typeinfo
- lookup_fully_qualified_alias
- missing_info
- missing_alias

## venv\Lib\site-packages\mypy\freetree.py

### Classes
- TreeFreer

### Functions
- free_tree

## venv\Lib\site-packages\mypy\fscache.py

### Classes
- FileSystemCache

### Functions
- copy_os_error

## venv\Lib\site-packages\mypy\fswatcher.py

### Classes
- FileData
- FileSystemWatcher

## venv\Lib\site-packages\mypy\gclogger.py

### Classes
- GcLogger

## venv\Lib\site-packages\mypy\git.py

### Functions
- is_git_repo
- have_git
- git_revision
- git_revision_no_subprocess
- is_dirty

## venv\Lib\site-packages\mypy\graph_utils.py

### Classes
- topsort

### Functions
- strongly_connected_components
- prepare_sccs

## venv\Lib\site-packages\mypy\indirection.py

### Classes
- TypeIndirectionVisitor

## venv\Lib\site-packages\mypy\infer.py

### Classes
- ArgumentInferContext

### Functions
- infer_function_type_arguments
- infer_type_arguments

## venv\Lib\site-packages\mypy\inspections.py

### Classes
- SearchVisitor
- SearchAllVisitor
- InspectionEngine

### Functions
- node_starts_after
- node_ends_before
- expr_span
- get_instance_fallback
- find_node
- find_module_by_fullname
- find_by_location
- find_all_by_location
- parse_location

## venv\Lib\site-packages\mypy\ipc.py

### Classes
- IPCException
- IPCBase
- IPCClient
- IPCServer
- BadStatus
- IPCMessage

### Functions
- read_status
- ready_to_read
- send
- receive

## venv\Lib\site-packages\mypy\join.py

### Classes
- InstanceJoiner
- TypeJoinVisitor

### Functions
- trivial_join
- join_types
- join_types
- join_types
- is_better
- normalize_callables
- is_similar_callables
- is_similar_params
- update_callable_ids
- match_generic_callables
- join_similar_callables
- safe_join
- safe_meet
- combine_similar_callables
- combine_arg_names
- object_from_instance
- object_or_any_from_type
- join_type_list
- unpack_callback_protocol

## venv\Lib\site-packages\mypy\known_modules.py

### Functions
- reset_known_modules_cache
- get_stdlib_modules
- get_known_modules

## venv\Lib\site-packages\mypy\literals.py

### Classes
- _Hasher

### Functions
- literal_hash
- literal
- subkeys
- extract_var_from_literal_hash

## venv\Lib\site-packages\mypy\lookup.py

### Functions
- lookup_fully_qualified
- lookup_stdlib_typeinfo

## venv\Lib\site-packages\mypy\main.py

### Classes
- BuildResultThunk
- AugmentedHelpFormatter
- PythonExecutableInferenceError
- CapturableArgumentParser
- CapturableVersionAction

### Functions
- stat_proxy
- main
- run_build
- show_messages
- invert_flag_name
- python_executable_prefix
- _python_executable_from_version
- infer_python_executable
- define_options
- process_options
- process_package_roots
- process_cache_map
- maybe_write_junit_xml
- fail
- read_types_packages_to_install
- install_types

## venv\Lib\site-packages\mypy\maptype.py

### Functions
- map_instance_to_supertype
- map_instance_to_supertypes
- class_derivation_paths
- map_instance_to_direct_supertypes

## venv\Lib\site-packages\mypy\meet.py

### Classes
- TypeMeetVisitor

### Functions
- trivial_meet
- meet_types
- narrow_declared_type
- get_possible_variants
- is_enum_overlapping_union
- is_literal_in_union
- is_object
- is_none_object_overlap
- are_related_types
- is_overlapping_types
- is_overlapping_erased_types
- are_typed_dicts_overlapping
- are_tuples_overlapping
- expand_tuple_if_possible
- adjust_tuple
- is_tuple
- meet_similar_callables
- meet_type_list
- typed_dict_mapping_pair
- typed_dict_mapping_overlap

## venv\Lib\site-packages\mypy\memprofile.py

### Functions
- collect_memory_stats
- print_memory_profile
- find_recursive_objects

## venv\Lib\site-packages\mypy\message_registry.py

### Classes
- ErrorMessage

## venv\Lib\site-packages\mypy\messages.py

### Classes
- MessageBuilder
- CollectAllNamedTypesQuery

### Functions
- quote_type_string
- should_format_arg_as_type
- format_callable_args
- format_type_inner
- collect_all_named_types
- scoped_type_var_name
- find_type_overlaps
- format_type
- format_type_bare
- format_type_distinctly
- pretty_class_or_static_decorator
- pretty_callable
- get_first_arg
- variance_string
- get_missing_protocol_members
- get_conflict_protocol_types
- get_bad_protocol_flags
- capitalize
- extract_type
- strip_quotes
- format_string_list
- format_item_name_list
- callable_name
- for_function
- wrong_type_arg_count
- find_defining_module
- _real_quick_ratio
- best_matches
- pretty_seq
- append_invariance_notes
- append_union_note
- append_numbers_notes
- make_inferred_type_note
- format_key_list
- ignore_last_known_values

## venv\Lib\site-packages\mypy\metastore.py

### Classes
- MetadataStore
- FilesystemMetadataStore
- SqliteMetadataStore

### Functions
- random_string
- connect_db

## venv\Lib\site-packages\mypy\mixedtraverser.py

### Classes
- MixedTraverserVisitor

## venv\Lib\site-packages\mypy\modulefinder.py

### Classes
- SearchPaths
- ModuleNotFoundReason
- BuildSource
- BuildSourceSet
- FindModuleCache

### Functions
- matches_exclude
- matches_gitignore
- find_gitignores
- is_init_file
- verify_module
- highest_init_level
- mypy_path
- default_lib_path
- get_search_dirs
- compute_search_paths
- load_stdlib_py_versions
- parse_version
- typeshed_py_version

## venv\Lib\site-packages\mypy\moduleinspect.py

### Classes
- ModuleProperties
- InspectError
- ModuleInspect

### Functions
- is_c_module
- is_pyc_only
- get_package_properties
- worker

## venv\Lib\site-packages\mypy\modules_state.py

### Classes
- ModulesState

## venv\Lib\site-packages\mypy\mro.py

### Classes
- MroError

### Functions
- calculate_mro
- linearize_hierarchy
- merge

## venv\Lib\site-packages\mypy\nativeparse.py

### Classes
- State

### Functions
- native_parse
- expect_end_tag
- expect_tag
- read_statements
- parse_to_binary_ast
- read_statement
- read_parameters
- read_type_params
- read_func_def
- read_class_def
- read_type_alias_stmt
- read_try_stmt
- read_type
- stringify_type_name
- extract_arg_name
- read_call_type
- read_pattern
- read_block
- read_optional_block
- read_expression
- read_fstring_items
- build_fstring_join
- collapse_consecutive_str_items
- read_fstring_item
- set_line_column
- set_line_column_range
- read_expression_list
- read_generator_expr
- read_loc
- strip_contents_from_if_stmt
- is_stripped_if_stmt
- fail_merge_overload
- check_ifstmt_for_overloads
- get_executable_if_block_with_overloads
- fix_function_overloads
- deserialize_imports
- _read_and_set_import_metadata

## venv\Lib\site-packages\mypy\nodes.py

### Classes
- NotParsed
- Context
- Node
- Statement
- Expression
- FakeExpression
- SymbolNode
- ParseError
- FileRawData
- MypyFile
- ImportBase
- Import
- ImportFrom
- ImportAll
- FuncBase
- OverloadedFuncDef
- Argument
- TypeParam
- FuncItem
- FuncDef
- Decorator
- Var
- ClassDef
- GlobalDecl
- NonlocalDecl
- Block
- ExpressionStmt
- AssignmentStmt
- OperatorAssignmentStmt
- WhileStmt
- ForStmt
- ReturnStmt
- AssertStmt
- DelStmt
- BreakStmt
- ContinueStmt
- PassStmt
- IfStmt
- RaiseStmt
- TryStmt
- WithStmt
- MatchStmt
- TypeAliasStmt
- IntExpr
- StrExpr
- BytesExpr
- FloatExpr
- ComplexExpr
- EllipsisExpr
- StarExpr
- RefExpr
- NameExpr
- MemberExpr
- ArgKind
- CallExpr
- YieldFromExpr
- YieldExpr
- IndexExpr
- UnaryExpr
- AssignmentExpr
- OpExpr
- ComparisonExpr
- SliceExpr
- CastExpr
- TypeFormExpr
- AssertTypeExpr
- RevealExpr
- SuperExpr
- LambdaExpr
- ListExpr
- DictExpr
- TemplateStrExpr
- TupleExpr
- SetExpr
- GeneratorExpr
- ListComprehension
- SetComprehension
- DictionaryComprehension
- ConditionalExpr
- TypeApplication
- TypeVarLikeExpr
- TypeVarExpr
- ParamSpecExpr
- TypeVarTupleExpr
- TypeAliasExpr
- NamedTupleExpr
- TypedDictExpr
- EnumCallExpr
- PromoteExpr
- NewTypeExpr
- AwaitExpr
- TempNode
- TypeInfo
- FakeInfo
- TypeAlias
- PlaceholderNode
- SymbolTableNode
- SymbolTable
- DataclassTransformSpec
- SplittingVisitor

### Functions
- write_parse_error
- read_parse_error
- is_StrExpr_list
- get_flags
- set_flags
- write_flags
- read_flags
- get_member_expr_fullname
- check_arg_kinds
- check_param_names
- is_class_var
- is_final_node
- get_func_def
- local_definitions
- set_info
- read_symbol
- read_overload_part

## venv\Lib\site-packages\mypy\operators.py

## venv\Lib\site-packages\mypy\options.py

### Classes
- BuildType
- Options

## venv\Lib\site-packages\mypy\parse.py

### Functions
- parse
- load_from_raw
- report_parse_error

## venv\Lib\site-packages\mypy\partially_defined.py

### Classes
- BranchState
- BranchStatement
- ScopeType
- Scope
- DefinedVariableTracker
- Loop
- PossiblyUndefinedVariableVisitor

## venv\Lib\site-packages\mypy\patterns.py

### Classes
- Pattern
- AsPattern
- OrPattern
- ValuePattern
- SingletonPattern
- SequencePattern
- StarredPattern
- MappingPattern
- ClassPattern

## venv\Lib\site-packages\mypy\plugin.py

### Classes
- TypeAnalyzerPluginInterface
- AnalyzeTypeContext
- CommonPluginApi
- CheckerPluginInterface
- SemanticAnalyzerPluginInterface
- ReportConfigContext
- FunctionSigContext
- FunctionContext
- MethodSigContext
- MethodContext
- AttributeContext
- ClassDefContext
- DynamicClassDefContext
- Plugin
- ChainedPlugin

## venv\Lib\site-packages\mypy\plugins\__init__.py

## venv\Lib\site-packages\mypy\plugins\attrs.py

### Classes
- Converter
- Attribute
- MethodAdder

### Functions
- _determine_eq_order
- _get_decorator_optional_bool_argument
- attr_tag_callback
- attr_class_maker_callback
- attr_class_maker_callback_impl
- _get_frozen
- _analyze_class
- _add_empty_metadata
- _detect_auto_attribs
- _attributes_from_assignment
- _cleanup_decorator
- _attribute_from_auto_attrib
- _attribute_from_attrib_maker
- _parse_converter
- is_valid_overloaded_converter
- _parse_assignments
- _add_order
- _make_frozen
- _add_init
- _add_attrs_magic_attribute
- _add_slots
- _add_match_args
- _remove_hashability
- _get_attrs_init_type
- _fail_not_attrs_class
- _get_expanded_attr_types
- _meet_fields
- evolve_function_sig_callback
- fields_function_sig_callback

## venv\Lib\site-packages\mypy\plugins\common.py

### Classes
- MethodSpec

### Functions
- _get_decorator_bool_argument
- _get_bool_argument
- _get_argument
- find_shallow_matching_overload_item
- _get_callee_type
- add_method
- add_method_to_class
- add_overloaded_method_to_class
- _prepare_class_namespace
- _add_method_by_spec
- add_attribute_to_class
- deserialize_and_fixup_type

## venv\Lib\site-packages\mypy\plugins\constants.py

## venv\Lib\site-packages\mypy\plugins\ctypes.py

### Functions
- _find_simplecdata_base_arg
- _autoconvertible_to_cdata
- _autounboxed_cdata
- _get_array_element_type
- array_constructor_callback
- array_getitem_callback
- array_setitem_callback
- array_iter_callback
- array_value_callback
- array_raw_callback

## venv\Lib\site-packages\mypy\plugins\dataclasses.py

### Classes
- DataclassAttribute
- DataclassTransformer

### Functions
- add_dataclass_tag
- dataclass_tag_callback
- dataclass_class_maker_callback
- _get_transform_spec
- _is_dataclasses_decorator
- _has_direct_dataclass_transform_metaclass
- _get_expanded_dataclasses_fields
- _meet_replace_sigs
- replace_function_sig_callback
- is_processed_dataclass
- check_post_init

## venv\Lib\site-packages\mypy\plugins\default.py

### Classes
- DefaultPlugin

### Functions
- len_callback
- typed_dict_get_signature_callback
- typed_dict_get_callback
- typed_dict_pop_signature_callback
- typed_dict_pop_callback
- typed_dict_setdefault_signature_callback
- typed_dict_setdefault_callback
- typed_dict_delitem_callback
- typed_dict_update_signature_callback
- int_pow_callback
- int_neg_callback
- int_pos_callback
- tuple_mul_callback

## venv\Lib\site-packages\mypy\plugins\enums.py

### Functions
- enum_name_callback
- _first
- _infer_value_type_with_auto_fallback
- _is_defined_in_stub
- _implements_new
- enum_member_callback
- enum_value_callback
- _extract_underlying_field_name

## venv\Lib\site-packages\mypy\plugins\functools.py

### Classes
- _MethodInfo

### Functions
- functools_total_ordering_maker_callback
- _find_other_type
- _analyze_class
- partial_new_callback
- handle_partial_with_callee
- partial_call_callback

## venv\Lib\site-packages\mypy\plugins\proper_plugin.py

### Classes
- ProperTypePlugin

### Functions
- isinstance_proper_hook
- is_special_target
- is_improper_type
- is_dangerous_target
- proper_type_hook
- proper_types_hook
- get_proper_type_instance
- plugin

## venv\Lib\site-packages\mypy\plugins\singledispatch.py

### Classes
- SingledispatchTypeVars
- RegisterCallableInfo

### Functions
- get_singledispatch_info
- get_first_arg
- make_fake_register_class_instance
- fail
- create_singledispatch_function_callback
- singledispatch_register_callback
- register_function
- get_dispatch_type
- call_singledispatch_function_after_register_argument
- call_singledispatch_function_callback

## venv\Lib\site-packages\mypy\pyinfo.py

### Functions
- getsitepackages
- getsyspath
- getsearchdirs

## venv\Lib\site-packages\mypy\reachability.py

### Classes
- MarkImportsUnreachableVisitor
- MarkImportsMypyOnlyVisitor

### Functions
- infer_reachability_of_if_statement
- infer_reachability_of_match_statement
- assert_will_always_fail
- infer_condition_value
- infer_pattern_value
- consider_sys_version_info
- consider_sys_platform
- fixed_comparison
- contains_int_or_tuple_of_ints
- contains_sys_version_info
- is_sys_attr
- mark_block_unreachable
- mark_block_mypy_only

## venv\Lib\site-packages\mypy\refinfo.py

### Classes
- RefInfoVisitor

### Functions
- type_fullname
- get_undocumented_ref_info_json

## venv\Lib\site-packages\mypy\renaming.py

### Classes
- VariableRenameVisitor
- LimitedVariableRenameVisitor

### Functions
- rename_refs

## venv\Lib\site-packages\mypy\report.py

### Classes
- Reports
- AbstractReporter
- FuncCounterVisitor
- LineCountReporter
- AnyExpressionsReporter
- LineCoverageVisitor
- LineCoverageReporter
- FileInfo
- MemoryXmlReporter
- CoberturaPackage
- CoberturaXmlReporter
- AbstractXmlReporter
- XmlReporter
- XsltHtmlReporter
- XsltTxtReporter
- LinePrecisionReporter

### Functions
- register_reporter
- alias_reporter
- should_skip_path
- iterate_python_lines
- get_line_rate

## venv\Lib\site-packages\mypy\scope.py

### Classes
- Scope

## venv\Lib\site-packages\mypy\semanal.py

### Classes
- SemanticAnalyzer
- MakeAnyNonExplicit
- MakeAnyNonUnimported

### Functions
- replace_implicit_first_type
- refers_to_fullname
- refers_to_class_or_function
- find_duplicate
- remove_imported_names_from_symtable
- make_any_non_explicit
- make_any_non_unimported
- apply_semantic_analyzer_patches
- names_modified_by_assignment
- names_modified_in_lvalue
- is_same_var_from_getattr
- dummy_context
- is_valid_replacement
- is_same_symbol
- is_trivial_body
- is_init_only
- erase_func_annotations

## venv\Lib\site-packages\mypy\semanal_classprop.py

### Functions
- calculate_class_abstract_status
- check_protocol_status
- calculate_class_vars
- add_type_promotion

## venv\Lib\site-packages\mypy\semanal_enum.py

### Classes
- EnumCallAnalyzer

## venv\Lib\site-packages\mypy\semanal_infer.py

### Functions
- infer_decorator_signature_if_simple
- is_identity_signature
- calculate_return_type
- find_fixed_callable_return

## venv\Lib\site-packages\mypy\semanal_main.py

### Functions
- semantic_analysis_for_scc
- cleanup_builtin_scc
- semantic_analysis_for_targets
- process_top_levels
- order_by_subclassing
- process_functions
- process_top_level_function
- get_all_leaf_targets
- semantic_analyze_target
- check_type_arguments
- check_type_arguments_in_targets
- apply_class_plugin_hooks
- apply_hooks_to_class
- calculate_class_properties
- check_blockers

## venv\Lib\site-packages\mypy\semanal_namedtuple.py

### Classes
- NamedTupleAnalyzer

## venv\Lib\site-packages\mypy\semanal_newtype.py

### Classes
- NewTypeAnalyzer

## venv\Lib\site-packages\mypy\semanal_pass1.py

### Classes
- SemanticAnalyzerPreAnalysis

## venv\Lib\site-packages\mypy\semanal_shared.py

### Classes
- SemanticAnalyzerCoreInterface
- SemanticAnalyzerInterface
- _NamedTypeCallback
- HasPlaceholders

### Functions
- set_callable_name
- calculate_tuple_fallback
- paramspec_args
- paramspec_kwargs
- has_placeholder
- find_dataclass_transform_spec
- require_bool_literal_argument
- require_bool_literal_argument
- require_bool_literal_argument
- parse_bool

## venv\Lib\site-packages\mypy\semanal_typeargs.py

### Classes
- TypeArgumentAnalyzer

## venv\Lib\site-packages\mypy\semanal_typeddict.py

### Classes
- TypedDictAnalyzer

## venv\Lib\site-packages\mypy\server\__init__.py

## venv\Lib\site-packages\mypy\server\astdiff.py

### Classes
- SnapshotTypeVisitor

### Functions
- compare_symbol_table_snapshots
- snapshot_symbol_table
- snapshot_definition
- snapshot_type
- snapshot_optional_type
- snapshot_types
- snapshot_simple_type
- encode_optional_str
- snapshot_untyped_signature

## venv\Lib\site-packages\mypy\server\astmerge.py

### Classes
- NodeReplaceVisitor
- TypeReplaceVisitor

### Functions
- merge_asts
- replacement_map_from_symbol_table
- replace_nodes_in_ast
- replace_nodes_in_symbol_table
- _get_ignored_slots

## venv\Lib\site-packages\mypy\server\aststrip.py

### Classes
- NodeStripVisitor

### Functions
- strip_target

## venv\Lib\site-packages\mypy\server\deps.py

### Classes
- DependencyVisitor
- TypeTriggersVisitor

### Functions
- get_dependencies
- get_dependencies_of_target
- get_type_triggers
- merge_dependencies
- non_trivial_bases
- has_user_bases
- dump_all_dependencies

## venv\Lib\site-packages\mypy\server\mergecheck.py

### Functions
- check_consistency
- path_to_str

## venv\Lib\site-packages\mypy\server\objgraph.py

### Functions
- isproperty
- get_edge_candidates
- get_edges
- get_reachable_graph
- get_path

## venv\Lib\site-packages\mypy\server\subexpr.py

### Classes
- SubexpressionFinder

### Functions
- get_subexpressions

## venv\Lib\site-packages\mypy\server\target.py

### Functions
- trigger_to_target

## venv\Lib\site-packages\mypy\server\trigger.py

### Functions
- make_trigger
- make_wildcard_trigger

## venv\Lib\site-packages\mypy\server\update.py

### Classes
- FineGrainedBuildManager
- NormalUpdate
- BlockedUpdate

### Functions
- find_unloaded_deps
- ensure_deps_loaded
- ensure_trees_loaded
- update_module_isolated
- find_relative_leaf_module
- delete_module
- dedupe_modules
- get_module_to_path_map
- get_sources
- calculate_active_triggers
- replace_modules_with_new_variants
- propagate_changes_using_dependencies
- find_targets_recursive
- reprocess_nodes
- find_symbol_tables_recursive
- update_deps
- lookup_target
- _lookup_target_impl
- is_verbose
- target_from_node
- refresh_suppressed_submodules
- extract_fnam_from_message
- extract_possible_fnam_from_message
- sort_messages_preserving_file_order

## venv\Lib\site-packages\mypy\sharedparse.py

### Functions
- special_function_elide_names
- argument_elide_name

## venv\Lib\site-packages\mypy\solve.py

### Functions
- solve_constraints
- solve_with_dependent
- solve_iteratively
- _join_sorted_key
- solve_one
- choose_free
- is_trivial_bound
- find_linear
- transitive_closure
- add_secondary_constraints
- compute_dependencies
- check_linear
- skip_reverse_union_constraints
- get_vars
- pre_validate_solutions
- is_callable_protocol

## venv\Lib\site-packages\mypy\split_namespace.py

### Classes
- SplitNamespace

## venv\Lib\site-packages\mypy\state.py

### Classes
- StrictOptionalState

## venv\Lib\site-packages\mypy\stats.py

### Classes
- StatisticsVisitor
- HasAnyQuery
- HasAnyQuery2

### Functions
- dump_type_stats
- is_special_module
- is_imprecise
- is_imprecise2
- is_generic
- is_complex
- is_special_form_any
- get_original_any

## venv\Lib\site-packages\mypy\strconv.py

### Classes
- StrConv

### Functions
- dump_tagged
- indent

## venv\Lib\site-packages\mypy\stubdoc.py

### Classes
- ArgSig
- FunctionSig
- DocStringParser

### Functions
- is_valid_type
- infer_sig_from_docstring
- infer_arg_sig_from_anon_docstring
- infer_ret_type_sig_from_docstring
- infer_ret_type_sig_from_anon_docstring
- parse_signature
- build_signature
- parse_all_signatures
- find_unique_signatures
- infer_prop_type_from_docstring

## venv\Lib\site-packages\mypy\stubgen.py

### Classes
- Options
- StubSource
- AliasPrinter
- DefinitionFinder
- ReferenceFinder
- ASTStubGenerator
- SelfTraverser

### Functions
- find_defined_names
- get_assigned_names
- find_referenced_names
- is_none_expr
- find_method_names
- find_self_initializers
- get_qualified_name
- remove_blacklisted_modules
- split_pyc_from_py
- is_blacklisted_path
- normalize_path_separators
- collect_build_targets
- find_module_paths_using_imports
- is_non_library_module
- translate_module_name
- find_module_paths_using_search
- mypy_options
- parse_source_file
- generate_asts_for_modules
- generate_stub_for_py_module
- generate_stubs
- parse_options
- main

## venv\Lib\site-packages\mypy\stubgenc.py

### Classes
- ExternalSignatureGenerator
- DocstringSignatureGenerator
- CFunctionStub
- InspectionStubGenerator

### Functions
- is_pybind11_overloaded_function_docstring
- generate_stub_for_c_module
- method_name_sort_key
- is_pybind_skipped_attribute
- infer_c_method_args

## venv\Lib\site-packages\mypy\stubinfo.py

### Functions
- stub_distribution_name

## venv\Lib\site-packages\mypy\stubtest.py

### Classes
- Missing
- Unrepresentable
- StubtestFailure
- Error
- Signature
- _TypeCheckOnlyBaseMapper
- _Arguments

### Functions
- _style
- _truncate
- silent_import_module
- test_module
- verify
- _verify_exported_names
- _module_symbol_table
- verify_mypyfile
- _is_decoratable
- _verify_final
- _shape_differs
- _is_disjoint_base
- _verify_disjoint_base
- _verify_metaclass
- verify_typeinfo
- _static_lookup_runtime
- _verify_static_class_methods
- _verify_arg_name
- _verify_arg_default_value
- maybe_strip_cls
- _verify_signature
- _is_private_parameter
- verify_funcitem
- verify_missing
- verify_var
- verify_overloadedfuncdef
- verify_typevarexpr
- verify_paramspecexpr
- _is_django_cached_property
- _verify_readonly_property
- _verify_abstract_status
- _verify_final_method
- _resolve_funcitem_from_decorator
- _resolve_funcitem_from_callable_type
- verify_decorator
- verify_typealias
- is_probably_private
- is_probably_a_function
- is_read_only_property
- safe_inspect_signature
- describe_runtime_callable
- _relax_type_check_only_type
- is_subtype_helper
- get_mypy_node_for_name
- get_mypy_type_of_runtime_value
- build_stubs
- get_stub
- get_typeshed_stdlib_modules
- get_importable_stdlib_modules
- get_allowlist_entries
- test_stubs
- safe_print
- parse_options
- main

## venv\Lib\site-packages\mypy\stubutil.py

### Classes
- CantImport
- AnnotationPrinter
- ClassInfo
- FunctionContext
- SignatureGenerator
- ImportTracker
- BaseStubGenerator

### Functions
- walk_packages
- find_module_path_using_sys_path
- find_module_path_and_all_py3
- generate_guarded
- report_missing
- fail_missing
- remove_misplaced_type_comments
- remove_misplaced_type_comments
- remove_misplaced_type_comments
- common_dir_prefix
- infer_method_ret_type
- infer_method_arg_types

## venv\Lib\site-packages\mypy\subtypes.py

### Classes
- SubtypeContext
- SubtypeVisitor

### Functions
- is_subtype
- is_proper_subtype
- is_equivalent
- is_same_type
- _is_subtype
- check_type_parameter
- pop_on_exit
- is_protocol_implementation
- get_protocol_member
- find_member
- find_member_simple
- get_member_flags
- is_descriptor
- find_node_type
- non_method_protocol_members
- is_callable_compatible
- are_trivial_parameters
- is_trivial_suffix
- are_parameters_compatible
- are_args_compatible
- flip_compat_check
- unify_generic_callable
- try_restrict_literal_union
- restrict_subtype_away
- covers_at_runtime
- is_more_precise
- all_non_object_members
- infer_variance
- has_underscore_prefix
- infer_class_variances
- erase_return_self_types
- is_erased_instance

## venv\Lib\site-packages\mypy\suggestions.py

### Classes
- PyAnnotateSignature
- Callsite
- SuggestionPlugin
- ReturnFinder
- ArgUseFinder
- SuggestionFailure
- SuggestionEngine
- TypeFormatter
- MakeSuggestionAny

### Functions
- get_return_types
- get_arg_uses
- is_explicit_any
- is_implicit_any
- _arg_accepts_function
- any_score_type
- any_score_callable
- is_tricky_callable
- make_suggestion_anys
- generate_type_combinations
- count_errors
- refine_type
- refine_union
- refine_callable
- dedup

## venv\Lib\site-packages\mypy\test\__init__.py

## venv\Lib\site-packages\mypy\test\config.py

## venv\Lib\site-packages\mypy\test\data.py

### Classes
- UpdateFile
- DeleteFile
- DataDrivenTestCase
- TestItem
- DataSuiteCollector
- DataFileFix
- DataFileCollector
- DataSuite

### Functions
- _file_arg_to_module
- parse_test_case
- module_from_path
- parse_test_data
- strip_list
- collapse_line_continuation
- expand_variables
- expand_errors
- fix_win_path
- fix_cobertura_filename
- pytest_sessionstart
- pytest_addoption
- pytest_cmdline_main
- pytest_pycollect_makeitem
- split_test_cases
- add_test_name_suffix
- is_incremental
- has_stable_flags

## venv\Lib\site-packages\mypy\test\helpers.py

### Functions
- run_mypy
- diff_ranges
- render_diff_range
- dump_original_errors
- module_order
- match_module_order
- assert_string_arrays_equal
- assert_module_equivalence
- assert_target_equivalence
- show_align_message
- clean_up
- local_sys_path_set
- testfile_pyversion
- normalize_error_messages
- retry_on_error
- good_repr
- assert_equal
- typename
- assert_type
- parse_options
- split_lines
- write_and_fudge_mtime
- perform_file_operations
- check_test_output_files
- normalize_file_output
- normalize_report_meta
- find_test_files
- remove_typevar_ids

## venv\Lib\site-packages\mypy\test\meta\__init__.py

## venv\Lib\site-packages\mypy\test\meta\_pytest.py

### Classes
- PytestResult

### Functions
- dedent_docstring
- run_pytest_data_suite

## venv\Lib\site-packages\mypy\test\meta\test_diff_helper.py

### Classes
- DiffHelperSuite

## venv\Lib\site-packages\mypy\test\meta\test_parse_data.py

### Classes
- ParseTestDataSuite

### Functions
- _run_pytest

## venv\Lib\site-packages\mypy\test\meta\test_update_data.py

### Classes
- UpdateDataSuite

### Functions
- _run_pytest_update_data

## venv\Lib\site-packages\mypy\test\test_config_parser.py

### Classes
- FindConfigFileSuite

### Functions
- chdir
- write_config

## venv\Lib\site-packages\mypy\test\test_diff_cache.py

### Classes
- DiffCacheIntegrationTests

## venv\Lib\site-packages\mypy\test\test_find_sources.py

### Classes
- FakeFSCache
- SourceFinderSuite

### Functions
- normalise_path
- normalise_build_source_list
- crawl
- find_sources_in_dir
- find_sources

## venv\Lib\site-packages\mypy\test\test_nativeparse.py

### Classes
- NativeParserSuite
- NativeParserImportsSuite
- TestNativeParserBinaryFormat

### Functions
- test_parser
- format_error
- format_ignore
- load_tree
- test_parser_imports
- format_reachable_imports
- temp_source

## venv\Lib\site-packages\mypy\test\test_ref_info.py

### Classes
- RefInfoSuite

## venv\Lib\site-packages\mypy\test\testapi.py

### Classes
- APISuite

## venv\Lib\site-packages\mypy\test\testargs.py

### Classes
- ArgSuite

## venv\Lib\site-packages\mypy\test\testcheck.py

### Classes
- TypeCheckSuite

## venv\Lib\site-packages\mypy\test\testcmdline.py

### Classes
- PythonCmdlineSuite

### Functions
- test_python_cmdline
- parse_args
- parse_cwd
- normalize_devnull

## venv\Lib\site-packages\mypy\test\testconstraints.py

### Classes
- ConstraintsSuite

## venv\Lib\site-packages\mypy\test\testdaemon.py

### Classes
- DaemonSuite
- DaemonUtilitySuite

### Functions
- test_daemon
- parse_script
- run_cmd

## venv\Lib\site-packages\mypy\test\testdeps.py

### Classes
- GetDependenciesSuite

## venv\Lib\site-packages\mypy\test\testdiff.py

### Classes
- ASTDiffSuite

## venv\Lib\site-packages\mypy\test\testerrorstream.py

### Classes
- ErrorStreamSuite

### Functions
- test_error_stream

## venv\Lib\site-packages\mypy\test\testexportjson.py

### Classes
- TypeExportSuite

### Functions
- filter_platform_specific

## venv\Lib\site-packages\mypy\test\testfinegrained.py

### Classes
- FineGrainedSuite
- TestMessageSorting

### Functions
- normalize_messages

## venv\Lib\site-packages\mypy\test\testfinegrainedcache.py

### Classes
- FineGrainedCacheSuite

## venv\Lib\site-packages\mypy\test\testformatter.py

### Classes
- FancyErrorFormattingTestCases

## venv\Lib\site-packages\mypy\test\testfscache.py

### Classes
- TestFileSystemCache

## venv\Lib\site-packages\mypy\test\testgraph.py

### Classes
- GraphSuite

## venv\Lib\site-packages\mypy\test\testinfer.py

### Classes
- MapActualsToFormalsSuite
- OperandDisjointDictSuite
- OperandComparisonGroupingSuite

### Functions
- expand_caller_kinds
- expand_callee_kinds

## venv\Lib\site-packages\mypy\test\testipc.py

### Classes
- IPCTests

### Functions
- server
- server_multi_message_echo

## venv\Lib\site-packages\mypy\test\testmerge.py

### Classes
- ASTMergeSuite

## venv\Lib\site-packages\mypy\test\testmodulefinder.py

### Classes
- ModuleFinderSuite
- ModuleFinderSitePackagesSuite

## venv\Lib\site-packages\mypy\test\testmypyc.py

### Classes
- MypycTest

## venv\Lib\site-packages\mypy\test\testoutput.py

### Classes
- OutputJSONsuite

### Functions
- test_output_json

## venv\Lib\site-packages\mypy\test\testparse.py

### Classes
- ParserSuite
- ParseErrorSuite

### Functions
- test_parser
- test_parse_error

## venv\Lib\site-packages\mypy\test\testpep561.py

### Classes
- PEP561Suite

### Functions
- virtualenv
- upgrade_pip
- install_package
- test_pep561
- parse_pkgs
- parse_mypy_args

## venv\Lib\site-packages\mypy\test\testpythoneval.py

### Classes
- PythonEvaluationSuite

### Functions
- test_python_evaluation
- adapt_output

## venv\Lib\site-packages\mypy\test\testreports.py

### Classes
- CoberturaReportSuite

## venv\Lib\site-packages\mypy\test\testsemanal.py

### Classes
- SemAnalSuite
- SemAnalErrorSuite
- SemAnalSymtableSuite
- SemAnalTypeInfoSuite
- TypeInfoMap

### Functions
- get_semanal_options
- test_semanal
- test_semanal_error

## venv\Lib\site-packages\mypy\test\testsolve.py

### Classes
- SolveSuite

## venv\Lib\site-packages\mypy\test\teststubgen.py

### Classes
- StubgenCmdLineSuite
- StubgenCliParseSuite
- StubgenUtilSuite
- StubgenHelpersSuite
- StubgenPythonSuite
- TestBaseClass
- TestClass
- StubgencSuite
- ArgSigSuite
- IsValidTypeSuite
- ModuleInspectSuite

### Functions
- module_to_path

## venv\Lib\site-packages\mypy\test\teststubinfo.py

### Classes
- TestStubInfo

## venv\Lib\site-packages\mypy\test\teststubtest.py

### Classes
- Case
- StubtestUnit
- StubtestMiscUnit

### Functions
- use_tmp_dir
- build_helper
- run_stubtest_with_stderr
- run_stubtest
- collect_cases
- remove_color_code

## venv\Lib\site-packages\mypy\test\testsubtypes.py

### Classes
- SubtypingSuite

## venv\Lib\site-packages\mypy\test\testtransform.py

### Classes
- TransformSuite

### Functions
- test_transform

## venv\Lib\site-packages\mypy\test\testtypegen.py

### Classes
- TypeExportSuite

## venv\Lib\site-packages\mypy\test\testtypes.py

### Classes
- TypesSuite
- TypeOpsSuite
- JoinSuite
- MeetSuite
- SameTypeSuite
- RemoveLastKnownValueSuite
- ShallowOverloadMatchingSuite
- TestExpandTypeLimitGetProperType

### Functions
- make_call

## venv\Lib\site-packages\mypy\test\testutil.py

### Classes
- TestGetTerminalSize
- TestWriteJunitXml

## venv\Lib\site-packages\mypy\test\typefixture.py

### Classes
- TypeFixture
- InterfaceTypeFixture

## venv\Lib\site-packages\mypy\test\update_data.py

### Functions
- update_testcase_output
- _iter_fixes

## venv\Lib\site-packages\mypy\test\visitors.py

### Classes
- SkippedNodeSearcher
- TypeAssertTransformVisitor

### Functions
- ignore_node

## venv\Lib\site-packages\mypy\traverser.py

### Classes
- TraverserVisitor
- ExtendedTraverserVisitor
- ReturnSeeker
- NameAndMemberCollector
- StringSeeker
- FuncCollectorBase
- YieldSeeker
- YieldFromSeeker
- AwaitSeeker
- ReturnCollector
- YieldCollector
- YieldFromCollector

### Functions
- has_return_statement
- all_name_and_member_expressions
- has_str_expression
- has_yield_expression
- has_yield_from_expression
- has_await_expression
- all_return_statements
- all_yield_expressions

## venv\Lib\site-packages\mypy\treetransform.py

### Classes
- TransformVisitor
- FuncMapInitializer

## venv\Lib\site-packages\mypy\tvar_scope.py

### Classes
- TypeVarLikeDefaultFixer
- TypeVarLikeScope

## venv\Lib\site-packages\mypy\type_visitor.py

### Classes
- TypeVisitor
- SyntheticTypeVisitor
- TypeTranslator
- TypeQuery
- BoolTypeQuery

## venv\Lib\site-packages\mypy\typeanal.py

### Classes
- TypeAnalyser
- MsgCallback
- DivergingAliasDetector
- HasExplicitAny
- HasAnyFromUnimportedType
- CollectAllInnerTypesQuery
- HasSelfType
- FindTypeVarVisitor
- TypeVarDefaultTranslator

### Functions
- analyze_type_alias
- get_omitted_any
- fix_type_var_tuple_argument
- fix_instance
- instantiate_type_alias
- set_any_tvars
- detect_diverging_alias
- check_for_explicit_any
- has_explicit_any
- has_any_from_unimported_type
- collect_all_inner_types
- make_optional_type
- validate_instance
- find_self_type
- unknown_unpack
- check_vec_type_args

## venv\Lib\site-packages\mypy\typeops.py

### Classes
- TypeVarExtractor
- FreezeTypeVarsVisitor

### Functions
- is_recursive_pair
- tuple_fallback
- get_self_type
- type_object_type
- is_valid_constructor
- type_object_type_from_function
- class_callable
- map_type_from_supertype
- supported_self_type
- bind_self
- erase_to_bound
- callable_corresponding_argument
- simple_literal_type
- is_simple_literal
- make_simplified_union
- _remove_redundant_union_items
- _get_type_method_ret_type
- true_only
- false_only
- true_or_false
- erase_def_to_union_or_bound
- erase_to_union_or_bound
- function_type
- callable_type
- try_getting_str_literals
- try_getting_str_literals_from_type
- try_getting_int_literals_from_type
- try_getting_literals_from_type
- is_literal_type_like
- is_singleton_identity_type
- is_singleton_equality_type
- try_expanding_sum_type_to_union
- try_contracting_literals_in_union
- coerce_to_literal
- get_type_vars
- get_all_type_vars
- freeze_all_type_vars
- custom_special_method
- separate_union_literals
- try_getting_instance_fallback
- fixup_partial_type
- _is_disjoint_base
- _get_disjoint_base_of
- can_have_shared_disjoint_base

## venv\Lib\site-packages\mypy\types.py

### Classes
- TypeOfAny
- Type
- TypeAliasType
- TypeGuardedType
- RequiredType
- ReadOnlyType
- ProperType
- TypeVarId
- TypeVarLikeType
- TypeVarType
- ParamSpecFlavor
- ParamSpecType
- TypeVarTupleType
- UnboundType
- CallableArgument
- TypeList
- UnpackType
- AnyType
- UninhabitedType
- NoneType
- ErasedType
- DeletedType
- ExtraAttrs
- Instance
- InstanceCache
- FunctionLike
- FormalArgument
- Parameters
- CallableType
- Overloaded
- TupleType
- TypedDictType
- RawExpressionType
- LiteralType
- UnionType
- PartialType
- EllipsisType
- TypeType
- PlaceholderType
- TypeStrVisitor
- TrivialSyntheticTypeTranslator
- CollectAliasesVisitor
- HasTypeVars
- HasRecursiveType
- InstantiateAliasVisitor

### Functions
- deserialize_type
- get_proper_type
- get_proper_type
- get_proper_type
- get_proper_types
- get_proper_types
- get_proper_types
- is_named_instance
- has_type_vars
- has_recursive_types
- split_with_prefix_and_suffix
- extend_args_for_prefix_and_suffix
- flatten_nested_unions
- find_unpack_in_list
- flatten_nested_tuples
- is_literal_type
- is_unannotated_any
- callable_with_ellipsis
- remove_dups
- type_vars_as_args
- read_type
- read_function_like
- read_type_var_likes
- read_type_opt
- write_type_opt
- read_type_list
- write_type_list
- read_type_map
- write_type_map

## venv\Lib\site-packages\mypy\types_utils.py

### Functions
- flatten_types
- strip_type
- is_invalid_recursive_alias
- get_bad_type_type_item
- is_union_with_any
- is_generic_instance
- is_overlapping_none
- remove_optional
- is_self_type_like
- store_argument_type

## venv\Lib\site-packages\mypy\typestate.py

### Classes
- TypeState

### Functions
- reset_global_state

## venv\Lib\site-packages\mypy\typetraverser.py

### Classes
- TypeTraverserVisitor

## venv\Lib\site-packages\mypy\typevars.py

### Functions
- fill_typevars
- fill_typevars_with_any
- has_no_typevars

## venv\Lib\site-packages\mypy\typevartuples.py

### Functions
- split_with_instance
- erased_vars

## venv\Lib\site-packages\mypy\util.py

### Classes
- DecodeError
- IdMapper
- FancyFormatter

### Functions
- is_dunder
- is_sunder
- split_module_names
- module_prefix
- split_target
- short_type
- find_python_encoding
- bytes_to_human_readable_repr
- decode_python_encoding
- read_py_file
- trim_source_line
- get_mypy_comments
- _generate_junit_contents
- write_junit_xml
- get_prefix
- correct_relative_import
- get_class_descriptors
- replace_object_state
- is_sub_path_normabs
- hard_exit
- unmangle
- get_unique_redefinition_name
- check_python_version
- count_stats
- split_words
- get_terminal_width
- soft_wrap
- hash_digest
- hash_digest_bytes
- parse_gray_color
- should_force_color
- is_typeshed_file
- is_stdlib_file
- is_stub_package_file
- unnamed_function
- time_spent_us
- plural_s
- quote_docstring
- json_dumps
- json_loads
- get_available_threads
- hash_path_stem

## venv\Lib\site-packages\mypy\version.py

## venv\Lib\site-packages\mypy\visitor.py

### Classes
- ExpressionVisitor
- StatementVisitor
- PatternVisitor
- NodeVisitor

## venv\Lib\site-packages\mypy_extensions.py

### Classes
- _TypedDictMeta
- _DEPRECATED_NoReturn
- _FlexibleAliasClsApplied
- _FlexibleAliasCls
- _NativeIntMeta
- i64
- i32
- i16
- u8

### Functions
- _check_fails
- _dict_new
- _typeddict_new
- Arg
- DefaultArg
- NamedArg
- DefaultNamedArg
- VarArg
- KwArg
- trait
- mypyc_attr
- _warn_deprecation
- __getattr__

## venv\Lib\site-packages\mypyc\__init__.py

## venv\Lib\site-packages\mypyc\__main__.py

### Functions
- main

## venv\Lib\site-packages\mypyc\analysis\__init__.py

## venv\Lib\site-packages\mypyc\analysis\attrdefined.py

### Classes
- AttributeMaybeDefinedVisitor
- AttributeMaybeUndefinedVisitor

### Functions
- analyze_always_defined_attrs
- analyze_always_defined_attrs_in_class
- find_always_defined_attributes
- find_sometimes_defined_attributes
- mark_attr_initialization_ops
- attributes_initialized_by_init_call
- attributes_maybe_initialized_by_init_call
- analyze_maybe_defined_attrs_in_init
- analyze_maybe_undefined_attrs_in_init
- update_always_defined_attrs_using_subclasses
- detect_undefined_bitmap

## venv\Lib\site-packages\mypyc\analysis\blockfreq.py

### Functions
- frequently_executed_blocks

## venv\Lib\site-packages\mypyc\analysis\capsule_deps.py

### Functions
- find_implicit_op_dependencies
- find_type_dependencies
- find_class_dependencies
- collect_type_deps

## venv\Lib\site-packages\mypyc\analysis\dataflow.py

### Classes
- CFG
- AnalysisResult
- BaseAnalysisVisitor
- DefinedVisitor
- BorrowedArgumentsVisitor
- UndefinedVisitor
- LivenessVisitor

### Functions
- get_cfg
- get_real_target
- cleanup_cfg
- analyze_maybe_defined_regs
- analyze_must_defined_regs
- analyze_borrowed_arguments
- non_trivial_sources
- analyze_live_regs
- run_analysis

## venv\Lib\site-packages\mypyc\analysis\ircheck.py

### Classes
- FnError
- IrCheckException
- OpChecker

### Functions
- check_func_ir
- assert_func_ir_valid
- check_op_sources_valid
- can_coerce_to
- is_valid_ptr_displacement_type
- is_pointer_arithmetic

## venv\Lib\site-packages\mypyc\analysis\selfleaks.py

### Classes
- SelfLeakedVisitor

### Functions
- analyze_self_leaks

## venv\Lib\site-packages\mypyc\annotate.py

### Classes
- Annotation
- AnnotatedSource
- ASTAnnotateVisitor

### Functions
- generate_annotated_html
- generate_annotations
- function_annotations
- get_str_literal
- get_max_prio
- generate_html_report
- colorize_line

## venv\Lib\site-packages\mypyc\build.py

### Classes
- ModDesc

### Functions
- get_extension
- setup_mypycify_vars
- fail
- emit_messages
- get_mypy_config
- is_package_source
- generate_c_extension_shim
- group_name
- include_dir
- generate_c
- build_using_shared_lib
- build_single_module
- write_file
- _patch_setuptools_copy_extensions_to_source
- construct_groups
- get_header_deps
- mypyc_build
- get_cflags
- mypycify

## venv\Lib\site-packages\mypyc\build_setup.py

### Functions
- spawn

## venv\Lib\site-packages\mypyc\codegen\__init__.py

## venv\Lib\site-packages\mypyc\codegen\cstring.py

### Functions
- encode_bytes_as_c_string
- c_string_initializer

## venv\Lib\site-packages\mypyc\codegen\emit.py

### Classes
- HeaderDeclaration
- EmitterContext
- ErrorHandler
- AssignHandler
- GotoHandler
- TracebackAndGotoHandler
- ReturnHandler
- Emitter

### Functions
- c_array_initializer
- native_function_doc_initializer

## venv\Lib\site-packages\mypyc\codegen\emitclass.py

### Functions
- native_slot
- dunder_attr_slot
- generate_call_wrapper
- slot_key
- generate_slots
- generate_class_type_decl
- generate_class_reuse
- generate_class
- getter_name
- setter_name
- generate_object_struct
- generate_vtables
- generate_offset_table
- generate_vtable
- generate_setup_for_class
- emit_clear_bitmaps
- emit_attr_defaults_func_call
- emit_setup_or_dunder_new_call
- generate_constructor_for_class
- generate_init_for_class
- generate_new_for_class
- generate_new_for_trait
- generate_traverse_for_class
- generate_clear_for_class
- generate_dealloc_for_class
- emit_reuse_dealloc
- generate_finalize_for_class
- generate_methods_table
- generate_side_table_for_class
- generate_getseter_declarations
- generate_getseters_table
- generate_getseters
- generate_getter
- generate_setter
- generate_readonly_getter
- generate_property_setter
- has_managed_dict
- native_class_doc_initializer
- generate_coroutine_setup

## venv\Lib\site-packages\mypyc\codegen\emitfunc.py

### Classes
- FunctionEmitterVisitor

### Functions
- native_function_type
- native_function_type_from_decl
- native_function_header
- generate_native_function
- encode_c_string_literal

## venv\Lib\site-packages\mypyc\codegen\emitmodule.py

### Classes
- MarkedDeclaration
- MypycPlugin
- GroupGenerator

### Functions
- parse_and_typecheck
- compile_scc_to_ir
- compile_modules_to_ir
- compile_ir_to_c
- _load_cached_group_files
- get_ir_cache_name
- get_state_ir_cache_name
- write_cache
- load_scc_from_cache
- collect_source_dependencies
- collect_header_dependencies
- compile_modules_to_c
- generate_function_declaration
- pointerize
- group_dir
- toposort
- is_fastcall_supported
- collect_literals
- c_string_array_initializer

## venv\Lib\site-packages\mypyc\codegen\emitwrapper.py

### Classes
- WrapperGenerator

### Functions
- wrapper_function_header
- generate_traceback_code
- make_arg_groups
- reorder_arg_groups
- make_static_kwlist
- make_format_string
- generate_wrapper_function
- legacy_wrapper_function_header
- generate_legacy_wrapper_function
- generate_dunder_wrapper
- generate_ipow_wrapper
- generate_bin_op_wrapper
- generate_bin_op_forward_only_wrapper
- generate_bin_op_reverse_only_wrapper
- generate_bin_op_both_wrappers
- generate_bin_op_reverse_dunder_call
- handle_third_pow_argument
- generate_richcompare_wrapper
- generate_get_wrapper
- generate_hash_wrapper
- generate_len_wrapper
- generate_bool_wrapper
- generate_del_item_wrapper
- generate_set_del_item_wrapper
- generate_set_del_item_wrapper_inner
- generate_contains_wrapper
- generate_wrapper_core
- generate_arg_check

## venv\Lib\site-packages\mypyc\codegen\literals.py

### Classes
- Literals

### Functions
- _is_literal_value
- _encode_str_values
- _encode_bytes_values
- format_int
- format_str_literal
- _encode_int_values
- float_to_c
- _encode_float_values
- _encode_complex_values

## venv\Lib\site-packages\mypyc\common.py

### Functions
- shared_lib_name
- short_name
- get_id_from_name
- short_id_from_name
- bitmap_name

## venv\Lib\site-packages\mypyc\crash.py

### Functions
- catch_errors
- crash_report

## venv\Lib\site-packages\mypyc\errors.py

### Classes
- Errors

## venv\Lib\site-packages\mypyc\ir\__init__.py

## venv\Lib\site-packages\mypyc\ir\class_ir.py

### Classes
- VTableMethod
- ClassIR
- NonExtClassInfo

### Functions
- serialize_vtable_entry
- serialize_vtable
- deserialize_vtable_entry
- deserialize_vtable
- all_concrete_classes

## venv\Lib\site-packages\mypyc\ir\deps.py

### Classes
- Capsule
- SourceDep
- HeaderDep

## venv\Lib\site-packages\mypyc\ir\func_ir.py

### Classes
- RuntimeArg
- FuncSignature
- FuncDecl
- FuncIR

### Functions
- num_bitmap_args
- all_values
- all_values_full
- get_text_signature
- _find_default_argument
- _extract_python_literal

## venv\Lib\site-packages\mypyc\ir\module_ir.py

### Classes
- ModuleIR

### Functions
- deserialize_modules

## venv\Lib\site-packages\mypyc\ir\ops.py

### Classes
- BasicBlock
- Value
- Register
- Integer
- Float
- CString
- Undef
- Op
- BaseAssign
- Assign
- AssignMulti
- ControlOp
- Goto
- Branch
- Return
- Unreachable
- RegisterOp
- IncRef
- DecRef
- Call
- MethodCall
- PrimitiveDescription
- PrimitiveOp
- LoadErrorValue
- LoadLiteral
- GetAttr
- SetAttr
- LoadStatic
- InitStatic
- TupleSet
- TupleGet
- Cast
- Box
- Unbox
- RaiseStandardError
- CallC
- Truncate
- Extend
- LoadGlobal
- IntOp
- ComparisonOp
- FloatOp
- FloatNeg
- FloatComparisonOp
- LoadMem
- SetMem
- GetElement
- GetElementPtr
- SetElement
- LoadAddress
- KeepAlive
- Unborrow
- OpVisitor
- DeserMaps

### Functions
- has_fixed_width_int

## venv\Lib\site-packages\mypyc\ir\pprint.py

### Classes
- IRPrettyPrintVisitor

### Functions
- format_registers
- format_blocks
- format_func
- format_modules
- generate_names_for_ir

## venv\Lib\site-packages\mypyc\ir\rtypes.py

### Classes
- RType
- RTypeVisitor
- RVoid
- RPrimitive
- TupleNameVisitor
- RTuple
- RStruct
- RInstance
- RVec
- RUnion
- RArray

### Functions
- deserialize_type
- is_native_rprimitive
- is_tagged
- is_any_int
- is_int_rprimitive
- is_short_int_rprimitive
- is_int16_rprimitive
- is_int32_rprimitive
- is_int64_rprimitive
- is_fixed_width_rtype
- is_uint8_rprimitive
- is_uint32_rprimitive
- is_uint64_rprimitive
- is_c_py_ssize_t_rprimitive
- is_pointer_rprimitive
- is_float_rprimitive
- is_bool_rprimitive
- is_bit_rprimitive
- is_bool_or_bit_rprimitive
- is_object_rprimitive
- is_none_rprimitive
- is_list_rprimitive
- is_dict_rprimitive
- is_set_rprimitive
- is_frozenset_rprimitive
- is_str_rprimitive
- is_bytes_rprimitive
- is_bytearray_rprimitive
- is_tuple_rprimitive
- is_range_rprimitive
- is_sequence_rprimitive
- is_immutable_rprimitive
- compute_rtype_alignment
- compute_rtype_size
- compute_aligned_offsets_and_size
- flatten_nested_unions
- optional_value_type
- is_optional_type
- check_native_int_range

## venv\Lib\site-packages\mypyc\irbuild\__init__.py

## venv\Lib\site-packages\mypyc\irbuild\ast_helpers.py

### Functions
- process_conditional
- maybe_process_conditional_comparison
- is_borrow_friendly_expr

## venv\Lib\site-packages\mypyc\irbuild\builder.py

### Classes
- IRVisitor
- UnsupportedException
- IRBuilder

### Functions
- gen_arg_defaults
- remangle_redefinition_name
- get_call_target_fullname
- create_type_params
- calculate_arg_defaults

## venv\Lib\site-packages\mypyc\irbuild\callable_class.py

### Functions
- setup_callable_class
- add_coroutine_properties
- add_call_to_callable_class
- add_get_to_callable_class
- instantiate_callable_class

## venv\Lib\site-packages\mypyc\irbuild\classdef.py

### Classes
- ClassBuilder
- NonExtClassBuilder
- ExtClassBuilder
- DataClassBuilder
- AttrsClassBuilder

### Functions
- transform_class_def
- allocate_class
- make_generic_base_class
- populate_non_ext_bases
- find_non_ext_metaclass
- setup_non_ext_dict
- add_non_ext_class_attr_ann
- add_non_ext_class_attr
- find_attr_initializers
- generate_attr_defaults_init
- check_deletable_declaration
- create_ne_from_eq
- gen_glue_ne_method
- load_non_ext_class
- load_decorated_class
- cache_class_attrs
- create_mypyc_attrs_tuple
- add_dunders_to_non_ext_dict

## venv\Lib\site-packages\mypyc\irbuild\constant_fold.py

### Functions
- constant_fold_expr
- constant_fold_binary_op_extended

## venv\Lib\site-packages\mypyc\irbuild\context.py

### Classes
- FuncInfo
- ImplicitClass
- GeneratorClass

## venv\Lib\site-packages\mypyc\irbuild\env_class.py

### Functions
- setup_env_class
- finalize_env_class
- instantiate_env_class
- load_env_registers
- load_outer_env
- load_outer_envs
- num_bitmap_args
- add_args_to_env
- add_vars_to_env
- setup_func_for_recursive_call
- is_free_variable

## venv\Lib\site-packages\mypyc\irbuild\expression.py

### Functions
- transform_name_expr
- transform_member_expr
- check_instance_attribute_access_through_class
- transform_super_expr
- transform_call_expr
- translate_call
- translate_refexpr_call
- translate_method_call
- call_classmethod
- translate_super_method_call
- _get_vec_capacity
- translate_vec_create_from_iterable
- vec_from_iterable
- translate_cast_expr
- transform_unary_expr
- transform_op_expr
- try_optimize_int_floor_divide
- transform_index_expr
- try_constant_fold
- try_gen_slice_op
- transform_conditional_expr
- set_literal_values
- precompute_set_literal
- transform_comparison_expr
- try_specialize_in_expr
- translate_is_none
- transform_basic_comparison
- translate_printf_style_formatting
- transform_int_expr
- transform_float_expr
- transform_complex_expr
- transform_str_expr
- transform_bytes_expr
- transform_ellipsis
- transform_list_expr
- _visit_list_display
- transform_tuple_expr
- _visit_tuple_display
- transform_dict_expr
- transform_set_expr
- _visit_display
- transform_list_comprehension
- transform_set_comprehension
- transform_dictionary_comprehension
- _dict_comp_body
- _translate_comprehension_with_scope
- transform_slice_expr
- transform_generator_expr
- transform_assignment_expr
- transform_math_literal

## venv\Lib\site-packages\mypyc\irbuild\for_helpers.py

### Classes
- ForGenerator
- ForIterable
- ForNativeGenerator
- ForAsyncIterable
- ForSequence
- ForDictionaryCommon
- ForDictionaryKeys
- ForDictionaryValues
- ForDictionaryItems
- ForRange
- ForInfiniteCounter
- ForEnumerate
- ForZip

### Functions
- for_loop_helper
- for_loop_helper_with_index
- sequence_from_generator_preallocate_helper
- translate_list_comprehension
- raise_error_if_contains_unreachable_names
- translate_set_comprehension
- translate_vec_comprehension
- comprehension_helper
- is_range_ref
- make_for_loop_generator
- unsafe_index
- get_expr_length
- get_expr_length_value

## venv\Lib\site-packages\mypyc\irbuild\format_str_tokenizer.py

### Classes
- FormatOp

### Functions
- generate_format_ops
- tokenizer_printf_style
- tokenizer_format_call
- convert_format_expr_to_str
- join_formatted_strings
- convert_format_expr_to_bytes
- join_formatted_bytes

## venv\Lib\site-packages\mypyc\irbuild\function.py

### Classes
- ArgInfo

### Functions
- transform_func_def
- transform_overloaded_func_def
- transform_decorator
- transform_lambda_expr
- gen_func_item
- gen_func_body
- has_nested_func_self_reference
- gen_func_ir
- generate_getattr_wrapper
- generate_setattr_wrapper
- handle_ext_method
- handle_non_ext_method
- gen_func_ns
- load_decorated_func
- is_decorated
- gen_glue
- get_args
- gen_glue_method
- check_native_override
- gen_glue_property
- gen_glue_property_setter
- get_func_target
- load_type
- load_func
- generate_singledispatch_dispatch_function
- gen_calls_to_correct_impl
- gen_dispatch_func_ir
- generate_dispatch_glue_native_function
- generate_singledispatch_callable_class_ctor
- add_register_method_to_callable_class
- load_singledispatch_registry
- singledispatch_main_func_name
- maybe_insert_into_registry_dict
- get_native_impl_ids
- gen_property_getter_ir
- gen_property_setter_ir

## venv\Lib\site-packages\mypyc\irbuild\generator.py

### Functions
- gen_generator_func
- gen_generator_func_body
- instantiate_generator_class
- setup_generator_class
- create_switch_for_generator_class
- populate_switch_for_generator_class
- add_raise_exception_blocks_to_generator_class
- add_methods_to_generator_class
- add_helper_to_generator_class
- add_iter_to_generator_class
- add_next_to_generator_class
- add_send_to_generator_class
- add_throw_to_generator_class
- add_close_to_generator_class
- add_await_to_generator_class
- setup_env_for_generator_class

## venv\Lib\site-packages\mypyc\irbuild\ll_builder.py

### Classes
- LowLevelIRBuilder
- ForBuilder

### Functions
- num_positional_args

## venv\Lib\site-packages\mypyc\irbuild\main.py

### Functions
- build_ir
- transform_mypy_file

## venv\Lib\site-packages\mypyc\irbuild\mapper.py

### Classes
- Mapper

## venv\Lib\site-packages\mypyc\irbuild\match.py

### Classes
- MatchVisitor

### Functions
- prep_sequence_pattern
- extract_dunder_match_args_names

## venv\Lib\site-packages\mypyc\irbuild\missingtypevisitor.py

### Classes
- MissingTypesVisitor

## venv\Lib\site-packages\mypyc\irbuild\nonlocalcontrol.py

### Classes
- NonlocalControl
- BaseNonlocalControl
- LoopNonlocalControl
- GeneratorNonlocalControl
- CleanupNonlocalControl
- TryFinallyNonlocalControl
- ExceptNonlocalControl
- FinallyNonlocalControl

## venv\Lib\site-packages\mypyc\irbuild\prebuildvisitor.py

### Classes
- _LambdaChecker
- PreBuildVisitor

### Functions
- _comprehension_has_lambda

## venv\Lib\site-packages\mypyc\irbuild\prepare.py

### Classes
- SingledispatchInfo
- SingledispatchVisitor
- RegisteredImpl

### Functions
- build_type_map
- is_from_module
- load_type_map
- get_module_func_defs
- prepare_func_def
- create_generator_class_for_func
- prepare_method_def
- prepare_fast_path
- is_valid_multipart_property_def
- can_subclass_builtin
- get_removed_base_fullname
- find_non_acyclic_base
- validate_acyclic_class_bases
- prepare_class_def
- prepare_methods_and_attributes
- prepare_implicit_property_accessors
- add_property_methods_for_attribute_if_needed
- add_getter_declaration
- add_setter_declaration
- check_matching_args
- prepare_init_method
- prepare_non_ext_class_def
- find_singledispatch_register_impls
- get_singledispatch_register_call_info
- registered_impl_from_possible_register_call
- adjust_generator_classes_of_methods

## venv\Lib\site-packages\mypyc\irbuild\specialize.py

### Functions
- _apply_specialization
- apply_function_specialization
- apply_method_specialization
- specialize_function
- specialize_dunder
- apply_dunder_specialization
- translate_globals
- translate_builtins_with_unary_dunder
- translate_len
- translate_vec_to_list
- dict_methods_fast_path
- translate_list_from_generator_call
- translate_vec_to_tuple
- translate_tuple_from_generator_call
- translate_set_from_generator_call
- faster_min_max
- translate_safe_generator_call
- translate_any_call
- translate_all_call
- any_all_helper
- translate_sum_call
- translate_dataclasses_field_call
- translate_next_call
- translate_isinstance
- translate_dict_setdefault
- translate_str_format
- translate_fstring
- str_encode_fast_path
- bytes_decode_fast_path
- translate_i64
- translate_i32
- translate_i16
- translate_u8
- truncate_literal
- translate_int
- translate_bool
- translate_float
- translate_ord
- is_object
- is_super_or_object
- translate_object_new
- translate_object_setattr
- specialize_int_to_bytes
- translate_getitem_with_bounds_check
- translate_bytes_writer_get_item
- translate_bytes_writer_set_item
- translate_string_writer_get_item
- translate_bytes_get_item
- translate_vec_append
- translate_vec_extend
- translate_vec_remove
- translate_vec_pop

## venv\Lib\site-packages\mypyc\irbuild\statement.py

### Classes
- ImportFromBucket
- AwaitDetector

### Functions
- transform_block
- transform_expression_stmt
- transform_return_stmt
- check_unsupported_cls_assignment
- transform_assignment_stmt
- is_simple_lvalue
- transform_operator_assignment_stmt
- import_globals_id_and_name
- transform_import
- split_import_group_to_python_and_native
- transform_imports_without_grouping
- transform_non_native_import_group
- transform_import_from
- group_consecutive
- classify_import_from
- transform_import_from_buckets
- transform_import_all
- transform_if_stmt
- transform_while_stmt
- transform_for_stmt
- transform_break_stmt
- transform_continue_stmt
- transform_raise_stmt
- transform_try_except
- transform_try_except_stmt
- try_finally_try
- try_finally_entry_blocks
- try_finally_body
- try_finally_resolve_control
- transform_try_finally_stmt
- transform_try_finally_stmt_async
- transform_try_stmt
- get_sys_exc_info
- transform_with
- transform_with_stmt
- transform_assert_stmt
- transform_del_stmt
- transform_del_item
- emit_yield
- emit_yield_from_or_await
- emit_await
- transform_yield_expr
- transform_yield_from_expr
- transform_await_expr
- transform_match_stmt
- transform_type_alias_stmt

## venv\Lib\site-packages\mypyc\irbuild\targets.py

### Classes
- AssignmentTarget
- AssignmentTargetRegister
- AssignmentTargetIndex
- AssignmentTargetAttr
- AssignmentTargetTuple

## venv\Lib\site-packages\mypyc\irbuild\util.py

### Classes
- MypycAttrs

### Functions
- is_final_decorator
- is_trait_decorator
- is_trait
- dataclass_decorator_type
- is_dataclass_decorator
- is_dataclass
- dataclass_type
- get_mypyc_attr_literal
- get_mypyc_attr_call
- get_mypyc_attrs
- is_extension_class
- get_explicit_native_class
- is_implicit_extension_class
- get_func_def
- concrete_arg_kind
- is_constant
- bytes_from_str

## venv\Lib\site-packages\mypyc\irbuild\vec.py

### Functions
- as_platform_int
- vec_create
- vec_create_initialized
- vec_create_from_values
- step_size
- vec_item_type_info
- vec_len
- vec_len_native
- vec_items
- vec_item_ptr
- vec_load_mem_item
- vec_set_mem_item
- vec_check_and_adjust_index
- vec_get_item
- vec_get_item_unsafe
- vec_set_item
- vec_init_item_unsafe
- convert_to_t_ext_item
- convert_from_t_ext_item
- vec_item_type
- vec_append
- vec_extend
- vec_pop
- vec_remove
- vec_contains
- vec_slice
- vec_to_list
- vec_to_tuple
- supports_vec_to_sequence
- _vec_to_sequence

## venv\Lib\site-packages\mypyc\irbuild\visitor.py

### Classes
- IRBuilderVisitor

## venv\Lib\site-packages\mypyc\irbuild\vtable.py

### Functions
- compute_vtable
- specialize_parent_vtable

## venv\Lib\site-packages\mypyc\lib-rt\build_setup.py

### Functions
- spawn

## venv\Lib\site-packages\mypyc\lower\__init__.py

## venv\Lib\site-packages\mypyc\lower\int_ops.py

### Classes
- IntComparisonOpDescription

### Functions
- compare_tagged
- lower_int_eq
- lower_int_ne
- lower_int_lt
- lower_int_le
- lower_int_gt
- lower_int_ge

## venv\Lib\site-packages\mypyc\lower\list_ops.py

### Functions
- buf_init_item
- list_items
- list_item_ptr
- list_get_item_unsafe

## venv\Lib\site-packages\mypyc\lower\misc_ops.py

### Functions
- var_object_size
- propagate_if_error_op

## venv\Lib\site-packages\mypyc\lower\registry.py

### Functions
- lower_primitive_op

## venv\Lib\site-packages\mypyc\namegen.py

### Classes
- NameGenerator

### Functions
- exported_name
- make_module_translation_map
- candidate_suffixes

## venv\Lib\site-packages\mypyc\options.py

### Classes
- CompilerOptions

## venv\Lib\site-packages\mypyc\primitives\__init__.py

## venv\Lib\site-packages\mypyc\primitives\bytearray_ops.py

## venv\Lib\site-packages\mypyc\primitives\bytes_ops.py

## venv\Lib\site-packages\mypyc\primitives\dict_ops.py

## venv\Lib\site-packages\mypyc\primitives\exc_ops.py

## venv\Lib\site-packages\mypyc\primitives\float_ops.py

## venv\Lib\site-packages\mypyc\primitives\generic_ops.py

## venv\Lib\site-packages\mypyc\primitives\int_ops.py

### Functions
- int_binary_primitive
- int_binary_op
- int_unary_op

## venv\Lib\site-packages\mypyc\primitives\librt_random_ops.py

## venv\Lib\site-packages\mypyc\primitives\librt_strings_ops.py

## venv\Lib\site-packages\mypyc\primitives\librt_time_ops.py

## venv\Lib\site-packages\mypyc\primitives\librt_vecs_ops.py

## venv\Lib\site-packages\mypyc\primitives\list_ops.py

## venv\Lib\site-packages\mypyc\primitives\misc_ops.py

## venv\Lib\site-packages\mypyc\primitives\registry.py

### Classes
- CFunctionDescription
- LoadAddressDescription

### Functions
- method_op
- function_op
- binary_op
- custom_op
- custom_primitive_op
- unary_op
- load_address_op
- load_global_op

## venv\Lib\site-packages\mypyc\primitives\set_ops.py

## venv\Lib\site-packages\mypyc\primitives\str_ops.py

## venv\Lib\site-packages\mypyc\primitives\tuple_ops.py

## venv\Lib\site-packages\mypyc\primitives\weakref_ops.py

## venv\Lib\site-packages\mypyc\rt_subtype.py

### Classes
- RTSubtypeVisitor

### Functions
- is_runtime_subtype

## venv\Lib\site-packages\mypyc\sametype.py

### Classes
- SameTypeVisitor

### Functions
- is_same_type
- is_same_signature
- is_same_method_signature

## venv\Lib\site-packages\mypyc\subtype.py

### Classes
- SubtypeVisitor

### Functions
- is_subtype

## venv\Lib\site-packages\mypyc\test\__init__.py

## venv\Lib\site-packages\mypyc\test\config.py

## venv\Lib\site-packages\mypyc\test\librt_cache.py

### Functions
- _librt_build_hash
- _generate_setup_py
- get_librt_path
- run_with_librt

## venv\Lib\site-packages\mypyc\test\test_alwaysdefined.py

### Classes
- TestAlwaysDefined

## venv\Lib\site-packages\mypyc\test\test_analysis.py

### Classes
- TestAnalysis

## venv\Lib\site-packages\mypyc\test\test_annotate.py

### Classes
- TestReport

## venv\Lib\site-packages\mypyc\test\test_capsule_deps.py

### Classes
- TestCapsuleDeps

## venv\Lib\site-packages\mypyc\test\test_cheader.py

### Classes
- TestHeaderInclusion

## venv\Lib\site-packages\mypyc\test\test_commandline.py

### Classes
- TestCommandLine

## venv\Lib\site-packages\mypyc\test\test_emit.py

### Classes
- TestEmitter

## venv\Lib\site-packages\mypyc\test\test_emitclass.py

### Classes
- TestEmitClass

## venv\Lib\site-packages\mypyc\test\test_emitfunc.py

### Classes
- TestFunctionEmitterVisitor
- TestGenerateFunction

## venv\Lib\site-packages\mypyc\test\test_emitmodule.py

### Classes
- FakeSCC
- TestEmitModule

## venv\Lib\site-packages\mypyc\test\test_emitwrapper.py

### Classes
- TestArgCheck

## venv\Lib\site-packages\mypyc\test\test_exceptions.py

### Classes
- TestExceptionTransform

## venv\Lib\site-packages\mypyc\test\test_external.py

### Classes
- TestExternal

## venv\Lib\site-packages\mypyc\test\test_irbuild.py

### Classes
- TestGenOps

## venv\Lib\site-packages\mypyc\test\test_ircheck.py

### Classes
- TestIrcheck

### Functions
- assert_has_error
- assert_no_errors

## venv\Lib\site-packages\mypyc\test\test_literals.py

### Classes
- TestLiterals

## venv\Lib\site-packages\mypyc\test\test_lowering.py

### Classes
- TestLowering

## venv\Lib\site-packages\mypyc\test\test_misc.py

### Classes
- TestMisc

## venv\Lib\site-packages\mypyc\test\test_namegen.py

### Classes
- TestNameGen

## venv\Lib\site-packages\mypyc\test\test_optimizations.py

### Classes
- OptimizationSuite
- TestCopyPropagation
- TestFlagElimination

## venv\Lib\site-packages\mypyc\test\test_pprint.py

### Classes
- TestGenerateNames

### Functions
- register
- make_block

## venv\Lib\site-packages\mypyc\test\test_rarray.py

### Classes
- TestRArray

## venv\Lib\site-packages\mypyc\test\test_refcount.py

### Classes
- TestRefCountTransform

## venv\Lib\site-packages\mypyc\test\test_run.py

### Classes
- TestRun
- TestRunMultiFile
- TestRunSeparate
- TestRunStrictDunderTyping

### Functions
- run_setup
- chdir_manager
- fix_native_line_number
- copy_output_files

## venv\Lib\site-packages\mypyc\test\test_serialization.py

### Functions
- get_dict
- get_function_dict
- assert_blobs_same
- assert_modules_same
- check_serialization_roundtrip

## venv\Lib\site-packages\mypyc\test\test_statement.py

### Classes
- TestStatementHelpers

### Functions
- make_builder

## venv\Lib\site-packages\mypyc\test\test_struct.py

### Classes
- TestStruct

## venv\Lib\site-packages\mypyc\test\test_tuplename.py

### Classes
- TestTupleNames

## venv\Lib\site-packages\mypyc\test\test_typeops.py

### Classes
- TestSubtype
- TestRuntimeSubtype
- TestUnionSimplification

## venv\Lib\site-packages\mypyc\test\testutil.py

### Classes
- MypycDataSuite

### Functions
- builtins_wrapper
- use_custom_builtins
- perform_test
- build_ir_for_single_file
- build_ir_for_single_file2
- update_testcase_output
- assert_test_output
- get_func_names
- remove_comment_lines
- print_with_line_numbers
- heading
- show_c
- fudge_dir_mtimes
- replace_word_size
- infer_ir_build_options_from_test_name
- has_test_name_tag

## venv\Lib\site-packages\mypyc\transform\__init__.py

## venv\Lib\site-packages\mypyc\transform\copy_propagation.py

### Classes
- CopyPropagationTransform

### Functions
- do_copy_propagation

## venv\Lib\site-packages\mypyc\transform\exceptions.py

### Functions
- insert_exception_handling
- add_default_handler_block
- split_blocks_at_errors
- primitive_call
- adjust_error_kinds
- insert_overlapping_error_value_check

## venv\Lib\site-packages\mypyc\transform\flag_elimination.py

### Classes
- FlagEliminationTransform

### Functions
- do_flag_elimination

## venv\Lib\site-packages\mypyc\transform\ir_transform.py

### Classes
- IRTransform
- PatchVisitor

### Functions
- is_empty_block

## venv\Lib\site-packages\mypyc\transform\log_trace.py

### Classes
- LogTraceEventTransform

### Functions
- insert_event_trace_logging
- get_load_global_name

## venv\Lib\site-packages\mypyc\transform\lower.py

### Classes
- LoweringVisitor

### Functions
- lower_ir

## venv\Lib\site-packages\mypyc\transform\refcount.py

### Functions
- insert_ref_count_opcodes
- is_maybe_undefined
- maybe_append_dec_ref
- maybe_append_inc_ref
- transform_block
- insert_branch_inc_and_decrefs
- after_branch_decrefs
- after_branch_increfs
- add_block
- make_value_ordering

## venv\Lib\site-packages\mypyc\transform\spill.py

### Functions
- insert_spills
- spill_regs

## venv\Lib\site-packages\mypyc\transform\uninit.py

### Functions
- insert_uninit_checks
- split_blocks_at_uninits
- check_for_uninit_using_bitmap
- update_register_assignments_to_set_bitmap

## venv\Lib\site-packages\numpy\__config__.py

### Classes
- DisplayModes

### Functions
- _cleanup
- _check_pyyaml
- show
- show_config

## venv\Lib\site-packages\numpy\__init__.py

### Functions
- _delvewheel_patch_1_11_2

## venv\Lib\site-packages\numpy\_array_api_info.py

### Classes
- __array_namespace_info__

## venv\Lib\site-packages\numpy\_configtool.py

### Functions
- main

## venv\Lib\site-packages\numpy\_core\__init__.py

### Functions
- _ufunc_reduce
- _DType_reconstruct
- _DType_reduce

## venv\Lib\site-packages\numpy\_core\_add_newdocs.py

### Functions
- _array_method_doc

## venv\Lib\site-packages\numpy\_core\_add_newdocs_scalars.py

### Functions
- numeric_type_aliases
- _get_platform_and_machine
- add_newdoc_for_scalar_type

## venv\Lib\site-packages\numpy\_core\_asarray.py

### Functions
- require

## venv\Lib\site-packages\numpy\_core\_dtype.py

### Functions
- _kind_name
- __str__
- __repr__
- _unpack_field
- _isunsized
- _construction_repr
- _scalar_str
- _byte_order_str
- _datetime_metadata_str
- _struct_dict_str
- _aligned_offset
- _is_packed
- _struct_list_str
- _struct_str
- _subarray_str
- _name_includes_bit_suffix
- _name_get

## venv\Lib\site-packages\numpy\_core\_dtype_ctypes.py

### Functions
- _from_ctypes_array
- _from_ctypes_structure
- _from_ctypes_scalar
- _from_ctypes_union
- dtype_from_ctypes_type

## venv\Lib\site-packages\numpy\_core\_exceptions.py

### Classes
- UFuncTypeError
- _UFuncNoLoopError
- _UFuncBinaryResolutionError
- _UFuncCastingError
- _UFuncInputCastingError
- _UFuncOutputCastingError
- _ArrayMemoryError

### Functions
- _unpack_tuple
- _display_as_base

## venv\Lib\site-packages\numpy\_core\_internal.py

### Classes
- dummy_ctype
- _missing_ctypes
- _ctypes
- _Stream

### Functions
- _makenames_list
- _usefields
- _array_descr
- _commastring
- _getintp_ctype
- _newnames
- _copy_fields
- _promote_fields
- _getfield_is_safe
- _view_is_safe
- _dtype_from_pep3118
- __dtype_from_pep3118
- _fix_names
- _add_trailing_padding
- _prod
- _gcd
- _lcm
- array_ufunc_errmsg_formatter
- array_function_errmsg_formatter
- _ufunc_doc_signature_formatter
- _ufunc_inspect_signature_builder
- npy_ctypes_check
- _convert_to_stringdtype_kwargs

## venv\Lib\site-packages\numpy\_core\_methods.py

### Functions
- _amax
- _amin
- _sum
- _prod
- _any
- _all
- _count_reduce_items
- _clip
- _mean
- _var
- _std
- _ptp
- _dump
- _dumps
- _bitwise_count

## venv\Lib\site-packages\numpy\_core\_string_helpers.py

### Functions
- english_lower
- english_upper
- english_capitalize

## venv\Lib\site-packages\numpy\_core\_type_aliases.py

## venv\Lib\site-packages\numpy\_core\_ufunc_config.py

### Classes
- _unspecified
- errstate

### Functions
- seterr
- geterr
- setbufsize
- getbufsize
- seterrcall
- geterrcall

## venv\Lib\site-packages\numpy\_core\arrayprint.py

### Classes
- FloatingFormat
- IntegerFormat
- BoolFormat
- ComplexFloatingFormat
- _TimelikeFormat
- DatetimeFormat
- TimedeltaFormat
- SubArrayFormat
- StructuredVoidFormat

### Functions
- _make_options_dict
- set_printoptions
- _set_printoptions
- get_printoptions
- _get_legacy_print_mode
- printoptions
- _leading_trailing
- _object_format
- repr_format
- str_format
- _get_formatdict
- _get_format_function
- _recursive_guard
- _array2string
- _array2string_dispatcher
- array2string
- _extendLine
- _extendLine_pretty
- _formatArray
- _none_or_positive_arg
- format_float_scientific
- format_float_positional
- _void_scalar_to_string
- dtype_is_implied
- dtype_short_repr
- _array_repr_implementation
- _array_repr_dispatcher
- array_repr
- _guarded_repr_or_str
- _array_str_implementation
- _array_str_dispatcher
- array_str

## venv\Lib\site-packages\numpy\_core\cversions.py

## venv\Lib\site-packages\numpy\_core\defchararray.py

### Classes
- chararray

### Functions
- _binary_op_dispatcher
- equal
- not_equal
- greater_equal
- less_equal
- greater
- less
- multiply
- partition
- rpartition
- array
- asarray

## venv\Lib\site-packages\numpy\_core\einsumfunc.py

### Functions
- _flop_count
- _compute_size_by_dict
- _find_contraction
- _optimal_path
- _parse_possible_contraction
- _update_other_results
- _greedy_path
- _parse_einsum_input
- _einsum_path_dispatcher
- einsum_path
- _parse_eq_to_pure_multiplication
- _parse_eq_to_batch_matmul
- _parse_output_order
- bmm_einsum
- _einsum_dispatcher
- einsum

## venv\Lib\site-packages\numpy\_core\fromnumeric.py

### Functions
- _wrapit
- _wrapfunc
- _wrapreduction
- _wrapreduction_any_all
- _take_dispatcher
- take
- _reshape_dispatcher
- reshape
- _choose_dispatcher
- choose
- _repeat_dispatcher
- repeat
- _put_dispatcher
- put
- _swapaxes_dispatcher
- swapaxes
- _transpose_dispatcher
- transpose
- _matrix_transpose_dispatcher
- matrix_transpose
- _partition_dispatcher
- partition
- _argpartition_dispatcher
- argpartition
- _sort_dispatcher
- sort
- _argsort_dispatcher
- argsort
- _argmax_dispatcher
- argmax
- _argmin_dispatcher
- argmin
- _searchsorted_dispatcher
- searchsorted
- _resize_dispatcher
- resize
- _squeeze_dispatcher
- squeeze
- _diagonal_dispatcher
- diagonal
- _trace_dispatcher
- trace
- _ravel_dispatcher
- ravel
- _nonzero_dispatcher
- nonzero
- _shape_dispatcher
- shape
- _compress_dispatcher
- compress
- _clip_dispatcher
- clip
- _sum_dispatcher
- sum
- _any_dispatcher
- any
- _all_dispatcher
- all
- _cumulative_func
- _cumulative_prod_dispatcher
- cumulative_prod
- _cumulative_sum_dispatcher
- cumulative_sum
- _cumsum_dispatcher
- cumsum
- _ptp_dispatcher
- ptp
- _max_dispatcher
- max
- amax
- _min_dispatcher
- min
- amin
- _prod_dispatcher
- prod
- _cumprod_dispatcher
- cumprod
- _ndim_dispatcher
- ndim
- _size_dispatcher
- size
- _round_dispatcher
- round
- around
- _mean_dispatcher
- mean
- _std_dispatcher
- std
- _var_dispatcher
- var

## venv\Lib\site-packages\numpy\_core\function_base.py

### Functions
- _linspace_dispatcher
- linspace
- _logspace_dispatcher
- logspace
- _geomspace_dispatcher
- geomspace
- _needs_add_docstring
- _add_docstring
- add_newdoc

## venv\Lib\site-packages\numpy\_core\getlimits.py

### Classes
- finfo
- iinfo

### Functions
- _fr0
- _fr1

## venv\Lib\site-packages\numpy\_core\memmap.py

### Classes
- memmap

## venv\Lib\site-packages\numpy\_core\multiarray.py

### Functions
- _override___module__
- empty_like
- concatenate
- inner
- where
- lexsort
- can_cast
- min_scalar_type
- result_type
- dot
- vdot
- bincount
- ravel_multi_index
- unravel_index
- copyto
- putmask
- packbits
- unpackbits
- shares_memory
- may_share_memory
- is_busday
- busday_offset
- busday_count
- datetime_as_string

## venv\Lib\site-packages\numpy\_core\numeric.py

### Functions
- _zeros_like_dispatcher
- zeros_like
- ones
- _ones_like_dispatcher
- ones_like
- _full_dispatcher
- full
- _full_like_dispatcher
- full_like
- _count_nonzero_dispatcher
- count_nonzero
- isfortran
- _argwhere_dispatcher
- argwhere
- _flatnonzero_dispatcher
- flatnonzero
- _correlate_dispatcher
- correlate
- _convolve_dispatcher
- convolve
- _outer_dispatcher
- outer
- _tensordot_dispatcher
- tensordot
- _roll_dispatcher
- roll
- _rollaxis_dispatcher
- rollaxis
- normalize_axis_tuple
- _moveaxis_dispatcher
- moveaxis
- _cross_dispatcher
- cross
- indices
- fromfunction
- _frombuffer
- isscalar
- binary_repr
- base_repr
- _maketup
- identity
- _allclose_dispatcher
- allclose
- _isclose_dispatcher
- isclose
- _array_equal_dispatcher
- _dtype_cannot_hold_nan
- array_equal
- _array_equiv_dispatcher
- array_equiv
- _astype_dispatcher
- astype
- extend_all

## venv\Lib\site-packages\numpy\_core\numerictypes.py

### Classes
- _PreprocessDTypeError

### Functions
- issctype
- obj2sctype
- issubclass_
- issubsctype
- _preprocess_dtype
- isdtype
- issubdtype
- sctype2char
- _scalar_type_key
- _register_types

## venv\Lib\site-packages\numpy\_core\overrides.py

### Functions
- get_array_function_like_doc
- finalize_array_function_like
- verify_matching_signatures
- array_function_dispatch
- array_function_from_dispatcher

## venv\Lib\site-packages\numpy\_core\printoptions.py

## venv\Lib\site-packages\numpy\_core\records.py

### Classes
- format_parser
- record
- recarray

### Functions
- find_duplicate
- _deprecate_shape_0_as_None
- fromarrays
- fromrecords
- fromstring
- get_remaining_size
- fromfile
- array

## venv\Lib\site-packages\numpy\_core\shape_base.py

### Functions
- _atleast_1d_dispatcher
- atleast_1d
- _atleast_2d_dispatcher
- atleast_2d
- _atleast_3d_dispatcher
- atleast_3d
- _arrays_for_stack_dispatcher
- _vhstack_dispatcher
- vstack
- hstack
- _stack_dispatcher
- stack
- _unstack_dispatcher
- unstack
- _block_format_index
- _block_check_depths_match
- _atleast_nd
- _accumulate
- _concatenate_shapes
- _block_info_recursion
- _block
- _block_dispatcher
- block
- _block_setup
- _block_slicing
- _block_concatenate

## venv\Lib\site-packages\numpy\_core\strings.py

### Functions
- _override___module__
- _get_num_chars
- _to_bytes_or_str_array
- _clean_args
- _multiply_dispatcher
- multiply
- _mod_dispatcher
- mod
- find
- rfind
- index
- rindex
- count
- startswith
- endswith
- _code_dispatcher
- decode
- encode
- _expandtabs_dispatcher
- expandtabs
- _just_dispatcher
- center
- ljust
- rjust
- _zfill_dispatcher
- zfill
- lstrip
- rstrip
- strip
- _unary_op_dispatcher
- upper
- lower
- swapcase
- capitalize
- title
- _replace_dispatcher
- replace
- _join_dispatcher
- _join
- _split_dispatcher
- _split
- _rsplit
- _splitlines_dispatcher
- _splitlines
- _partition_dispatcher
- partition
- rpartition
- _translate_dispatcher
- translate
- slice

## venv\Lib\site-packages\numpy\_core\tests\_locales.py

### Classes
- CommaDecimalPointLocale

### Functions
- find_comma_decimal_point_locale

## venv\Lib\site-packages\numpy\_core\tests\_natype.py

### Classes
- NAType

### Functions
- _create_binary_propagating_op
- _create_unary_propagating_op

## venv\Lib\site-packages\numpy\_core\tests\examples\cython\setup.py

## venv\Lib\site-packages\numpy\_core\tests\examples\limited_api\setup.py

## venv\Lib\site-packages\numpy\_core\tests\test__exceptions.py

### Classes
- TestArrayMemoryError
- TestUFuncNoLoopError
- TestAxisError

## venv\Lib\site-packages\numpy\_core\tests\test_abc.py

### Classes
- TestABC

## venv\Lib\site-packages\numpy\_core\tests\test_api.py

### Functions
- test_array_array
- test___array___refcount
- test_array_impossible_casts
- test_array_astype
- test_array_astype_to_string_discovery_empty
- test_array_astype_to_void
- test_object_array_astype_to_void
- test_array_astype_warning
- test_string_to_boolean_cast
- test_string_to_complex_cast
- test_none_to_nan_cast
- test_copyto_fromscalar
- test_copyto
- test_copyto_cast_safety
- test_copyto_permute
- test_copy_order
- test_contiguous_flags
- test_broadcast_arrays
- test_full_from_list
- test_astype_copyflag

## venv\Lib\site-packages\numpy\_core\tests\test_argparse.py

### Functions
- test_thread_safe_argparse_cache
- test_invalid_integers
- test_missing_arguments
- test_too_many_positional
- test_multiple_values
- test_string_fallbacks
- test_too_many_arguments_method_forwarding

## venv\Lib\site-packages\numpy\_core\tests\test_array_api_info.py

### Functions
- test_capabilities
- test_default_device
- test_default_dtypes
- test_dtypes_all
- test_dtypes_kind
- test_dtypes_tuple
- test_dtypes_invalid_kind
- test_dtypes_invalid_device
- test_devices

## venv\Lib\site-packages\numpy\_core\tests\test_array_coercion.py

### Classes
- TestStringDiscovery
- TestScalarDiscovery
- TestTimeScalars
- TestNested
- TestBadSequences
- TestArrayLikes
- TestAsArray
- TestSpecialAttributeLookupFailure

### Functions
- arraylikes
- scalar_instances
- is_parametric_dtype
- test_subarray_from_array_construction
- test_empty_string
- test_string_to_float_coercion_errors

## venv\Lib\site-packages\numpy\_core\tests\test_array_interface.py

### Functions
- get_module
- test_cstruct

## venv\Lib\site-packages\numpy\_core\tests\test_arraymethod.py

### Classes
- TestResolveDescriptors
- TestSimpleStridedCall
- TestClassGetItem

## venv\Lib\site-packages\numpy\_core\tests\test_arrayobject.py

### Classes
- MyArr
- MyArrNoWrap

### Functions
- test_matrix_transpose_raises_error_for_1d
- test_matrix_transpose_equals_transpose_2d
- test_matrix_transpose_equals_swapaxes
- test_array_wrap
- test_cleanup_with_refs_non_contig
- test_real_imag_attributes_non_complex
- test_real_imag_attributes_complex
- test_real_imag_attributes_object
- test_real_imag_ufunc_minimal

## venv\Lib\site-packages\numpy\_core\tests\test_arrayprint.py

### Classes
- TestArrayRepr
- TestComplexArray
- TestArray2String
- TestPrintOptions
- TestContextManager

### Functions
- test_unicode_object_array
- test_scalar_repr_numbers
- test_scalar_repr_special
- test_scalar_void_float_str
- test_printoptions_asyncio_safe
- test_multithreaded_array_printing
- test_user_defined_floating_dtype_printing_does_not_corrupt_precision
- test_array_dtype_short_repr

## venv\Lib\site-packages\numpy\_core\tests\test_casting_floatingpoint_errors.py

### Functions
- values_and_dtypes
- check_operations
- test_floatingpoint_errors_casting

## venv\Lib\site-packages\numpy\_core\tests\test_casting_unittests.py

### Classes
- Casting
- TestChanges
- TestCasting

### Functions
- simple_dtype_instances
- get_expected_stringlength
- _get_cancast_table

## venv\Lib\site-packages\numpy\_core\tests\test_conversion_utils.py

### Classes
- StringConverterTestCase
- TestByteorderConverter
- TestSortkindConverter
- TestSelectkindConverter
- TestSearchsideConverter
- TestOrderConverter
- TestClipmodeConverter
- TestCastingConverter
- TestIntpConverter

## venv\Lib\site-packages\numpy\_core\tests\test_cpu_dispatcher.py

### Functions
- test_dispatcher

## venv\Lib\site-packages\numpy\_core\tests\test_cpu_features.py

### Classes
- AbstractTest
- TestEnvPrivation
- Test_X86_Features
- Test_POWER_Features
- Test_ZARCH_Features
- Test_ARM_Features
- Test_LOONGARCH_Features
- Test_RISCV_Features

### Functions
- assert_features_equal
- _text_to_list

## venv\Lib\site-packages\numpy\_core\tests\test_custom_dtypes.py

### Classes
- TestSFloat

### Functions
- test_type_pickle
- test_is_numeric

## venv\Lib\site-packages\numpy\_core\tests\test_cython.py

### Classes
- TestDatetimeStrings

### Functions
- install_temp
- test_is_timedelta64_object
- test_is_datetime64_object
- test_get_datetime64_value
- test_get_timedelta64_value
- test_get_datetime64_unit
- test_abstract_scalars
- test_default_int
- test_ravel_axis
- test_convert_datetime64_to_datetimestruct
- test_multiiter_fields
- test_dtype_flags
- test_conv_intp
- test_npyiter_api
- test_fillwithbytes
- test_complex
- test_npystring_pack
- test_npystring_load
- test_npystring_multiple_allocators
- test_npystring_allocators_other_dtype
- test_npy_uintp_type_enum
- test_resize_refcheck

## venv\Lib\site-packages\numpy\_core\tests\test_datetime.py

### Classes
- TestDateTime
- TestDateTimeData

### Functions
- _assert_equal_hash
- test_comparisons_return_not_implemented

## venv\Lib\site-packages\numpy\_core\tests\test_defchararray.py

### Classes
- TestBasic
- TestVecString
- TestWhitespace
- TestChar
- TestComparisons
- TestComparisonsMixed1
- TestComparisonsMixed2
- TestInformation
- TestMethods
- TestOperations
- TestMethodsEmptyArray
- TestMethodsScalarValues

### Functions
- test_empty_indexing

## venv\Lib\site-packages\numpy\_core\tests\test_deprecations.py

### Classes
- _DeprecationTestCase
- _VisibleDeprecationTestCase
- TestTestDeprecated
- TestCtypesGetter
- TestPyIntConversion
- TestRemovedGlobals
- TestCharArray
- TestDeprecatedDTypeAliases
- TestDeprecatedArrayWrap
- TestDeprecatedArrayAttributeSetting
- TestDeprecatedViewDtypePropertySetter
- TestDeprecatedDTypeParenthesizedRepeatCount
- TestDTypeAlignBool
- TestFlatiterIndexing0dBoolIndex
- TestFlatiterIndexingFloatIndex
- TestWarningUtilityDeprecations
- TestTooManyArgsExtremum
- TestTypenameDeprecation
- TestRoundDeprecation
- TestDeprecatedGenericTimedelta
- TestTriDeprecationWithNonInteger
- TestTakeOutDtype

### Functions
- test_future_scalar_attributes

## venv\Lib\site-packages\numpy\_core\tests\test_dlpack.py

### Classes
- TestDLPack
- TestRegisterDlpackDtype

### Functions
- new_and_old_dlpack

## venv\Lib\site-packages\numpy\_core\tests\test_dtype.py

### Classes
- TestBuiltin
- TestRecord
- TestSubarray
- TestStructuredDtypeSparseFields
- TestMonsterType
- TestMetadata
- TestString
- TestDtypeAttributeDeletion
- TestDtypeAttributes
- TestDTypeMakeCanonical
- TestPickling
- TestPromotion
- TestFromDTypeAttribute
- TestFromDTypeProtocol
- TestDTypeClasses
- TestFromCTypes
- TestUserDType
- TestClassGetItem
- TestDTypeSignatures

### Functions
- assert_dtype_equal
- assert_dtype_not_equal
- iter_struct_object_dtypes
- test_rational2_uses_new_dtype_api
- test_rational_dtype
- test_dtypes_are_true
- test_invalid_dtype_string
- test_keyword_argument
- test_result_type_integers_and_unitless_timedelta64
- test_creating_dtype_with_dtype_class_errors

## venv\Lib\site-packages\numpy\_core\tests\test_einsum.py

### Classes
- TestEinsum
- TestEinsumPath

### Functions
- test_overlap
- test_einsum_chunking_precision

## venv\Lib\site-packages\numpy\_core\tests\test_errstate.py

### Classes
- TestErrstate

## venv\Lib\site-packages\numpy\_core\tests\test_extint128.py

### Functions
- exc_iter
- test_safe_binop
- test_to_128
- test_to_64
- test_mul_64_64
- test_add_128
- test_sub_128
- test_neg_128
- test_shl_128
- test_shr_128
- test_gt_128
- test_divmod_128_64
- test_floordiv_128_64
- test_ceildiv_128_64

## venv\Lib\site-packages\numpy\_core\tests\test_finfo.py

### Classes
- MachArLike

### Functions
- float16_ma
- float32_ma
- float64_ma
- test_finfo_properties

## venv\Lib\site-packages\numpy\_core\tests\test_function_base.py

### Classes
- PhysicalQuantity
- PhysicalQuantity2
- TestLogspace
- TestGeomspace
- TestLinspace
- TestAdd_newdoc

### Functions
- _is_armhf

## venv\Lib\site-packages\numpy\_core\tests\test_getlimits.py

### Classes
- TestPythonFloat
- TestHalf
- TestSingle
- TestDouble
- TestLongdouble
- TestFinfo
- TestIinfo
- TestRepr
- TestRuntimeSubscriptable

### Functions
- assert_finfo_equal
- assert_iinfo_equal
- test_instances
- test_subnormal_warning
- test_plausible_finfo

## venv\Lib\site-packages\numpy\_core\tests\test_half.py

### Classes
- TestHalf

### Functions
- assert_raises_fpe

## venv\Lib\site-packages\numpy\_core\tests\test_hashtable.py

### Functions
- test_identity_hashtable_get_set
- test_identity_hashtable_default_thread_safety
- test_identity_hashtable_set_thread_safety
- test_identity_hashtable_get_thread_safety
- test_identity_hashtable_get_set_concurrent
- test_identity_hashtable_get_set_concurrent_collisions

## venv\Lib\site-packages\numpy\_core\tests\test_indexerrors.py

### Classes
- TestIndexErrors

## venv\Lib\site-packages\numpy\_core\tests\test_indexing.py

### Classes
- TestIndexing
- TestFieldIndexing
- TestBroadcastedAssignments
- TestSubclasses
- TestFancyIndexingCast
- TestFancyIndexingEquivalence
- TestMultiIndexingAutomated
- TestFloatNonIntegerArgument
- TestBooleanIndexing
- TestArrayToIndexDeprecation
- TestNonIntegerArrayLike
- TestMultipleEllipsisError
- TestCApiAccess
- TestFlatiterIndexing

### Functions
- test_flatiter_method_signatures

## venv\Lib\site-packages\numpy\_core\tests\test_item_selection.py

### Classes
- TestTake
- TestPutMask
- TestPut

## venv\Lib\site-packages\numpy\_core\tests\test_limited_api.py

### Functions
- install_temp
- test_limited_api
- test_limited_opaque

## venv\Lib\site-packages\numpy\_core\tests\test_longdouble.py

### Classes
- TestFileBased
- TestCommaDecimalPointLocale

### Functions
- test_scalar_extraction
- test_str_roundtrip
- test_str_roundtrip_bytes
- test_array_and_stringlike_roundtrip
- test_bogus_string
- test_fromstring
- test_fromstring_complex
- test_fromstring_bogus
- test_fromstring_empty
- test_fromstring_missing
- test_str_exact
- test_format
- test_percent
- test_array_repr
- test_longdouble_from_int
- test_longdouble_from_bool
- test_musllinux_x86_64_signature
- test_eps_positive

## venv\Lib\site-packages\numpy\_core\tests\test_mem_overlap.py

### Classes
- TestUFunc

### Functions
- _indices_for_nelems
- _indices_for_axis
- _indices
- _check_assignment
- test_overlapping_assignments
- test_diophantine_fuzz
- test_diophantine_overflow
- check_may_share_memory_exact
- test_may_share_memory_manual
- iter_random_view_pairs
- check_may_share_memory_easy_fuzz
- test_may_share_memory_easy_fuzz
- test_may_share_memory_harder_fuzz
- test_shares_memory_api
- test_may_share_memory_bad_max_work
- test_internal_overlap_diophantine
- test_internal_overlap_slices
- check_internal_overlap
- test_internal_overlap_manual
- test_internal_overlap_fuzz
- test_non_ndarray_inputs
- view_element_first_byte
- assert_copy_equivalent

## venv\Lib\site-packages\numpy\_core\tests\test_mem_policy.py

### Functions
- get_module
- test_set_policy
- test_default_policy_singleton
- test_policy_propagation
- test_context_locality
- concurrent_thread1
- concurrent_thread2
- test_thread_locality
- test_new_policy
- test_switch_owner
- test_owner_is_base

## venv\Lib\site-packages\numpy\_core\tests\test_memmap.py

### Classes
- TestMemmap
- TestPatternMatching

## venv\Lib\site-packages\numpy\_core\tests\test_multiarray.py

### Classes
- TestFlags
- TestHash
- TestAttributes
- TestArrayConstruction
- TestAssignment
- TestDtypedescr
- TestZeroRank
- TestScalarIndexing
- TestCreation
- TestStructured
- TestBool
- TestZeroSizeFlexible
- TestMethods
- TestCequenceMethods
- TestBinop
- TestTemporaryElide
- TestCAPI
- TestSubscripting
- TestPickling
- TestFancyIndexing
- TestStringCompare
- TestArgmaxArgminCommon
- TestArgmax
- TestArgmin
- TestMinMax
- TestNewaxis
- TestClip
- TestCompress
- TestPutmask
- TestTake
- TestLexsort
- TestIO
- TestFromBuffer
- TestFlat
- TestResize
- TestRecord
- TestView
- TestStats
- TestVdot
- TestDot
- MatmulCommon
- TestMatmul
- TestMatmulOperator
- TestMatmulInplace
- TestInner
- TestChoose
- TestRepeat
- TestNeighborhoodIter
- TestStackedNeighborhoodIter
- TestWarnings
- TestMinScalarType
- TestPEP3118Dtype
- TestNewBufferProtocol
- TestArrayCreationCopyArgument
- TestArrayAttributeDeletion
- TestArrayInterface
- TestAsCArray
- TestConversion
- TestWhere
- TestSizeOf
- TestHashing
- TestArrayPriority
- TestBytestringArrayNonzero
- TestUnicodeEncoding
- TestUnicodeArrayNonzero
- TestFormat
- TestCTypes
- TestWritebackIfCopy
- TestArange
- TestDTypeCoercionForbidden
- TestDateTimeCreationTuple
- TestArrayFinalize
- TestAlignment
- TestViewDtype
- TestDevice
- TestTextSignatures
- TestPatternMatching

### Functions
- assert_arg_sorted
- assert_arr_partitioned
- _aligned_zeros
- normalize_filename
- _mean
- _var
- _std
- test_matmul_axes
- test_interface_empty_shape
- test_interface_no_shape_error
- test_interface_nullptr
- test_interface_nullptr_size_check
- test_array_interface_itemsize
- test_array_interface_empty_shape
- test_array_interface_offset
- test_array_interface_unicode_typestr
- test_flat_element_deletion
- test_scalar_element_deletion
- test_orderconverter_with_nonASCII_unicode_ordering
- test_equal_override
- test_equal_subclass_no_override
- test_no_loop_gives_all_true_or_false
- test_comparisons_forwards_error
- test_richcompare_scalar_boolean_singleton_return
- test_ragged_comparison_fails
- test_npymath_complex
- test_npymath_real
- test_uintalignment_and_alignment
- test_getfield
- test_sort_float
- test_sort_float16
- test_sort_int
- test_sort_uint
- test_private_get_ndarray_c_version
- test_argsort_float
- test_argsort_int
- test_sort_largearrays
- test_argsort_largearrays
- test_gh_22683
- test_gh_24459
- test_gh_28206
- test_partition_int
- test_partition_fp
- test_cannot_assign_data
- test_insufficient_width
- test_npy_char_raises
- test_array_interface_excess_dimensions_raises
- test_array_dunder_array_preserves_dtype_on_none

## venv\Lib\site-packages\numpy\_core\tests\test_multiprocessing.py

### Functions
- bool_array_writer
- bool_array_reader
- test_read_write_bool_array

## venv\Lib\site-packages\numpy\_core\tests\test_multithreading.py

### Functions
- test_parallel_randomstate
- test_parallel_ufunc_execution
- test_temp_elision_thread_safety
- test_eigvalsh_thread_safety
- _detected_blas
- _openblas_predates_gemm_fix
- test_blas_gemm_thread_safety
- test_printoptions_thread_safety
- test_parallel_reduction
- test_parallel_flat_iterator
- test_multithreaded_repeat
- test_structured_advanced_indexing
- test_structured_threadsafety2
- test_stringdtype_multithreaded_access_and_mutation
- test_legacy_usertype_cast_init_thread_safety
- test_nonzero
- np_broadcast
- create_array
- create_nditer
- test_arg_locking
- test_array__buffer__thread_safety
- test_void_dtype__buffer__thread_safety
- assert_no_deadlock
- threaded_deadlock_reproducer
- allocator_lock_order_workload
- test_setitem_reentrant_no_deadlock
- test_concurrent_allocator_acquire_no_deadlock
- unique_deadlock_workload
- test_concurrent_unique_no_deadlock

## venv\Lib\site-packages\numpy\_core\tests\test_nditer.py

### Classes
- TestIterNested

### Functions
- iter_multi_index
- iter_indices
- iter_iterindices
- test_iter_refcount
- test_iter_best_order
- test_iter_c_order
- test_iter_f_order
- test_iter_c_or_f_order
- test_nditer_multi_index_set
- test_nditer_multi_index_set_refcount
- test_iter_best_order_multi_index_1d
- test_iter_best_order_multi_index_2d
- test_iter_best_order_multi_index_3d
- test_iter_best_order_c_index_1d
- test_iter_best_order_c_index_2d
- test_iter_best_order_c_index_3d
- test_iter_best_order_f_index_1d
- test_iter_best_order_f_index_2d
- test_iter_best_order_f_index_3d
- test_iter_no_inner_full_coalesce
- test_iter_no_inner_dim_coalescing
- test_iter_dim_coalescing
- test_iter_broadcasting
- test_iter_itershape
- test_iter_broadcasting_errors
- test_iter_flags_errors
- test_iter_slice
- test_iter_assign_mapping
- test_iter_nbo_align_contig
- test_iter_array_cast
- test_iter_array_cast_errors
- test_iter_scalar_cast
- test_iter_scalar_cast_errors
- test_iter_object_arrays_basic
- test_iter_object_arrays_conversions
- test_iter_common_dtype
- test_iter_copy_if_overlap
- test_iter_op_axes
- test_iter_op_axes_errors
- test_iter_copy
- test_iter_copy_casts
- test_iter_copy_casts_structured
- test_iter_copy_casts_structured2
- test_iter_allocate_output_simple
- test_iter_allocate_output_buffered_readwrite
- test_iter_allocate_output_itorder
- test_iter_allocate_output_opaxes
- test_iter_allocate_output_types_promotion
- test_iter_allocate_output_types_byte_order
- test_iter_allocate_output_types_scalar
- test_iter_allocate_output_subtype
- test_iter_allocate_output_errors
- test_all_allocated
- test_iter_remove_axis
- test_iter_remove_multi_index_inner_loop
- test_iter_iterindex
- test_iter_iterrange
- test_iter_buffering
- test_iter_write_buffering
- test_iter_buffering_delayed_alloc
- test_iter_buffered_cast_simple
- test_iter_buffered_cast_byteswapped
- test_iter_buffered_cast_byteswapped_complex
- test_iter_buffered_cast_structured_type
- test_iter_buffered_cast_structured_type_failure_with_cleanup
- test_buffered_cast_error_paths
- test_buffered_cast_error_paths_unraisable
- test_iter_buffered_cast_subarray
- test_iter_buffering_badwriteback
- test_iter_buffering_string
- test_iter_buffering_growinner
- test_iter_contig_flag_reduce_error
- test_iter_contig_flag_single_operand_strides
- test_iter_contig_flag_incorrect
- test_iter_buffered_reduce_reuse
- test_iter_buffered_reduce_reuse_core
- test_iter_no_broadcast
- test_iter_reduction_error
- test_iter_reduction
- test_iter_buffering_reduction
- test_iter_buffering_reduction_reuse_reduce_loops
- test_iter_writemasked_badinput
- _is_buffered
- test_iter_writemasked
- test_iter_writemasked_broadcast_error
- test_iter_writemasked_decref
- test_iter_non_writable_attribute_deletion
- test_iter_writable_attribute_deletion
- test_iter_element_deletion
- test_iter_allocated_array_dtypes
- test_0d_iter
- test_object_iter_cleanup
- test_object_iter_cleanup_reduce
- test_object_iter_cleanup_large_reduce
- test_iter_too_large
- test_iter_too_large_with_multiindex
- test_invalid_call_of_enable_external_loop
- test_writebacks
- test_close_equivalent
- test_close_raises
- test_close_parameters
- test_warn_noclose
- test_partial_iteration_cleanup
- test_partial_iteration_error
- test_arbitrary_number_of_ops
- test_arbitrary_number_of_ops_nested
- test_arbitrary_number_of_ops_error
- test_debug_print
- test_signature_constructor
- test_signature_methods
- test_nditer_multi_index_no_segfault

## venv\Lib\site-packages\numpy\_core\tests\test_nep50_promotions.py

### Functions
- test_nep50_examples
- test_nep50_weak_integers
- test_nep50_weak_integers_with_inexact
- test_weak_promotion_scalar_path
- test_nep50_complex_promotion
- test_nep50_integer_conversion_errors
- test_nep50_with_axisconcatenator
- test_nep50_huge_integers
- test_nep50_in_concat_and_choose
- test_expected_promotion
- test_integer_comparison
- test_integer_comparison_with_cast
- test_integer_integer_comparison
- create_with_scalar
- create_with_array
- test_oob_creation

## venv\Lib\site-packages\numpy\_core\tests\test_numeric.py

### Classes
- TestResize
- TestNonarrayArgs
- TestIsscalar
- TestBoolScalar
- TestBoolArray
- TestBoolCmp
- TestSeterr
- TestFloatExceptions
- TestTypes
- NIterError
- TestFromiter
- TestNonzero
- TestIndex
- TestBinaryRepr
- TestBaseRepr
- TestArrayComparisons
- TestClip
- TestAllclose
- TestIsclose
- TestStdVar
- TestStdVarComplex
- TestCreationFuncs
- TestLikeFuncs
- TestCorrelate
- TestConvolve
- TestArgwhere
- TestRoll
- TestRollaxis
- TestMoveaxis
- TestCross
- TestIndices
- TestRequire
- TestBroadcast
- TestKeepdims
- TestTensordot
- TestAsType

### Functions
- _test_array_equal_parametrizations
- assert_array_strict_equal
- test_outer_out_param

## venv\Lib\site-packages\numpy\_core\tests\test_numerictypes.py

### Classes
- CreateZeros
- TestCreateZerosPlain
- TestCreateZerosNested
- CreateValues
- TestCreateValuesPlainSingle
- TestCreateValuesPlainMultiple
- TestCreateValuesNestedSingle
- TestCreateValuesNestedMultiple
- ReadValuesPlain
- TestReadValuesPlainSingle
- TestReadValuesPlainMultiple
- ReadValuesNested
- TestReadValuesNestedSingle
- TestReadValuesNestedMultiple
- TestEmptyField
- TestMultipleFields
- TestIsSubDType
- TestIsDType
- TestSctypeDict
- Test_sctype2char
- TestDocStrings
- TestScalarTypeNames
- TestScalarTypeOrder
- TestBoolDefinition

### Functions
- normalize_descr
- test_issctype

## venv\Lib\site-packages\numpy\_core\tests\test_overrides.py

### Classes
- TestGetImplementingArgs
- TestNDArrayArrayFunction
- TestArrayFunctionDispatch
- TestVerifyMatchingSignatures
- TestArrayFunctionImplementation
- TestNDArrayMethods
- TestNumPyFunctions
- TestArrayLike

### Functions
- _return_not_implemented
- dispatched_one_arg
- dispatched_two_arg
- _new_duck_type_and_implements
- test_function_like

## venv\Lib\site-packages\numpy\_core\tests\test_print.py

### Classes
- TestCommaDecimalPointLocale

### Functions
- test_float_types
- test_nan_inf_float
- test_complex_types
- test_complex_inf_nan
- _test_redirected_print
- test_float_type_print
- test_complex_type_print
- test_scalar_format

## venv\Lib\site-packages\numpy\_core\tests\test_protocols.py

### Functions
- test_getattr_warning
- test_array_called

## venv\Lib\site-packages\numpy\_core\tests\test_records.py

### Classes
- TestFromrecords
- TestPathUsage
- TestRecord
- TestPatternMatching

### Functions
- test_find_duplicate

## venv\Lib\site-packages\numpy\_core\tests\test_regression.py

### Classes
- TestRegression

## venv\Lib\site-packages\numpy\_core\tests\test_scalar_ctors.py

### Classes
- TestFromString
- TestExtraArgs
- TestFromInt
- TestArrayFromScalar

### Functions
- test_void_via_length
- test_void_from_byteslike
- test_void_arraylike_trumps_byteslike
- test_void_dtype_arg
- test_void_from_integer_with_dtype
- test_void_from_structure
- test_void_bad_dtype

## venv\Lib\site-packages\numpy\_core\tests\test_scalar_methods.py

### Classes
- TestAsIntegerRatio
- TestIsInteger
- TestClassGetItem
- TestBitCount
- TestDevice
- TestSignature

### Functions
- test_array_wrap

## venv\Lib\site-packages\numpy\_core\tests\test_scalarbuffer.py

### Classes
- TestScalarPEP3118

## venv\Lib\site-packages\numpy\_core\tests\test_scalarinherit.py

### Classes
- A
- B
- C
- D
- B0
- C0
- HasNew
- B1
- TestInherit
- TestCharacter

## venv\Lib\site-packages\numpy\_core\tests\test_scalarmath.py

### Classes
- TestTypes
- TestBaseMath
- TestPower
- TestModulus
- TestComparison
- TestComplexDivision
- TestConversion
- TestRepr
- TestSizeOf
- TestMultiply
- TestNegative
- TestSubtract
- TestAbs
- TestBitShifts
- TestHash

### Functions
- check_ufunc_scalar_equivalence
- test_array_scalar_ufunc_equivalence
- test_array_scalar_ufunc_dtypes
- test_int_float_promotion_truediv
- floordiv_and_mod
- _signs
- recursionlimit
- test_operator_object_left
- test_operator_object_right
- test_operator_scalars
- test_longdouble_operators_with_obj
- test_longdouble_with_arrlike
- test_longdouble_operators_with_large_int
- test_scalar_integer_operation_overflow
- test_scalar_signed_integer_overflow
- test_scalar_unsigned_integer_overflow
- test_scalar_integer_operation_divbyzero
- test_subclass_deferral
- test_longdouble_complex
- test_pyscalar_subclasses
- test_truediv_int
- test_scalar_matches_array_op_with_pyscalar

## venv\Lib\site-packages\numpy\_core\tests\test_scalarprint.py

### Classes
- TestRealScalars

## venv\Lib\site-packages\numpy\_core\tests\test_shape_base.py

### Classes
- TestAtleast1d
- TestAtleast2d
- TestAtleast3d
- TestHstack
- TestVstack
- TestConcatenate
- TestBlock

### Functions
- test_stack
- test_unstack
- test_stack_out_and_dtype
- test_block_dispatcher

## venv\Lib\site-packages\numpy\_core\tests\test_simd.py

### Classes
- _Test_Utility
- _SIMD_BOOL
- _SIMD_INT
- _SIMD_FP32
- _SIMD_FP64
- _SIMD_FP
- _SIMD_ALL

### Functions
- check_floatstatus

## venv\Lib\site-packages\numpy\_core\tests\test_simd_module.py

### Classes
- Test_SIMD_MODULE

## venv\Lib\site-packages\numpy\_core\tests\test_stringdtype.py

### Classes
- TestStringLikeCasts
- TestImplementation

### Functions
- random_unicode_string_list
- get_dtype
- coerce
- na_object
- dtype
- string_list
- coerce2
- na_object2
- dtype2
- test_dtype_creation
- test_dtype_equality
- test_dtype_repr
- test_create_with_na
- test_create_with_failing_na_comparison
- test_set_replace_na
- test_null_roundtripping
- test_np_str_trailing_nul_preserved
- test_embedded_null_comparisons
- test_embedded_null_sorting_and_search
- test_embedded_null_string_like_casts
- test_string_too_large_error
- test_array_creation_utf8
- test_scalars_string_conversion
- test_self_casts
- test_cast_method_names
- test_additional_unicode_cast
- test_invalid_numeric_casts_error
- test_insert_scalar
- test_comparisons
- test_isnan
- test_pickle
- test_stdlib_copy
- test_sort
- test_searchsorted_gh31533
- test_nonzero
- test_where
- test_fancy_indexing
- test_flatiter_indexing
- test_creation_functions
- test_concatenate
- test_resize_method
- test_create_with_copy_none
- test_astype_copy_false
- test_argmax
- test_arrfuncs_zeros
- test_cast_to_bool
- test_cast_from_bool
- test_sized_integer_casts
- test_unsized_integer_casts
- test_float_casts
- test_float_nan_cast_na_object
- test_string_to_bytes_invalid_ascii_error
- test_void_to_string_invalid_utf8_error
- test_cfloat_casts
- test_string_to_cfloat_cast_distinct_components
- test_take
- test_ufuncs_minmax
- test_max_regression
- test_ufunc_add
- test_ufunc_add_reduce
- test_add_promoter
- test_add_no_legacy_promote_with_signature
- test_add_promoter_reduce
- test_multiply_reduce
- test_multiply_two_string_raises
- test_ufunc_multiply
- test_findlike_promoters
- test_strip_promoter
- test_replace_promoter
- test_center_promoter
- test_datetime_timedelta_cast
- test_nat_casts
- test_nat_conversion
- test_growing_strings
- test_assign_medium_strings
- string_array
- unicode_array
- test_unary
- call_func
- test_binary
- test_non_default_start_stop
- test_replace_non_default_repeat
- test_trailing_null_is_not_padding
- test_trailing_null_is_not_stripped_as_whitespace
- test_strip_ljust_rjust_consistency
- test_unset_na_coercion
- test_coerce_promotion_commutative
- test_repeat
- test_accumulation
- _make_distinct_arena_arrays
- test_put_distinct_allocators
- test_putmask_distinct_allocators
- test_putmask_distinct_allocators_na
- test_choose_distinct_allocators
- test_place_distinct_allocators
- test_view_distinct_instance
- test_concatenate_distinct_allocators
- test_where_distinct_allocators
- test_indexing_ops_distinct_allocators
- test_setops_distinct_allocators
- test_unique_arena_strings
- test_lexsort_distinct_allocators
- test_strings_ufuncs_distinct_allocators
- test_assignment_distinct_allocators
- test_ufunc_at_distinct_allocators
- test_flatiter_subscript_distinct_allocators
- test_flat_assignment_distinct_allocators

## venv\Lib\site-packages\numpy\_core\tests\test_strings.py

### Classes
- TestMethods
- TestMethodsWithUnicode
- TestMixedTypeMethods
- TestUnicodeOnlyMethodsRaiseWithBytes
- TestReplaceOnArrays
- TestOverride

### Functions
- test_mixed_string_comparison_ufuncs_fail
- test_mixed_string_comparisons_ufuncs_with_cast
- test_string_comparisons
- test_string_comparisons_empty
- test_float_to_string_cast
- test_string_size_dtype_errors
- test_string_size_dtype_large_repr
- test_large_string_coercion_error
- test_large_string_addition_error
- test_large_string_cast
- test_in_place_multiply_no_overflow
- check_itemsize

## venv\Lib\site-packages\numpy\_core\tests\test_ufunc.py

### Classes
- TestUfuncKwargs
- TestUfuncGenericLoops
- TestUfunc
- TestGUFuncProcessCoreDims
- TestLowlevelAPIAccess
- TestUFuncInspectSignature

### Functions
- _pickleable_module_global
- test_ufunc_types
- test_ufunc_noncontiguous
- test_ufunc_warn_with_nan
- test_ufunc_out_casterrors
- test_ufunc_input_casterrors
- test_ufunc_input_floatingpoint_error
- test_ufunc_method_signatures
- test_trivial_loop_invalid_cast
- test_reduce_casterrors
- test_reduction_no_reference_leak
- test_object_reduce_cleanup_on_failure
- test_ufunc_methods_floaterrors
- _check_neg_zero
- test_addition_negative_zero
- test_addition_reduce_negative_zero
- test_addition_string_types
- test_addition_unicode_inverse_byte_order
- test_find_non_long_args
- test_find_access_past_buffer

## venv\Lib\site-packages\numpy\_core\tests\test_umath.py

### Classes
- _FilterInvalids
- TestConstants
- TestOut
- TestComparisons
- TestAdd
- TestDivision
- TestRemainder
- TestDivisionIntegerOverflowsAndDivideByZero
- TestCbrt
- TestPower
- TestFloat_power
- TestLog2
- TestExp2
- TestLogAddExp2
- TestLog
- TestExp
- TestSpecialFloats
- TestFPClass
- TestLDExp
- TestFRExp
- TestAVXUfuncs
- TestAVXFloat32Transcendental
- TestLogAddExp
- TestLog1p
- TestExpm1
- TestHypot
- TestHypotSpecialValues
- TestArctan2SpecialValues
- TestLdexp
- TestMaximum
- TestMinimum
- TestFmax
- TestFmin
- TestBool
- TestBitwiseUFuncs
- TestInt
- TestFloatingPoint
- TestDegrees
- TestRadians
- TestHeavside
- TestSign
- TestMinMax
- TestAbsoluteNegative
- TestPositive
- TestSpecialMethods
- TestChoose
- TestRationalFunctions
- TestRoundingFunctions
- TestComplexFunctions
- TestAttributes
- TestSubclass
- TestFrompyfunc
- TestReplaceLoopBySignature
- TestAddDocstring
- TestHypotErrorMessages

### Functions
- interesting_binop_operands
- on_powerpc
- bad_arcsinh
- floor_divide_and_remainder
- _signs
- assert_hypot_isnan
- assert_hypot_isinf
- assert_arctan2_isnan
- assert_arctan2_ispinf
- assert_arctan2_isninf
- assert_arctan2_ispzero
- assert_arctan2_isnzero
- _check_branch_cut
- test_copysign
- _test_nextafter
- test_nextafter
- test_nextafterf
- test_nextafterl
- test_nextafter_0
- test_nextafter_signed_zero
- _test_spacing
- test_spacing
- test_spacingf
- test_spacingl
- test_spacing_gfortran
- test_nextafter_vs_spacing
- test_pos_nan
- test_abs_nan_signbit
- test_abs_nan_signbit_array
- test_reduceat
- test_negative_value_raises
- test_reduceat_empty
- test_complex_nan_comparisons
- test_rint_big_int
- test_memoverlap_accumulate
- test_memoverlap_accumulate_cmp
- test_memoverlap_accumulate_symmetric
- test_signaling_nan_exceptions
- test_outer_subclass_preserve
- test_outer_bad_subclass
- test_outer_exceeds_maxdims
- test_bad_legacy_ufunc_silent_errors
- test_bad_legacy_unary_ufunc_silent_errors
- test_bad_legacy_gufunc_silent_errors

## venv\Lib\site-packages\numpy\_core\tests\test_umath_accuracy.py

### Classes
- TestAccuracy

### Functions
- convert

## venv\Lib\site-packages\numpy\_core\tests\test_umath_complex.py

### Classes
- TestCexp
- TestClog
- TestCsqrt
- TestCpow
- TestCabs
- TestCarg
- TestSpecialComplexAVX
- TestComplexAbsoluteAVX
- TestComplexAbsoluteMixedDTypes

### Functions
- check_real_value
- check_complex_value

## venv\Lib\site-packages\numpy\_core\tests\test_unicode.py

### Classes
- CreateZeros
- TestCreateZeros_1
- TestCreateZeros_2
- TestCreateZeros_1009
- CreateValues
- TestCreateValues_1_UCS2
- TestCreateValues_1_UCS4
- TestCreateValues_2_UCS2
- TestCreateValues_2_UCS4
- TestCreateValues_1009_UCS2
- TestCreateValues_1009_UCS4
- AssignValues
- TestAssignValues_1_UCS2
- TestAssignValues_1_UCS4
- TestAssignValues_2_UCS2
- TestAssignValues_2_UCS4
- TestAssignValues_1009_UCS2
- TestAssignValues_1009_UCS4
- ByteorderValues
- TestByteorder_1_UCS2
- TestByteorder_1_UCS4
- TestByteorder_2_UCS2
- TestByteorder_2_UCS4
- TestByteorder_1009_UCS2
- TestByteorder_1009_UCS4

### Functions
- buffer_length
- test_string_cast

## venv\Lib\site-packages\numpy\_core\umath.py

## venv\Lib\site-packages\numpy\_distributor_init.py

## venv\Lib\site-packages\numpy\_expired_attrs_2_0.py

## venv\Lib\site-packages\numpy\_globals.py

### Classes
- _NoValueType
- _CopyMode
- _SignatureDescriptor

## venv\Lib\site-packages\numpy\_pyinstaller\__init__.py

## venv\Lib\site-packages\numpy\_pyinstaller\hook-numpy.py

## venv\Lib\site-packages\numpy\_pyinstaller\tests\__init__.py

## venv\Lib\site-packages\numpy\_pyinstaller\tests\pyinstaller-smoke.py

## venv\Lib\site-packages\numpy\_pyinstaller\tests\test_pyinstaller.py

### Functions
- test_pyinstaller

## venv\Lib\site-packages\numpy\_pytesttester.py

### Classes
- PytestTester

### Functions
- _show_numpy_info

## venv\Lib\site-packages\numpy\_typing\__init__.py

## venv\Lib\site-packages\numpy\_typing\_add_docstring.py

### Functions
- add_newdoc
- _parse_docstrings

## venv\Lib\site-packages\numpy\_typing\_array_like.py

### Classes
- _SupportsArray
- _SupportsArrayFunc

## venv\Lib\site-packages\numpy\_typing\_char_codes.py

## venv\Lib\site-packages\numpy\_typing\_dtype_like.py

### Classes
- _DTypeDict
- _HasDType
- _HasNumPyDType

## venv\Lib\site-packages\numpy\_typing\_extended_precision.py

## venv\Lib\site-packages\numpy\_typing\_nbit.py

## venv\Lib\site-packages\numpy\_typing\_nbit_base.py

### Classes
- NBitBase
- _128Bit
- _96Bit
- _64Bit
- _32Bit
- _16Bit
- _8Bit

## venv\Lib\site-packages\numpy\_typing\_nested_sequence.py

### Classes
- _NestedSequence

## venv\Lib\site-packages\numpy\_typing\_scalars.py

## venv\Lib\site-packages\numpy\_typing\_shape.py

## venv\Lib\site-packages\numpy\_typing\_ufunc.py

## venv\Lib\site-packages\numpy\_utils\__init__.py

### Functions
- set_module
- _rename_parameter

## venv\Lib\site-packages\numpy\_utils\_conversions.py

### Functions
- asunicode
- asbytes

## venv\Lib\site-packages\numpy\_utils\_inspect.py

### Functions
- ismethod
- isfunction
- iscode
- getargs
- getargspec
- getargvalues
- joinseq
- strseq
- formatargspec
- formatargvalues

## venv\Lib\site-packages\numpy\_utils\_pep440.py

### Classes
- Infinity
- NegativeInfinity
- InvalidVersion
- _BaseVersion
- LegacyVersion
- Version

### Functions
- parse
- _parse_version_parts
- _legacy_cmpkey
- _parse_letter_version
- _parse_local_version
- _cmpkey

## venv\Lib\site-packages\numpy\char\__init__.py

### Functions
- __getattr__
- __dir__

## venv\Lib\site-packages\numpy\conftest.py

### Functions
- pytest_configure
- pytest_addoption
- pytest_sessionstart
- pytest_terminal_summary
- pytest_itemcollected
- check_fpu_mode
- add_np

## venv\Lib\site-packages\numpy\core\__init__.py

### Functions
- _ufunc_reconstruct
- __getattr__

## venv\Lib\site-packages\numpy\core\_dtype.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\_dtype_ctypes.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\_internal.py

### Functions
- _reconstruct
- __getattr__

## venv\Lib\site-packages\numpy\core\_multiarray_umath.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\_utils.py

### Functions
- _raise_warning

## venv\Lib\site-packages\numpy\core\arrayprint.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\defchararray.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\einsumfunc.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\fromnumeric.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\function_base.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\getlimits.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\multiarray.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\numeric.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\numerictypes.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\overrides.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\records.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\shape_base.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\core\umath.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\ctypeslib\__init__.py

## venv\Lib\site-packages\numpy\ctypeslib\_ctypeslib.py

### Classes
- _ndptr
- _concrete_ndptr

### Functions
- _num_fromflags
- _flags_fromnum
- ndpointer

## venv\Lib\site-packages\numpy\doc\ufuncs.py

## venv\Lib\site-packages\numpy\dtypes.py

### Functions
- register_dlpack_dtype
- _add_dtype_helper

## venv\Lib\site-packages\numpy\exceptions.py

### Classes
- ComplexWarning
- ModuleDeprecationWarning
- VisibleDeprecationWarning
- RankWarning
- TooHardError
- AxisError
- DTypePromotionError

## venv\Lib\site-packages\numpy\f2py\__init__.py

### Functions
- get_include
- __getattr__
- __dir__

## venv\Lib\site-packages\numpy\f2py\__main__.py

## venv\Lib\site-packages\numpy\f2py\__version__.py

## venv\Lib\site-packages\numpy\f2py\_backends\__init__.py

### Functions
- f2py_build_generator

## venv\Lib\site-packages\numpy\f2py\_backends\_backend.py

### Classes
- Backend

## venv\Lib\site-packages\numpy\f2py\_backends\_meson.py

### Classes
- MesonTemplate
- MesonBackend

### Functions
- _prepare_sources
- _prepare_objects
- _get_flags

## venv\Lib\site-packages\numpy\f2py\_isocbind.py

## venv\Lib\site-packages\numpy\f2py\_src_pyf.py

### Functions
- parse_structure
- find_repl_patterns
- find_and_remove_repl_patterns
- conv
- unique_key
- expand_sub
- process_str
- resolve_includes
- process_file

## venv\Lib\site-packages\numpy\f2py\auxfuncs.py

### Classes
- F2PYError
- throw_error

### Functions
- outmess
- debugcapi
- _ischaracter
- _isstring
- ischaracter_or_characterarray
- ischaracter
- ischaracterarray
- isstring_or_stringarray
- isstring
- isstringarray
- isarrayofstrings
- isarray
- isscalar
- iscomplex
- islogical
- isinteger
- isreal
- get_kind
- isint1
- islong_long
- isunsigned_char
- isunsigned_short
- isunsigned
- isunsigned_long_long
- isdouble
- islong_double
- islong_complex
- iscomplexarray
- isint1array
- isunsigned_chararray
- isunsigned_shortarray
- isunsignedarray
- isunsigned_long_longarray
- issigned_chararray
- issigned_shortarray
- issigned_array
- issigned_long_longarray
- isallocatable
- ismutable
- ismoduleroutine
- ismodule
- isfunction
- isfunction_wrap
- issubroutine
- issubroutine_wrap
- isattr_value
- hasassumedshape
- requiresf90wrapper
- isroutine
- islogicalfunction
- islong_longfunction
- islong_doublefunction
- iscomplexfunction
- iscomplexfunction_warn
- isstringfunction
- hasexternals
- isthreadsafe
- hasvariables
- isoptional
- isexternal
- getdimension
- isrequired
- iscstyledirective
- isintent_in
- isintent_inout
- isintent_out
- isintent_hide
- isintent_nothide
- isintent_c
- isintent_cache
- isintent_copy
- isintent_overwrite
- isintent_callback
- isintent_inplace
- isintent_aux
- isintent_aligned4
- isintent_aligned8
- isintent_aligned16
- isprivate
- isvariable
- hasinitvalue
- hasinitvalueasstring
- hasnote
- hasresultnote
- hascommon
- containscommon
- hasderivedtypes
- containsderivedtypes
- containsmodule
- hasbody
- hascallstatement
- istrue
- isfalse
- l_and
- l_or
- l_not
- isdummyroutine
- getfortranname
- getmultilineblock
- getcallstatement
- getcallprotoargument
- getusercode
- getusercode1
- getpymethoddef
- getargs
- getargs2
- getrestdoc
- gentitle
- flatlist
- stripcomma
- replace
- dictappend
- applyrules
- get_f2py_modulename
- getuseblocks
- process_f2cmap_dict

## venv\Lib\site-packages\numpy\f2py\capi_maps.py

### Functions
- load_f2cmap_file
- getctype
- f2cexpr
- getstrlength
- getarrdims
- getpydocsign
- getarrdocsign
- getinit
- get_elsize
- sign2map
- routsign2map
- modsign2map
- cb_sign2map
- cb_routsign2map
- common_sign2map

## venv\Lib\site-packages\numpy\f2py\cb_rules.py

### Functions
- buildcallbacks
- buildcallback

## venv\Lib\site-packages\numpy\f2py\cfuncs.py

### Functions
- errmess
- buildcfuncs
- append_needs
- get_needs

## venv\Lib\site-packages\numpy\f2py\common_rules.py

### Functions
- findcommonblocks
- buildhooks

## venv\Lib\site-packages\numpy\f2py\crackfortran.py

### Functions
- reset_global_f2py_vars
- outmess
- rmbadname1
- rmbadname
- undo_rmbadname1
- undo_rmbadname
- openhook
- is_free_format
- readfortrancode
- split_by_unquoted
- _simplifyargs
- crackline
- markouterparen
- markoutercomma
- unmarkouterparen
- appenddecl
- _is_intent_callback
- _resolvetypedefpattern
- parse_name_for_bind
- _resolvenameargspattern
- analyzeline
- appendmultiline
- cracktypespec0
- removespaces
- markinnerspaces
- updatevars
- cracktypespec
- setattrspec
- setkindselector
- setcharselector
- getblockname
- setmesstext
- get_usedict
- get_useparameters
- postcrack2
- postcrack
- sortvarnames
- analyzecommon
- analyzebody
- buildimplicitrules
- myeval
- getlincoef
- _get_depend_dict
- _calc_depend_dict
- get_sorted_names
- _kind_func
- _selected_int_kind_func
- _selected_real_kind_func
- get_parameters
- _eval_length
- _eval_scalar
- analyzevars
- param_eval
- param_parse
- expr2name
- analyzeargs
- _ensure_exprdict
- determineexprtype
- crack2fortrangen
- common2fortran
- use2fortran
- true_intent_list
- vars2fortran
- crackfortran
- crack2fortran
- _is_visit_pair
- traverse
- character_backward_compatibility_hook

## venv\Lib\site-packages\numpy\f2py\diagnose.py

### Functions
- run

## venv\Lib\site-packages\numpy\f2py\f2py2e.py

### Classes
- CombineIncludePaths

### Functions
- scaninputline
- callcrackfortran
- buildmodules
- dict_append
- run_main
- filter_files
- get_prefix
- f2py_parser
- get_newer_options
- make_f2py_compile_parser
- preparse_sysargv
- run_compile
- validate_modulename
- main

## venv\Lib\site-packages\numpy\f2py\f90mod_rules.py

### Functions
- findf90modules
- buildhooks

## venv\Lib\site-packages\numpy\f2py\func2subr.py

### Functions
- var2fixfortran
- useiso_c_binding
- createfuncwrapper
- createsubrwrapper
- assubr

## venv\Lib\site-packages\numpy\f2py\rules.py

### Functions
- buildmodule
- buildapi

## venv\Lib\site-packages\numpy\f2py\symbolic.py

### Classes
- Language
- Op
- RelOp
- ArithOp
- OpError
- Precedence
- ExprWarning
- Expr
- _Pair
- _FromStringWorker

### Functions
- _pairs_add
- ewarn
- normalize
- as_expr
- as_symbol
- as_number
- as_integer
- as_real
- as_string
- as_array
- as_complex
- as_apply
- as_ternary
- as_ref
- as_deref
- as_eq
- as_ne
- as_lt
- as_le
- as_gt
- as_ge
- as_terms
- as_factors
- as_term_coeff
- as_numer_denom
- _counter
- eliminate_quotes
- insert_quotes
- replace_parenthesis
- _get_parenthesis_kind
- unreplace_parenthesis
- fromstring

## venv\Lib\site-packages\numpy\f2py\tests\__init__.py

## venv\Lib\site-packages\numpy\f2py\tests\test_abstract_interface.py

### Classes
- TestAbstractInterface

## venv\Lib\site-packages\numpy\f2py\tests\test_array_from_pyobj.py

### Classes
- Intent
- Type
- Array
- TestIntent
- TestSharedMemory

### Functions
- get_testdir
- setup_module
- flags_info
- flags2names

## venv\Lib\site-packages\numpy\f2py\tests\test_assumed_shape.py

### Classes
- TestAssumedShapeSumExample
- TestF2cmapOption

## venv\Lib\site-packages\numpy\f2py\tests\test_block_docstring.py

### Classes
- TestBlockDocString

## venv\Lib\site-packages\numpy\f2py\tests\test_callback.py

### Classes
- TestF77Callback
- TestF77CallbackPythonTLS
- TestF90Callback
- TestGH18335
- TestGH25211
- TestCBFortranCallstatement

## venv\Lib\site-packages\numpy\f2py\tests\test_capi_maps.py

### Functions
- test_complex_long_double_capi_map
- test_complex_long_double_is_distinct

## venv\Lib\site-packages\numpy\f2py\tests\test_character.py

### Classes
- TestCharacterString
- TestCharacter
- TestMiscCharacter
- TestStringScalarArr
- TestStringAssumedLength
- TestStringOptionalInOut
- TestNewCharHandling
- TestBCCharHandling

## venv\Lib\site-packages\numpy\f2py\tests\test_common.py

### Classes
- TestCommonBlock
- TestCommonWithUse

## venv\Lib\site-packages\numpy\f2py\tests\test_crackfortran.py

### Classes
- TestNoSpace
- TestPublicPrivate
- TestModuleProcedure
- TestExternal
- TestCrackFortran
- TestMarkinnerspaces
- TestDimSpec
- TestModuleDeclaration
- TestEval
- TestFortranReader
- TestUnicodeComment
- TestNameArgsPatternBacktracking
- TestFunctionReturn
- TestFortranGroupCounters
- TestF77CommonBlockReader
- TestParamEval
- TestLowerF2PYDirective

## venv\Lib\site-packages\numpy\f2py\tests\test_data.py

### Classes
- TestData
- TestDataF77
- TestDataMultiplierF77
- TestDataWithCommentsF77

## venv\Lib\site-packages\numpy\f2py\tests\test_docs.py

### Classes
- TestDocAdvanced

### Functions
- get_docdir
- _path

## venv\Lib\site-packages\numpy\f2py\tests\test_f2cmap.py

### Classes
- TestF2Cmap

## venv\Lib\site-packages\numpy\f2py\tests\test_f2py2e.py

### Functions
- compiler_check_f2pycli
- get_io_paths
- hello_world_f90
- gh23598_warn
- gh22819_cli
- hello_world_f77
- retreal_f77
- f2cmap_f90
- test_gh22819_cli
- test_gh22819_many_pyf
- test_gh23598_warn
- test_gen_pyf
- test_gen_pyf_stdout
- test_gen_pyf_no_overwrite
- test_untitled_cli
- test_no_distutils_backend
- test_f2py_skip
- test_f2py_only
- test_file_processing_switch
- test_mod_gen_f77
- test_mod_gen_gh25263
- test_lower_cmod
- test_lower_sig
- test_build_dir
- test_overwrite
- test_latexdoc
- test_nolatexdoc
- test_latex_doc_gh30268
- test_shortlatex
- test_restdoc
- test_norestexdoc
- test_debugcapi
- test_debugcapi_bld
- test_wrapfunc_def
- test_nowrapfunc
- test_inclheader
- test_cli_obj
- test_inclpath
- test_hlink
- test_f2cmap
- test_quiet
- test_verbose
- test_version
- test_npdistop
- test_no_freethreading_compatible
- test_freethreading_compatible
- test_npd_fcompiler
- test_npd_compiler
- test_npd_help_fcompiler
- test_npd_f77exec
- test_npd_f90exec
- test_npd_f77flags
- test_npd_f90flags
- test_npd_opt
- test_npd_arch
- test_npd_noopt
- test_npd_noarch
- test_npd_debug
- test_npd_link_auto
- test_npd_lib
- test_npd_define
- test_npd_undefine
- test_npd_incl
- test_npd_linker

## venv\Lib\site-packages\numpy\f2py\tests\test_inplace.py

### Classes
- TestInplace

## venv\Lib\site-packages\numpy\f2py\tests\test_isoc.py

### Classes
- TestISOC

### Functions
- test_process_f2cmap_dict

## venv\Lib\site-packages\numpy\f2py\tests\test_kind.py

### Classes
- TestKind

## venv\Lib\site-packages\numpy\f2py\tests\test_mixed.py

### Classes
- TestMixed

## venv\Lib\site-packages\numpy\f2py\tests\test_modules.py

### Classes
- TestModuleFilterPublicEntities
- TestModuleWithoutPublicEntities
- TestModuleDocString
- TestModuleAndSubroutine
- TestUsedModule

## venv\Lib\site-packages\numpy\f2py\tests\test_parameter.py

### Classes
- TestParameters

## venv\Lib\site-packages\numpy\f2py\tests\test_pyf_src.py

### Functions
- normalize_whitespace
- test_from_template

## venv\Lib\site-packages\numpy\f2py\tests\test_quoted_character.py

### Classes
- TestQuotedCharacter

## venv\Lib\site-packages\numpy\f2py\tests\test_regression.py

### Classes
- TestIntentInOut
- TestDataOnlyMultiModule
- TestModuleWithDerivedType
- TestNegativeBounds
- TestNumpyVersionAttribute
- TestIncludeFiles
- TestF77Comments
- TestF90Continuation
- TestLowerF2PYDirectives
- TestComplexStructCompat
- TestAssignmentOnlyModules

### Functions
- test_include_path
- test_gh26623
- test_gh25784

## venv\Lib\site-packages\numpy\f2py\tests\test_return_character.py

### Classes
- TestReturnCharacter
- TestFReturnCharacter

## venv\Lib\site-packages\numpy\f2py\tests\test_return_complex.py

### Classes
- TestReturnComplex
- TestFReturnComplex

## venv\Lib\site-packages\numpy\f2py\tests\test_return_integer.py

### Classes
- TestReturnInteger
- TestFReturnInteger

## venv\Lib\site-packages\numpy\f2py\tests\test_return_logical.py

### Classes
- TestReturnLogical
- TestFReturnLogical

## venv\Lib\site-packages\numpy\f2py\tests\test_return_real.py

### Classes
- TestReturnReal
- TestCReturnReal
- TestFReturnReal

## venv\Lib\site-packages\numpy\f2py\tests\test_routines.py

### Classes
- TestRenamedFunc
- TestRenamedSubroutine

## venv\Lib\site-packages\numpy\f2py\tests\test_semicolon_split.py

### Classes
- TestMultiline
- TestCallstatement

## venv\Lib\site-packages\numpy\f2py\tests\test_size.py

### Classes
- TestSizeSumExample

## venv\Lib\site-packages\numpy\f2py\tests\test_string.py

### Classes
- TestString
- TestDocStringArguments
- TestFixedString

## venv\Lib\site-packages\numpy\f2py\tests\test_symbolic.py

### Classes
- TestSymbolic

## venv\Lib\site-packages\numpy\f2py\tests\test_value_attrspec.py

### Classes
- TestValueAttr

## venv\Lib\site-packages\numpy\f2py\tests\util.py

### Classes
- CompilerChecker
- SimplifiedMesonBackend
- F2PyTest

### Functions
- check_language
- has_c_compiler
- has_f77_compiler
- has_f90_compiler
- has_fortran_compiler
- _cleanup
- get_module_dir
- get_temp_module_name
- _memoize
- build_module
- build_code
- build_meson
- getpath
- switchdir

## venv\Lib\site-packages\numpy\f2py\use_rules.py

### Functions
- buildusevars
- buildusevar

## venv\Lib\site-packages\numpy\fft\__init__.py

## venv\Lib\site-packages\numpy\fft\_helper.py

### Functions
- _fftshift_dispatcher
- fftshift
- ifftshift
- fftfreq
- rfftfreq

## venv\Lib\site-packages\numpy\fft\_pocketfft.py

### Functions
- _raw_fft
- _swap_direction
- _fft_dispatcher
- fft
- ifft
- rfft
- irfft
- hfft
- ihfft
- _cook_nd_args
- _raw_fftnd
- _fftn_dispatcher
- fftn
- ifftn
- fft2
- ifft2
- rfftn
- rfft2
- irfftn
- irfft2

## venv\Lib\site-packages\numpy\fft\tests\__init__.py

## venv\Lib\site-packages\numpy\fft\tests\test_helper.py

### Classes
- TestFFTShift
- TestFFTFreq
- TestRFFTFreq
- TestIRFFTN

## venv\Lib\site-packages\numpy\fft\tests\test_pocketfft.py

### Classes
- TestFFTShift
- TestFFT1D
- TestFFTThreadSafe

### Functions
- fft1
- test_fft_with_order
- test_fft_output_order
- test_irfft_with_n_1_regression
- test_irfft_with_n_large_regression
- test_fft_with_integer_or_bool_input

## venv\Lib\site-packages\numpy\lib\__init__.py

### Functions
- __getattr__

## venv\Lib\site-packages\numpy\lib\_array_utils_impl.py

### Functions
- byte_bounds

## venv\Lib\site-packages\numpy\lib\_arraypad_impl.py

### Functions
- _round_if_needed
- _slice_at_axis
- _view_roi
- _pad_simple
- _set_pad_area
- _get_edges
- _get_linear_ramps
- _get_stats
- _set_reflect_both
- _set_wrap_both
- _as_pairs
- _pad_dispatcher
- pad

## venv\Lib\site-packages\numpy\lib\_arraysetops_impl.py

### Classes
- UniqueAllResult
- UniqueCountsResult
- UniqueInverseResult

### Functions
- _ediff1d_dispatcher
- ediff1d
- _unpack_tuple
- _unique_dispatcher
- unique
- _unique1d
- _unique_all_dispatcher
- unique_all
- _unique_counts_dispatcher
- unique_counts
- _unique_inverse_dispatcher
- unique_inverse
- _unique_values_dispatcher
- unique_values
- _intersect1d_dispatcher
- intersect1d
- _setxor1d_dispatcher
- setxor1d
- _isin
- _isin_dispatcher
- isin
- _union1d_dispatcher
- union1d
- _setdiff1d_dispatcher
- setdiff1d

## venv\Lib\site-packages\numpy\lib\_arrayterator_impl.py

### Classes
- Arrayterator

## venv\Lib\site-packages\numpy\lib\_datasource.py

### Classes
- _FileOpeners
- DataSource
- Repository

### Functions
- _check_mode
- open

## venv\Lib\site-packages\numpy\lib\_format_impl.py

### Functions
- _check_version
- magic
- read_magic
- dtype_to_descr
- descr_to_dtype
- header_data_from_array_1_0
- _wrap_header
- _wrap_header_guess_version
- _write_array_header
- write_array_header_1_0
- write_array_header_2_0
- read_array_header_1_0
- read_array_header_2_0
- _filter_header
- _read_array_header
- write_array
- read_array
- open_memmap
- _read_bytes
- isfileobj

## venv\Lib\site-packages\numpy\lib\_function_base_impl.py

### Classes
- vectorize

### Functions
- _rot90_dispatcher
- rot90
- _flip_dispatcher
- flip
- iterable
- _weights_are_valid
- _average_dispatcher
- average
- asarray_chkfinite
- _piecewise_dispatcher
- piecewise
- _select_dispatcher
- select
- _copy_dispatcher
- copy
- _gradient_dispatcher
- gradient
- _diff_dispatcher
- diff
- _interp_dispatcher
- interp
- _angle_dispatcher
- angle
- _unwrap_dispatcher
- unwrap
- _sort_complex
- sort_complex
- _arg_trim_zeros
- _trim_zeros
- trim_zeros
- _extract_dispatcher
- extract
- _place_dispatcher
- place
- _parse_gufunc_signature
- _update_dim_sizes
- _parse_input_dimensions
- _calculate_shapes
- _create_arrays
- _get_vectorize_dtype
- _cov_dispatcher
- cov
- _corrcoef_dispatcher
- corrcoef
- blackman
- bartlett
- hanning
- hamming
- _chbevl
- _i0_1
- _i0_2
- _i0_dispatcher
- i0
- kaiser
- _sinc_dispatcher
- sinc
- _ureduce
- _median_dispatcher
- median
- _median
- _percentile_dispatcher
- percentile
- _quantile_dispatcher
- quantile
- _quantile_unchecked
- _quantile_is_valid
- _compute_virtual_index
- _get_gamma
- _lerp
- _get_gamma_mask
- _discrete_interpolation_to_boundaries
- _closest_observation
- _inverted_cdf
- _quantile_ureduce_func
- _get_indexes
- _quantile
- _trapezoid_dispatcher
- trapezoid
- _meshgrid_dispatcher
- meshgrid
- _delete_dispatcher
- delete
- _insert_dispatcher
- insert
- _append_dispatcher
- append
- _digitize_dispatcher
- digitize

## venv\Lib\site-packages\numpy\lib\_histograms_impl.py

### Functions
- _ptp
- _hist_bin_sqrt
- _hist_bin_sturges
- _hist_bin_rice
- _hist_bin_scott
- _hist_bin_stone
- _hist_bin_doane
- _hist_bin_fd
- _hist_bin_auto
- _ravel_and_check_weights
- _get_outer_edges
- _unsigned_subtract
- _get_bin_edges
- _search_sorted_inclusive
- _histogram_bin_edges_dispatcher
- histogram_bin_edges
- _histogram_dispatcher
- histogram
- _histogramdd_dispatcher
- histogramdd

## venv\Lib\site-packages\numpy\lib\_index_tricks_impl.py

### Classes
- nd_grid
- MGridClass
- OGridClass
- AxisConcatenator
- RClass
- CClass
- ndenumerate
- ndindex
- IndexExpression

### Functions
- _ix__dispatcher
- ix_
- _fill_diagonal_dispatcher
- fill_diagonal
- diag_indices
- _diag_indices_from
- diag_indices_from

## venv\Lib\site-packages\numpy\lib\_iotools.py

### Classes
- LineSplitter
- NameValidator
- ConverterError
- ConverterLockError
- ConversionWarning
- StringConverter

### Functions
- _decode_line
- _is_string_like
- _is_bytes_like
- has_nested_fields
- flatten_dtype
- str2bool
- easy_dtype

## venv\Lib\site-packages\numpy\lib\_nanfunctions_impl.py

### Functions
- _nan_mask
- _replace_nan
- _copyto
- _remove_nan_1d
- _divide_by_count
- _nanmin_dispatcher
- nanmin
- _nanmax_dispatcher
- nanmax
- _nanargmin_dispatcher
- nanargmin
- _nanargmax_dispatcher
- nanargmax
- _nansum_dispatcher
- nansum
- _nanprod_dispatcher
- nanprod
- _nancumsum_dispatcher
- nancumsum
- _nancumprod_dispatcher
- nancumprod
- _nanmean_dispatcher
- nanmean
- _nanmedian1d
- _nanmedian
- _nanmedian_small
- _nanmedian_dispatcher
- nanmedian
- _nanpercentile_dispatcher
- nanpercentile
- _nanquantile_dispatcher
- nanquantile
- _nanquantile_unchecked
- _nanquantile_ureduce_func
- _nanquantile_1d
- _nanvar_dispatcher
- nanvar
- _nanstd_dispatcher
- nanstd

## venv\Lib\site-packages\numpy\lib\_npyio_impl.py

### Classes
- BagObj
- NpzFile

### Functions
- zipfile_factory
- load
- _save_dispatcher
- save
- _savez_dispatcher
- savez
- _savez_compressed_dispatcher
- savez_compressed
- _savez
- _ensure_ndmin_ndarray_check_param
- _ensure_ndmin_ndarray
- _check_nonneg_int
- _preprocess_comments
- _read
- loadtxt
- _savetxt_dispatcher
- savetxt
- fromregex
- genfromtxt

## venv\Lib\site-packages\numpy\lib\_polynomial_impl.py

### Classes
- poly1d

### Functions
- _poly_dispatcher
- poly
- _roots_dispatcher
- roots
- _polyint_dispatcher
- polyint
- _polyder_dispatcher
- polyder
- _polyfit_dispatcher
- polyfit
- _polyval_dispatcher
- polyval
- _binary_op_dispatcher
- polyadd
- polysub
- polymul
- _polydiv_dispatcher
- polydiv
- _raise_power

## venv\Lib\site-packages\numpy\lib\_scimath_impl.py

### Functions
- _tocomplex
- _fix_real_lt_zero
- _fix_int_lt_zero
- _fix_real_abs_gt_1
- _unary_dispatcher
- sqrt
- log
- log10
- _logn_dispatcher
- logn
- log2
- _power_dispatcher
- power
- arccos
- arcsin
- arctanh

## venv\Lib\site-packages\numpy\lib\_shape_base_impl.py

### Functions
- _make_along_axis_idx
- _take_along_axis_dispatcher
- take_along_axis
- _put_along_axis_dispatcher
- put_along_axis
- _apply_along_axis_dispatcher
- apply_along_axis
- _apply_over_axes_dispatcher
- apply_over_axes
- _expand_dims_dispatcher
- expand_dims
- _column_stack_dispatcher
- column_stack
- _dstack_dispatcher
- dstack
- _array_split_dispatcher
- array_split
- _split_dispatcher
- split
- _hvdsplit_dispatcher
- hsplit
- vsplit
- dsplit
- _kron_dispatcher
- kron
- _tile_dispatcher
- tile

## venv\Lib\site-packages\numpy\lib\_stride_tricks_impl.py

### Classes
- DummyArray

### Functions
- _maybe_view_as_subclass
- as_strided
- _sliding_window_view_dispatcher
- sliding_window_view
- _broadcast_to
- _broadcast_to_dispatcher
- broadcast_to
- _broadcast_shape
- broadcast_shapes
- _broadcast_arrays_dispatcher
- broadcast_arrays

## venv\Lib\site-packages\numpy\lib\_twodim_base_impl.py

### Functions
- _min_int
- _flip_dispatcher
- fliplr
- flipud
- eye
- _diag_dispatcher
- diag
- diagflat
- tri
- _trilu_dispatcher
- tril
- triu
- _vander_dispatcher
- vander
- _histogram2d_dispatcher
- histogram2d
- mask_indices
- tril_indices
- _trilu_indices_form_dispatcher
- tril_indices_from
- triu_indices
- triu_indices_from

## venv\Lib\site-packages\numpy\lib\_type_check_impl.py

### Functions
- mintypecode
- _real_dispatcher
- real
- _imag_dispatcher
- imag
- _is_type_dispatcher
- iscomplex
- isreal
- iscomplexobj
- isrealobj
- _getmaxmin
- _nan_to_num_dispatcher
- nan_to_num
- _real_if_close_dispatcher
- real_if_close
- typename
- _common_type_dispatcher
- common_type

## venv\Lib\site-packages\numpy\lib\_ufunclike_impl.py

### Functions
- _dispatcher
- fix
- isposinf
- isneginf

## venv\Lib\site-packages\numpy\lib\_user_array_impl.py

### Classes
- container

## venv\Lib\site-packages\numpy\lib\_utils_impl.py

### Functions
- show_runtime
- get_include
- _get_indent
- _split_line
- _makenamedict
- _info
- info
- _median_nancheck
- _opt_info
- drop_metadata

## venv\Lib\site-packages\numpy\lib\_version.py

### Classes
- NumpyVersion

## venv\Lib\site-packages\numpy\lib\array_utils.py

## venv\Lib\site-packages\numpy\lib\format.py

## venv\Lib\site-packages\numpy\lib\introspect.py

### Functions
- opt_func_info

## venv\Lib\site-packages\numpy\lib\mixins.py

### Classes
- NDArrayOperatorsMixin

### Functions
- _disables_array_ufunc
- _binary_method
- _reflected_binary_method
- _inplace_binary_method
- _numeric_methods
- _unary_method

## venv\Lib\site-packages\numpy\lib\npyio.py

## venv\Lib\site-packages\numpy\lib\recfunctions.py

### Functions
- _recursive_fill_fields_dispatcher
- recursive_fill_fields
- _get_fieldspec
- get_names
- get_names_flat
- flatten_descr
- _zip_dtype
- _zip_descr
- get_fieldstructure
- _izip_fields_flat
- _izip_fields
- _izip_records
- _fix_output
- _fix_defaults
- _merge_arrays_dispatcher
- merge_arrays
- _drop_fields_dispatcher
- drop_fields
- _keep_fields
- _rec_drop_fields_dispatcher
- rec_drop_fields
- _rename_fields_dispatcher
- rename_fields
- _append_fields_dispatcher
- append_fields
- _rec_append_fields_dispatcher
- rec_append_fields
- _repack_fields_dispatcher
- repack_fields
- _get_fields_and_offsets
- _common_stride
- _structured_to_unstructured_dispatcher
- structured_to_unstructured
- _unstructured_to_structured_dispatcher
- unstructured_to_structured
- _apply_along_fields_dispatcher
- apply_along_fields
- _assign_fields_by_name_dispatcher
- assign_fields_by_name
- _require_fields_dispatcher
- require_fields
- _stack_arrays_dispatcher
- stack_arrays
- _find_duplicates_dispatcher
- find_duplicates
- _join_by_dispatcher
- join_by
- _rec_join_dispatcher
- rec_join

## venv\Lib\site-packages\numpy\lib\scimath.py

## venv\Lib\site-packages\numpy\lib\stride_tricks.py

## venv\Lib\site-packages\numpy\lib\tests\__init__.py

## venv\Lib\site-packages\numpy\lib\tests\test__datasource.py

### Classes
- TestDataSourceOpen
- TestDataSourceExists
- TestDataSourceAbspath
- TestRepositoryAbspath
- TestRepositoryExists
- TestOpenFunc

### Functions
- urlopen_stub
- setup_module
- teardown_module
- valid_textfile
- invalid_textfile
- valid_httpurl
- invalid_httpurl
- valid_baseurl
- invalid_baseurl
- valid_httpfile
- invalid_httpfile
- test_del_attr_handling

## venv\Lib\site-packages\numpy\lib\tests\test__iotools.py

### Classes
- TestLineSplitter
- TestNameValidator
- TestStringConverter
- TestMiscFunctions

### Functions
- _bytes_to_date

## venv\Lib\site-packages\numpy\lib\tests\test__version.py

### Functions
- test_main_versions
- test_version_1_point_10
- test_alpha_beta_rc
- test_dev_version
- test_dev_a_b_rc_mixed
- test_dev0_version
- test_dev0_a_b_rc_mixed
- test_raises

## venv\Lib\site-packages\numpy\lib\tests\test_array_utils.py

### Classes
- TestByteBounds

## venv\Lib\site-packages\numpy\lib\tests\test_arraypad.py

### Classes
- TestAsPairs
- TestConditionalShortcuts
- TestStatistic
- TestConstant
- TestLinearRamp
- TestReflect
- TestEmptyArray
- TestSymmetric
- TestWrap
- TestEdge
- TestEmpty
- TestPadWidth

### Functions
- test_legacy_vector_functionality
- test_unicode_mode
- test_object_input
- test_kwargs
- test_constant_zero_default
- test_unsupported_mode
- test_non_contiguous_array
- test_memory_layout_persistence
- test_dtype_persistence
- test_pad_dict_pad_width

## venv\Lib\site-packages\numpy\lib\tests\test_arraysetops.py

### Classes
- TestSetOps
- TestUnique

## venv\Lib\site-packages\numpy\lib\tests\test_arrayterator.py

### Functions
- test

## venv\Lib\site-packages\numpy\lib\tests\test_format.py

### Classes
- BytesIOSRandomSize

### Functions
- roundtrip
- roundtrip_randsize
- roundtrip_truncated
- assert_equal_
- test_roundtrip
- test_roundtrip_randsize
- test_roundtrip_truncated
- test_file_truncated
- test_long_str
- test_memmap_roundtrip
- test_compressed_roundtrip
- test_load_padded_dtype
- test_pickle_python2_python3
- test_pickle_disallow
- test_descr_to_dtype
- test_version_2_0
- test_version_2_0_memmap
- test_huge_header
- test_huge_header_npz
- test_write_version
- test_read_magic
- test_read_magic_bad_magic
- test_read_version_1_0_bad_magic
- test_bad_magic_args
- test_large_header
- test_read_array_header_1_0
- test_read_array_header_2_0
- test_bad_header
- test_large_file_support
- test_large_archive
- test_empty_npz
- test_unicode_field_names
- test_header_growth_axis
- test_metadata_dtype

## venv\Lib\site-packages\numpy\lib\tests\test_function_base.py

### Classes
- TestRot90
- TestFlip
- TestAny
- TestAll
- TestCopy
- TestAverage
- TestSelect
- TestInsert
- TestAmax
- TestAmin
- TestPtp
- TestCumsum
- TestProd
- TestCumprod
- TestDiff
- TestDelete
- TestGradient
- TestAngle
- TestTrimZeros
- TestExtins
- TestVectorize
- TestLeaks
- TestDigitize
- TestUnwrap
- TestFilterwindows
- TestTrapezoid
- TestSinc
- TestUnique
- TestCheckFinite
- TestCorrCoef
- TestCov
- Test_I0
- TestKaiser
- TestMeshgrid
- TestPiecewise
- TestBincount
- TestInterp
- TestPercentile
- TestQuantile
- TestLerp
- TestMedian
- TestSortComplex

### Functions
- get_mat
- _make_complex
- test_any_and_all_result_dtype
- test_cumulative_include_initial
- _foo1
- _foo2

## venv\Lib\site-packages\numpy\lib\tests\test_histograms.py

### Classes
- TestHistogram
- TestHistogramOptimBinNums
- TestHistogramdd

## venv\Lib\site-packages\numpy\lib\tests\test_index_tricks.py

### Classes
- TestRavelUnravelIndex
- TestGrid
- TestConcatenator
- TestNdenumerate
- TestIndexExpression
- TestIx_
- TestFillDiagonal
- TestDiagIndicesFrom

### Functions
- test_c_
- test_diag_indices
- test_ndindex
- test_ndindex_zero_dimensions_explicit
- test_ndindex_non_integer_dimensions
- test_ndindex_stop_iteration_behavior
- test_ndindex_iterator_independence
- test_ndindex_tuple_vs_args_consistency
- test_ndindex_against_ndenumerate_compatibility
- test_ndindex_multidimensional_correctness
- test_ndindex_large_dimensions_behavior
- test_ndindex_empty_iterator_behavior
- test_ndindex_negative_dimensions
- test_ndindex_empty_shape
- test_ndindex_negative_dim_raises

## venv\Lib\site-packages\numpy\lib\tests\test_io.py

### Classes
- TextIO
- RoundtripTest
- TestSaveLoad
- TestSavezLoad
- TestSaveTxt
- LoadTxtBase
- TestLoadTxt
- Testfromregex
- TestFromTxt
- TestPathUsage
- JustWriter
- JustReader

### Functions
- strptime
- test_gzip_load
- test_ducktyping
- test_gzip_loadtxt
- test_gzip_loadtxt_from_string
- test_npzfile_dict
- test_load_refcount
- test_load_multiple_arrays_until_eof
- test_savez_nopickle

## venv\Lib\site-packages\numpy\lib\tests\test_loadtxt.py

### Classes
- TestCReaderUnitTests

### Functions
- test_scientific_notation
- test_comment_multiple_chars
- mixed_types_structured
- test_structured_dtype_and_skiprows_no_empty_lines
- test_unpack_structured
- test_structured_dtype_with_shape
- test_structured_dtype_with_multi_shape
- test_nested_structured_subarray
- test_structured_dtype_offsets
- test_exception_negative_row_limits
- test_exception_noninteger_row_limits
- test_ndmin_single_row_or_col
- test_bad_ndmin
- test_blank_lines_spaces_delimit
- test_blank_lines_normal_delimiter
- test_maxrows_no_blank_lines
- test_exception_message_bad_values
- test_converters_negative_indices
- test_converters_negative_indices_with_usecols
- test_ragged_error
- test_ragged_usecols
- test_empty_usecols
- test_large_unicode_characters
- test_unicode_with_converter
- test_converter_with_structured_dtype
- test_converter_with_unicode_dtype
- test_read_huge_row
- test_huge_float
- test_string_no_length_given
- test_float_conversion
- test_bool
- test_integer_signs
- test_implicit_cast_float_to_int_fails
- test_complex_parsing
- test_read_from_generator
- test_read_from_generator_multitype
- test_read_from_bad_generator
- test_object_cleanup_on_read_error
- test_character_not_bytes_compatible
- test_invalid_converter
- test_converters_dict_raises_non_integer_key
- test_converters_dict_raises_non_col_key
- test_converters_dict_raises_val_not_callable
- test_quoted_field
- test_quoted_field_with_whitespace_delimiter
- test_quote_support_default
- test_quotechar_multichar_error
- test_comment_multichar_error_with_quote
- test_structured_dtype_with_quotes
- test_quoted_field_is_not_empty
- test_quoted_field_is_not_empty_nonstrict
- test_consecutive_quotechar_escaped
- test_warn_on_no_data
- test_warn_on_skipped_data
- test_byteswapping_and_unaligned
- test_unicode_whitespace_stripping
- test_unicode_whitespace_stripping_complex
- test_bad_complex
- test_nul_character_error
- test_no_thousands_support
- test_bad_newline_in_iterator
- test_good_newline_in_iterator
- test_universal_newlines_quoted
- test_null_character
- test_iterator_fails_getting_next_line
- test_delimiter_comment_collision_raises
- test_delimiter_quotechar_collision_raises
- test_comment_quotechar_collision_raises
- test_delimiter_and_multiple_comments_collision_raises
- test_collision_with_default_delimiter_raises
- test_control_character_newline_raises
- test_parametric_unit_discovery
- test_str_dtype_unit_discovery_with_converter
- test_control_character_empty
- test_control_characters_as_bytes
- test_field_growing_cases
- test_maxrows_exceeding_chunksize
- test_skiprow_exceeding_maxrows_exceeding_chunksize

## venv\Lib\site-packages\numpy\lib\tests\test_mixins.py

### Classes
- ArrayLike
- TestNDArrayOperatorsMixin

### Functions
- wrap_array_like
- _assert_equal_type_and_value

## venv\Lib\site-packages\numpy\lib\tests\test_nanfunctions.py

### Classes
- TestSignatureMatch
- TestNanFunctions_MinMax
- TestNanFunctions_ArgminArgmax
- TestNanFunctions_NumberTypes
- SharedNanFunctionsTestsMixin
- TestNanFunctions_SumProd
- TestNanFunctions_CumSumProd
- TestNanFunctions_MeanVarStd
- TestNanFunctions_Median
- TestNanFunctions_Percentile
- TestNanFunctions_Quantile

### Functions
- test__nan_mask
- test__replace_nan
- test_memmap_takes_fast_route

## venv\Lib\site-packages\numpy\lib\tests\test_packbits.py

### Classes
- TestCount

### Functions
- test_packbits
- test_packbits_empty
- test_packbits_empty_with_axis
- test_packbits_large
- test_packbits_very_large
- test_unpackbits
- test_pack_unpack_order
- test_unpackbits_empty
- test_unpackbits_empty_with_axis
- test_unpackbits_large

## venv\Lib\site-packages\numpy\lib\tests\test_polynomial.py

### Classes
- TestPolynomial

## venv\Lib\site-packages\numpy\lib\tests\test_recfunctions.py

### Classes
- TestRecFunctions
- TestRecursiveFillFields
- TestMergeArrays
- TestAppendFields
- TestStackArrays
- TestJoinBy
- TestJoinBy2
- TestAppendFieldsObj

## venv\Lib\site-packages\numpy\lib\tests\test_regression.py

### Classes
- TestRegression

## venv\Lib\site-packages\numpy\lib\tests\test_shape_base.py

### Classes
- TestTakeAlongAxis
- TestPutAlongAxis
- TestApplyAlongAxis
- TestApplyOverAxes
- TestExpandDims
- TestArraySplit
- TestSplit
- TestColumnStack
- TestDstack
- TestHsplit
- TestVsplit
- TestDsplit
- TestSqueeze
- TestKron
- TestTile
- TestMayShareMemory

### Functions
- _add_keepdims
- compare_results

## venv\Lib\site-packages\numpy\lib\tests\test_stride_tricks.py

### Classes
- TestSlidingWindowView
- VerySimpleSubClass
- SimpleSubClass

### Functions
- assert_shapes_correct
- assert_incompatible_shapes_raise
- assert_same_as_ufunc
- test_same
- test_broadcast_kwargs
- test_one_off
- test_same_input_shapes
- test_two_compatible_by_ones_input_shapes
- test_two_compatible_by_prepending_ones_input_shapes
- test_incompatible_shapes_raise_valueerror
- test_same_as_ufunc
- test_broadcast_to_succeeds
- test_broadcast_to_raises
- test_broadcast_shape
- test_broadcast_shapes_succeeds
- test_broadcast_shapes_raises
- test_as_strided
- as_strided_writeable
- test_subclasses
- test_writeable
- test_writeable_memoryview
- test_reference_types
- test_as_strided_checked_different_dtypes
- test_as_strided_checked_1d_positive_strides
- test_as_strided_checked_sliding_window_1d
- test_as_strided_checked_2d_default_strides
- test_as_strided_checked_zero_stride_broadcasting
- test_as_strided_checked_out_of_bounds_positive_strides
- test_as_strided_checked_view_of_larger_array
- test_as_strided_checked_view_with_offset
- test_as_strided_checked_view_out_of_bounds_negative
- test_as_strided_checked_view_out_of_bounds_positive
- test_as_strided_checked_nested_views
- test_as_strided_checked_sliced_array
- test_as_strided_checked_view_parametrized

## venv\Lib\site-packages\numpy\lib\tests\test_twodim_base.py

### Classes
- TestEye
- TestDiag
- TestFliplr
- TestFlipud
- TestHistogram2d
- TestTri
- TestTriuIndices
- TestTrilIndicesFrom
- TestTriuIndicesFrom
- TestVander

### Functions
- get_mat
- test_tril_triu_ndim2
- test_tril_triu_ndim3
- test_tril_triu_with_inf
- test_tril_triu_dtype
- test_mask_indices
- test_tril_indices

## venv\Lib\site-packages\numpy\lib\tests\test_type_check.py

### Classes
- TestCommonType
- TestMintypecode
- TestIsscalar
- TestReal
- TestImag
- TestIscomplex
- TestIsreal
- TestIscomplexobj
- TestIsrealobj
- TestIsnan
- TestIsfinite
- TestIsinf
- TestIsposinf
- TestIsneginf
- TestNanToNum
- TestRealIfClose

### Functions
- assert_all

## venv\Lib\site-packages\numpy\lib\tests\test_ufunclike.py

### Classes
- TestUfunclike
- TestFixDeprecation

## venv\Lib\site-packages\numpy\lib\tests\test_utils.py

### Functions
- test_assert_raises_regex_context_manager
- test_info_method_heading
- test_drop_metadata
- test_drop_metadata_identity_and_copy

## venv\Lib\site-packages\numpy\lib\user_array.py

## venv\Lib\site-packages\numpy\linalg\__init__.py

## venv\Lib\site-packages\numpy\linalg\_linalg.py

### Classes
- EigResult
- EighResult
- QRResult
- SlogdetResult
- SVDResult
- LinAlgError

### Functions
- _raise_linalgerror_singular
- _raise_linalgerror_nonposdef
- _raise_linalgerror_eigenvalues_nonconvergence
- _raise_linalgerror_svd_nonconvergence
- _raise_linalgerror_lstsq
- _raise_linalgerror_qr
- _makearray
- isComplexType
- _realType
- _complexType
- _to_real_if_imag_zero
- _commonType
- _to_native_byte_order
- _assert_2d
- _assert_stacked_2d
- _assert_stacked_square
- _assert_finite
- _is_empty_2d
- transpose
- _tensorsolve_dispatcher
- tensorsolve
- _solve_dispatcher
- solve
- _tensorinv_dispatcher
- tensorinv
- _unary_dispatcher
- inv
- _matrix_power_dispatcher
- matrix_power
- _cholesky_dispatcher
- cholesky
- _outer_dispatcher
- outer
- _qr_dispatcher
- qr
- eigvals
- _eigvalsh_dispatcher
- eigvalsh
- eig
- eigh
- _svd_dispatcher
- svd
- _svdvals_dispatcher
- svdvals
- _cond_dispatcher
- cond
- _matrix_rank_dispatcher
- matrix_rank
- _pinv_dispatcher
- pinv
- slogdet
- det
- _lstsq_dispatcher
- lstsq
- _multi_svd_norm
- _norm_dispatcher
- norm
- _multidot_dispatcher
- multi_dot
- _multi_dot_three
- _multi_dot_matrix_chain_order
- _multi_dot
- _diagonal_dispatcher
- diagonal
- _trace_dispatcher
- trace
- _cross_dispatcher
- cross
- _matmul_dispatcher
- matmul
- _tensordot_dispatcher
- tensordot
- _matrix_transpose_dispatcher
- matrix_transpose
- _matrix_norm_dispatcher
- matrix_norm
- _vector_norm_dispatcher
- vector_norm
- _vecdot_dispatcher
- vecdot

## venv\Lib\site-packages\numpy\linalg\tests\__init__.py

## venv\Lib\site-packages\numpy\linalg\tests\test_deprecations.py

### Functions
- test_qr_mode_full_future_warning

## venv\Lib\site-packages\numpy\linalg\tests\test_linalg.py

### Classes
- LinalgCase
- LinalgTestCase
- LinalgSquareTestCase
- LinalgNonsquareTestCase
- HermitianTestCase
- LinalgGeneralizedSquareTestCase
- LinalgGeneralizedNonsquareTestCase
- HermitianGeneralizedTestCase
- SolveCases
- TestSolve
- InvCases
- TestInv
- EigvalsCases
- TestEigvals
- EigCases
- TestEig
- SVDBaseTests
- SVDCases
- TestSVD
- SVDHermitianCases
- TestSVDHermitian
- CondCases
- TestCond
- PinvCases
- TestPinv
- PinvHermitianCases
- TestPinvHermitian
- DetCases
- TestDet
- LstsqCases
- TestLstsq
- TestMatrixPower
- TestEigvalshCases
- TestEigvalsh
- TestEighCases
- TestEigh
- _TestNormBase
- _TestNormGeneral
- _TestNorm2D
- _TestNorm
- TestNorm_NonSystematic
- _TestNormDoubleBase
- _TestNormSingleBase
- _TestNormInt64Base
- TestNormDouble
- TestNormSingle
- TestNormInt64
- TestMatrixRank
- TestQR
- TestCholesky
- TestOuter
- TestMultiDot
- TestTensorinv
- TestTensorsolve

### Functions
- consistent_subclass
- assert_almost_equal
- get_real_dtype
- get_complex_dtype
- get_rtol
- apply_tag
- _make_generalized_cases
- _stride_comb_iter
- _make_strided_cases
- identity_like_generalized
- test_pinv_rtol_arg
- test_reduced_rank
- test_byteorder_check
- test_generalized_raise_multiloop
- test_xerbla_override
- test_sdot_bug_8577
- test_unsupported_commontype
- test_blas64_dot
- test_blas64_geqrf_lwork_smoketest
- test_diagonal
- test_trace
- test_cross
- test_tensordot
- test_matmul
- test_matrix_transpose
- test_matrix_norm
- test_matrix_norm_empty
- test_vector_norm
- test_vector_norm_empty
- test_empty_matrix_rank

## venv\Lib\site-packages\numpy\linalg\tests\test_regression.py

### Classes
- TestRegression

## venv\Lib\site-packages\numpy\ma\__init__.py

## venv\Lib\site-packages\numpy\ma\core.py

### Classes
- MaskedArrayFutureWarning
- MAError
- MaskError
- _DomainCheckInterval
- _DomainTan
- _DomainSafeDivide
- _DomainGreater
- _DomainGreaterEqual
- _MaskedUFunc
- _MaskedUnaryOperation
- _MaskedBinaryOperation
- _DomainedBinaryOperation
- _MaskedPrintOption
- MaskedIterator
- MaskedArray
- mvoid
- MaskedConstant
- _extrema_operation

### Functions
- _deprecate_argsort_axis
- doc_note
- _recursive_fill_value
- _get_dtype_of
- default_fill_value
- _extremum_fill_value
- minimum_fill_value
- maximum_fill_value
- _recursive_set_fill_value
- _check_fill_value
- set_fill_value
- get_fill_value
- common_fill_value
- filled
- get_masked_subclass
- getdata
- fix_invalid
- is_string_or_list_of_strings
- _replace_dtype_fields_recursive
- _replace_dtype_fields
- make_mask_descr
- getmask
- getmaskarray
- is_mask
- _shrink_mask
- make_mask
- make_mask_none
- _recursive_mask_or
- mask_or
- flatten_mask
- _check_mask_axis
- masked_where
- masked_greater
- masked_greater_equal
- masked_less
- masked_less_equal
- masked_not_equal
- masked_equal
- masked_inside
- masked_outside
- masked_object
- masked_values
- masked_invalid
- _recursive_printoption
- _recursive_filled
- flatten_structured_array
- _arraymethod
- _mareconstruct
- isMaskedArray
- array
- is_masked
- min
- max
- ptp
- _frommethod
- take
- power
- argsort
- sort
- compressed
- concatenate
- diag
- left_shift
- right_shift
- put
- putmask
- transpose
- reshape
- resize
- ndim
- shape
- size
- diff
- where
- choose
- round
- round_
- _mask_propagate
- dot
- inner
- outer
- _convolve_or_correlate
- correlate
- convolve
- allequal
- allclose
- asarray
- asanyarray
- fromfile
- fromflex
- _convert2ma
- append

## venv\Lib\site-packages\numpy\ma\extras.py

### Classes
- MAxisConcatenator
- mr_class

### Functions
- issequence
- count_masked
- masked_all
- masked_all_like
- _fromnxfunction_function
- _fromnxfunction_single
- _fromnxfunction_seq
- _fromnxfunction_allargs
- flatten_inplace
- apply_along_axis
- apply_over_axes
- average
- median
- _median
- compress_nd
- compress_rowcols
- compress_rows
- compress_cols
- mask_rowcols
- mask_rows
- mask_cols
- ediff1d
- unique
- intersect1d
- setxor1d
- in1d
- isin
- union1d
- setdiff1d
- _covhelper
- cov
- corrcoef
- ndenumerate
- flatnotmasked_edges
- notmasked_edges
- flatnotmasked_contiguous
- notmasked_contiguous
- _ezclump
- clump_unmasked
- clump_masked
- vander
- polyfit

## venv\Lib\site-packages\numpy\ma\mrecords.py

### Classes
- MaskedRecords

### Functions
- _checknames
- _get_fieldmask
- _mrreconstruct
- fromarrays
- fromrecords
- _guessvartypes
- openfile
- fromtextfile
- addfield

## venv\Lib\site-packages\numpy\ma\tests\__init__.py

## venv\Lib\site-packages\numpy\ma\tests\test_arrayobject.py

### Functions
- test_matrix_transpose_raises_error_for_1d
- test_matrix_transpose_equals_transpose_2d
- test_matrix_transpose_equals_swapaxes

## venv\Lib\site-packages\numpy\ma\tests\test_core.py

### Classes
- TestMaskedArray
- TestMaskedArrayArithmetic
- TestMaskedArrayAttributes
- TestFillingValues
- TestUfuncs
- TestMaskedArrayInPlaceArithmetic
- TestMaskedArrayMethods
- TestMaskedArrayMathMethods
- TestMaskedArrayMathMethodsComplex
- TestMaskedArrayFunctions
- TestMaskedFields
- TestMaskedObjectArray
- TestMaskedView
- TestOptionalArgs
- TestMaskedConstant
- TestMaskedWhereAliases
- TestPatternMatching

### Functions
- err_status
- test_masked_array
- test_masked_array_no_copy
- test_append_masked_array
- test_append_masked_array_along_axis
- test_default_fill_value_complex
- test_string_dtype_fill_value_on_construction
- test_string_dtype_default_fill_value
- test_string_dtype_fill_value_persists_through_slice
- test_setting_fill_value_attribute
- test_ufunc_with_output
- test_ufunc_with_out_varied
- test_astype_mask_ordering
- test_astype_basic
- test_fieldless_void
- test_mask_shape_assignment_does_not_break_masked
- test_doc_note
- test_gh_22556
- test_gh_21022
- test_deepcopy_2d_obj
- test_deepcopy_0d_obj
- test_uint_fill_value_and_filled
- test_frommethod_signature
- test_convert2ma_signature

## venv\Lib\site-packages\numpy\ma\tests\test_deprecations.py

### Classes
- TestArgsort
- TestMinimumMaximum
- TestDtypeSet

## venv\Lib\site-packages\numpy\ma\tests\test_extras.py

### Classes
- TestGeneric
- TestAverage
- TestConcatenator
- TestNotMasked
- TestCompressFunctions
- TestApplyAlongAxis
- TestApplyOverAxes
- TestMedian
- TestCov
- TestCorrcoef
- TestPolynomial
- TestArraySetOps
- TestShapeBase
- TestNDEnumerate
- TestStack

## venv\Lib\site-packages\numpy\ma\tests\test_mrecords.py

### Classes
- TestMRecords
- TestView
- TestMRecordsImport

### Functions
- test_record_array_with_object_field

## venv\Lib\site-packages\numpy\ma\tests\test_old_ma.py

### Classes
- TestMa
- TestUfuncs
- TestArrayMethods

### Functions
- eq
- eqmask

## venv\Lib\site-packages\numpy\ma\tests\test_regression.py

### Classes
- TestRegression

## venv\Lib\site-packages\numpy\ma\tests\test_subclassing.py

### Classes
- SubArray
- SubMaskedArray
- MSubArray
- CSAIterator
- ComplicatedSubArray
- WrappedArray
- TestSubclassing
- ArrayNoInheritance
- TestClassWrapping

### Functions
- assert_startswith
- test_array_no_inheritance

## venv\Lib\site-packages\numpy\ma\testutils.py

### Functions
- approx
- almost
- _assert_equal_on_sequences
- assert_equal_records
- assert_equal
- fail_if_equal
- assert_almost_equal
- assert_array_compare
- assert_array_equal
- fail_if_array_equal
- assert_array_approx_equal
- assert_array_almost_equal
- assert_array_less
- assert_mask_equal

## venv\Lib\site-packages\numpy\matlib.py

### Functions
- empty
- ones
- zeros
- identity
- eye
- rand
- randn
- repmat

## venv\Lib\site-packages\numpy\matrixlib\__init__.py

## venv\Lib\site-packages\numpy\matrixlib\defmatrix.py

### Classes
- matrix

### Functions
- _convert_from_string
- asmatrix
- _from_string
- bmat

## venv\Lib\site-packages\numpy\matrixlib\tests\__init__.py

## venv\Lib\site-packages\numpy\matrixlib\tests\test_defmatrix.py

### Classes
- TestCtor
- TestProperties
- TestCasting
- TestAlgebra
- TestMatrixReturn
- TestIndexing
- TestNewScalarIndexing
- TestPower
- TestShape
- TestPatternMatching

## venv\Lib\site-packages\numpy\matrixlib\tests\test_interaction.py

### Classes
- TestConcatenatorMatrix

### Functions
- test_fancy_indexing
- test_polynomial_mapdomain
- test_sort_matrix_none
- test_partition_matrix_none
- test_dot_scalar_and_matrix_of_objects
- test_inner_scalar_and_matrix
- test_inner_scalar_and_matrix_of_objects
- test_iter_allocate_output_subtype
- like_function
- test_array_astype
- test_stack
- test_object_scalar_multiply
- test_nanfunctions_matrices
- test_nanfunctions_matrices_general
- test_average_matrix
- test_dot_matrix
- test_ediff1d_matrix
- test_apply_along_axis_matrix
- test_kron_matrix
- test_array_equal_error_message_matrix
- test_array_almost_equal_matrix

## venv\Lib\site-packages\numpy\matrixlib\tests\test_masked_matrix.py

### Classes
- MMatrix
- TestMaskedMatrix
- TestSubclassing
- TestConcatenator

## venv\Lib\site-packages\numpy\matrixlib\tests\test_matrix_linalg.py

### Classes
- MatrixTestCase
- TestSolveMatrix
- TestInvMatrix
- TestEigvalsMatrix
- TestEigMatrix
- TestSVDMatrix
- TestCondMatrix
- TestPinvMatrix
- TestDetMatrix
- TestLstsqMatrix
- _TestNorm2DMatrix
- TestNormDoubleMatrix
- TestNormSingleMatrix
- TestNormInt64Matrix
- TestQRMatrix

## venv\Lib\site-packages\numpy\matrixlib\tests\test_multiarray.py

### Classes
- TestView

## venv\Lib\site-packages\numpy\matrixlib\tests\test_numeric.py

### Classes
- TestDot

### Functions
- test_diagonal

## venv\Lib\site-packages\numpy\matrixlib\tests\test_regression.py

### Classes
- TestRegression

## venv\Lib\site-packages\numpy\polynomial\__init__.py

### Functions
- set_default_printstyle

## venv\Lib\site-packages\numpy\polynomial\_polybase.py

### Classes
- ABCPolyBase

## venv\Lib\site-packages\numpy\polynomial\chebyshev.py

### Classes
- Chebyshev

### Functions
- _cseries_to_zseries
- _zseries_to_cseries
- _zseries_mul
- _zseries_div
- _zseries_der
- _zseries_int
- poly2cheb
- cheb2poly
- chebline
- chebfromroots
- chebadd
- chebsub
- chebmulx
- chebmul
- chebdiv
- chebpow
- chebder
- chebint
- chebval
- chebval2d
- chebgrid2d
- chebval3d
- chebvalnd
- chebgrid3d
- chebvander
- chebvander2d
- chebvander3d
- chebfit
- chebcompanion
- chebroots
- chebinterpolate
- chebgauss
- chebweight
- chebpts1
- chebpts2

## venv\Lib\site-packages\numpy\polynomial\hermite.py

### Classes
- Hermite

### Functions
- poly2herm
- herm2poly
- hermline
- hermfromroots
- hermadd
- hermsub
- hermmulx
- hermmul
- hermdiv
- hermpow
- hermder
- hermint
- hermval
- hermval2d
- hermgrid2d
- hermval3d
- hermvalnd
- hermgrid3d
- hermvander
- hermvander2d
- hermvander3d
- hermfit
- hermcompanion
- hermroots
- _normed_hermite_n
- hermgauss
- hermweight

## venv\Lib\site-packages\numpy\polynomial\hermite_e.py

### Classes
- HermiteE

### Functions
- poly2herme
- herme2poly
- hermeline
- hermefromroots
- hermeadd
- hermesub
- hermemulx
- hermemul
- hermediv
- hermepow
- hermeder
- hermeint
- hermeval
- hermeval2d
- hermegrid2d
- hermeval3d
- hermevalnd
- hermegrid3d
- hermevander
- hermevander2d
- hermevander3d
- hermefit
- hermecompanion
- hermeroots
- _normed_hermite_e_n
- hermegauss
- hermeweight

## venv\Lib\site-packages\numpy\polynomial\laguerre.py

### Classes
- Laguerre

### Functions
- poly2lag
- lag2poly
- lagline
- lagfromroots
- lagadd
- lagsub
- lagmulx
- lagmul
- lagdiv
- lagpow
- lagder
- lagint
- lagval
- lagval2d
- laggrid2d
- lagval3d
- lagvalnd
- laggrid3d
- lagvander
- lagvander2d
- lagvander3d
- lagfit
- lagcompanion
- lagroots
- laggauss
- lagweight

## venv\Lib\site-packages\numpy\polynomial\legendre.py

### Classes
- Legendre

### Functions
- poly2leg
- leg2poly
- legline
- legfromroots
- legadd
- legsub
- legmulx
- legmul
- legdiv
- legpow
- legder
- legint
- legval
- legval2d
- leggrid2d
- legval3d
- legvalnd
- leggrid3d
- legvander
- legvander2d
- legvander3d
- legfit
- legcompanion
- legroots
- leggauss
- legweight

## venv\Lib\site-packages\numpy\polynomial\polynomial.py

### Classes
- Polynomial

### Functions
- polyline
- polyfromroots
- polyadd
- polysub
- polymulx
- polymul
- polydiv
- polypow
- polyder
- polyint
- polyval
- polyvalfromroots
- _polyval2d_dispatcher
- _polygrid2d_dispatcher
- polyval2d
- polygrid2d
- polyval3d
- _polyvalnd_dispatcher
- polyvalnd
- polygrid3d
- polyvander
- polyvander2d
- polyvander3d
- polyfit
- polycompanion
- polyroots

## venv\Lib\site-packages\numpy\polynomial\polyutils.py

### Functions
- trimseq
- as_series
- trimcoef
- getdomain
- mapparms
- mapdomain
- _nth_slice
- _vander_nd
- _vander_nd_flat
- _fromroots
- _valnd
- _gridnd
- _div
- _add
- _sub
- _fit
- _pow
- _as_int
- format_float

## venv\Lib\site-packages\numpy\polynomial\tests\__init__.py

## venv\Lib\site-packages\numpy\polynomial\tests\test_chebyshev.py

### Classes
- TestPrivate
- TestConstants
- TestArithmetic
- TestEvaluation
- TestIntegral
- TestDerivative
- TestVander
- TestFitting
- TestInterpolate
- TestCompanion
- TestGauss
- TestMisc

### Functions
- trim

## venv\Lib\site-packages\numpy\polynomial\tests\test_classes.py

### Classes
- TestInterpolate

### Functions
- Poly
- assert_poly_almost_equal
- test_conversion
- test_cast
- test_identity
- test_basis
- test_fromroots
- test_bad_conditioned_fit
- test_fit
- test_equal
- test_not_equal
- test_add
- test_sub
- test_mul
- test_floordiv
- test_truediv
- test_mod
- test_divmod
- test_roots
- test_degree
- test_copy
- test_integ
- test_deriv
- test_linspace
- test_pow
- test_call
- test_call_with_list
- test_cutdeg
- test_truncate
- test_trim
- test_mapparms
- test_ufunc_override

## venv\Lib\site-packages\numpy\polynomial\tests\test_hermite.py

### Classes
- TestConstants
- TestArithmetic
- TestEvaluation
- TestIntegral
- TestDerivative
- TestVander
- TestFitting
- TestCompanion
- TestGauss
- TestMisc

### Functions
- trim

## venv\Lib\site-packages\numpy\polynomial\tests\test_hermite_e.py

### Classes
- TestConstants
- TestArithmetic
- TestEvaluation
- TestIntegral
- TestDerivative
- TestVander
- TestFitting
- TestCompanion
- TestGauss
- TestMisc

### Functions
- trim

## venv\Lib\site-packages\numpy\polynomial\tests\test_laguerre.py

### Classes
- TestConstants
- TestArithmetic
- TestEvaluation
- TestIntegral
- TestDerivative
- TestVander
- TestFitting
- TestCompanion
- TestGauss
- TestMisc

### Functions
- trim

## venv\Lib\site-packages\numpy\polynomial\tests\test_legendre.py

### Classes
- TestConstants
- TestArithmetic
- TestEvaluation
- TestIntegral
- TestDerivative
- TestVander
- TestFitting
- TestCompanion
- TestGauss
- TestMisc

### Functions
- trim

## venv\Lib\site-packages\numpy\polynomial\tests\test_polynomial.py

### Classes
- TestConstants
- TestArithmetic
- TestFraction
- TestEvaluation
- TestIntegral
- TestDerivative
- TestVander
- TestCompanion
- TestMisc
- ArrayFunctionInterceptor

### Functions
- trim
- test_polyval2d_array_function_hook
- test_polygrid2d_array_function_hook

## venv\Lib\site-packages\numpy\polynomial\tests\test_polyutils.py

### Classes
- TestMisc
- TestDomain

## venv\Lib\site-packages\numpy\polynomial\tests\test_printing.py

### Classes
- TestStrUnicodeSuperSubscripts
- TestStrAscii
- TestLinebreaking
- TestFormat
- TestRepr
- TestLatexRepr
- TestPrintOptions

### Functions
- test_set_default_printoptions
- test_complex_coefficients
- test_numeric_object_coefficients
- test_nonnumeric_object_coefficients
- test_symbol

## venv\Lib\site-packages\numpy\polynomial\tests\test_symbol.py

### Classes
- TestInit
- TestUnaryOperators
- TestBinaryOperatorsSameSymbol
- TestBinaryOperatorsDifferentSymbol
- TestEquality
- TestExtraMethods

### Functions
- test_composition
- test_fit
- test_froomroots
- test_identity
- test_basis

## venv\Lib\site-packages\numpy\random\__init__.py

### Functions
- __RandomState_ctor

## venv\Lib\site-packages\numpy\random\_examples\cffi\extending.py

## venv\Lib\site-packages\numpy\random\_examples\cffi\parse.py

### Functions
- parse_distributions_h

## venv\Lib\site-packages\numpy\random\_examples\numba\extending.py

### Functions
- normals
- numbacall
- numpycall
- bounded_uint
- bounded_uints

## venv\Lib\site-packages\numpy\random\_examples\numba\extending_distributions.py

### Functions
- normals

## venv\Lib\site-packages\numpy\random\_pickle.py

### Functions
- __bit_generator_ctor
- __generator_ctor
- __randomstate_ctor

## venv\Lib\site-packages\numpy\random\tests\__init__.py

## venv\Lib\site-packages\numpy\random\tests\data\__init__.py

## venv\Lib\site-packages\numpy\random\tests\test_direct.py

### Classes
- Base
- TestPhilox
- TestPCG64
- TestPCG64DXSM
- TestMT19937
- TestSFC64
- TestDefaultRNG

### Functions
- assert_state_equal
- uint32_to_float32
- uniform32_from_uint64
- uniform32_from_uint53
- uniform32_from_uint32
- uniform32_from_uint
- uniform_from_uint
- uniform_from_uint64
- uniform_from_uint32
- uniform_from_dsfmt
- gauss_from_uint
- test_seedsequence
- test_generator_spawning
- test_spawn_negative_n_children
- test_non_spawnable

## venv\Lib\site-packages\numpy\random\tests\test_extending.py

### Functions
- test_cython
- test_numba
- test_cffi

## venv\Lib\site-packages\numpy\random\tests\test_generator_mt19937.py

### Classes
- TestSeed
- TestBinomial
- TestMultinomial
- TestMultivariateHypergeometric
- TestSetState
- TestIntegers
- TestRandomDist
- TestBroadcast
- TestThread
- TestSingleEltArrayInput

### Functions
- endpoint
- test_jumped
- test_broadcast_size_error
- test_broadcast_size_scalar
- test_ragged_shuffle
- test_single_arg_integer_exception
- test_c_contig_req_out
- test_contig_req_out
- test_generator_ctor_old_style_pickle
- test_pickle_preserves_seed_sequence
- test_legacy_pickle

## venv\Lib\site-packages\numpy\random\tests\test_generator_mt19937_regressions.py

### Classes
- TestRegression

## venv\Lib\site-packages\numpy\random\tests\test_random.py

### Classes
- TestSeed
- TestBinomial
- TestMultinomial
- TestSetState
- TestRandint
- TestRandomDist
- TestBroadcast
- TestThread
- TestSingleEltArrayInput

## venv\Lib\site-packages\numpy\random\tests\test_randomstate.py

### Classes
- TestSeed
- TestBinomial
- TestMultinomial
- TestSetState
- TestRandint
- TestRandomDist
- TestBroadcast
- TestThread
- TestSingleEltArrayInput

### Functions
- int_func
- restore_singleton_bitgen
- assert_mt19937_state_equal
- test_integer_dtype
- test_integer_repeat
- test_broadcast_size_error
- test_randomstate_ctor_old_style_pickle
- test_hot_swap
- test_seed_alt_bit_gen
- test_state_error_alt_bit_gen
- test_swap_worked
- test_swapped_singleton_against_direct

## venv\Lib\site-packages\numpy\random\tests\test_randomstate_regression.py

### Classes
- TestRegression

### Functions
- test_multinomial_empty
- test_multinomial_1d_pval

## venv\Lib\site-packages\numpy\random\tests\test_regression.py

### Classes
- TestRegression

## venv\Lib\site-packages\numpy\random\tests\test_seed_sequence.py

### Functions
- test_reference_data
- test_zero_padding
- test_seedsequence_rejects_nested_sequence

## venv\Lib\site-packages\numpy\random\tests\test_smoke.py

### Classes
- RNGData
- RNG
- TestMT19937
- TestPhilox
- TestSFC64
- TestPCG64
- TestPCG64DXSM
- TestDefaultRNG

### Functions
- params_0
- params_1
- comp_state
- warmup

## venv\Lib\site-packages\numpy\rec\__init__.py

## venv\Lib\site-packages\numpy\strings\__init__.py

## venv\Lib\site-packages\numpy\testing\__init__.py

## venv\Lib\site-packages\numpy\testing\_private\__init__.py

## venv\Lib\site-packages\numpy\testing\_private\extbuild.py

### Functions
- build_and_import_extension
- compile_extension_module
- _convert_str_to_file
- _make_methods
- _make_source
- _c_compile
- build
- get_so_suffix

## venv\Lib\site-packages\numpy\testing\_private\utils.py

### Classes
- KnownFailureException
- _Dummy
- IgnoreException
- clear_and_catch_warnings
- suppress_warnings

### Functions
- assert_
- build_err_msg
- assert_equal
- print_assert_equal
- assert_almost_equal
- assert_approx_equal
- assert_array_compare
- assert_array_equal
- assert_array_almost_equal
- assert_array_less
- runstring
- assert_string_equal
- rundocs
- check_support_sve
- assert_raises
- assert_raises_regex
- decorate_methods
- measure
- _assert_valid_refcount
- assert_allclose
- assert_array_almost_equal_nulp
- assert_array_max_ulp
- nulp_diff
- _integer_repr
- integer_repr
- _assert_warns_context
- assert_warns
- _assert_no_warnings_context
- assert_no_warnings
- _gen_alignment_data
- tempdir
- temppath
- _assert_no_gc_cycles_context
- assert_no_gc_cycles
- break_cycles
- requires_memory
- check_free_memory
- _parse_size
- _get_mem_available
- _no_tracing
- _get_glibc_version
- run_threaded
- requires_deep_recursion
- run_subprocess

## venv\Lib\site-packages\numpy\testing\overrides.py

### Functions
- get_overridable_numpy_ufuncs
- allows_array_ufunc_override
- get_overridable_numpy_array_functions
- allows_array_function_override

## venv\Lib\site-packages\numpy\testing\print_coercion_tables.py

### Classes
- GenericObject

### Functions
- print_cancast_table
- print_coercion_table
- print_new_cast_table

## venv\Lib\site-packages\numpy\testing\tests\__init__.py

## venv\Lib\site-packages\numpy\testing\tests\test_utils.py

### Classes
- _GenericTest
- TestArrayEqual
- TestBuildErrorMessage
- TestEqual
- TestArrayAlmostEqual
- TestAlmostEqual
- TestApproxEqual
- TestArrayAssertLess
- TestWarns
- TestAssertAllclose
- TestArrayAlmostEqualNulp
- TestULP
- TestStringEqual
- my_cacw
- TestAssertNoGcCycles

### Functions
- assert_warn_len_equal
- test_warn_len_equal_call_scenarios
- _get_fresh_mod
- test_clear_and_catch_warnings
- test_suppress_warnings_module
- test_suppress_warnings_type
- test_suppress_warnings_decorate_no_record
- test_suppress_warnings_record
- test_suppress_warnings_forwarding
- test_tempdir
- test_temppath
- test_clear_and_catch_warnings_inherit

## venv\Lib\site-packages\numpy\tests\__init__.py

## venv\Lib\site-packages\numpy\tests\test__all__.py

### Functions
- test_no_duplicates_in_np__all__

## venv\Lib\site-packages\numpy\tests\test_configtool.py

### Classes
- TestNumpyConfig

### Functions
- test_pkg_config_entrypoint
- test_pkg_config_config_exists

## venv\Lib\site-packages\numpy\tests\test_ctypeslib.py

### Classes
- TestLoadLibrary
- TestNdpointer
- TestNdpointerCFunc
- TestAsArray
- TestAsCtypesType

## venv\Lib\site-packages\numpy\tests\test_lazyloading.py

### Functions
- test_lazy_load

## venv\Lib\site-packages\numpy\tests\test_matlib.py

### Functions
- test_empty
- test_ones
- test_zeros
- test_identity
- test_eye
- test_rand
- test_randn
- test_repmat

## venv\Lib\site-packages\numpy\tests\test_numpy_config.py

### Classes
- TestNumPyConfigs

## venv\Lib\site-packages\numpy\tests\test_numpy_version.py

### Functions
- test_valid_numpy_version
- test_short_version
- test_version_module

## venv\Lib\site-packages\numpy\tests\test_public_api.py

### Functions
- check_dir
- test_numpy_namespace
- test_import_lazy_import
- test_dir_testing
- test_numpy_linalg
- test_numpy_fft
- test_NPY_NO_EXPORT
- is_unexpected
- test_all_modules_are_expected
- test_all_modules_are_expected_2
- test_api_importable
- test_array_api_entry_point
- test_main_namespace_all_dir_coherence
- test_core_shims_coherence
- test_functions_single_location
- test___module___attribute
- _check_correct_qualname_and_module
- test___qualname___and___module___attribute

## venv\Lib\site-packages\numpy\tests\test_reloading.py

### Functions
- test_numpy_reloading
- test_novalue
- test_full_reimport

## venv\Lib\site-packages\numpy\tests\test_scripts.py

### Functions
- find_f2py_commands
- test_f2py
- test_pep338

## venv\Lib\site-packages\numpy\tests\test_warnings.py

### Classes
- ParseCall
- FindFuncs

### Functions
- test_warning_calls

## venv\Lib\site-packages\numpy\typing\__init__.py

### Functions
- __dir__
- __getattr__

## venv\Lib\site-packages\numpy\typing\mypy_plugin.py

### Functions
- _get_precision_dict
- _get_extended_precision_list
- _get_c_intp_name

## venv\Lib\site-packages\numpy\typing\tests\__init__.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\arithmetic.py

### Classes
- Object

## venv\Lib\site-packages\numpy\typing\tests\data\pass\array_constructors.py

### Classes
- Index
- SubClass

### Functions
- func

## venv\Lib\site-packages\numpy\typing\tests\data\pass\array_like.py

### Classes
- A

## venv\Lib\site-packages\numpy\typing\tests\data\pass\arrayprint.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\arrayterator.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\bitwise_ops.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\comparisons.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\dtype.py

### Classes
- Test

## venv\Lib\site-packages\numpy\typing\tests\data\pass\einsumfunc.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\flatiter.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\fromnumeric.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\index_tricks.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\lib_user_array.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\lib_utils.py

### Functions
- func

## venv\Lib\site-packages\numpy\typing\tests\data\pass\lib_version.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\literal.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\ma.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\mod.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\modules.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\multiarray.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\ndarray_conversion.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\ndarray_misc.py

### Classes
- SubClass
- IntSubClass

### Functions
- f

## venv\Lib\site-packages\numpy\typing\tests\data\pass\ndarray_shape_manipulation.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\nditer.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\numeric.py

### Classes
- SubClass

## venv\Lib\site-packages\numpy\typing\tests\data\pass\numerictypes.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\random.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\recfunctions.py

### Functions
- test_recursive_fill_fields
- test_get_names
- test_get_names_flat
- test_flatten_descr
- test_get_fieldstructure
- test_merge_arrays
- test_drop_fields
- test_rename_fields
- test_repack_fields
- test_structured_to_unstructured
- unstructured_to_structured
- test_apply_along_fields
- test_assign_fields_by_name
- test_require_fields
- test_stack_arrays
- test_find_duplicates

## venv\Lib\site-packages\numpy\typing\tests\data\pass\scalars.py

### Classes
- D
- C
- B
- A

## venv\Lib\site-packages\numpy\typing\tests\data\pass\shape.py

### Classes
- XYGrid

### Functions
- accepts_2d

## venv\Lib\site-packages\numpy\typing\tests\data\pass\simple.py

### Functions
- ndarray_func
- iterable_func

## venv\Lib\site-packages\numpy\typing\tests\data\pass\ufunc_config.py

### Classes
- Write1
- Write2
- Write3

### Functions
- func1
- func2
- func3

## venv\Lib\site-packages\numpy\typing\tests\data\pass\ufunclike.py

### Classes
- Object

## venv\Lib\site-packages\numpy\typing\tests\data\pass\ufuncs.py

## venv\Lib\site-packages\numpy\typing\tests\data\pass\warnings_and_errors.py

## venv\Lib\site-packages\numpy\typing\tests\test_isfile.py

### Classes
- TestIsFile

## venv\Lib\site-packages\numpy\typing\tests\test_runtime.py

### Classes
- TypeTup
- TestRuntimeProtocol

### Functions
- test_get_args
- test_get_origin
- test_get_type_hints
- test_get_type_hints_str
- test_keys

## venv\Lib\site-packages\numpy\typing\tests\test_typing.py

### Functions
- _key_func
- _strip_filename
- strip_func
- run_mypy
- get_test_cases
- test_pass
- test_reveal
- test_code_runs

## venv\Lib\site-packages\numpy\version.py

## venv\Lib\site-packages\packaging\__init__.py

## venv\Lib\site-packages\packaging\_elffile.py

### Classes
- ELFInvalid
- EIClass
- EIData
- EMachine
- ELFFile

## venv\Lib\site-packages\packaging\_manylinux.py

### Classes
- _GLibCVersion

### Functions
- _parse_elf
- _is_linux_armhf
- _is_linux_i686
- _have_compatible_abi
- _glibc_version_string_confstr
- _glibc_version_string_ctypes
- _glibc_version_string
- _parse_glibc_version
- _get_glibc_version
- _is_compatible
- platform_tags

## venv\Lib\site-packages\packaging\_musllinux.py

### Classes
- _MuslVersion

### Functions
- _parse_musl_version
- _get_musl_version
- platform_tags

## venv\Lib\site-packages\packaging\_parser.py

### Classes
- Node
- Variable
- Value
- Op
- ParsedRequirement

### Functions
- parse_requirement
- _parse_requirement
- _parse_requirement_details
- _parse_requirement_marker
- _parse_extras
- _parse_extras_list
- _parse_specifier
- _parse_version_many
- parse_marker
- _parse_full_marker
- _parse_marker
- _parse_marker_atom
- _parse_marker_item
- _parse_marker_var
- process_env_var
- process_python_str
- _parse_marker_op

## venv\Lib\site-packages\packaging\_structures.py

### Classes
- InfinityType
- NegativeInfinityType

## venv\Lib\site-packages\packaging\_tokenizer.py

### Classes
- Token
- ParserSyntaxError
- Tokenizer

## venv\Lib\site-packages\packaging\dependency_groups.py

### Classes
- DuplicateGroupNames
- CyclicDependencyGroup
- InvalidDependencyGroupObject
- DependencyGroupInclude
- DependencyGroupResolver

### Functions
- __dir__
- resolve_dependency_groups
- _normalize_name
- _normalize_group_names

## venv\Lib\site-packages\packaging\direct_url.py

### Classes
- _FromMappingProtocol
- DirectUrlValidationError
- _DirectUrlRequiredKeyError
- VcsInfo
- ArchiveInfo
- DirInfo
- DirectUrl

### Functions
- __dir__
- _json_dict_factory
- _get
- _get_required
- _get_object
- _strip_auth_from_netloc
- _strip_url

## venv\Lib\site-packages\packaging\errors.py

### Classes
- _ErrorCollector

### Functions
- __dir__

## venv\Lib\site-packages\packaging\licenses\__init__.py

### Classes
- InvalidLicenseExpression

### Functions
- __dir__
- canonicalize_license_expression

## venv\Lib\site-packages\packaging\licenses\_spdx.py

### Classes
- SPDXLicense
- SPDXException

## venv\Lib\site-packages\packaging\markers.py

### Classes
- InvalidMarker
- UndefinedComparison
- UndefinedEnvironmentName
- Environment
- Marker

### Functions
- __dir__
- _normalize_extras
- _normalize_extra_values
- _format_marker
- _eval_op
- _normalize
- _evaluate_markers
- _format_full_version
- default_environment
- _repair_python_full_version

## venv\Lib\site-packages\packaging\metadata.py

### Classes
- InvalidMetadata
- RawMetadata
- RFC822Policy
- RFC822Message
- _Validator
- Metadata

### Functions
- __dir__
- _parse_keywords
- _parse_project_urls
- _get_payload
- parse_email

## venv\Lib\site-packages\packaging\pylock.py

### Classes
- _FromMappingProtocol
- PylockValidationError
- _PylockRequiredKeyError
- PylockUnsupportedVersionError
- PylockSelectError
- PackageVcs
- PackageDirectory
- PackageArchive
- PackageSdist
- PackageWheel
- Package
- Pylock

### Functions
- __dir__
- is_valid_pylock_path
- _toml_key
- _toml_value
- _toml_dict_factory
- _get
- _get_required
- _get_sequence
- _get_as
- _get_required_as
- _get_sequence_as
- _get_object
- _get_sequence_of_objects
- _get_required_sequence_of_objects
- _validate_normalized_name
- _validate_path_url
- _path_name
- _url_name
- _validate_hashes

## venv\Lib\site-packages\packaging\requirements.py

### Classes
- InvalidRequirement
- Requirement

### Functions
- __dir__

## venv\Lib\site-packages\packaging\specifiers.py

### Classes
- _BoundaryKind
- _BoundaryVersion
- _LowerBound
- _UpperBound
- InvalidSpecifier
- BaseSpecifier
- Specifier
- SpecifierSet

### Functions
- __dir__
- _validate_spec
- _validate_pre
- _trim_release
- _range_is_empty
- _intersect_ranges
- _next_prefix_dev0
- _base_dev0
- _coerce_version
- _public_version
- _post_base
- _earliest_prerelease
- _nearest_non_prerelease
- _pep440_filter_prereleases
- _version_split
- _version_join
- _is_not_suffix
- _numeric_prefix_len
- _left_pad
- _operator_cost

## venv\Lib\site-packages\packaging\tags.py

### Classes
- UnsortedTagsError
- Tag

### Functions
- __dir__
- _compute_32_bit_interpreter
- parse_tag
- _get_config_var
- _normalize_string
- _is_threaded_cpython
- _abi3_applies
- _abi3t_applies
- _cpython_abis
- cpython_tags
- _generic_abi
- generic_tags
- _py_interpreter_range
- compatible_tags
- _mac_arch
- _mac_binary_formats
- mac_platforms
- ios_platforms
- android_platforms
- _linux_platforms
- _emscripten_platforms
- _generic_platforms
- platform_tags
- interpreter_name
- interpreter_version
- _version_nodot
- sys_tags
- create_compatible_tags_selector

## venv\Lib\site-packages\packaging\utils.py

### Classes
- InvalidName
- InvalidWheelFilename
- InvalidSdistFilename

### Functions
- __dir__
- canonicalize_name
- is_normalized_name
- canonicalize_version
- parse_wheel_filename
- parse_sdist_filename

## venv\Lib\site-packages\packaging\version.py

### Classes
- _VersionReplace
- InvalidVersion
- _BaseVersion
- _Version
- Version
- _TrimmedRelease

### Functions
- __dir__
- normalize_pre
- parse
- _validate_epoch
- _validate_release
- _validate_pre
- _validate_post
- _validate_dev
- _validate_local
- _parse_letter_version
- _parse_local_version
- _cmpkey

## venv\Lib\site-packages\pathspec\__init__.py

## venv\Lib\site-packages\pathspec\_backends\__init__.py

## venv\Lib\site-packages\pathspec\_backends\_utils.py

### Functions
- enumerate_patterns

## venv\Lib\site-packages\pathspec\_backends\agg.py

### Functions
- make_gitignore_backend
- make_pathspec_backend

## venv\Lib\site-packages\pathspec\_backends\hyperscan\__init__.py

## venv\Lib\site-packages\pathspec\_backends\hyperscan\_base.py

### Classes
- HyperscanExprDat
- HyperscanExprDebug

## venv\Lib\site-packages\pathspec\_backends\hyperscan\base.py

## venv\Lib\site-packages\pathspec\_backends\hyperscan\gitignore.py

### Classes
- HyperscanGiBackend

## venv\Lib\site-packages\pathspec\_backends\hyperscan\pathspec.py

### Classes
- HyperscanPsBackend

## venv\Lib\site-packages\pathspec\_backends\re2\__init__.py

## venv\Lib\site-packages\pathspec\_backends\re2\_base.py

### Classes
- Re2RegexDat
- Re2RegexDebug

## venv\Lib\site-packages\pathspec\_backends\re2\base.py

## venv\Lib\site-packages\pathspec\_backends\re2\gitignore.py

### Classes
- Re2GiBackend

## venv\Lib\site-packages\pathspec\_backends\re2\pathspec.py

### Classes
- Re2PsBackend

## venv\Lib\site-packages\pathspec\_backends\simple\__init__.py

## venv\Lib\site-packages\pathspec\_backends\simple\gitignore.py

### Classes
- SimpleGiBackend

## venv\Lib\site-packages\pathspec\_backends\simple\pathspec.py

### Classes
- SimplePsBackend

## venv\Lib\site-packages\pathspec\_meta.py

## venv\Lib\site-packages\pathspec\_typing.py

### Functions
- assert_unreachable

## venv\Lib\site-packages\pathspec\_version.py

## venv\Lib\site-packages\pathspec\backend.py

### Classes
- _Backend

## venv\Lib\site-packages\pathspec\gitignore.py

### Classes
- GitIgnoreSpec

## venv\Lib\site-packages\pathspec\pathspec.py

### Classes
- PathSpec

## venv\Lib\site-packages\pathspec\pattern.py

### Classes
- Pattern
- RegexPattern
- RegexMatchResult

## venv\Lib\site-packages\pathspec\patterns\__init__.py

## venv\Lib\site-packages\pathspec\patterns\gitignore\__init__.py

## venv\Lib\site-packages\pathspec\patterns\gitignore\base.py

### Classes
- _GitIgnoreBasePattern
- GitIgnorePatternError
- _RangeError

## venv\Lib\site-packages\pathspec\patterns\gitignore\basic.py

### Classes
- GitIgnoreBasicPattern

## venv\Lib\site-packages\pathspec\patterns\gitignore\spec.py

### Classes
- GitIgnoreSpecPattern

## venv\Lib\site-packages\pathspec\patterns\gitwildmatch.py

### Classes
- GitWildMatchPattern

## venv\Lib\site-packages\pathspec\util.py

### Classes
- AlreadyRegisteredError
- RecursionError
- CheckResult
- MatchDetail
- TreeEntry

### Functions
- append_dir_sep
- check_match_file
- detailed_match_files
- _filter_check_patterns
- _is_iterable
- iter_tree
- iter_tree_entries
- _iter_tree_entries_next
- iter_tree_files
- _iter_tree_files_next
- lookup_pattern
- match_file
- match_files
- normalize_file
- normalize_files
- register_pattern

## venv\Lib\site-packages\pip\__init__.py

### Functions
- main

## venv\Lib\site-packages\pip\__main__.py

## venv\Lib\site-packages\pip\__pip-runner__.py

### Classes
- PipImportRedirectingFinder

### Functions
- version_str

## venv\Lib\site-packages\pip\_internal\__init__.py

### Functions
- main

## venv\Lib\site-packages\pip\_internal\build_env.py

### Classes
- _Prefix
- BuildEnvironmentInstaller
- SubprocessBuildEnvironmentInstaller
- InprocessBuildEnvironmentInstaller
- BuildEnvironment
- NoOpBuildEnvironment

### Functions
- _dedup
- get_runnable_pip
- _get_system_sitepackages

## venv\Lib\site-packages\pip\_internal\cache.py

### Classes
- Cache
- SimpleWheelCache
- EphemWheelCache
- CacheEntry
- WheelCache

### Functions
- _hash_dict

## venv\Lib\site-packages\pip\_internal\cli\__init__.py

## venv\Lib\site-packages\pip\_internal\cli\autocompletion.py

### Functions
- autocomplete
- get_path_completion_type
- auto_complete_paths

## venv\Lib\site-packages\pip\_internal\cli\base_command.py

### Classes
- Command

## venv\Lib\site-packages\pip\_internal\cli\cmdoptions.py

### Classes
- PipOption

### Functions
- raise_option_error
- make_option_group
- check_dist_restriction
- check_build_constraints
- _path_option_check
- _package_name_option_check
- exists_action
- extra_index_url
- find_links
- _handle_uploaded_prior_to
- uploaded_prior_to
- trusted_host
- constraints
- build_constraints
- requirements
- requirements_from_scripts
- editable
- _handle_src
- _get_format_control
- _handle_no_binary
- _handle_only_binary
- no_binary
- only_binary
- _get_release_control
- _handle_all_releases
- _handle_only_final
- all_releases
- only_final
- check_release_control_exclusive
- _convert_python_version
- _handle_python_version
- add_target_python_options
- make_target_python
- prefer_binary
- _handle_no_cache_dir
- _handle_dependency_group
- _handle_config_settings
- _handle_merge_hash
- check_list_path_option

## venv\Lib\site-packages\pip\_internal\cli\command_context.py

### Classes
- CommandContextMixIn

## venv\Lib\site-packages\pip\_internal\cli\index_command.py

### Classes
- SessionCommandMixin
- IndexGroupCommand

### Functions
- _create_truststore_ssl_context
- _pip_self_version_check_fetch
- _pip_self_version_check_emit

## venv\Lib\site-packages\pip\_internal\cli\main.py

### Functions
- main

## venv\Lib\site-packages\pip\_internal\cli\main_parser.py

### Functions
- create_main_parser
- identify_python_interpreter
- parse_command

## venv\Lib\site-packages\pip\_internal\cli\parser.py

### Classes
- PrettyHelpFormatter
- UpdatingDefaultsHelpFormatter
- CustomOptionParser
- ConfigOptionParser

## venv\Lib\site-packages\pip\_internal\cli\progress_bars.py

### Functions
- _rich_download_progress_bar
- _rich_install_progress_bar
- _raw_progress_bar
- get_download_progress_renderer
- get_install_progress_renderer

## venv\Lib\site-packages\pip\_internal\cli\req_command.py

### Classes
- RequirementCommand

### Functions
- should_ignore_regular_constraints
- with_cleanup
- parse_constraint_files

## venv\Lib\site-packages\pip\_internal\cli\spinners.py

### Classes
- SpinnerInterface
- InteractiveSpinner
- NonInteractiveSpinner
- RateLimiter
- _PipRichSpinner

### Functions
- open_spinner
- open_rich_spinner
- hidden_cursor

## venv\Lib\site-packages\pip\_internal\cli\status_codes.py

## venv\Lib\site-packages\pip\_internal\commands\__init__.py

### Functions
- create_command
- get_similar_commands

## venv\Lib\site-packages\pip\_internal\commands\cache.py

### Classes
- CacheCommand

## venv\Lib\site-packages\pip\_internal\commands\check.py

### Classes
- CheckCommand

## venv\Lib\site-packages\pip\_internal\commands\completion.py

### Classes
- CompletionCommand

## venv\Lib\site-packages\pip\_internal\commands\configuration.py

### Classes
- ConfigurationCommand

## venv\Lib\site-packages\pip\_internal\commands\debug.py

### Classes
- DebugCommand

### Functions
- show_value
- show_sys_implementation
- create_vendor_txt_map
- get_module_from_module_name
- get_vendor_version_from_module
- show_actual_vendor_versions
- show_vendor_versions
- show_tags
- ca_bundle_info

## venv\Lib\site-packages\pip\_internal\commands\download.py

### Classes
- DownloadCommand

## venv\Lib\site-packages\pip\_internal\commands\freeze.py

### Classes
- FreezeCommand

### Functions
- _should_suppress_build_backends
- _dev_pkgs

## venv\Lib\site-packages\pip\_internal\commands\hash.py

### Classes
- HashCommand

### Functions
- _hash_of_file

## venv\Lib\site-packages\pip\_internal\commands\help.py

### Classes
- HelpCommand

## venv\Lib\site-packages\pip\_internal\commands\index.py

### Classes
- IndexCommand

## venv\Lib\site-packages\pip\_internal\commands\inspect.py

### Classes
- InspectCommand

## venv\Lib\site-packages\pip\_internal\commands\install.py

### Classes
- InstallCommand

### Functions
- _prevent_import_hook
- _eagerly_import_modules
- _prevent_further_imports
- _arg_refers_to_pip
- installed_packages_summary
- get_lib_location_guesses
- site_packages_writable
- decide_user_install
- create_os_error_message

## venv\Lib\site-packages\pip\_internal\commands\list.py

### Classes
- ListCommand

### Functions
- format_for_columns
- format_for_json

## venv\Lib\site-packages\pip\_internal\commands\lock.py

### Classes
- LockCommand

## venv\Lib\site-packages\pip\_internal\commands\search.py

### Classes
- TransformedHit
- SearchCommand

### Functions
- transform_hits
- print_dist_installation_info
- get_installed_distribution
- print_results
- highest_version

## venv\Lib\site-packages\pip\_internal\commands\show.py

### Classes
- ShowCommand
- _PackageInfo

### Functions
- normalize_project_url_label
- search_packages_info
- print_results

## venv\Lib\site-packages\pip\_internal\commands\uninstall.py

### Classes
- UninstallCommand

## venv\Lib\site-packages\pip\_internal\commands\wheel.py

### Classes
- WheelCommand

## venv\Lib\site-packages\pip\_internal\configuration.py

### Classes
- Configuration

### Functions
- _normalize_name
- _disassemble_key
- get_configuration_files

## venv\Lib\site-packages\pip\_internal\distributions\__init__.py

### Functions
- make_distribution_for_install_requirement

## venv\Lib\site-packages\pip\_internal\distributions\base.py

### Classes
- AbstractDistribution

## venv\Lib\site-packages\pip\_internal\distributions\installed.py

### Classes
- InstalledDistribution

## venv\Lib\site-packages\pip\_internal\distributions\sdist.py

### Classes
- SourceDistribution

## venv\Lib\site-packages\pip\_internal\distributions\wheel.py

### Classes
- WheelDistribution

## venv\Lib\site-packages\pip\_internal\exceptions.py

### Classes
- PipError
- DiagnosticPipError
- ConfigurationError
- InstallationError
- FailedToPrepareCandidate
- MissingPyProjectBuildRequires
- InvalidPyProjectBuildRequires
- NoneMetadataError
- UserInstallationInvalid
- InvalidSchemeCombination
- DistributionNotFound
- RequirementsFileParseError
- BestVersionAlreadyInstalled
- BadCommand
- CommandError
- PreviousBuildDirError
- NetworkConnectionError
- InvalidWheelFilename
- UnsupportedWheel
- InvalidWheel
- MetadataInconsistent
- MetadataInvalid
- InstallationSubprocessError
- MetadataGenerationFailed
- HashErrors
- HashError
- VcsHashUnsupported
- DirectoryUrlHashUnsupported
- HashMissing
- HashUnpinned
- HashMismatch
- UnsupportedPythonVersion
- ConfigurationFileCouldNotBeLoaded
- ExternallyManagedEnvironment
- UninstallMissingRecord
- LegacyDistutilsInstall
- InvalidInstalledPackage
- IncompleteDownloadError
- ResolutionTooDeepError
- InstallWheelBuildError
- InvalidEggFragment
- BuildDependencyInstallError

### Functions
- _is_kebab_case
- _prefix_with_indent

## venv\Lib\site-packages\pip\_internal\index\__init__.py

## venv\Lib\site-packages\pip\_internal\index\collector.py

### Classes
- _NotAPIContent
- _NotHTTP
- CacheablePageContent
- ParseLinks
- IndexContent
- HTMLLinkParser
- CollectedSources
- LinkCollector

### Functions
- _match_vcs_scheme
- _ensure_api_header
- _ensure_api_response
- _get_simple_response
- _get_encoding_from_headers
- with_cached_index_content
- parse_links
- _handle_get_simple_fail
- _make_index_content
- _get_index_content

## venv\Lib\site-packages\pip\_internal\index\package_finder.py

### Classes
- LinkType
- LinkEvaluator
- CandidatePreferences
- BestCandidateResult
- CandidateEvaluator
- PackageFinder

### Functions
- _check_link_requires_python
- filter_unallowed_hashes
- _find_name_version_sep
- _extract_version_from_fragment

## venv\Lib\site-packages\pip\_internal\index\sources.py

### Classes
- LinkSource
- _FlatDirectoryToUrls
- _FlatDirectorySource
- _LocalFileSource
- _RemoteFileSource
- _IndexDirectorySource

### Functions
- _is_html_file
- build_source

## venv\Lib\site-packages\pip\_internal\locations\__init__.py

### Functions
- _should_use_sysconfig
- _looks_like_bpo_44860
- _looks_like_red_hat_patched_platlib_purelib
- _looks_like_red_hat_lib
- _looks_like_debian_scheme
- _looks_like_red_hat_scheme
- _looks_like_slackware_scheme
- _looks_like_msys2_mingw_scheme
- _warn_mismatched
- _warn_if_mismatch
- _log_context
- get_scheme
- get_bin_prefix
- get_bin_user
- _looks_like_deb_system_dist_packages
- get_purelib
- get_platlib

## venv\Lib\site-packages\pip\_internal\locations\_distutils.py

### Functions
- distutils_scheme
- get_scheme
- get_bin_prefix
- get_purelib
- get_platlib

## venv\Lib\site-packages\pip\_internal\locations\_sysconfig.py

### Functions
- _should_use_osx_framework_prefix
- _infer_prefix
- _infer_user
- _infer_home
- get_scheme
- get_bin_prefix
- get_purelib
- get_platlib

## venv\Lib\site-packages\pip\_internal\locations\base.py

### Functions
- get_major_minor_version
- change_root
- get_src_prefix
- is_osx_framework

## venv\Lib\site-packages\pip\_internal\main.py

### Functions
- main

## venv\Lib\site-packages\pip\_internal\metadata\__init__.py

### Classes
- Backend

### Functions
- _should_use_importlib_metadata
- _emit_pkg_resources_deprecation_if_needed
- select_backend
- get_default_environment
- get_environment
- get_directory_distribution
- get_wheel_distribution
- get_metadata_distribution

## venv\Lib\site-packages\pip\_internal\metadata\_json.py

### Functions
- json_name
- msg_to_json

## venv\Lib\site-packages\pip\_internal\metadata\base.py

### Classes
- BaseEntryPoint
- RequiresEntry
- BaseDistribution
- BaseEnvironment
- Wheel
- FilesystemWheel
- MemoryWheel

### Functions
- _convert_installed_files_path

## venv\Lib\site-packages\pip\_internal\metadata\importlib\__init__.py

## venv\Lib\site-packages\pip\_internal\metadata\importlib\_compat.py

### Classes
- BadMetadata
- BasePath

### Functions
- get_info_location
- parse_name_and_version_from_info_directory
- get_dist_canonical_name

## venv\Lib\site-packages\pip\_internal\metadata\importlib\_dists.py

### Classes
- WheelDistribution
- Distribution

## venv\Lib\site-packages\pip\_internal\metadata\importlib\_envs.py

### Classes
- _DistributionFinder
- Environment

### Functions
- _looks_like_wheel

## venv\Lib\site-packages\pip\_internal\metadata\pkg_resources.py

### Classes
- EntryPoint
- InMemoryMetadata
- Distribution
- Environment

## venv\Lib\site-packages\pip\_internal\models\__init__.py

## venv\Lib\site-packages\pip\_internal\models\candidate.py

### Classes
- InstallationCandidate

## venv\Lib\site-packages\pip\_internal\models\direct_url.py

### Classes
- DirectUrl

## venv\Lib\site-packages\pip\_internal\models\format_control.py

### Classes
- FormatControl

## venv\Lib\site-packages\pip\_internal\models\index.py

### Classes
- PackageIndex

## venv\Lib\site-packages\pip\_internal\models\installation_report.py

### Classes
- InstallationReport

## venv\Lib\site-packages\pip\_internal\models\link.py

### Classes
- LinkHash
- MetadataFile
- Link
- _CleanResult

### Functions
- supported_hashes
- _clean_url_path_part
- _clean_file_url_path
- _clean_url_path
- _ensure_quoted_url
- _absolute_link_url
- _clean_link
- links_equivalent

## venv\Lib\site-packages\pip\_internal\models\release_control.py

### Classes
- ReleaseControl

## venv\Lib\site-packages\pip\_internal\models\scheme.py

### Classes
- Scheme

## venv\Lib\site-packages\pip\_internal\models\search_scope.py

### Classes
- SearchScope

## venv\Lib\site-packages\pip\_internal\models\selection_prefs.py

### Classes
- SelectionPreferences

## venv\Lib\site-packages\pip\_internal\models\target_python.py

### Classes
- TargetPython

## venv\Lib\site-packages\pip\_internal\models\wheel.py

### Classes
- Wheel

## venv\Lib\site-packages\pip\_internal\network\__init__.py

## venv\Lib\site-packages\pip\_internal\network\auth.py

### Classes
- Credentials
- KeyRingBaseProvider
- KeyRingNullProvider
- KeyRingPythonProvider
- KeyRingCliProvider
- MultiDomainBasicAuth

### Functions
- get_keyring_provider

## venv\Lib\site-packages\pip\_internal\network\cache.py

### Classes
- SafeFileCache

### Functions
- is_from_cache
- suppressed_cache_errors

## venv\Lib\site-packages\pip\_internal\network\download.py

### Classes
- _FileDownload
- Downloader

### Functions
- _get_http_response_size
- _get_http_response_etag_or_last_modified
- _log_download
- sanitize_content_filename
- parse_content_disposition
- _get_http_response_filename

## venv\Lib\site-packages\pip\_internal\network\lazy_wheel.py

### Classes
- HTTPRangeRequestUnsupported
- LazyZipOverHTTP

### Functions
- dist_from_wheel_url

## venv\Lib\site-packages\pip\_internal\network\session.py

### Classes
- LocalFSAdapter
- _SSLContextAdapterMixin
- HTTPAdapter
- CacheControlAdapter
- InsecureHTTPAdapter
- InsecureCacheControlAdapter
- PipSession

### Functions
- looks_like_ci
- user_agent

## venv\Lib\site-packages\pip\_internal\network\utils.py

### Functions
- raise_for_status
- response_chunks

## venv\Lib\site-packages\pip\_internal\network\xmlrpc.py

### Classes
- PipXmlrpcTransport

## venv\Lib\site-packages\pip\_internal\operations\__init__.py

## venv\Lib\site-packages\pip\_internal\operations\build\__init__.py

## venv\Lib\site-packages\pip\_internal\operations\build\build_tracker.py

### Classes
- TrackerId
- BuildTracker

### Functions
- update_env_context_manager
- get_build_tracker

## venv\Lib\site-packages\pip\_internal\operations\build\metadata.py

### Functions
- generate_metadata

## venv\Lib\site-packages\pip\_internal\operations\build\metadata_editable.py

### Functions
- generate_editable_metadata

## venv\Lib\site-packages\pip\_internal\operations\build\wheel.py

### Functions
- build_wheel_pep517

## venv\Lib\site-packages\pip\_internal\operations\build\wheel_editable.py

### Functions
- build_wheel_editable

## venv\Lib\site-packages\pip\_internal\operations\check.py

### Classes
- PackageDetails

### Functions
- create_package_set_from_installed
- check_package_set
- check_install_conflicts
- check_unsupported
- _simulate_installation_of
- _create_whitelist

## venv\Lib\site-packages\pip\_internal\operations\freeze.py

### Classes
- _EditableInfo
- FrozenRequirement

### Functions
- freeze
- _format_as_name_version
- _get_editable_info

## venv\Lib\site-packages\pip\_internal\operations\install\__init__.py

## venv\Lib\site-packages\pip\_internal\operations\install\wheel.py

### Classes
- File
- ZipBackedFile
- ScriptFile
- MissingCallableSuffix
- PipScriptMaker

### Functions
- rehash
- csv_io_kwargs
- fix_script
- wheel_root_is_purelib
- get_entrypoints
- message_about_scripts_not_on_PATH
- _normalized_outrows
- _record_to_fs_path
- _fs_to_record_path
- get_csv_rows_for_installed
- get_console_script_specs
- _raise_for_invalid_entrypoint
- _install_wheel
- req_error_context
- install_wheel

## venv\Lib\site-packages\pip\_internal\operations\prepare.py

### Classes
- File
- RequirementPreparer

### Functions
- _get_prepared_distribution
- unpack_vcs_link
- get_http_url
- get_file_url
- unpack_url
- _check_download_dir

## venv\Lib\site-packages\pip\_internal\pyproject.py

### Functions
- _is_list_of_str
- make_pyproject_path
- load_pyproject_toml

## venv\Lib\site-packages\pip\_internal\req\__init__.py

### Classes
- InstallationResult

### Functions
- _validate_requirements
- install_given_reqs

## venv\Lib\site-packages\pip\_internal\req\constructors.py

### Classes
- RequirementParts

### Functions
- _strip_extras
- convert_extras
- _set_requirement_extras
- _parse_direct_url_editable
- _parse_pip_syntax_editable
- parse_editable
- check_first_requirement_in_file
- deduce_helpful_msg
- parse_req_from_editable
- install_req_from_editable
- _looks_like_path
- _get_url_from_path
- parse_req_from_line
- install_req_from_line
- install_req_from_req_string
- install_req_from_parsed_requirement
- install_req_from_link_and_ireq
- install_req_drop_extras
- install_req_extend_extras
- _pylock_hashes_to_hash_options
- install_req_from_pylock_package

## venv\Lib\site-packages\pip\_internal\req\pep723.py

### Classes
- PEP723Exception

### Functions
- pep723_metadata

## venv\Lib\site-packages\pip\_internal\req\req_dependency_group.py

### Functions
- parse_dependency_groups
- _resolve_all_groups
- _build_resolvers
- _load_pyproject

## venv\Lib\site-packages\pip\_internal\req\req_file.py

### Classes
- ParsedRequirement
- ParsedLine
- RequirementsFileParser
- OptionParsingError

### Functions
- parse_requirements
- preprocess
- handle_requirement_line
- handle_option_line
- handle_line
- get_line_parser
- break_args_options
- build_parser
- join_lines
- ignore_comments
- expand_env_variables
- get_file_content
- _decode_req_file

## venv\Lib\site-packages\pip\_internal\req\req_install.py

### Classes
- InstallRequirement

### Functions
- check_invalid_constraint_type
- _has_option

## venv\Lib\site-packages\pip\_internal\req\req_set.py

### Classes
- RequirementSet

## venv\Lib\site-packages\pip\_internal\req\req_uninstall.py

### Classes
- StashedUninstallPathSet
- UninstallPathSet
- UninstallPthEntries

### Functions
- _script_names
- _unique
- uninstallation_paths
- compact
- compress_for_rename
- compress_for_output_listing

## venv\Lib\site-packages\pip\_internal\resolution\__init__.py

## venv\Lib\site-packages\pip\_internal\resolution\base.py

### Classes
- BaseResolver

## venv\Lib\site-packages\pip\_internal\resolution\legacy\__init__.py

## venv\Lib\site-packages\pip\_internal\resolution\legacy\resolver.py

### Classes
- Resolver

### Functions
- _check_dist_requires_python

## venv\Lib\site-packages\pip\_internal\resolution\resolvelib\__init__.py

## venv\Lib\site-packages\pip\_internal\resolution\resolvelib\base.py

### Classes
- Constraint
- Requirement
- Candidate

### Functions
- format_name
- _match_link

## venv\Lib\site-packages\pip\_internal\resolution\resolvelib\candidates.py

### Classes
- _InstallRequirementBackedCandidate
- LinkCandidate
- EditableCandidate
- AlreadyInstalledCandidate
- ExtrasCandidate
- RequiresPythonCandidate

### Functions
- as_base_candidate
- make_install_req_from_link
- make_install_req_from_editable
- _make_install_req_from_dist

## venv\Lib\site-packages\pip\_internal\resolution\resolvelib\factory.py

### Classes
- CollectedRootRequirements
- Factory

## venv\Lib\site-packages\pip\_internal\resolution\resolvelib\found_candidates.py

### Classes
- FoundCandidates

### Functions
- _iter_built
- _iter_built_with_prepended
- _iter_built_with_inserted

## venv\Lib\site-packages\pip\_internal\resolution\resolvelib\provider.py

### Classes
- PipProvider

### Functions
- _get_with_identifier

## venv\Lib\site-packages\pip\_internal\resolution\resolvelib\reporter.py

### Classes
- PipReporter
- PipDebuggingReporter

## venv\Lib\site-packages\pip\_internal\resolution\resolvelib\requirements.py

### Classes
- ExplicitRequirement
- SpecifierRequirement
- SpecifierWithoutExtrasRequirement
- RequiresPythonRequirement
- UnsatisfiableRequirement

## venv\Lib\site-packages\pip\_internal\resolution\resolvelib\resolver.py

### Classes
- Resolver

### Functions
- get_topological_weights
- _req_set_item_sorter

## venv\Lib\site-packages\pip\_internal\self_outdated_check.py

### Classes
- SelfCheckState
- UpgradePrompt

### Functions
- _get_statefile_name
- _get_current_remote_pip_version
- _compute_upgrade_prompt
- pip_self_version_check_fetch
- pip_self_version_check_emit

## venv\Lib\site-packages\pip\_internal\utils\__init__.py

## venv\Lib\site-packages\pip\_internal\utils\_jaraco_text.py

### Functions
- _nonblank
- yield_lines
- _
- drop_comment
- join_continuation

## venv\Lib\site-packages\pip\_internal\utils\_log.py

### Classes
- VerboseLogger

### Functions
- getLogger
- init_logging

## venv\Lib\site-packages\pip\_internal\utils\appdirs.py

### Functions
- user_cache_dir
- _macos_user_config_dir
- user_config_dir
- site_config_dirs

## venv\Lib\site-packages\pip\_internal\utils\compat.py

### Functions
- has_tls
- get_path_uid

## venv\Lib\site-packages\pip\_internal\utils\compatibility_tags.py

### Functions
- version_info_to_nodot
- _mac_platforms
- _ios_platforms
- _android_platforms
- _custom_manylinux_platforms
- _get_custom_platforms
- _expand_allowed_platforms
- _get_python_version
- _get_custom_interpreter
- get_supported

## venv\Lib\site-packages\pip\_internal\utils\datetime.py

### Functions
- today_is_later_than
- parse_iso_datetime

## venv\Lib\site-packages\pip\_internal\utils\deprecation.py

### Classes
- PipDeprecationWarning

### Functions
- _showwarning
- install_warning_logger
- deprecated

## venv\Lib\site-packages\pip\_internal\utils\direct_url_helpers.py

### Functions
- direct_url_as_pep440_direct_reference
- direct_url_for_editable
- direct_url_from_link

## venv\Lib\site-packages\pip\_internal\utils\egg_link.py

### Functions
- _egg_link_names
- egg_link_path_from_sys_path
- egg_link_path_from_location

## venv\Lib\site-packages\pip\_internal\utils\entrypoints.py

### Functions
- _wrapper
- get_best_invocation_for_this_pip
- get_best_invocation_for_this_python

## venv\Lib\site-packages\pip\_internal\utils\filesystem.py

### Functions
- check_path_owner
- adjacent_tmp_file
- test_writable_dir
- _test_writable_dir_win
- find_files
- file_size
- format_file_size
- directory_size
- format_directory_size
- copy_directory_permissions
- _subdirs_without_generic
- subdirs_without_files
- subdirs_without_wheels

## venv\Lib\site-packages\pip\_internal\utils\filetypes.py

### Functions
- is_archive_file

## venv\Lib\site-packages\pip\_internal\utils\glibc.py

### Functions
- glibc_version_string
- glibc_version_string_confstr
- glibc_version_string_ctypes
- libc_ver

## venv\Lib\site-packages\pip\_internal\utils\hashes.py

### Classes
- Hashes
- MissingHashes

## venv\Lib\site-packages\pip\_internal\utils\logging.py

### Classes
- BrokenStdoutLoggingError
- IndentingFormatter
- IndentedRenderable
- PipConsole
- RichPipStreamHandler
- BetterRotatingFileHandler
- MaxLevelFilter
- ExcludeLoggerFilter

### Functions
- _is_broken_pipe_error
- capture_logging
- indent_log
- get_indentation
- get_console
- setup_logging

## venv\Lib\site-packages\pip\_internal\utils\misc.py

### Classes
- StreamWrapper
- HiddenText
- ConfiguredBuildBackendHookCaller

### Functions
- get_pip_version
- normalize_version_info
- ensure_dir
- get_prog
- rmtree
- _onerror_ignore
- _onerror_reraise
- rmtree_errorhandler
- display_path
- backup_dir
- ask_path_exists
- _check_no_input
- ask
- ask_input
- ask_password
- strtobool
- format_size
- tabulate
- is_installable_dir
- read_chunks
- normalize_path
- splitext
- renames
- is_local
- write_output
- enum
- build_netloc
- build_url_from_netloc
- parse_netloc
- split_auth_from_netloc
- redact_netloc
- _transform_url
- _get_netloc
- _redact_netloc
- split_auth_netloc_from_url
- remove_auth_from_url
- redact_auth_from_url
- redact_auth_from_requirement
- hide_value
- hide_url
- protect_pip_from_modification_on_windows
- check_externally_managed
- is_console_interactive
- hash_file
- pairwise
- partition
- warn_if_run_as_root

## venv\Lib\site-packages\pip\_internal\utils\packaging.py

### Functions
- check_requires_python
- get_requirement

## venv\Lib\site-packages\pip\_internal\utils\pylock.py

### Functions
- _pylock_package_from_install_requirement
- pylock_from_install_requirements
- _is_url
- is_valid_pylock_filename
- _package_dist_url
- package_vcs_requirement_url
- package_archive_requirement_url
- package_directory_requirement_url
- package_sdist_requirement_url
- package_wheel_requirement_url
- _get_pylock_path_or_url_content
- select_from_pylock_path_or_url

## venv\Lib\site-packages\pip\_internal\utils\retry.py

### Functions
- retry

## venv\Lib\site-packages\pip\_internal\utils\subprocess.py

### Functions
- make_command
- format_command_args
- reveal_command_args
- call_subprocess
- runner_with_spinner_message

## venv\Lib\site-packages\pip\_internal\utils\temp_dir.py

### Classes
- TempDirectoryTypeRegistry
- _Default
- TempDirectory
- AdjacentTempDirectory

### Functions
- global_tempdir_manager
- tempdir_registry

## venv\Lib\site-packages\pip\_internal\utils\unpacking.py

### Functions
- current_umask
- split_leading_dir
- has_leading_dir
- is_within_directory
- _get_default_mode_plus_executable
- set_extracted_file_to_default_mode_plus_executable
- zip_item_is_executable
- unzip_file
- untar_file
- is_symlink_target_in_tar
- _untar_without_filter
- unpack_file

## venv\Lib\site-packages\pip\_internal\utils\urls.py

### Functions
- path_to_url
- url_to_path

## venv\Lib\site-packages\pip\_internal\utils\virtualenv.py

### Functions
- _running_under_venv
- _running_under_legacy_virtualenv
- running_under_virtualenv
- _get_pyvenv_cfg_lines
- _no_global_under_venv
- _no_global_under_legacy_virtualenv
- virtualenv_no_global

## venv\Lib\site-packages\pip\_internal\utils\wheel.py

### Functions
- parse_wheel
- wheel_dist_info_dir
- read_wheel_metadata_file
- wheel_metadata
- wheel_version
- check_compatibility

## venv\Lib\site-packages\pip\_internal\vcs\__init__.py

## venv\Lib\site-packages\pip\_internal\vcs\bazaar.py

### Classes
- Bazaar

## venv\Lib\site-packages\pip\_internal\vcs\git.py

### Classes
- Git

### Functions
- looks_like_hash

## venv\Lib\site-packages\pip\_internal\vcs\mercurial.py

### Classes
- Mercurial

## venv\Lib\site-packages\pip\_internal\vcs\subversion.py

### Classes
- Subversion

## venv\Lib\site-packages\pip\_internal\vcs\versioncontrol.py

### Classes
- RemoteNotFoundError
- RemoteNotValidError
- RevOptions
- VcsSupport
- VersionControl

### Functions
- is_url
- make_vcs_requirement_url
- find_path_to_project_root_from_repo_root

## venv\Lib\site-packages\pip\_internal\wheel_builder.py

### Functions
- _contains_egg_info
- _should_cache
- _get_cache_dir
- _verify_one
- _build_one
- _build_one_inside_env
- build

## venv\Lib\site-packages\pip\_vendor\__init__.py

### Functions
- vendored

## venv\Lib\site-packages\pip\_vendor\cachecontrol\__init__.py

## venv\Lib\site-packages\pip\_vendor\cachecontrol\_cmd.py

### Functions
- setup_logging
- get_session
- get_args
- main

## venv\Lib\site-packages\pip\_vendor\cachecontrol\adapter.py

### Classes
- CacheControlAdapter

## venv\Lib\site-packages\pip\_vendor\cachecontrol\cache.py

### Classes
- BaseCache
- DictCache
- SeparateBodyBaseCache

## venv\Lib\site-packages\pip\_vendor\cachecontrol\caches\__init__.py

## venv\Lib\site-packages\pip\_vendor\cachecontrol\caches\file_cache.py

### Classes
- _FileCacheMixin
- FileCache
- SeparateBodyFileCache

### Functions
- url_to_file_path

## venv\Lib\site-packages\pip\_vendor\cachecontrol\caches\redis_cache.py

### Classes
- RedisCache

## venv\Lib\site-packages\pip\_vendor\cachecontrol\controller.py

### Classes
- CacheController

### Functions
- parse_uri

## venv\Lib\site-packages\pip\_vendor\cachecontrol\filewrapper.py

### Classes
- CallbackFileWrapper

## venv\Lib\site-packages\pip\_vendor\cachecontrol\heuristics.py

### Classes
- BaseHeuristic
- OneDayCache
- ExpiresAfter
- LastModified

### Functions
- expire_after
- datetime_to_header

## venv\Lib\site-packages\pip\_vendor\cachecontrol\serialize.py

### Classes
- Serializer

## venv\Lib\site-packages\pip\_vendor\cachecontrol\wrapper.py

### Functions
- CacheControl

## venv\Lib\site-packages\pip\_vendor\certifi\__init__.py

## venv\Lib\site-packages\pip\_vendor\certifi\__main__.py

## venv\Lib\site-packages\pip\_vendor\certifi\core.py

### Functions
- exit_cacert_ctx

## venv\Lib\site-packages\pip\_vendor\distlib\__init__.py

### Classes
- DistlibException

## venv\Lib\site-packages\pip\_vendor\distlib\compat.py

## venv\Lib\site-packages\pip\_vendor\distlib\resources.py

### Classes
- ResourceCache
- ResourceBase
- Resource
- ResourceContainer
- ResourceFinder
- ZipResourceFinder

### Functions
- register_finder
- finder
- finder_for_path

## venv\Lib\site-packages\pip\_vendor\distlib\scripts.py

### Classes
- ScriptMaker

### Functions
- enquote_executable

## venv\Lib\site-packages\pip\_vendor\distlib\util.py

### Classes
- cached_property
- FileOperator
- ExportEntry
- Cache
- EventMixin
- Sequencer
- Progress
- Transport
- ServerProxy
- CSVBase
- CSVReader
- CSVWriter
- Configurator
- SubprocessMixin
- PyPIRCFile

### Functions
- parse_marker
- parse_requirement
- get_resources_dests
- in_venv
- get_executable
- proceed
- extract_by_key
- read_exports
- write_exports
- tempdir
- chdir
- socket_timeout
- convert_path
- resolve
- get_export_entry
- get_cache_base
- path_to_cache_dir
- ensure_slash
- parse_credentials
- get_process_umask
- is_string_sequence
- split_filename
- parse_name_and_version
- get_extras
- _get_external_data
- get_project_data
- get_package_data
- unarchive
- zip_dir
- iglob
- _iglob
- _csv_open
- normalize_name
- _load_pypirc
- _store_pypirc
- get_host_platform
- get_platform

## venv\Lib\site-packages\pip\_vendor\distro\__init__.py

## venv\Lib\site-packages\pip\_vendor\distro\__main__.py

## venv\Lib\site-packages\pip\_vendor\distro\distro.py

### Classes
- VersionDict
- InfoDict
- LinuxDistribution

### Functions
- linux_distribution
- id
- name
- version
- version_parts
- major_version
- minor_version
- build_number
- like
- codename
- info
- os_release_info
- lsb_release_info
- distro_release_info
- uname_info
- os_release_attr
- lsb_release_attr
- distro_release_attr
- uname_attr
- main

## venv\Lib\site-packages\pip\_vendor\idna\__init__.py

## venv\Lib\site-packages\pip\_vendor\idna\codec.py

### Classes
- Codec
- IncrementalEncoder
- IncrementalDecoder
- StreamWriter
- StreamReader

### Functions
- search_function

## venv\Lib\site-packages\pip\_vendor\idna\compat.py

### Functions
- ToASCII
- ToUnicode
- nameprep

## venv\Lib\site-packages\pip\_vendor\idna\core.py

### Classes
- IDNAError
- IDNABidiError
- InvalidCodepoint
- InvalidCodepointContext

### Functions
- _combining_class
- _is_script
- _punycode
- _unot
- valid_label_length
- valid_string_length
- check_bidi
- check_initial_combiner
- check_hyphen_ok
- check_nfc
- valid_contextj
- valid_contexto
- check_label
- alabel
- ulabel
- uts46_remap
- encode
- decode

## venv\Lib\site-packages\pip\_vendor\idna\idnadata.py

## venv\Lib\site-packages\pip\_vendor\idna\intranges.py

### Functions
- intranges_from_list
- _encode_range
- _decode_range
- intranges_contain

## venv\Lib\site-packages\pip\_vendor\idna\package_data.py

## venv\Lib\site-packages\pip\_vendor\idna\uts46data.py

### Functions
- _seg_0
- _seg_1
- _seg_2
- _seg_3
- _seg_4
- _seg_5
- _seg_6
- _seg_7
- _seg_8
- _seg_9
- _seg_10
- _seg_11
- _seg_12
- _seg_13
- _seg_14
- _seg_15
- _seg_16
- _seg_17
- _seg_18
- _seg_19
- _seg_20
- _seg_21
- _seg_22
- _seg_23
- _seg_24
- _seg_25
- _seg_26
- _seg_27
- _seg_28
- _seg_29
- _seg_30
- _seg_31
- _seg_32
- _seg_33
- _seg_34
- _seg_35
- _seg_36
- _seg_37
- _seg_38
- _seg_39
- _seg_40
- _seg_41
- _seg_42
- _seg_43
- _seg_44
- _seg_45
- _seg_46
- _seg_47
- _seg_48
- _seg_49
- _seg_50
- _seg_51
- _seg_52
- _seg_53
- _seg_54
- _seg_55
- _seg_56
- _seg_57
- _seg_58
- _seg_59
- _seg_60
- _seg_61
- _seg_62
- _seg_63
- _seg_64
- _seg_65
- _seg_66
- _seg_67
- _seg_68
- _seg_69
- _seg_70
- _seg_71
- _seg_72
- _seg_73
- _seg_74
- _seg_75
- _seg_76
- _seg_77
- _seg_78
- _seg_79
- _seg_80
- _seg_81
- _seg_82
- _seg_83

## venv\Lib\site-packages\pip\_vendor\msgpack\__init__.py

### Functions
- pack
- packb
- unpack

## venv\Lib\site-packages\pip\_vendor\msgpack\exceptions.py

### Classes
- UnpackException
- BufferFull
- OutOfData
- FormatError
- StackError
- ExtraData

## venv\Lib\site-packages\pip\_vendor\msgpack\ext.py

### Classes
- ExtType
- Timestamp

## venv\Lib\site-packages\pip\_vendor\msgpack\fallback.py

### Classes
- Unpacker
- Packer

### Functions
- _check_type_strict
- _get_data_from_buffer
- unpackb

## venv\Lib\site-packages\pip\_vendor\packaging\__init__.py

## venv\Lib\site-packages\pip\_vendor\packaging\_elffile.py

### Classes
- ELFInvalid
- EIClass
- EIData
- EMachine
- ELFFile

## venv\Lib\site-packages\pip\_vendor\packaging\_manylinux.py

### Classes
- _GLibCVersion

### Functions
- _parse_elf
- _is_linux_armhf
- _is_linux_i686
- _have_compatible_abi
- _glibc_version_string_confstr
- _glibc_version_string_ctypes
- _glibc_version_string
- _parse_glibc_version
- _get_glibc_version
- _is_compatible
- platform_tags

## venv\Lib\site-packages\pip\_vendor\packaging\_musllinux.py

### Classes
- _MuslVersion

### Functions
- _parse_musl_version
- _get_musl_version
- platform_tags

## venv\Lib\site-packages\pip\_vendor\packaging\_parser.py

### Classes
- Node
- Variable
- Value
- Op
- ParsedRequirement

### Functions
- parse_requirement
- _parse_requirement
- _parse_requirement_details
- _parse_requirement_marker
- _parse_extras
- _parse_extras_list
- _parse_specifier
- _parse_version_many
- parse_marker
- _parse_full_marker
- _parse_marker
- _parse_marker_atom
- _parse_marker_item
- _parse_marker_var
- process_env_var
- process_python_str
- _parse_marker_op

## venv\Lib\site-packages\pip\_vendor\packaging\_structures.py

### Classes
- InfinityType
- NegativeInfinityType

## venv\Lib\site-packages\pip\_vendor\packaging\_tokenizer.py

### Classes
- Token
- ParserSyntaxError
- Tokenizer

## venv\Lib\site-packages\pip\_vendor\packaging\dependency_groups.py

### Classes
- DuplicateGroupNames
- CyclicDependencyGroup
- InvalidDependencyGroupObject
- DependencyGroupInclude
- DependencyGroupResolver

### Functions
- __dir__
- resolve_dependency_groups
- _normalize_name
- _normalize_group_names

## venv\Lib\site-packages\pip\_vendor\packaging\direct_url.py

### Classes
- _FromMappingProtocol
- DirectUrlValidationError
- _DirectUrlRequiredKeyError
- VcsInfo
- ArchiveInfo
- DirInfo
- DirectUrl

### Functions
- __dir__
- _json_dict_factory
- _get
- _get_required
- _get_object
- _strip_auth_from_netloc
- _strip_url

## venv\Lib\site-packages\pip\_vendor\packaging\errors.py

### Classes
- _ErrorCollector

### Functions
- __dir__

## venv\Lib\site-packages\pip\_vendor\packaging\licenses\__init__.py

### Classes
- InvalidLicenseExpression

### Functions
- __dir__
- canonicalize_license_expression

## venv\Lib\site-packages\pip\_vendor\packaging\licenses\_spdx.py

### Classes
- SPDXLicense
- SPDXException

## venv\Lib\site-packages\pip\_vendor\packaging\markers.py

### Classes
- InvalidMarker
- UndefinedComparison
- UndefinedEnvironmentName
- Environment
- Marker

### Functions
- __dir__
- _normalize_extras
- _normalize_extra_values
- _format_marker
- _eval_op
- _normalize
- _evaluate_markers
- _format_full_version
- default_environment
- _repair_python_full_version

## venv\Lib\site-packages\pip\_vendor\packaging\metadata.py

### Classes
- InvalidMetadata
- RawMetadata
- RFC822Policy
- RFC822Message
- _Validator
- Metadata

### Functions
- __dir__
- _parse_keywords
- _parse_project_urls
- _get_payload
- parse_email

## venv\Lib\site-packages\pip\_vendor\packaging\pylock.py

### Classes
- _FromMappingProtocol
- PylockValidationError
- _PylockRequiredKeyError
- PylockUnsupportedVersionError
- PylockSelectError
- PackageVcs
- PackageDirectory
- PackageArchive
- PackageSdist
- PackageWheel
- Package
- Pylock

### Functions
- __dir__
- is_valid_pylock_path
- _toml_key
- _toml_value
- _toml_dict_factory
- _get
- _get_required
- _get_sequence
- _get_as
- _get_required_as
- _get_sequence_as
- _get_object
- _get_sequence_of_objects
- _get_required_sequence_of_objects
- _validate_normalized_name
- _validate_path_url
- _path_name
- _url_name
- _validate_hashes

## venv\Lib\site-packages\pip\_vendor\packaging\requirements.py

### Classes
- InvalidRequirement
- Requirement

### Functions
- __dir__

## venv\Lib\site-packages\pip\_vendor\packaging\specifiers.py

### Classes
- _BoundaryKind
- _BoundaryVersion
- _LowerBound
- _UpperBound
- InvalidSpecifier
- BaseSpecifier
- Specifier
- SpecifierSet

### Functions
- __dir__
- _validate_spec
- _validate_pre
- _trim_release
- _range_is_empty
- _intersect_ranges
- _next_prefix_dev0
- _base_dev0
- _coerce_version
- _public_version
- _post_base
- _earliest_prerelease
- _nearest_non_prerelease
- _pep440_filter_prereleases
- _version_split
- _version_join
- _is_not_suffix
- _numeric_prefix_len
- _left_pad
- _operator_cost

## venv\Lib\site-packages\pip\_vendor\packaging\tags.py

### Classes
- UnsortedTagsError
- Tag

### Functions
- __dir__
- _compute_32_bit_interpreter
- parse_tag
- _get_config_var
- _normalize_string
- _is_threaded_cpython
- _abi3_applies
- _abi3t_applies
- _cpython_abis
- cpython_tags
- _generic_abi
- generic_tags
- _py_interpreter_range
- compatible_tags
- _mac_arch
- _mac_binary_formats
- mac_platforms
- ios_platforms
- android_platforms
- _linux_platforms
- _emscripten_platforms
- _generic_platforms
- platform_tags
- interpreter_name
- interpreter_version
- _version_nodot
- sys_tags
- create_compatible_tags_selector

## venv\Lib\site-packages\pip\_vendor\packaging\utils.py

### Classes
- InvalidName
- InvalidWheelFilename
- InvalidSdistFilename

### Functions
- __dir__
- canonicalize_name
- is_normalized_name
- canonicalize_version
- parse_wheel_filename
- parse_sdist_filename

## venv\Lib\site-packages\pip\_vendor\packaging\version.py

### Classes
- _VersionReplace
- InvalidVersion
- _BaseVersion
- _Version
- Version
- _TrimmedRelease

### Functions
- __dir__
- normalize_pre
- parse
- _validate_epoch
- _validate_release
- _validate_pre
- _validate_post
- _validate_dev
- _validate_local
- _parse_letter_version
- _parse_local_version
- _cmpkey

## venv\Lib\site-packages\pip\_vendor\pkg_resources\__init__.py

### Classes
- _LoaderProtocol
- _ZipLoaderModule
- PEP440Warning
- ResolutionError
- VersionConflict
- ContextualVersionConflict
- DistributionNotFound
- UnknownExtra
- IMetadataProvider
- IResourceProvider
- WorkingSet
- _ReqExtras
- Environment
- ExtractionError
- ResourceManager
- NullProvider
- EggProvider
- DefaultProvider
- EmptyProvider
- ZipManifests
- MemoizedZipManifests
- ZipProvider
- FileMetadata
- PathMetadata
- EggMetadata
- NoDists
- EntryPoint
- Distribution
- EggInfoDistribution
- DistInfoDistribution
- RequirementParseError
- Requirement
- PkgResourcesDeprecationWarning

### Functions
- _declare_state
- __getstate__
- __setstate__
- _sget_dict
- _sset_dict
- _sget_object
- _sset_object
- get_supported_platform
- register_loader_type
- get_provider
- get_provider
- get_provider
- _macos_vers
- _macos_arch
- get_build_platform
- compatible_platforms
- get_distribution
- get_distribution
- get_distribution
- load_entry_point
- get_entry_map
- get_entry_map
- get_entry_map
- get_entry_info
- get_default_cache
- safe_name
- safe_version
- _forgiving_version
- _safe_segment
- safe_extra
- to_filename
- invalid_marker
- evaluate_marker
- _parents
- register_finder
- find_distributions
- find_eggs_in_zip
- find_nothing
- find_on_path
- dist_factory
- safe_listdir
- distributions_from_metadata
- non_empty_lines
- resolve_egg_link
- register_namespace_handler
- _handle_ns
- _rebuild_mod_path
- declare_namespace
- fixup_namespace_packages
- file_ns_handler
- null_ns_handler
- normalize_path
- normalize_path
- normalize_path
- _cygwin_patch
- _is_egg_path
- _is_zip_egg
- _is_unpacked_egg
- _set_parent_ns
- _version_from_file
- issue_warning
- parse_requirements
- _always_object
- _find_adapter
- ensure_directory
- _bypass_ensure_directory
- split_sections
- _mkstemp
- _read_utf8_with_fallback
- _call_aside
- _initialize
- _initialize_master_working_set

## venv\Lib\site-packages\pip\_vendor\platformdirs\__init__.py

### Functions
- _set_platform_dir_class
- user_data_dir
- site_data_dir
- user_config_dir
- site_config_dir
- user_cache_dir
- site_cache_dir
- user_state_dir
- user_log_dir
- user_documents_dir
- user_downloads_dir
- user_pictures_dir
- user_videos_dir
- user_music_dir
- user_desktop_dir
- user_runtime_dir
- site_runtime_dir
- user_data_path
- site_data_path
- user_config_path
- site_config_path
- site_cache_path
- user_cache_path
- user_state_path
- user_log_path
- user_documents_path
- user_downloads_path
- user_pictures_path
- user_videos_path
- user_music_path
- user_desktop_path
- user_runtime_path
- site_runtime_path

## venv\Lib\site-packages\pip\_vendor\platformdirs\__main__.py

### Functions
- main

## venv\Lib\site-packages\pip\_vendor\platformdirs\android.py

### Classes
- Android

### Functions
- _android_folder
- _android_documents_folder
- _android_downloads_folder
- _android_pictures_folder
- _android_videos_folder
- _android_music_folder

## venv\Lib\site-packages\pip\_vendor\platformdirs\api.py

### Classes
- PlatformDirsABC

## venv\Lib\site-packages\pip\_vendor\platformdirs\macos.py

### Classes
- MacOS

## venv\Lib\site-packages\pip\_vendor\platformdirs\unix.py

### Classes
- Unix

### Functions
- _get_user_media_dir
- _get_user_dirs_folder

## venv\Lib\site-packages\pip\_vendor\platformdirs\version.py

## venv\Lib\site-packages\pip\_vendor\platformdirs\windows.py

### Classes
- Windows

### Functions
- get_win_folder_from_env_vars
- get_win_folder_if_csidl_name_not_env_var
- get_win_folder_from_registry
- get_win_folder_via_ctypes
- _pick_get_win_folder

## venv\Lib\site-packages\pip\_vendor\pygments\__init__.py

### Functions
- lex
- format
- highlight

## venv\Lib\site-packages\pip\_vendor\pygments\__main__.py

## venv\Lib\site-packages\pip\_vendor\pygments\console.py

### Functions
- reset_color
- colorize
- ansiformat

## venv\Lib\site-packages\pip\_vendor\pygments\filter.py

### Classes
- Filter
- FunctionFilter

### Functions
- apply_filters
- simplefilter

## venv\Lib\site-packages\pip\_vendor\pygments\filters\__init__.py

### Classes
- CodeTagFilter
- SymbolFilter
- KeywordCaseFilter
- NameHighlightFilter
- ErrorToken
- RaiseOnErrorTokenFilter
- VisibleWhitespaceFilter
- GobbleFilter
- TokenMergeFilter

### Functions
- find_filter_class
- get_filter_by_name
- get_all_filters
- _replace_special

## venv\Lib\site-packages\pip\_vendor\pygments\formatter.py

### Classes
- Formatter

### Functions
- _lookup_style

## venv\Lib\site-packages\pip\_vendor\pygments\formatters\__init__.py

### Classes
- _automodule

### Functions
- _fn_matches
- _load_formatters
- get_all_formatters
- find_formatter_class
- get_formatter_by_name
- load_formatter_from_file
- get_formatter_for_filename

## venv\Lib\site-packages\pip\_vendor\pygments\formatters\_mapping.py

## venv\Lib\site-packages\pip\_vendor\pygments\lexer.py

### Classes
- LexerMeta
- Lexer
- DelegatingLexer
- include
- _inherit
- combined
- _PseudoMatch
- _This
- default
- words
- RegexLexerMeta
- RegexLexer
- LexerContext
- ExtendedRegexLexer
- ProfilingRegexLexerMeta
- ProfilingRegexLexer

### Functions
- bygroups
- using
- do_insertions

## venv\Lib\site-packages\pip\_vendor\pygments\lexers\__init__.py

### Classes
- _automodule

### Functions
- _fn_matches
- _load_lexers
- get_all_lexers
- find_lexer_class
- find_lexer_class_by_name
- get_lexer_by_name
- load_lexer_from_file
- find_lexer_class_for_filename
- get_lexer_for_filename
- get_lexer_for_mimetype
- _iter_lexerclasses
- guess_lexer_for_filename
- guess_lexer

## venv\Lib\site-packages\pip\_vendor\pygments\lexers\_mapping.py

## venv\Lib\site-packages\pip\_vendor\pygments\lexers\python.py

### Classes
- PythonLexer
- Python2Lexer
- _PythonConsoleLexerBase
- PythonConsoleLexer
- PythonTracebackLexer
- Python2TracebackLexer
- CythonLexer
- DgLexer
- NumPyLexer

## venv\Lib\site-packages\pip\_vendor\pygments\modeline.py

### Functions
- get_filetype_from_line
- get_filetype_from_buffer

## venv\Lib\site-packages\pip\_vendor\pygments\plugin.py

### Functions
- iter_entry_points
- find_plugin_lexers
- find_plugin_formatters
- find_plugin_styles
- find_plugin_filters

## venv\Lib\site-packages\pip\_vendor\pygments\regexopt.py

### Functions
- make_charset
- regex_opt_inner
- regex_opt

## venv\Lib\site-packages\pip\_vendor\pygments\scanner.py

### Classes
- EndOfText
- Scanner

## venv\Lib\site-packages\pip\_vendor\pygments\sphinxext.py

### Classes
- PygmentsDoc

### Functions
- setup

## venv\Lib\site-packages\pip\_vendor\pygments\style.py

### Classes
- StyleMeta
- Style

## venv\Lib\site-packages\pip\_vendor\pygments\styles\__init__.py

### Functions
- get_style_by_name
- get_all_styles

## venv\Lib\site-packages\pip\_vendor\pygments\styles\_mapping.py

## venv\Lib\site-packages\pip\_vendor\pygments\token.py

### Classes
- _TokenType

### Functions
- is_token_subtype
- string_to_tokentype

## venv\Lib\site-packages\pip\_vendor\pygments\unistring.py

### Functions
- combine
- allexcept
- _handle_runs

## venv\Lib\site-packages\pip\_vendor\pygments\util.py

### Classes
- ClassNotFound
- OptionError
- Future
- UnclosingTextIOWrapper

### Functions
- get_choice_opt
- get_bool_opt
- get_int_opt
- get_list_opt
- docstring_headline
- make_analysator
- shebang_matches
- doctype_matches
- html_doctype_matches
- looks_like_xml
- surrogatepair
- format_lines
- duplicates_removed
- guess_decode
- guess_decode_from_terminal
- terminal_encoding

## venv\Lib\site-packages\pip\_vendor\pyproject_hooks\__init__.py

## venv\Lib\site-packages\pip\_vendor\pyproject_hooks\_impl.py

### Classes
- BackendUnavailable
- HookMissing
- UnsupportedOperation
- BuildBackendHookCaller

### Functions
- write_json
- read_json
- default_subprocess_runner
- quiet_subprocess_runner
- norm_and_check

## venv\Lib\site-packages\pip\_vendor\pyproject_hooks\_in_process\__init__.py

## venv\Lib\site-packages\pip\_vendor\pyproject_hooks\_in_process\_in_process.py

### Classes
- BackendUnavailable
- HookMissing
- _BackendPathFinder
- _DummyException
- GotUnsupportedOperation

### Functions
- write_json
- read_json
- _build_backend
- _supported_features
- get_requires_for_build_wheel
- get_requires_for_build_editable
- prepare_metadata_for_build_wheel
- prepare_metadata_for_build_editable
- _dist_info_files
- _get_wheel_metadata_from_wheel
- _find_already_built_wheel
- build_wheel
- build_editable
- get_requires_for_build_sdist
- build_sdist
- main

## venv\Lib\site-packages\pip\_vendor\requests\__init__.py

### Functions
- check_compatibility
- _check_cryptography

## venv\Lib\site-packages\pip\_vendor\requests\__version__.py

## venv\Lib\site-packages\pip\_vendor\requests\_internal_utils.py

### Functions
- to_native_string
- unicode_is_ascii

## venv\Lib\site-packages\pip\_vendor\requests\adapters.py

### Classes
- BaseAdapter
- HTTPAdapter

### Functions
- _urllib3_request_context

## venv\Lib\site-packages\pip\_vendor\requests\api.py

### Functions
- request
- get
- options
- head
- post
- put
- patch
- delete

## venv\Lib\site-packages\pip\_vendor\requests\auth.py

### Classes
- AuthBase
- HTTPBasicAuth
- HTTPProxyAuth
- HTTPDigestAuth

### Functions
- _basic_auth_str

## venv\Lib\site-packages\pip\_vendor\requests\certs.py

## venv\Lib\site-packages\pip\_vendor\requests\compat.py

### Functions
- _resolve_char_detection

## venv\Lib\site-packages\pip\_vendor\requests\cookies.py

### Classes
- MockRequest
- MockResponse
- CookieConflictError
- RequestsCookieJar

### Functions
- extract_cookies_to_jar
- get_cookie_header
- remove_cookie_by_name
- _copy_cookie_jar
- create_cookie
- morsel_to_cookie
- cookiejar_from_dict
- merge_cookies

## venv\Lib\site-packages\pip\_vendor\requests\exceptions.py

### Classes
- RequestException
- InvalidJSONError
- JSONDecodeError
- HTTPError
- ConnectionError
- ProxyError
- SSLError
- Timeout
- ConnectTimeout
- ReadTimeout
- URLRequired
- TooManyRedirects
- MissingSchema
- InvalidSchema
- InvalidURL
- InvalidHeader
- InvalidProxyURL
- ChunkedEncodingError
- ContentDecodingError
- StreamConsumedError
- RetryError
- UnrewindableBodyError
- RequestsWarning
- FileModeWarning
- RequestsDependencyWarning

## venv\Lib\site-packages\pip\_vendor\requests\help.py

### Functions
- _implementation
- info
- main

## venv\Lib\site-packages\pip\_vendor\requests\hooks.py

### Functions
- default_hooks
- dispatch_hook

## venv\Lib\site-packages\pip\_vendor\requests\models.py

### Classes
- RequestEncodingMixin
- RequestHooksMixin
- Request
- PreparedRequest
- Response

## venv\Lib\site-packages\pip\_vendor\requests\packages.py

## venv\Lib\site-packages\pip\_vendor\requests\sessions.py

### Classes
- SessionRedirectMixin
- Session

### Functions
- merge_setting
- merge_hooks
- session

## venv\Lib\site-packages\pip\_vendor\requests\status_codes.py

### Functions
- _init

## venv\Lib\site-packages\pip\_vendor\requests\structures.py

### Classes
- CaseInsensitiveDict
- LookupDict

## venv\Lib\site-packages\pip\_vendor\requests\utils.py

### Functions
- dict_to_sequence
- super_len
- get_netrc_auth
- guess_filename
- extract_zipped_paths
- atomic_open
- from_key_val_list
- to_key_val_list
- parse_list_header
- parse_dict_header
- unquote_header_value
- dict_from_cookiejar
- add_dict_to_cookiejar
- get_encodings_from_content
- _parse_content_type_header
- get_encoding_from_headers
- stream_decode_response_unicode
- iter_slices
- get_unicode_from_response
- unquote_unreserved
- requote_uri
- address_in_network
- dotted_netmask
- is_ipv4_address
- is_valid_cidr
- set_environ
- should_bypass_proxies
- get_environ_proxies
- select_proxy
- resolve_proxies
- default_user_agent
- default_headers
- parse_header_links
- guess_json_utf
- prepend_scheme_if_needed
- get_auth_from_url
- check_header_validity
- _validate_header_part
- urldefragauth
- rewind_body

## venv\Lib\site-packages\pip\_vendor\resolvelib\__init__.py

## venv\Lib\site-packages\pip\_vendor\resolvelib\providers.py

### Classes
- AbstractProvider

## venv\Lib\site-packages\pip\_vendor\resolvelib\reporters.py

### Classes
- BaseReporter

## venv\Lib\site-packages\pip\_vendor\resolvelib\resolvers\__init__.py

## venv\Lib\site-packages\pip\_vendor\resolvelib\resolvers\abstract.py

### Classes
- AbstractResolver

## venv\Lib\site-packages\pip\_vendor\resolvelib\resolvers\criterion.py

### Classes
- Criterion

## venv\Lib\site-packages\pip\_vendor\resolvelib\resolvers\exceptions.py

### Classes
- ResolverException
- RequirementsConflicted
- InconsistentCandidate
- ResolutionError
- ResolutionImpossible
- ResolutionTooDeep

## venv\Lib\site-packages\pip\_vendor\resolvelib\resolvers\resolution.py

### Classes
- Resolution
- Resolver

### Functions
- _build_result
- _has_route_to_root

## venv\Lib\site-packages\pip\_vendor\resolvelib\structs.py

### Classes
- DirectedGraph
- IteratorMapping
- _FactoryIterableView
- _SequenceIterableView

### Functions
- build_iter_view

## venv\Lib\site-packages\pip\_vendor\rich\__init__.py

### Functions
- get_console
- reconfigure
- print
- print_json
- inspect

## venv\Lib\site-packages\pip\_vendor\rich\__main__.py

### Classes
- ColorBox

### Functions
- make_test_card

## venv\Lib\site-packages\pip\_vendor\rich\_cell_widths.py

## venv\Lib\site-packages\pip\_vendor\rich\_emoji_codes.py

## venv\Lib\site-packages\pip\_vendor\rich\_emoji_replace.py

### Functions
- _emoji_replace

## venv\Lib\site-packages\pip\_vendor\rich\_export_format.py

## venv\Lib\site-packages\pip\_vendor\rich\_extension.py

### Functions
- load_ipython_extension

## venv\Lib\site-packages\pip\_vendor\rich\_fileno.py

### Functions
- get_fileno

## venv\Lib\site-packages\pip\_vendor\rich\_inspect.py

### Classes
- Inspect

### Functions
- _first_paragraph
- get_object_types_mro
- get_object_types_mro_as_strings
- is_object_one_of_types

## venv\Lib\site-packages\pip\_vendor\rich\_log_render.py

### Classes
- LogRender

## venv\Lib\site-packages\pip\_vendor\rich\_loop.py

### Functions
- loop_first
- loop_last
- loop_first_last

## venv\Lib\site-packages\pip\_vendor\rich\_null_file.py

### Classes
- NullFile

## venv\Lib\site-packages\pip\_vendor\rich\_palettes.py

## venv\Lib\site-packages\pip\_vendor\rich\_pick.py

### Functions
- pick_bool

## venv\Lib\site-packages\pip\_vendor\rich\_ratio.py

### Classes
- Edge

### Functions
- ratio_resolve
- ratio_reduce
- ratio_distribute

## venv\Lib\site-packages\pip\_vendor\rich\_spinners.py

## venv\Lib\site-packages\pip\_vendor\rich\_stack.py

### Classes
- Stack

## venv\Lib\site-packages\pip\_vendor\rich\_timer.py

### Functions
- timer

## venv\Lib\site-packages\pip\_vendor\rich\_win32_console.py

### Classes
- LegacyWindowsError
- WindowsCoordinates
- CONSOLE_SCREEN_BUFFER_INFO
- CONSOLE_CURSOR_INFO
- LegacyWindowsTerm

### Functions
- GetStdHandle
- GetConsoleMode
- FillConsoleOutputCharacter
- FillConsoleOutputAttribute
- SetConsoleTextAttribute
- GetConsoleScreenBufferInfo
- SetConsoleCursorPosition
- GetConsoleCursorInfo
- SetConsoleCursorInfo
- SetConsoleTitle

## venv\Lib\site-packages\pip\_vendor\rich\_windows.py

### Classes
- WindowsConsoleFeatures

## venv\Lib\site-packages\pip\_vendor\rich\_windows_renderer.py

### Functions
- legacy_windows_render

## venv\Lib\site-packages\pip\_vendor\rich\_wrap.py

### Functions
- words
- divide_line

## venv\Lib\site-packages\pip\_vendor\rich\abc.py

### Classes
- RichRenderable

## venv\Lib\site-packages\pip\_vendor\rich\align.py

### Classes
- Align
- VerticalCenter

## venv\Lib\site-packages\pip\_vendor\rich\ansi.py

### Classes
- _AnsiToken
- AnsiDecoder

### Functions
- _ansi_tokenize

## venv\Lib\site-packages\pip\_vendor\rich\bar.py

### Classes
- Bar

## venv\Lib\site-packages\pip\_vendor\rich\box.py

### Classes
- Box

## venv\Lib\site-packages\pip\_vendor\rich\cells.py

### Functions
- cached_cell_len
- cell_len
- get_character_cell_size
- set_cell_size
- chop_cells

## venv\Lib\site-packages\pip\_vendor\rich\color.py

### Classes
- ColorSystem
- ColorType
- ColorParseError
- Color

### Functions
- parse_rgb_hex
- blend_rgb

## venv\Lib\site-packages\pip\_vendor\rich\color_triplet.py

### Classes
- ColorTriplet

## venv\Lib\site-packages\pip\_vendor\rich\columns.py

### Classes
- Columns

## venv\Lib\site-packages\pip\_vendor\rich\console.py

### Classes
- NoChange
- ConsoleDimensions
- ConsoleOptions
- RichCast
- ConsoleRenderable
- CaptureError
- NewLine
- ScreenUpdate
- Capture
- ThemeContext
- PagerContext
- ScreenContext
- Group
- ConsoleThreadLocals
- RenderHook
- Console

### Functions
- group
- _is_jupyter
- get_windows_console_features
- detect_legacy_windows
- _svg_hash

## venv\Lib\site-packages\pip\_vendor\rich\constrain.py

### Classes
- Constrain

## venv\Lib\site-packages\pip\_vendor\rich\containers.py

### Classes
- Renderables
- Lines

## venv\Lib\site-packages\pip\_vendor\rich\control.py

### Classes
- Control

### Functions
- strip_control_codes
- escape_control_codes

## venv\Lib\site-packages\pip\_vendor\rich\default_styles.py

## venv\Lib\site-packages\pip\_vendor\rich\diagnose.py

### Functions
- report

## venv\Lib\site-packages\pip\_vendor\rich\emoji.py

### Classes
- NoEmoji
- Emoji

## venv\Lib\site-packages\pip\_vendor\rich\errors.py

### Classes
- ConsoleError
- StyleError
- StyleSyntaxError
- MissingStyle
- StyleStackError
- NotRenderableError
- MarkupError
- LiveError
- NoAltScreen

## venv\Lib\site-packages\pip\_vendor\rich\file_proxy.py

### Classes
- FileProxy

## venv\Lib\site-packages\pip\_vendor\rich\filesize.py

### Functions
- _to_str
- pick_unit_and_suffix
- decimal

## venv\Lib\site-packages\pip\_vendor\rich\highlighter.py

### Classes
- Highlighter
- NullHighlighter
- RegexHighlighter
- ReprHighlighter
- JSONHighlighter
- ISO8601Highlighter

### Functions
- _combine_regex

## venv\Lib\site-packages\pip\_vendor\rich\json.py

### Classes
- JSON

## venv\Lib\site-packages\pip\_vendor\rich\jupyter.py

### Classes
- JupyterRenderable
- JupyterMixin

### Functions
- _render_segments
- display
- print

## venv\Lib\site-packages\pip\_vendor\rich\layout.py

### Classes
- LayoutRender
- LayoutError
- NoSplitter
- _Placeholder
- Splitter
- RowSplitter
- ColumnSplitter
- Layout

## venv\Lib\site-packages\pip\_vendor\rich\live.py

### Classes
- _RefreshThread
- Live

## venv\Lib\site-packages\pip\_vendor\rich\live_render.py

### Classes
- LiveRender

## venv\Lib\site-packages\pip\_vendor\rich\logging.py

### Classes
- RichHandler

## venv\Lib\site-packages\pip\_vendor\rich\markup.py

### Classes
- Tag

### Functions
- escape
- _parse
- render

## venv\Lib\site-packages\pip\_vendor\rich\measure.py

### Classes
- Measurement

### Functions
- measure_renderables

## venv\Lib\site-packages\pip\_vendor\rich\padding.py

### Classes
- Padding

## venv\Lib\site-packages\pip\_vendor\rich\pager.py

### Classes
- Pager
- SystemPager

## venv\Lib\site-packages\pip\_vendor\rich\palette.py

### Classes
- Palette

## venv\Lib\site-packages\pip\_vendor\rich\panel.py

### Classes
- Panel

## venv\Lib\site-packages\pip\_vendor\rich\pretty.py

### Classes
- Pretty
- Node
- _Line

### Functions
- _is_attr_object
- _get_attr_fields
- _is_dataclass_repr
- _has_default_namedtuple_repr
- _ipy_display_hook
- _safe_isinstance
- install
- _get_braces_for_defaultdict
- _get_braces_for_deque
- _get_braces_for_array
- is_expandable
- _is_namedtuple
- traverse
- pretty_repr
- pprint

## venv\Lib\site-packages\pip\_vendor\rich\progress.py

### Classes
- _TrackThread
- _Reader
- _ReadContext
- ProgressColumn
- RenderableColumn
- SpinnerColumn
- TextColumn
- BarColumn
- TimeElapsedColumn
- TaskProgressColumn
- TimeRemainingColumn
- FileSizeColumn
- TotalFileSizeColumn
- MofNCompleteColumn
- DownloadColumn
- TransferSpeedColumn
- ProgressSample
- Task
- Progress

### Functions
- track
- wrap_file
- open
- open
- open

## venv\Lib\site-packages\pip\_vendor\rich\progress_bar.py

### Classes
- ProgressBar

## venv\Lib\site-packages\pip\_vendor\rich\prompt.py

### Classes
- PromptError
- InvalidResponse
- PromptBase
- Prompt
- IntPrompt
- FloatPrompt
- Confirm

## venv\Lib\site-packages\pip\_vendor\rich\protocol.py

### Functions
- is_renderable
- rich_cast

## venv\Lib\site-packages\pip\_vendor\rich\region.py

### Classes
- Region

## venv\Lib\site-packages\pip\_vendor\rich\repr.py

### Classes
- ReprError

### Functions
- auto
- auto
- auto
- rich_repr
- rich_repr
- rich_repr

## venv\Lib\site-packages\pip\_vendor\rich\rule.py

### Classes
- Rule

## venv\Lib\site-packages\pip\_vendor\rich\scope.py

### Functions
- render_scope

## venv\Lib\site-packages\pip\_vendor\rich\screen.py

### Classes
- Screen

## venv\Lib\site-packages\pip\_vendor\rich\segment.py

### Classes
- ControlType
- Segment
- Segments
- SegmentLines

## venv\Lib\site-packages\pip\_vendor\rich\spinner.py

### Classes
- Spinner

## venv\Lib\site-packages\pip\_vendor\rich\status.py

### Classes
- Status

## venv\Lib\site-packages\pip\_vendor\rich\style.py

### Classes
- _Bit
- Style
- StyleStack

## venv\Lib\site-packages\pip\_vendor\rich\styled.py

### Classes
- Styled

## venv\Lib\site-packages\pip\_vendor\rich\syntax.py

### Classes
- SyntaxTheme
- PygmentsSyntaxTheme
- ANSISyntaxTheme
- _SyntaxHighlightRange
- PaddingProperty
- Syntax

### Functions
- _get_code_index_for_syntax_position

## venv\Lib\site-packages\pip\_vendor\rich\table.py

### Classes
- Column
- Row
- _Cell
- Table

## venv\Lib\site-packages\pip\_vendor\rich\terminal_theme.py

### Classes
- TerminalTheme

## venv\Lib\site-packages\pip\_vendor\rich\text.py

### Classes
- Span
- Text

## venv\Lib\site-packages\pip\_vendor\rich\theme.py

### Classes
- Theme
- ThemeStackError
- ThemeStack

## venv\Lib\site-packages\pip\_vendor\rich\themes.py

## venv\Lib\site-packages\pip\_vendor\rich\traceback.py

### Classes
- Frame
- _SyntaxError
- Stack
- Trace
- PathHighlighter
- Traceback

### Functions
- _iter_syntax_lines
- install

## venv\Lib\site-packages\pip\_vendor\rich\tree.py

### Classes
- Tree

## venv\Lib\site-packages\pip\_vendor\tomli\__init__.py

## venv\Lib\site-packages\pip\_vendor\tomli\_parser.py

### Classes
- DEPRECATED_DEFAULT
- TOMLDecodeError
- Flags
- NestedDict
- Output

### Functions
- load
- loads
- skip_chars
- skip_until
- skip_comment
- skip_comments_and_array_ws
- create_dict_rule
- create_list_rule
- key_value_rule
- parse_key_value_pair
- parse_key
- parse_key_part
- parse_one_line_basic_str
- parse_array
- parse_inline_table
- parse_basic_str_escape
- parse_basic_str_escape_multiline
- parse_hex_char
- parse_literal_str
- parse_multiline_str
- parse_basic_str
- parse_value
- is_unicode_scalar_value
- make_safe_parse_float

## venv\Lib\site-packages\pip\_vendor\tomli\_re.py

### Functions
- match_to_datetime
- cached_tz
- match_to_localtime
- match_to_number

## venv\Lib\site-packages\pip\_vendor\tomli\_types.py

## venv\Lib\site-packages\pip\_vendor\tomli_w\__init__.py

## venv\Lib\site-packages\pip\_vendor\tomli_w\_writer.py

### Classes
- Context

### Functions
- dump
- dumps
- gen_table_chunks
- format_literal
- format_decimal
- format_inline_table
- format_inline_array
- format_key_part
- format_string
- is_aot
- is_suitable_inline_table

## venv\Lib\site-packages\pip\_vendor\truststore\__init__.py

## venv\Lib\site-packages\pip\_vendor\truststore\_api.py

### Classes
- SSLContext

### Functions
- inject_into_ssl
- extract_from_ssl
- _verify_peercerts

## venv\Lib\site-packages\pip\_vendor\truststore\_macos.py

### Classes
- CFConst

### Functions
- _load_cdll
- _handle_osstatus
- _bytes_to_cf_data_ref
- _bytes_to_cf_string
- _cf_string_ref_to_str
- _der_certs_to_cf_cert_array
- _configure_context
- _verify_peercerts_impl
- _verify_peercerts_impl_macos_10_13
- _verify_peercerts_impl_macos_10_14

## venv\Lib\site-packages\pip\_vendor\truststore\_openssl.py

### Functions
- _configure_context
- _capath_contains_certs
- _verify_peercerts_impl

## venv\Lib\site-packages\pip\_vendor\truststore\_ssl_constants.py

### Functions
- _set_ssl_context_verify_mode

## venv\Lib\site-packages\pip\_vendor\truststore\_windows.py

### Classes
- CERT_CONTEXT
- CERT_ENHKEY_USAGE
- CERT_USAGE_MATCH
- CERT_CHAIN_PARA
- CERT_TRUST_STATUS
- CERT_CHAIN_ELEMENT
- CERT_SIMPLE_CHAIN
- CERT_CHAIN_CONTEXT
- SSL_EXTRA_CERT_CHAIN_POLICY_PARA
- CERT_CHAIN_POLICY_PARA
- CERT_CHAIN_POLICY_STATUS
- CERT_CHAIN_ENGINE_CONFIG

### Functions
- _handle_win_error
- _verify_peercerts_impl
- _get_and_verify_cert_chain
- _verify_using_custom_ca_certs
- _configure_context

## venv\Lib\site-packages\pip\_vendor\urllib3\__init__.py

### Functions
- add_stderr_logger
- disable_warnings
- request

## venv\Lib\site-packages\pip\_vendor\urllib3\_base_connection.py

### Classes
- ProxyConfig
- _ResponseOptions

## venv\Lib\site-packages\pip\_vendor\urllib3\_collections.py

### Classes
- _Sentinel
- RecentlyUsedContainer
- HTTPHeaderDictItemView
- HTTPHeaderDict

### Functions
- ensure_can_construct_http_header_dict

## venv\Lib\site-packages\pip\_vendor\urllib3\_request_methods.py

### Classes
- RequestMethods

## venv\Lib\site-packages\pip\_vendor\urllib3\_version.py

## venv\Lib\site-packages\pip\_vendor\urllib3\connection.py

### Classes
- HTTPConnection
- HTTPSConnection
- _WrappedAndVerifiedSocket
- DummyConnection

### Functions
- _ssl_wrap_socket_and_match_hostname
- _match_hostname
- _wrap_proxy_error
- _get_default_user_agent
- _url_from_connection

## venv\Lib\site-packages\pip\_vendor\urllib3\connectionpool.py

### Classes
- ConnectionPool
- HTTPConnectionPool
- HTTPSConnectionPool

### Functions
- connection_from_url
- _normalize_host
- _normalize_host
- _normalize_host
- _url_from_pool
- _close_pool_connections

## venv\Lib\site-packages\pip\_vendor\urllib3\contrib\__init__.py

## venv\Lib\site-packages\pip\_vendor\urllib3\contrib\emscripten\__init__.py

### Functions
- inject_into_urllib3

## venv\Lib\site-packages\pip\_vendor\urllib3\contrib\emscripten\connection.py

### Classes
- EmscriptenHTTPConnection
- EmscriptenHTTPSConnection

## venv\Lib\site-packages\pip\_vendor\urllib3\contrib\emscripten\fetch.py

### Classes
- _RequestError
- _StreamingError
- _TimeoutError
- _ReadStream
- _StreamingFetcher
- _JSPIReadStream

### Functions
- _obj_from_dict
- is_in_browser_main_thread
- is_cross_origin_isolated
- is_in_node
- is_worker_available
- send_streaming_request
- _show_timeout_warning
- _show_streaming_warning
- send_request
- send_jspi_request
- _run_sync_with_timeout
- has_jspi
- _is_node_js
- streaming_ready

## venv\Lib\site-packages\pip\_vendor\urllib3\contrib\emscripten\request.py

### Classes
- EmscriptenRequest

## venv\Lib\site-packages\pip\_vendor\urllib3\contrib\emscripten\response.py

### Classes
- EmscriptenResponse
- EmscriptenHttpResponseWrapper

## venv\Lib\site-packages\pip\_vendor\urllib3\contrib\pyopenssl.py

### Classes
- WrappedSocket
- PyOpenSSLContext

### Functions
- inject_into_urllib3
- extract_from_urllib3
- _validate_dependencies_met
- _dnsname_to_stdlib
- get_subj_alt_name
- _verify_callback

## venv\Lib\site-packages\pip\_vendor\urllib3\contrib\socks.py

### Classes
- _TYPE_SOCKS_OPTIONS
- SOCKSConnection
- SOCKSHTTPSConnection
- SOCKSHTTPConnectionPool
- SOCKSHTTPSConnectionPool
- SOCKSProxyManager

## venv\Lib\site-packages\pip\_vendor\urllib3\exceptions.py

### Classes
- HTTPError
- HTTPWarning
- PoolError
- RequestError
- SSLError
- ProxyError
- DecodeError
- ProtocolError
- MaxRetryError
- HostChangedError
- TimeoutStateError
- TimeoutError
- ReadTimeoutError
- ConnectTimeoutError
- NewConnectionError
- NameResolutionError
- EmptyPoolError
- FullPoolError
- ClosedPoolError
- LocationValueError
- LocationParseError
- URLSchemeUnknown
- ResponseError
- SecurityWarning
- InsecureRequestWarning
- NotOpenSSLWarning
- SystemTimeWarning
- InsecurePlatformWarning
- DependencyWarning
- ResponseNotChunked
- BodyNotHttplibCompatible
- IncompleteRead
- InvalidChunkLength
- InvalidHeader
- ProxySchemeUnknown
- ProxySchemeUnsupported
- HeaderParsingError
- UnrewindableBodyError

## venv\Lib\site-packages\pip\_vendor\urllib3\fields.py

### Classes
- RequestField

### Functions
- guess_content_type
- format_header_param_rfc2231
- format_multipart_header_param
- format_header_param_html5
- format_header_param

## venv\Lib\site-packages\pip\_vendor\urllib3\filepost.py

### Functions
- choose_boundary
- iter_field_objects
- encode_multipart_formdata

## venv\Lib\site-packages\pip\_vendor\urllib3\http2\__init__.py

### Functions
- inject_into_urllib3
- extract_from_urllib3

## venv\Lib\site-packages\pip\_vendor\urllib3\http2\connection.py

### Classes
- _LockedObject
- HTTP2Connection
- HTTP2Response

### Functions
- _is_legal_header_name
- _is_illegal_header_value

## venv\Lib\site-packages\pip\_vendor\urllib3\http2\probe.py

### Classes
- _HTTP2ProbeCache

## venv\Lib\site-packages\pip\_vendor\urllib3\poolmanager.py

### Classes
- PoolKey
- PoolManager
- ProxyManager

### Functions
- _default_key_normalizer
- proxy_from_url

## venv\Lib\site-packages\pip\_vendor\urllib3\response.py

### Classes
- ContentDecoder
- DeflateDecoder
- GzipDecoderState
- GzipDecoder
- MultiDecoder
- BytesQueueBuffer
- BaseHTTPResponse
- HTTPResponse

### Functions
- _get_decoder

## venv\Lib\site-packages\pip\_vendor\urllib3\util\__init__.py

## venv\Lib\site-packages\pip\_vendor\urllib3\util\connection.py

### Functions
- is_connection_dropped
- create_connection
- _set_socket_options
- allowed_gai_family
- _has_ipv6

## venv\Lib\site-packages\pip\_vendor\urllib3\util\proxy.py

### Functions
- connection_requires_http_tunnel

## venv\Lib\site-packages\pip\_vendor\urllib3\util\request.py

### Classes
- _TYPE_FAILEDTELL
- ChunksAndContentLength

### Functions
- make_headers
- set_file_position
- rewind_body
- body_to_chunks

## venv\Lib\site-packages\pip\_vendor\urllib3\util\response.py

### Functions
- is_fp_closed
- assert_header_parsing
- is_response_to_head

## venv\Lib\site-packages\pip\_vendor\urllib3\util\retry.py

### Classes
- RequestHistory
- Retry

## venv\Lib\site-packages\pip\_vendor\urllib3\util\ssl_.py

### Functions
- _is_bpo_43522_fixed
- _is_has_never_check_common_name_reliable
- assert_fingerprint
- resolve_cert_reqs
- resolve_ssl_version
- create_urllib3_context
- ssl_wrap_socket
- ssl_wrap_socket
- ssl_wrap_socket
- is_ipaddress
- _is_key_file_encrypted
- _ssl_wrap_socket_impl

## venv\Lib\site-packages\pip\_vendor\urllib3\util\ssl_match_hostname.py

### Classes
- CertificateError

### Functions
- _dnsname_match
- _ipaddress_match
- match_hostname

## venv\Lib\site-packages\pip\_vendor\urllib3\util\ssltransport.py

### Classes
- SSLTransport

## venv\Lib\site-packages\pip\_vendor\urllib3\util\timeout.py

### Classes
- _TYPE_DEFAULT
- Timeout

## venv\Lib\site-packages\pip\_vendor\urllib3\util\url.py

### Classes
- Url

### Functions
- _encode_invalid_chars
- _encode_invalid_chars
- _encode_invalid_chars
- _remove_path_dot_segments
- _normalize_host
- _normalize_host
- _normalize_host
- _idna_encode
- _encode_target
- parse_url

## venv\Lib\site-packages\pip\_vendor\urllib3\util\util.py

### Functions
- to_bytes
- to_str
- reraise

## venv\Lib\site-packages\pip\_vendor\urllib3\util\wait.py

### Functions
- select_wait_for_socket
- poll_wait_for_socket
- _have_working_poll
- wait_for_socket
- wait_for_read
- wait_for_write

## venv\Lib\site-packages\pluggy\__init__.py

## venv\Lib\site-packages\pluggy\_callers.py

### Functions
- run_old_style_hookwrapper
- _raise_wrapfail
- _warn_teardown_exception
- _multicall

## venv\Lib\site-packages\pluggy\_hooks.py

### Classes
- HookspecOpts
- HookimplOpts
- HookspecMarker
- HookimplMarker
- HookRelay
- HookCaller
- _SubsetHookCaller
- HookImpl
- HookSpec

### Functions
- normalize_hookimpl_opts
- varnames

## venv\Lib\site-packages\pluggy\_manager.py

### Classes
- PluginValidationError
- DistFacade
- PluginManager

### Functions
- _warn_for_function
- _formatdef

## venv\Lib\site-packages\pluggy\_result.py

### Classes
- HookCallError
- Result

## venv\Lib\site-packages\pluggy\_tracing.py

### Classes
- TagTracer
- TagTracerSub

## venv\Lib\site-packages\pluggy\_version.py

## venv\Lib\site-packages\pluggy\_warnings.py

### Classes
- PluggyWarning
- PluggyTeardownRaisedWarning

## venv\Lib\site-packages\py.py

## venv\Lib\site-packages\pygame\__init__.py

### Classes
- MissingModule

### Functions
- _attribute_undefined
- packager_imports
- __rect_constructor
- __rect_reduce
- __color_constructor
- __color_reduce

## venv\Lib\site-packages\pygame\__pyinstaller\__init__.py

### Functions
- get_hook_dirs

## venv\Lib\site-packages\pygame\__pyinstaller\hook-pygame.py

### Functions
- _append_to_datas

## venv\Lib\site-packages\pygame\_camera_opencv.py

### Classes
- Camera
- CameraMac

### Functions
- list_cameras
- list_cameras_darwin

## venv\Lib\site-packages\pygame\_camera_vidcapture.py

### Classes
- Camera

### Functions
- list_cameras
- init
- quit

## venv\Lib\site-packages\pygame\_sdl2\__init__.py

## venv\Lib\site-packages\pygame\camera.py

### Classes
- AbstractCamera
- _PreInitPlaceholderCamera

### Functions
- _pre_init_placeholder
- _pre_init_placeholder_varargs
- _colorspace_not_available
- _setup_backend
- get_backends
- init
- quit

## venv\Lib\site-packages\pygame\colordict.py

## venv\Lib\site-packages\pygame\cursors.py

### Classes
- Cursor

### Functions
- set_cursor
- get_cursor
- compile
- load_xbm

## venv\Lib\site-packages\pygame\docs\__main__.py

### Functions
- _iterpath
- has_local_docs
- open_docs

## venv\Lib\site-packages\pygame\draw_py.py

### Functions
- frac
- inv_frac
- set_at
- draw_pixel
- _drawhorzline
- _drawvertline
- _clip_and_draw_horizline
- _clip_and_draw_vertline
- encode
- clip_line
- _draw_line
- _draw_aaline
- _draw_aaline_dy
- _draw_aaline_dx
- _clip_and_draw_line
- _clip_and_draw_line_width
- _clip_and_draw_aaline
- draw_aaline
- draw_line
- _multi_lines
- draw_lines
- draw_aalines
- draw_polygon
- _draw_polygon_inner_loop

## venv\Lib\site-packages\pygame\examples\__init__.py

## venv\Lib\site-packages\pygame\examples\aacircle.py

### Functions
- main

## venv\Lib\site-packages\pygame\examples\aliens.py

### Classes
- Player
- Alien
- Explosion
- Shot
- Bomb
- Score

### Functions
- load_image
- load_sound
- main

## venv\Lib\site-packages\pygame\examples\arraydemo.py

### Functions
- surfdemo_show
- main

## venv\Lib\site-packages\pygame\examples\audiocapture.py

### Functions
- callback
- postmix_callback

## venv\Lib\site-packages\pygame\examples\blend_fill.py

### Functions
- usage
- main

## venv\Lib\site-packages\pygame\examples\blit_blends.py

### Functions
- main
- usage

## venv\Lib\site-packages\pygame\examples\camera.py

### Classes
- VideoCapturePlayer

### Functions
- main

## venv\Lib\site-packages\pygame\examples\chimp.py

### Classes
- Fist
- Chimp

### Functions
- load_image
- load_sound
- main

## venv\Lib\site-packages\pygame\examples\cursors.py

### Functions
- check_circle
- main

## venv\Lib\site-packages\pygame\examples\dropevent.py

### Functions
- main

## venv\Lib\site-packages\pygame\examples\eventlist.py

### Functions
- showtext
- drawstatus
- drawhistory
- draw_usage_in_history
- main

## venv\Lib\site-packages\pygame\examples\font_viewer.py

### Classes
- FontViewer

## venv\Lib\site-packages\pygame\examples\fonty.py

### Functions
- main

## venv\Lib\site-packages\pygame\examples\freetype_misc.py

### Functions
- run

## venv\Lib\site-packages\pygame\examples\glcube.py

### Classes
- Rotation

### Functions
- translate
- frustum
- perspective
- rotate
- drawcube_old
- init_gl_stuff_old
- init_gl_modern
- draw_cube_modern
- main

## venv\Lib\site-packages\pygame\examples\go_over_there.py

### Classes
- Ball

### Functions
- reset

## venv\Lib\site-packages\pygame\examples\grid.py

### Classes
- Player
- Game

## venv\Lib\site-packages\pygame\examples\headless_no_windows_needed.py

### Functions
- scaleit
- main

## venv\Lib\site-packages\pygame\examples\joystick.py

### Classes
- TextPrint

### Functions
- main

## venv\Lib\site-packages\pygame\examples\liquid.py

### Functions
- main

## venv\Lib\site-packages\pygame\examples\mask.py

### Classes
- Sprite

### Functions
- main

## venv\Lib\site-packages\pygame\examples\midi.py

### Classes
- NullKey
- KeyData
- Key
- Keyboard

### Functions
- print_device_info
- _print_device_info
- input_main
- output_main
- make_key_mapping
- key_class
- key_images
- fill_region
- is_white_key
- usage
- main

## venv\Lib\site-packages\pygame\examples\moveit.py

### Classes
- GameObject

### Functions
- load_image
- main

## venv\Lib\site-packages\pygame\examples\music_drop_fade.py

### Functions
- add_file
- play_file
- play_next
- draw_text_line
- change_music_position
- main

## venv\Lib\site-packages\pygame\examples\pixelarray.py

### Functions
- show
- main

## venv\Lib\site-packages\pygame\examples\playmus.py

### Classes
- Window

### Functions
- show_usage_message
- main

## venv\Lib\site-packages\pygame\examples\resizing_new.py

## venv\Lib\site-packages\pygame\examples\scaletest.py

### Functions
- main
- SpeedTest

## venv\Lib\site-packages\pygame\examples\scrap_clipboard.py

### Functions
- usage

## venv\Lib\site-packages\pygame\examples\scroll.py

### Functions
- draw_arrow
- add_arrow_button
- scroll_view
- main

## venv\Lib\site-packages\pygame\examples\setmodescale.py

## venv\Lib\site-packages\pygame\examples\sound.py

### Functions
- main

## venv\Lib\site-packages\pygame\examples\sound_array_demos.py

### Functions
- make_echo
- slow_down_sound
- sound_from_pos
- main

## venv\Lib\site-packages\pygame\examples\sprite_texture.py

### Classes
- Something

### Functions
- load_img

## venv\Lib\site-packages\pygame\examples\stars.py

### Functions
- init_star
- initialize_stars
- draw_stars
- move_stars
- main

## venv\Lib\site-packages\pygame\examples\testsprite.py

### Classes
- Thingy
- Static

### Functions
- main

## venv\Lib\site-packages\pygame\examples\textinput.py

### Classes
- TextInput
- Game

### Functions
- main

## venv\Lib\site-packages\pygame\examples\vgrade.py

### Functions
- stopwatch
- VertGradientColumn
- DisplayGradient
- main

## venv\Lib\site-packages\pygame\examples\video.py

### Functions
- load_img

## venv\Lib\site-packages\pygame\fastevent.py

### Functions
- _ft_init_check
- _quit_hook
- init
- get_init
- pump
- wait
- poll
- get
- post

## venv\Lib\site-packages\pygame\freetype.py

### Functions
- SysFont

## venv\Lib\site-packages\pygame\ftfont.py

### Classes
- Font

### Functions
- get_init
- SysFont

## venv\Lib\site-packages\pygame\locals.py

## venv\Lib\site-packages\pygame\macosx.py

### Functions
- Video_AutoInit

## venv\Lib\site-packages\pygame\midi.py

### Classes
- Input
- Output
- MidiException

### Functions
- _module_init
- init
- quit
- get_init
- _check_init
- get_count
- get_default_input_id
- get_default_output_id
- get_device_info
- time
- midis2events
- frequency_to_midi
- midi_to_frequency
- midi_to_ansi_note

## venv\Lib\site-packages\pygame\pkgdata.py

### Functions
- getResource

## venv\Lib\site-packages\pygame\sndarray.py

### Functions
- array
- samples
- make_sound
- use_arraytype
- get_arraytype
- get_arraytypes

## venv\Lib\site-packages\pygame\sprite.py

### Classes
- Sprite
- WeakSprite
- DirtySprite
- WeakDirtySprite
- AbstractGroup
- Group
- RenderUpdates
- OrderedUpdates
- LayeredUpdates
- LayeredDirty
- GroupSingle
- collide_rect_ratio
- collide_circle_ratio

### Functions
- collide_rect
- collide_circle
- collide_mask
- spritecollide
- groupcollide
- spritecollideany

## venv\Lib\site-packages\pygame\surfarray.py

### Functions
- blit_array
- make_surface
- array2d
- pixels2d
- array3d
- pixels3d
- array_alpha
- pixels_alpha
- pixels_red
- array_red
- pixels_green
- array_green
- pixels_blue
- array_blue
- array_colorkey
- map_array
- use_arraytype
- get_arraytype
- get_arraytypes

## venv\Lib\site-packages\pygame\sysfont.py

### Functions
- _simplename
- _addfont
- initsysfonts_win32
- _parse_font_entry_win
- _parse_font_entry_darwin
- _font_finder_darwin
- initsysfonts_darwin
- initsysfonts_unix
- _parse_font_entry_unix
- create_aliases
- initsysfonts
- font_constructor
- SysFont
- get_fonts
- match_font

## venv\Lib\site-packages\pygame\tests\__init__.py

## venv\Lib\site-packages\pygame\tests\__main__.py

## venv\Lib\site-packages\pygame\tests\base_test.py

### Classes
- BaseModuleTest

### Functions
- quit_hook

## venv\Lib\site-packages\pygame\tests\blit_test.py

### Classes
- BlitTest
- BlitsTest

## venv\Lib\site-packages\pygame\tests\bufferproxy_test.py

### Classes
- BufferProxyTest
- BufferProxyLegacyTest

## venv\Lib\site-packages\pygame\tests\camera_test.py

### Classes
- CameraModuleTest

## venv\Lib\site-packages\pygame\tests\color_test.py

### Classes
- ColorTypeTest
- SubclassTest

### Functions
- rgba_combos_Color_generator
- gamma_correct
- _assignr
- _assigng
- _assignb
- _assigna
- _assign_item

## venv\Lib\site-packages\pygame\tests\constants_test.py

### Classes
- KConstantsTests
- KscanConstantsTests
- KmodConstantsTests

### Functions
- create_overlap_set

## venv\Lib\site-packages\pygame\tests\controller_test.py

### Classes
- ControllerModuleTest
- ControllerTypeTest
- ControllerInteractiveTest

## venv\Lib\site-packages\pygame\tests\cursors_test.py

### Classes
- CursorsModuleTest

## venv\Lib\site-packages\pygame\tests\display_test.py

### Classes
- DisplayModuleTest
- DisplayUpdateTest
- DisplayUpdateInteractiveTest
- DisplayInteractiveTest
- FullscreenToggleTests
- DisplayOpenGLTest
- X11CrashTest

## venv\Lib\site-packages\pygame\tests\docs_test.py

### Classes
- DocsIncludedTest

## venv\Lib\site-packages\pygame\tests\draw_test.py

### Classes
- InvalidBool
- DrawTestCase
- PythonDrawTestCase
- DrawEllipseMixin
- DrawEllipseTest
- BaseLineMixin
- LineMixin
- DrawLineTest
- LinesMixin
- DrawLinesTest
- AALineMixin
- DrawAALineTest
- AALinesMixin
- DrawAALinesTest
- DrawPolygonMixin
- DrawPolygonTest
- DrawRectMixin
- DrawRectTest
- DrawCircleMixin
- DrawCircleTest
- DrawArcMixin
- DrawArcTest
- DrawModuleTest

### Functions
- get_border_values
- corners
- rect_corners_mids_and_center
- border_pos_and_color
- get_color_points
- create_bounding_rect

## venv\Lib\site-packages\pygame\tests\event_test.py

### Classes
- EventTypeTest
- EventModuleArgsTest
- EventCustomTypeTest
- EventModuleTest
- EventModuleTestsWithTiming

## venv\Lib\site-packages\pygame\tests\font_test.py

### Classes
- FontModuleTest
- FontTest
- FontTypeTest
- VisualTests

### Functions
- equal_images

## venv\Lib\site-packages\pygame\tests\freetype_tags.py

## venv\Lib\site-packages\pygame\tests\freetype_test.py

### Classes
- FreeTypeFontTest
- FreeTypeTest

### Functions
- nullfont
- surf_same_image

## venv\Lib\site-packages\pygame\tests\ftfont_tags.py

## venv\Lib\site-packages\pygame\tests\ftfont_test.py

## venv\Lib\site-packages\pygame\tests\gfxdraw_test.py

### Classes
- GfxdrawDefaultTest

### Functions
- intensity

## venv\Lib\site-packages\pygame\tests\image__save_gl_surface_test.py

### Classes
- GL_ImageSave

## venv\Lib\site-packages\pygame\tests\image_tags.py

## venv\Lib\site-packages\pygame\tests\image_test.py

### Classes
- ImageModuleTest

### Functions
- test_magic

## venv\Lib\site-packages\pygame\tests\imageext_tags.py

## venv\Lib\site-packages\pygame\tests\imageext_test.py

### Classes
- ImageextModuleTest

## venv\Lib\site-packages\pygame\tests\joystick_test.py

### Classes
- JoystickTypeTest
- JoystickModuleTest
- JoystickInteractiveTest

## venv\Lib\site-packages\pygame\tests\key_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\locals_test.py

### Classes
- LocalsTest

## venv\Lib\site-packages\pygame\tests\mask_test.py

### Classes
- MaskTypeTest
- SubMask
- SubMaskCopy
- SubMaskDunderCopy
- SubMaskCopyAndDunderCopy
- MaskSubclassTest
- MaskModuleTest

### Functions
- random_mask
- maskFromSurface
- create_bounding_rect
- zero_size_pairs
- corners
- off_corners
- assertSurfaceFilled
- assertSurfaceFilledIgnoreArea
- assertMaskEqual

## venv\Lib\site-packages\pygame\tests\math_test.py

### Classes
- MathModuleTest
- Vector2TypeTest
- Vector3TypeTest

## venv\Lib\site-packages\pygame\tests\midi_test.py

### Classes
- MidiInputTest
- MidiOutputTest
- MidiModuleTest
- MidiModuleNonInteractiveTest

## venv\Lib\site-packages\pygame\tests\mixer_music_tags.py

## venv\Lib\site-packages\pygame\tests\mixer_music_test.py

### Classes
- MixerMusicModuleTest

## venv\Lib\site-packages\pygame\tests\mixer_tags.py

## venv\Lib\site-packages\pygame\tests\mixer_test.py

### Classes
- InvalidBool
- MixerModuleTest
- ChannelTypeTest
- ChannelSetVolumeTest
- ChannelEndEventTest
- TestSoundPlay
- SoundTypeTest
- TestSoundFadeout
- TestGetBusy

## venv\Lib\site-packages\pygame\tests\mouse_test.py

### Classes
- MouseTests
- MouseModuleInteractiveTest
- MouseModuleTest

## venv\Lib\site-packages\pygame\tests\pixelarray_test.py

### Classes
- TestMixin
- PixelArrayTypeTest
- PixelArrayArrayInterfaceTest
- PixelArrayNewBufferTest

## venv\Lib\site-packages\pygame\tests\pixelcopy_test.py

### Classes
- PixelcopyModuleTest
- PixelCopyTestWithArrayNumpy
- PixelCopyTestWithArrayNewBuf

### Functions
- unsigned32

## venv\Lib\site-packages\pygame\tests\rect_test.py

### Classes
- RectTypeTest
- SubclassTest

### Functions
- _random_int

## venv\Lib\site-packages\pygame\tests\run_tests__tests\__init__.py

## venv\Lib\site-packages\pygame\tests\run_tests__tests\all_ok\__init__.py

## venv\Lib\site-packages\pygame\tests\run_tests__tests\all_ok\fake_2_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\all_ok\fake_3_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\all_ok\fake_4_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\all_ok\fake_5_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\all_ok\fake_6_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\all_ok\no_assertions__ret_code_of_1__test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\all_ok\zero_tests_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\everything\__init__.py

## venv\Lib\site-packages\pygame\tests\run_tests__tests\everything\fake_2_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\everything\incomplete_todo_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\everything\magic_tag_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\everything\sleep_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\exclude\__init__.py

## venv\Lib\site-packages\pygame\tests\run_tests__tests\exclude\fake_2_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\exclude\invisible_tag_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\exclude\magic_tag_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\failures1\__init__.py

## venv\Lib\site-packages\pygame\tests\run_tests__tests\failures1\fake_2_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\failures1\fake_3_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\failures1\fake_4_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\incomplete\__init__.py

## venv\Lib\site-packages\pygame\tests\run_tests__tests\incomplete\fake_2_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\incomplete\fake_3_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\incomplete_todo\__init__.py

## venv\Lib\site-packages\pygame\tests\run_tests__tests\incomplete_todo\fake_2_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\incomplete_todo\fake_3_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\infinite_loop\__init__.py

## venv\Lib\site-packages\pygame\tests\run_tests__tests\infinite_loop\fake_1_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\infinite_loop\fake_2_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\print_stderr\__init__.py

## venv\Lib\site-packages\pygame\tests\run_tests__tests\print_stderr\fake_2_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\print_stderr\fake_3_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\print_stderr\fake_4_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\print_stdout\__init__.py

## venv\Lib\site-packages\pygame\tests\run_tests__tests\print_stdout\fake_2_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\print_stdout\fake_3_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\print_stdout\fake_4_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\run_tests__test.py

### Functions
- norm_result
- call_proc
- assert_on_results
- all_ok_test
- failures1_test

## venv\Lib\site-packages\pygame\tests\run_tests__tests\timeout\__init__.py

## venv\Lib\site-packages\pygame\tests\run_tests__tests\timeout\fake_2_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\run_tests__tests\timeout\sleep_test.py

### Classes
- KeyModuleTest

## venv\Lib\site-packages\pygame\tests\rwobject_test.py

### Classes
- RWopsEncodeStringTest
- RWopsEncodeFilePathTest

## venv\Lib\site-packages\pygame\tests\scrap_tags.py

## venv\Lib\site-packages\pygame\tests\scrap_test.py

### Classes
- ScrapModuleTest
- ScrapModuleClipboardNotOwnedTest
- X11InteractiveTest

### Functions
- word_wrap
- iwords

## venv\Lib\site-packages\pygame\tests\sndarray_tags.py

## venv\Lib\site-packages\pygame\tests\sndarray_test.py

### Classes
- SndarrayTest

## venv\Lib\site-packages\pygame\tests\sprite_test.py

### Classes
- SpriteModuleTest
- SpriteCollideTest
- AbstractGroupTypeTest
- LayeredGroupBase
- LayeredUpdatesTypeTest__SpriteTest
- LayeredUpdatesTypeTest__DirtySprite
- LayeredDirtyTypeTest__DirtySprite
- SpriteBase
- SpriteTypeTest
- DirtySpriteTypeTest
- WeakSpriteTypeTest
- DirtyWeakSpriteTypeTest
- SingleGroupBugsTest

## venv\Lib\site-packages\pygame\tests\surface_test.py

### Classes
- SurfaceTypeTest
- TestSurfaceBlit
- GeneralSurfaceTests
- SurfaceSubtypeTest
- SurfaceGetBufferTest
- SurfaceBlendTest
- SurfaceSelfBlitTest
- SurfaceFillTest

## venv\Lib\site-packages\pygame\tests\surfarray_tags.py

## venv\Lib\site-packages\pygame\tests\surfarray_test.py

### Classes
- SurfarrayModuleTest

## venv\Lib\site-packages\pygame\tests\surflock_test.py

### Classes
- SurfaceLockTest

## venv\Lib\site-packages\pygame\tests\sysfont_test.py

### Classes
- SysfontModuleTest

## venv\Lib\site-packages\pygame\tests\test_utils\__init__.py

### Classes
- SurfaceSubclass

### Functions
- tostring
- geterror
- trunk_relative_path
- fixture_path
- example_path
- get_tmp_dir
- question
- prompt
- rgba_between
- combinations
- gradient
- rect_area_pts
- rect_perimeter_pts
- rect_outer_bounds
- import_submodule
- test

## venv\Lib\site-packages\pygame\tests\test_utils\arrinter.py

### Classes
- PyArrayInterface
- ArrayInterface
- Exporter
- Array
- ExporterTest
- ArrayTest

### Functions
- capsule_new
- format_flags
- format_shape
- format_strides

## venv\Lib\site-packages\pygame\tests\test_utils\async_sub.py

### Classes
- Popen
- AsyncTest

### Functions
- geterror
- proc_in_time_or_kill

## venv\Lib\site-packages\pygame\tests\test_utils\buftools.py

### Classes
- Exporter
- Importer
- ExporterTest

### Functions
- _prop_get

## venv\Lib\site-packages\pygame\tests\test_utils\endian.py

### Functions
- little_endian_uint32
- big_endian_uint32

## venv\Lib\site-packages\pygame\tests\test_utils\png.py

### Classes
- Error
- FormatError
- ChunkError
- Writer
- Image
- _readable
- Reader
- Test

### Functions
- group
- isarray
- interleave_planes
- check_palette
- write_chunk
- write_chunks
- filter_scanline
- from_array
- test
- topngbytes
- testWithIO
- mycallersname
- seqtobytes
- _dehex
- _enhex
- test_suite
- read_pam_header
- read_pnm_header
- write_pnm
- color_triple
- _main

## venv\Lib\site-packages\pygame\tests\test_utils\run_tests.py

### Functions
- run
- count_results
- run_and_exit

## venv\Lib\site-packages\pygame\tests\test_utils\test_machinery.py

### Classes
- PygameTestLoader
- TestTags

## venv\Lib\site-packages\pygame\tests\test_utils\test_runner.py

### Functions
- prepare_test_env
- exclude_callback
- extract_tracebacks
- output_into_dots
- combine_results
- get_test_results
- run_test

## venv\Lib\site-packages\pygame\tests\threads_test.py

### Classes
- WorkerQueueTypeTest
- ThreadsModuleTest

## venv\Lib\site-packages\pygame\tests\time_test.py

### Classes
- ClockTypeTest
- TimeModuleTest

## venv\Lib\site-packages\pygame\tests\touch_test.py

### Classes
- TouchTest
- TouchInteractiveTest

## venv\Lib\site-packages\pygame\tests\transform_test.py

### Classes
- TransformModuleTest
- TransformDisplayModuleTest

### Functions
- show_image
- threshold

## venv\Lib\site-packages\pygame\tests\version_test.py

### Classes
- VersionTest

## venv\Lib\site-packages\pygame\tests\video_test.py

### Classes
- VideoModuleTest

## venv\Lib\site-packages\pygame\threads\__init__.py

### Classes
- WorkerQueue
- FuncResult

### Functions
- init
- quit
- benchmark_workers
- tmap

## venv\Lib\site-packages\pygame\version.py

### Classes
- SoftwareVersion
- PygameVersion
- SDLVersion

## venv\Lib\site-packages\pygments\__init__.py

### Functions
- lex
- format
- highlight

## venv\Lib\site-packages\pygments\__main__.py

## venv\Lib\site-packages\pygments\cmdline.py

### Classes
- HelpFormatter

### Functions
- _parse_options
- _parse_filters
- _print_help
- _print_list
- _print_list_as_json
- main_inner
- main

## venv\Lib\site-packages\pygments\console.py

### Functions
- reset_color
- colorize
- ansiformat

## venv\Lib\site-packages\pygments\filter.py

### Classes
- Filter
- FunctionFilter

### Functions
- apply_filters
- simplefilter

## venv\Lib\site-packages\pygments\filters\__init__.py

### Classes
- CodeTagFilter
- SymbolFilter
- KeywordCaseFilter
- NameHighlightFilter
- ErrorToken
- RaiseOnErrorTokenFilter
- VisibleWhitespaceFilter
- GobbleFilter
- TokenMergeFilter

### Functions
- find_filter_class
- get_filter_by_name
- get_all_filters
- _replace_special

## venv\Lib\site-packages\pygments\formatter.py

### Classes
- Formatter

### Functions
- _lookup_style

## venv\Lib\site-packages\pygments\formatters\__init__.py

### Classes
- _automodule

### Functions
- _fn_matches
- _load_formatters
- get_all_formatters
- find_formatter_class
- get_formatter_by_name
- load_formatter_from_file
- get_formatter_for_filename

## venv\Lib\site-packages\pygments\formatters\_mapping.py

## venv\Lib\site-packages\pygments\formatters\bbcode.py

### Classes
- BBCodeFormatter

## venv\Lib\site-packages\pygments\formatters\groff.py

### Classes
- GroffFormatter

## venv\Lib\site-packages\pygments\formatters\html.py

### Classes
- HtmlFormatter

### Functions
- escape_html
- webify
- _get_ttype_class

## venv\Lib\site-packages\pygments\formatters\img.py

### Classes
- PilNotAvailable
- FontNotFound
- FontManager
- ImageFormatter
- GifImageFormatter
- JpgImageFormatter
- BmpImageFormatter

## venv\Lib\site-packages\pygments\formatters\irc.py

### Classes
- IRCFormatter

### Functions
- ircformat

## venv\Lib\site-packages\pygments\formatters\latex.py

### Classes
- LatexFormatter
- LatexEmbeddedLexer

### Functions
- escape_tex
- _get_ttype_name

## venv\Lib\site-packages\pygments\formatters\other.py

### Classes
- NullFormatter
- RawTokenFormatter
- TestcaseFormatter

## venv\Lib\site-packages\pygments\formatters\pangomarkup.py

### Classes
- PangoMarkupFormatter

### Functions
- escape_special_chars

## venv\Lib\site-packages\pygments\formatters\rtf.py

### Classes
- RtfFormatter

## venv\Lib\site-packages\pygments\formatters\svg.py

### Classes
- SvgFormatter

### Functions
- escape_html

## venv\Lib\site-packages\pygments\formatters\terminal.py

### Classes
- TerminalFormatter

## venv\Lib\site-packages\pygments\formatters\terminal256.py

### Classes
- EscapeSequence
- Terminal256Formatter
- TerminalTrueColorFormatter

## venv\Lib\site-packages\pygments\lexer.py

### Classes
- LexerMeta
- Lexer
- DelegatingLexer
- include
- _inherit
- combined
- _PseudoMatch
- _This
- default
- words
- RegexLexerMeta
- RegexLexer
- LexerContext
- ExtendedRegexLexer
- ProfilingRegexLexerMeta
- ProfilingRegexLexer

### Functions
- bygroups
- using
- do_insertions

## venv\Lib\site-packages\pygments\lexers\__init__.py

### Classes
- _automodule

### Functions
- _fn_matches
- _load_lexers
- get_all_lexers
- find_lexer_class
- find_lexer_class_by_name
- get_lexer_by_name
- load_lexer_from_file
- find_lexer_class_for_filename
- get_lexer_for_filename
- get_lexer_for_mimetype
- _iter_lexerclasses
- guess_lexer_for_filename
- guess_lexer

## venv\Lib\site-packages\pygments\lexers\_ada_builtins.py

## venv\Lib\site-packages\pygments\lexers\_asy_builtins.py

## venv\Lib\site-packages\pygments\lexers\_cl_builtins.py

## venv\Lib\site-packages\pygments\lexers\_cocoa_builtins.py

## venv\Lib\site-packages\pygments\lexers\_csound_builtins.py

## venv\Lib\site-packages\pygments\lexers\_css_builtins.py

## venv\Lib\site-packages\pygments\lexers\_googlesql_builtins.py

## venv\Lib\site-packages\pygments\lexers\_julia_builtins.py

## venv\Lib\site-packages\pygments\lexers\_lasso_builtins.py

## venv\Lib\site-packages\pygments\lexers\_lilypond_builtins.py

## venv\Lib\site-packages\pygments\lexers\_lua_builtins.py

## venv\Lib\site-packages\pygments\lexers\_luau_builtins.py

## venv\Lib\site-packages\pygments\lexers\_mapping.py

## venv\Lib\site-packages\pygments\lexers\_mql_builtins.py

## venv\Lib\site-packages\pygments\lexers\_mysql_builtins.py

## venv\Lib\site-packages\pygments\lexers\_openedge_builtins.py

## venv\Lib\site-packages\pygments\lexers\_php_builtins.py

## venv\Lib\site-packages\pygments\lexers\_postgres_builtins.py

## venv\Lib\site-packages\pygments\lexers\_qlik_builtins.py

## venv\Lib\site-packages\pygments\lexers\_scheme_builtins.py

## venv\Lib\site-packages\pygments\lexers\_scilab_builtins.py

## venv\Lib\site-packages\pygments\lexers\_sourcemod_builtins.py

## venv\Lib\site-packages\pygments\lexers\_sql_builtins.py

## venv\Lib\site-packages\pygments\lexers\_stan_builtins.py

## venv\Lib\site-packages\pygments\lexers\_stata_builtins.py

## venv\Lib\site-packages\pygments\lexers\_tsql_builtins.py

## venv\Lib\site-packages\pygments\lexers\_usd_builtins.py

## venv\Lib\site-packages\pygments\lexers\_vbscript_builtins.py

## venv\Lib\site-packages\pygments\lexers\_vim_builtins.py

### Functions
- _getauto
- _getcommand
- _getoption

## venv\Lib\site-packages\pygments\lexers\actionscript.py

### Classes
- ActionScriptLexer
- ActionScript3Lexer
- MxmlLexer

## venv\Lib\site-packages\pygments\lexers\ada.py

### Classes
- AdaLexer

## venv\Lib\site-packages\pygments\lexers\agile.py

## venv\Lib\site-packages\pygments\lexers\algebra.py

### Classes
- GAPLexer
- GAPConsoleLexer
- MathematicaLexer
- MuPADLexer
- BCLexer

## venv\Lib\site-packages\pygments\lexers\ambient.py

### Classes
- AmbientTalkLexer

## venv\Lib\site-packages\pygments\lexers\amdgpu.py

### Classes
- AMDGPULexer

## venv\Lib\site-packages\pygments\lexers\ampl.py

### Classes
- AmplLexer

## venv\Lib\site-packages\pygments\lexers\apdlexer.py

### Classes
- apdlexer

## venv\Lib\site-packages\pygments\lexers\apl.py

### Classes
- APLLexer

## venv\Lib\site-packages\pygments\lexers\archetype.py

### Classes
- AtomsLexer
- OdinLexer
- CadlLexer
- AdlLexer

## venv\Lib\site-packages\pygments\lexers\arrow.py

### Classes
- ArrowLexer

## venv\Lib\site-packages\pygments\lexers\arturo.py

### Classes
- ArturoLexer

## venv\Lib\site-packages\pygments\lexers\asc.py

### Classes
- AscLexer

## venv\Lib\site-packages\pygments\lexers\asm.py

### Classes
- GasLexer
- ObjdumpLexer
- DObjdumpLexer
- CppObjdumpLexer
- CObjdumpLexer
- HsailLexer
- LlvmLexer
- LlvmMirBodyLexer
- LlvmMirLexer
- NasmLexer
- NasmObjdumpLexer
- TasmLexer
- Ca65Lexer
- Dasm16Lexer

### Functions
- _objdump_lexer_tokens

## venv\Lib\site-packages\pygments\lexers\asn1.py

### Classes
- Asn1Lexer

### Functions
- word_sequences

## venv\Lib\site-packages\pygments\lexers\automation.py

### Classes
- AutohotkeyLexer
- AutoItLexer

## venv\Lib\site-packages\pygments\lexers\bare.py

### Classes
- BareLexer

## venv\Lib\site-packages\pygments\lexers\basic.py

### Classes
- BlitzMaxLexer
- BlitzBasicLexer
- MonkeyLexer
- CbmBasicV2Lexer
- QBasicLexer
- VBScriptLexer
- BBCBasicLexer

## venv\Lib\site-packages\pygments\lexers\bdd.py

### Classes
- BddLexer

## venv\Lib\site-packages\pygments\lexers\berry.py

### Classes
- BerryLexer

## venv\Lib\site-packages\pygments\lexers\bibtex.py

### Classes
- BibTeXLexer
- BSTLexer

## venv\Lib\site-packages\pygments\lexers\blueprint.py

### Classes
- BlueprintLexer

## venv\Lib\site-packages\pygments\lexers\boa.py

### Classes
- BoaLexer

## venv\Lib\site-packages\pygments\lexers\bqn.py

### Classes
- BQNLexer

## venv\Lib\site-packages\pygments\lexers\business.py

### Classes
- CobolLexer
- CobolFreeformatLexer
- ABAPLexer
- OpenEdgeLexer
- GoodDataCLLexer
- MaqlLexer

## venv\Lib\site-packages\pygments\lexers\c_cpp.py

### Classes
- CFamilyLexer
- CLexer
- CppLexer

## venv\Lib\site-packages\pygments\lexers\c_like.py

### Classes
- PikeLexer
- NesCLexer
- ClayLexer
- ECLexer
- ValaLexer
- CudaLexer
- SwigLexer
- MqlLexer
- ArduinoLexer
- CharmciLexer
- OmgIdlLexer
- PromelaLexer

## venv\Lib\site-packages\pygments\lexers\capnproto.py

### Classes
- CapnProtoLexer

## venv\Lib\site-packages\pygments\lexers\carbon.py

### Classes
- CarbonLexer

## venv\Lib\site-packages\pygments\lexers\cddl.py

### Classes
- CddlLexer

## venv\Lib\site-packages\pygments\lexers\chapel.py

### Classes
- ChapelLexer

## venv\Lib\site-packages\pygments\lexers\clean.py

### Classes
- CleanLexer

## venv\Lib\site-packages\pygments\lexers\codeql.py

### Classes
- CodeQLLexer

## venv\Lib\site-packages\pygments\lexers\comal.py

### Classes
- Comal80Lexer

## venv\Lib\site-packages\pygments\lexers\compiled.py

## venv\Lib\site-packages\pygments\lexers\configs.py

### Classes
- IniLexer
- DesktopLexer
- SystemdLexer
- RegeditLexer
- PropertiesLexer
- KconfigLexer
- Cfengine3Lexer
- ApacheConfLexer
- SquidConfLexer
- NginxConfLexer
- LighttpdConfLexer
- DockerLexer
- TerraformLexer
- TermcapLexer
- TerminfoLexer
- PkgConfigLexer
- PacmanConfLexer
- AugeasLexer
- TOMLLexer
- NestedTextLexer
- SingularityLexer
- UnixConfigLexer

### Functions
- _rx_indent

## venv\Lib\site-packages\pygments\lexers\console.py

### Classes
- VCTreeStatusLexer
- PyPyLogLexer

## venv\Lib\site-packages\pygments\lexers\cplint.py

### Classes
- CplintLexer

## venv\Lib\site-packages\pygments\lexers\crystal.py

### Classes
- CrystalLexer

## venv\Lib\site-packages\pygments\lexers\csound.py

### Classes
- CsoundLexer
- CsoundScoreLexer
- CsoundOrchestraLexer
- CsoundDocumentLexer

## venv\Lib\site-packages\pygments\lexers\css.py

### Classes
- CssLexer
- SassLexer
- ScssLexer
- LessCssLexer

### Functions
- _indentation
- _starts_block

## venv\Lib\site-packages\pygments\lexers\d.py

### Classes
- DLexer
- CrocLexer
- MiniDLexer

## venv\Lib\site-packages\pygments\lexers\dalvik.py

### Classes
- SmaliLexer

## venv\Lib\site-packages\pygments\lexers\data.py

### Classes
- YamlLexerContext
- YamlLexer
- JsonLexer
- JsonBareObjectLexer
- JsonLdLexer

## venv\Lib\site-packages\pygments\lexers\dax.py

### Classes
- DaxLexer

## venv\Lib\site-packages\pygments\lexers\devicetree.py

### Classes
- DevicetreeLexer

## venv\Lib\site-packages\pygments\lexers\diff.py

### Classes
- DiffLexer
- DarcsPatchLexer
- WDiffLexer

## venv\Lib\site-packages\pygments\lexers\dns.py

### Classes
- DnsZoneLexer

## venv\Lib\site-packages\pygments\lexers\dotnet.py

### Classes
- CSharpLexer
- NemerleLexer
- BooLexer
- VbNetLexer
- GenericAspxLexer
- CSharpAspxLexer
- VbNetAspxLexer
- FSharpLexer
- XppLexer

## venv\Lib\site-packages\pygments\lexers\dsls.py

### Classes
- ProtoBufLexer
- ThriftLexer
- ZeekLexer
- PuppetLexer
- RslLexer
- MscgenLexer
- VGLLexer
- AlloyLexer
- PanLexer
- CrmshLexer
- FlatlineLexer
- SnowballLexer

## venv\Lib\site-packages\pygments\lexers\dylan.py

### Classes
- DylanLexer
- DylanLidLexer
- DylanConsoleLexer

## venv\Lib\site-packages\pygments\lexers\ecl.py

### Classes
- ECLLexer

## venv\Lib\site-packages\pygments\lexers\eiffel.py

### Classes
- EiffelLexer

## venv\Lib\site-packages\pygments\lexers\elm.py

### Classes
- ElmLexer

## venv\Lib\site-packages\pygments\lexers\elpi.py

### Classes
- ElpiLexer

## venv\Lib\site-packages\pygments\lexers\email.py

### Classes
- EmailHeaderLexer
- EmailLexer

## venv\Lib\site-packages\pygments\lexers\erlang.py

### Classes
- ErlangLexer
- ErlangShellLexer
- ElixirLexer
- ElixirConsoleLexer

### Functions
- gen_elixir_string_rules
- gen_elixir_sigstr_rules

## venv\Lib\site-packages\pygments\lexers\esoteric.py

### Classes
- BrainfuckLexer
- BefungeLexer
- CAmkESLexer
- CapDLLexer
- RedcodeLexer
- AheuiLexer

## venv\Lib\site-packages\pygments\lexers\ezhil.py

### Classes
- EzhilLexer

## venv\Lib\site-packages\pygments\lexers\factor.py

### Classes
- FactorLexer

## venv\Lib\site-packages\pygments\lexers\fantom.py

### Classes
- FantomLexer

## venv\Lib\site-packages\pygments\lexers\felix.py

### Classes
- FelixLexer

## venv\Lib\site-packages\pygments\lexers\fift.py

### Classes
- FiftLexer

## venv\Lib\site-packages\pygments\lexers\floscript.py

### Classes
- FloScriptLexer

## venv\Lib\site-packages\pygments\lexers\forth.py

### Classes
- ForthLexer

## venv\Lib\site-packages\pygments\lexers\fortran.py

### Classes
- FortranLexer
- FortranFixedLexer

## venv\Lib\site-packages\pygments\lexers\foxpro.py

### Classes
- FoxProLexer

## venv\Lib\site-packages\pygments\lexers\freefem.py

### Classes
- FreeFemLexer

## venv\Lib\site-packages\pygments\lexers\func.py

### Classes
- FuncLexer

## venv\Lib\site-packages\pygments\lexers\functional.py

## venv\Lib\site-packages\pygments\lexers\futhark.py

### Classes
- FutharkLexer

## venv\Lib\site-packages\pygments\lexers\gcodelexer.py

### Classes
- GcodeLexer

## venv\Lib\site-packages\pygments\lexers\gdscript.py

### Classes
- GDScriptLexer

## venv\Lib\site-packages\pygments\lexers\gleam.py

### Classes
- GleamLexer

## venv\Lib\site-packages\pygments\lexers\go.py

### Classes
- GoLexer

## venv\Lib\site-packages\pygments\lexers\grammar_notation.py

### Classes
- BnfLexer
- AbnfLexer
- JsgfLexer
- PegLexer

## venv\Lib\site-packages\pygments\lexers\graph.py

### Classes
- CypherLexer

## venv\Lib\site-packages\pygments\lexers\graphics.py

### Classes
- GLShaderLexer
- HLSLShaderLexer
- PostScriptLexer
- AsymptoteLexer
- GnuplotLexer
- PovrayLexer

### Functions
- _shortened
- _shortened_many

## venv\Lib\site-packages\pygments\lexers\graphql.py

### Classes
- GraphQLLexer

## venv\Lib\site-packages\pygments\lexers\graphviz.py

### Classes
- GraphvizLexer

## venv\Lib\site-packages\pygments\lexers\gsql.py

### Classes
- GSQLLexer

## venv\Lib\site-packages\pygments\lexers\hare.py

### Classes
- HareLexer

## venv\Lib\site-packages\pygments\lexers\haskell.py

### Classes
- HaskellLexer
- HspecLexer
- IdrisLexer
- AgdaLexer
- CryptolLexer
- LiterateLexer
- LiterateHaskellLexer
- LiterateIdrisLexer
- LiterateAgdaLexer
- LiterateCryptolLexer
- KokaLexer

## venv\Lib\site-packages\pygments\lexers\haxe.py

### Classes
- HaxeLexer
- HxmlLexer

## venv\Lib\site-packages\pygments\lexers\hdl.py

### Classes
- VerilogLexer
- SystemVerilogLexer
- VhdlLexer

## venv\Lib\site-packages\pygments\lexers\hexdump.py

### Classes
- HexdumpLexer

## venv\Lib\site-packages\pygments\lexers\html.py

### Classes
- HtmlLexer
- DtdLexer
- XmlLexer
- XsltLexer
- HamlLexer
- ScamlLexer
- PugLexer
- UrlEncodedLexer
- VueLexer

## venv\Lib\site-packages\pygments\lexers\idl.py

### Classes
- IDLLexer

## venv\Lib\site-packages\pygments\lexers\igor.py

### Classes
- IgorLexer

## venv\Lib\site-packages\pygments\lexers\inferno.py

### Classes
- LimboLexer

## venv\Lib\site-packages\pygments\lexers\installers.py

### Classes
- NSISLexer
- RPMSpecLexer
- DebianSourcesLexer
- SourcesListLexer
- DebianControlLexer

## venv\Lib\site-packages\pygments\lexers\int_fiction.py

### Classes
- Inform6Lexer
- Inform7Lexer
- Inform6TemplateLexer
- Tads3Lexer

## venv\Lib\site-packages\pygments\lexers\iolang.py

### Classes
- IoLexer

## venv\Lib\site-packages\pygments\lexers\j.py

### Classes
- JLexer

## venv\Lib\site-packages\pygments\lexers\javascript.py

### Classes
- JavascriptLexer
- TypeScriptLexer
- KalLexer
- LiveScriptLexer
- DartLexer
- LassoLexer
- ObjectiveJLexer
- CoffeeScriptLexer
- MaskLexer
- EarlGreyLexer
- JuttleLexer
- NodeConsoleLexer

## venv\Lib\site-packages\pygments\lexers\jmespath.py

### Classes
- JMESPathLexer

## venv\Lib\site-packages\pygments\lexers\jslt.py

### Classes
- JSLTLexer

## venv\Lib\site-packages\pygments\lexers\json5.py

### Classes
- Json5Lexer

### Functions
- string_rules
- quoted_field_name

## venv\Lib\site-packages\pygments\lexers\jsonnet.py

### Classes
- JsonnetLexer

### Functions
- string_rules
- quoted_field_name

## venv\Lib\site-packages\pygments\lexers\jsx.py

### Classes
- JsxLexer
- TsxLexer

## venv\Lib\site-packages\pygments\lexers\julia.py

### Classes
- JuliaLexer
- JuliaConsoleLexer

## venv\Lib\site-packages\pygments\lexers\jvm.py

### Classes
- JavaLexer
- AspectJLexer
- ScalaLexer
- GosuLexer
- GosuTemplateLexer
- GroovyLexer
- IokeLexer
- ClojureLexer
- ClojureScriptLexer
- TeaLangLexer
- CeylonLexer
- KotlinLexer
- XtendLexer
- PigLexer
- GoloLexer
- JasminLexer
- SarlLexer

## venv\Lib\site-packages\pygments\lexers\kuin.py

### Classes
- KuinLexer

## venv\Lib\site-packages\pygments\lexers\kusto.py

### Classes
- KustoLexer

## venv\Lib\site-packages\pygments\lexers\ldap.py

### Classes
- LdifLexer
- LdaprcLexer

## venv\Lib\site-packages\pygments\lexers\lean.py

### Classes
- Lean3Lexer
- Lean4Lexer

## venv\Lib\site-packages\pygments\lexers\lilypond.py

### Classes
- LilyPondLexer

### Functions
- builtin_words

## venv\Lib\site-packages\pygments\lexers\lisp.py

### Classes
- SchemeLexer
- CommonLispLexer
- HyLexer
- RacketLexer
- NewLispLexer
- EmacsLispLexer
- ShenLexer
- CPSALexer
- XtlangLexer
- FennelLexer
- JanetLexer

## venv\Lib\site-packages\pygments\lexers\macaulay2.py

### Classes
- Macaulay2Lexer

## venv\Lib\site-packages\pygments\lexers\make.py

### Classes
- MakefileLexer
- BaseMakefileLexer
- CMakeLexer

## venv\Lib\site-packages\pygments\lexers\maple.py

### Classes
- MapleLexer

## venv\Lib\site-packages\pygments\lexers\markup.py

### Classes
- BBCodeLexer
- MoinWikiLexer
- RstLexer
- TexLexer
- GroffLexer
- MozPreprocHashLexer
- MozPreprocPercentLexer
- MozPreprocXulLexer
- MozPreprocJavascriptLexer
- MozPreprocCssLexer
- MarkdownLexer
- OrgLexer
- TiddlyWiki5Lexer
- WikitextLexer

## venv\Lib\site-packages\pygments\lexers\math.py

## venv\Lib\site-packages\pygments\lexers\matlab.py

### Classes
- MatlabLexer
- MatlabSessionLexer
- OctaveLexer
- ScilabLexer

## venv\Lib\site-packages\pygments\lexers\maxima.py

### Classes
- MaximaLexer

## venv\Lib\site-packages\pygments\lexers\meson.py

### Classes
- MesonLexer

## venv\Lib\site-packages\pygments\lexers\mime.py

### Classes
- MIMELexer

## venv\Lib\site-packages\pygments\lexers\minecraft.py

### Classes
- SNBTLexer
- MCFunctionLexer
- MCSchemaLexer

## venv\Lib\site-packages\pygments\lexers\mips.py

### Classes
- MIPSLexer

## venv\Lib\site-packages\pygments\lexers\ml.py

### Classes
- SMLLexer
- OcamlLexer
- OpaLexer
- ReasonLexer
- FStarLexer

## venv\Lib\site-packages\pygments\lexers\modeling.py

### Classes
- ModelicaLexer
- BugsLexer
- JagsLexer
- StanLexer

## venv\Lib\site-packages\pygments\lexers\modula2.py

### Classes
- Modula2Lexer

## venv\Lib\site-packages\pygments\lexers\mojo.py

### Classes
- MojoLexer

## venv\Lib\site-packages\pygments\lexers\monte.py

### Classes
- MonteLexer

## venv\Lib\site-packages\pygments\lexers\mosel.py

### Classes
- MoselLexer

## venv\Lib\site-packages\pygments\lexers\ncl.py

### Classes
- NCLLexer

## venv\Lib\site-packages\pygments\lexers\nimrod.py

### Classes
- NimrodLexer

## venv\Lib\site-packages\pygments\lexers\nit.py

### Classes
- NitLexer

## venv\Lib\site-packages\pygments\lexers\nix.py

### Classes
- NixLexer

## venv\Lib\site-packages\pygments\lexers\numbair.py

### Classes
- NumbaIRLexer

## venv\Lib\site-packages\pygments\lexers\oberon.py

### Classes
- ComponentPascalLexer

## venv\Lib\site-packages\pygments\lexers\objective.py

### Classes
- ObjectiveCLexer
- ObjectiveCppLexer
- LogosLexer
- SwiftLexer

### Functions
- objective

## venv\Lib\site-packages\pygments\lexers\ooc.py

### Classes
- OocLexer

## venv\Lib\site-packages\pygments\lexers\openscad.py

### Classes
- OpenScadLexer

## venv\Lib\site-packages\pygments\lexers\other.py

## venv\Lib\site-packages\pygments\lexers\parasail.py

### Classes
- ParaSailLexer

## venv\Lib\site-packages\pygments\lexers\parsers.py

### Classes
- RagelLexer
- RagelEmbeddedLexer
- RagelRubyLexer
- RagelCLexer
- RagelDLexer
- RagelCppLexer
- RagelObjectiveCLexer
- RagelJavaLexer
- AntlrLexer
- AntlrCppLexer
- AntlrObjectiveCLexer
- AntlrCSharpLexer
- AntlrPythonLexer
- AntlrJavaLexer
- AntlrRubyLexer
- AntlrPerlLexer
- AntlrActionScriptLexer
- TreetopBaseLexer
- TreetopLexer
- EbnfLexer

## venv\Lib\site-packages\pygments\lexers\pascal.py

### Classes
- PortugolLexer
- DelphiLexer

## venv\Lib\site-packages\pygments\lexers\pawn.py

### Classes
- SourcePawnLexer
- PawnLexer

## venv\Lib\site-packages\pygments\lexers\pddl.py

### Classes
- PddlLexer

## venv\Lib\site-packages\pygments\lexers\perl.py

### Classes
- PerlLexer
- Perl6Lexer

## venv\Lib\site-packages\pygments\lexers\phix.py

### Classes
- PhixLexer

## venv\Lib\site-packages\pygments\lexers\php.py

### Classes
- ZephirLexer
- PsyshConsoleLexer
- PhpLexer

## venv\Lib\site-packages\pygments\lexers\pointless.py

### Classes
- PointlessLexer

## venv\Lib\site-packages\pygments\lexers\pony.py

### Classes
- PonyLexer

## venv\Lib\site-packages\pygments\lexers\praat.py

### Classes
- PraatLexer

## venv\Lib\site-packages\pygments\lexers\procfile.py

### Classes
- ProcfileLexer

## venv\Lib\site-packages\pygments\lexers\prolog.py

### Classes
- PrologLexer
- LogtalkLexer

## venv\Lib\site-packages\pygments\lexers\promql.py

### Classes
- PromQLLexer

## venv\Lib\site-packages\pygments\lexers\prql.py

### Classes
- PrqlLexer

## venv\Lib\site-packages\pygments\lexers\ptx.py

### Classes
- PtxLexer

## venv\Lib\site-packages\pygments\lexers\python.py

### Classes
- PythonLexer
- Python2Lexer
- _PythonConsoleLexerBase
- PythonConsoleLexer
- PythonTracebackLexer
- Python2TracebackLexer
- CythonLexer
- DgLexer
- NumPyLexer

## venv\Lib\site-packages\pygments\lexers\q.py

### Classes
- KLexer
- QLexer

## venv\Lib\site-packages\pygments\lexers\qlik.py

### Classes
- QlikLexer

## venv\Lib\site-packages\pygments\lexers\qvt.py

### Classes
- QVToLexer

## venv\Lib\site-packages\pygments\lexers\r.py

### Classes
- RConsoleLexer
- SLexer
- RdLexer

## venv\Lib\site-packages\pygments\lexers\rdf.py

### Classes
- SparqlLexer
- TurtleLexer
- ShExCLexer

## venv\Lib\site-packages\pygments\lexers\rebol.py

### Classes
- RebolLexer
- RedLexer

## venv\Lib\site-packages\pygments\lexers\rego.py

### Classes
- RegoLexer

## venv\Lib\site-packages\pygments\lexers\rell.py

### Classes
- RellLexer

## venv\Lib\site-packages\pygments\lexers\resource.py

### Classes
- ResourceLexer

## venv\Lib\site-packages\pygments\lexers\ride.py

### Classes
- RideLexer

## venv\Lib\site-packages\pygments\lexers\rita.py

### Classes
- RitaLexer

## venv\Lib\site-packages\pygments\lexers\rnc.py

### Classes
- RNCCompactLexer

## venv\Lib\site-packages\pygments\lexers\roboconf.py

### Classes
- RoboconfGraphLexer
- RoboconfInstancesLexer

## venv\Lib\site-packages\pygments\lexers\robotframework.py

### Classes
- RobotFrameworkLexer
- VariableTokenizer
- RowTokenizer
- RowSplitter
- Tokenizer
- Comment
- Setting
- ImportSetting
- TestCaseSetting
- KeywordSetting
- Variable
- KeywordCall
- GherkinTokenizer
- TemplatedKeywordCall
- ForLoop
- _Table
- UnknownTable
- VariableTable
- SettingTable
- TestCaseTable
- KeywordTable
- VariableSplitter

### Functions
- normalize

## venv\Lib\site-packages\pygments\lexers\ruby.py

### Classes
- RubyLexer
- RubyConsoleLexer
- FancyLexer

## venv\Lib\site-packages\pygments\lexers\rust.py

### Classes
- RustLexer

## venv\Lib\site-packages\pygments\lexers\sas.py

### Classes
- SASLexer

## venv\Lib\site-packages\pygments\lexers\savi.py

### Classes
- SaviLexer

## venv\Lib\site-packages\pygments\lexers\scdoc.py

### Classes
- ScdocLexer

## venv\Lib\site-packages\pygments\lexers\scripting.py

### Classes
- LuaLexer
- LuauLexer
- MoonScriptLexer
- ChaiscriptLexer
- LSLLexer
- AppleScriptLexer
- RexxLexer
- MOOCodeLexer
- HybrisLexer
- EasytrieveLexer
- JclLexer
- MiniScriptLexer

### Functions
- all_lua_builtins
- _luau_make_expression
- _luau_make_expression_special

## venv\Lib\site-packages\pygments\lexers\sgf.py

### Classes
- SmartGameFormatLexer

## venv\Lib\site-packages\pygments\lexers\shell.py

### Classes
- BashLexer
- SlurmBashLexer
- ShellSessionBaseLexer
- BashSessionLexer
- BatchLexer
- MSDOSSessionLexer
- TcshLexer
- TcshSessionLexer
- PowerShellLexer
- PowerShellSessionLexer
- FishShellLexer
- ExeclineLexer

## venv\Lib\site-packages\pygments\lexers\sieve.py

### Classes
- SieveLexer

## venv\Lib\site-packages\pygments\lexers\slash.py

### Classes
- SlashLanguageLexer
- SlashLexer

## venv\Lib\site-packages\pygments\lexers\smalltalk.py

### Classes
- SmalltalkLexer
- NewspeakLexer

## venv\Lib\site-packages\pygments\lexers\smithy.py

### Classes
- SmithyLexer

## venv\Lib\site-packages\pygments\lexers\smv.py

### Classes
- NuSMVLexer

## venv\Lib\site-packages\pygments\lexers\snobol.py

### Classes
- SnobolLexer

## venv\Lib\site-packages\pygments\lexers\solidity.py

### Classes
- SolidityLexer

## venv\Lib\site-packages\pygments\lexers\soong.py

### Classes
- SoongLexer

## venv\Lib\site-packages\pygments\lexers\sophia.py

### Classes
- SophiaLexer

## venv\Lib\site-packages\pygments\lexers\special.py

### Classes
- TextLexer
- OutputLexer
- RawTokenLexer

## venv\Lib\site-packages\pygments\lexers\spice.py

### Classes
- SpiceLexer

## venv\Lib\site-packages\pygments\lexers\sql.py

### Classes
- PostgresBase
- PostgresLexer
- PlPgsqlLexer
- PsqlRegexLexer
- lookahead
- PostgresConsoleLexer
- PostgresExplainLexer
- SqlLexer
- TransactSqlLexer
- MySqlLexer
- GoogleSqlLexer
- SqliteConsoleLexer
- RqlLexer

### Functions
- language_callback

## venv\Lib\site-packages\pygments\lexers\srcinfo.py

### Classes
- SrcinfoLexer

## venv\Lib\site-packages\pygments\lexers\stata.py

### Classes
- StataLexer

## venv\Lib\site-packages\pygments\lexers\supercollider.py

### Classes
- SuperColliderLexer

## venv\Lib\site-packages\pygments\lexers\tablegen.py

### Classes
- TableGenLexer

## venv\Lib\site-packages\pygments\lexers\tact.py

### Classes
- TactLexer

## venv\Lib\site-packages\pygments\lexers\tal.py

### Classes
- TalLexer

## venv\Lib\site-packages\pygments\lexers\tcl.py

### Classes
- TclLexer

## venv\Lib\site-packages\pygments\lexers\teal.py

### Classes
- TealLexer

## venv\Lib\site-packages\pygments\lexers\templates.py

### Classes
- ErbLexer
- SmartyLexer
- VelocityLexer
- VelocityHtmlLexer
- VelocityXmlLexer
- DjangoLexer
- MyghtyLexer
- MyghtyHtmlLexer
- MyghtyXmlLexer
- MyghtyJavascriptLexer
- MyghtyCssLexer
- MasonLexer
- MakoLexer
- MakoHtmlLexer
- MakoXmlLexer
- MakoJavascriptLexer
- MakoCssLexer
- CheetahPythonLexer
- CheetahLexer
- CheetahHtmlLexer
- CheetahXmlLexer
- CheetahJavascriptLexer
- GenshiTextLexer
- GenshiMarkupLexer
- HtmlGenshiLexer
- GenshiLexer
- JavascriptGenshiLexer
- CssGenshiLexer
- RhtmlLexer
- XmlErbLexer
- CssErbLexer
- JavascriptErbLexer
- HtmlPhpLexer
- XmlPhpLexer
- CssPhpLexer
- JavascriptPhpLexer
- HtmlSmartyLexer
- XmlSmartyLexer
- CssSmartyLexer
- JavascriptSmartyLexer
- HtmlDjangoLexer
- XmlDjangoLexer
- CssDjangoLexer
- JavascriptDjangoLexer
- JspRootLexer
- JspLexer
- EvoqueLexer
- EvoqueHtmlLexer
- EvoqueXmlLexer
- ColdfusionLexer
- ColdfusionMarkupLexer
- ColdfusionHtmlLexer
- ColdfusionCFCLexer
- SspLexer
- TeaTemplateRootLexer
- TeaTemplateLexer
- LassoHtmlLexer
- LassoXmlLexer
- LassoCssLexer
- LassoJavascriptLexer
- HandlebarsLexer
- HandlebarsHtmlLexer
- YamlJinjaLexer
- LiquidLexer
- TwigLexer
- TwigHtmlLexer
- Angular2Lexer
- Angular2HtmlLexer
- SqlJinjaLexer

## venv\Lib\site-packages\pygments\lexers\teraterm.py

### Classes
- TeraTermLexer

## venv\Lib\site-packages\pygments\lexers\testing.py

### Classes
- GherkinLexer
- TAPLexer

## venv\Lib\site-packages\pygments\lexers\text.py

## venv\Lib\site-packages\pygments\lexers\textedit.py

### Classes
- AwkLexer
- SedLexer
- VimLexer

## venv\Lib\site-packages\pygments\lexers\textfmts.py

### Classes
- IrcLogsLexer
- GettextLexer
- HttpLexer
- TodotxtLexer
- NotmuchLexer
- KernelLogLexer

## venv\Lib\site-packages\pygments\lexers\theorem.py

### Classes
- RocqLexer
- IsabelleLexer

## venv\Lib\site-packages\pygments\lexers\thingsdb.py

### Classes
- ThingsDBLexer

## venv\Lib\site-packages\pygments\lexers\tlb.py

### Classes
- TlbLexer

## venv\Lib\site-packages\pygments\lexers\tls.py

### Classes
- TlsLexer

## venv\Lib\site-packages\pygments\lexers\tnt.py

### Classes
- TNTLexer

## venv\Lib\site-packages\pygments\lexers\trafficscript.py

### Classes
- RtsLexer

## venv\Lib\site-packages\pygments\lexers\typoscript.py

### Classes
- TypoScriptCssDataLexer
- TypoScriptHtmlDataLexer
- TypoScriptLexer

## venv\Lib\site-packages\pygments\lexers\typst.py

### Classes
- TypstLexer

## venv\Lib\site-packages\pygments\lexers\ul4.py

### Classes
- UL4Lexer
- HTMLUL4Lexer
- XMLUL4Lexer
- CSSUL4Lexer
- JavascriptUL4Lexer
- PythonUL4Lexer

## venv\Lib\site-packages\pygments\lexers\unicon.py

### Classes
- UniconLexer
- IconLexer
- UcodeLexer

## venv\Lib\site-packages\pygments\lexers\urbi.py

### Classes
- UrbiscriptLexer

## venv\Lib\site-packages\pygments\lexers\usd.py

### Classes
- UsdLexer

### Functions
- _keywords

## venv\Lib\site-packages\pygments\lexers\varnish.py

### Classes
- VCLLexer
- VCLSnippetLexer

## venv\Lib\site-packages\pygments\lexers\verification.py

### Classes
- BoogieLexer
- SilverLexer

## venv\Lib\site-packages\pygments\lexers\verifpal.py

### Classes
- VerifpalLexer

## venv\Lib\site-packages\pygments\lexers\vip.py

### Classes
- VisualPrologBaseLexer
- VisualPrologLexer
- VisualPrologGrammarLexer

## venv\Lib\site-packages\pygments\lexers\vyper.py

### Classes
- VyperLexer

## venv\Lib\site-packages\pygments\lexers\web.py

## venv\Lib\site-packages\pygments\lexers\webassembly.py

### Classes
- WatLexer

## venv\Lib\site-packages\pygments\lexers\webidl.py

### Classes
- WebIDLLexer

## venv\Lib\site-packages\pygments\lexers\webmisc.py

### Classes
- DuelLexer
- XQueryLexer
- QmlLexer
- CirruLexer
- SlimLexer

## venv\Lib\site-packages\pygments\lexers\wgsl.py

### Classes
- WgslLexer

## venv\Lib\site-packages\pygments\lexers\whiley.py

### Classes
- WhileyLexer

## venv\Lib\site-packages\pygments\lexers\wowtoc.py

### Classes
- WoWTocLexer

### Functions
- _create_tag_line_pattern
- _create_tag_line_token

## venv\Lib\site-packages\pygments\lexers\wren.py

### Classes
- WrenLexer

## venv\Lib\site-packages\pygments\lexers\x10.py

### Classes
- X10Lexer

## venv\Lib\site-packages\pygments\lexers\xorg.py

### Classes
- XorgLexer

## venv\Lib\site-packages\pygments\lexers\yang.py

### Classes
- YangLexer

## venv\Lib\site-packages\pygments\lexers\yara.py

### Classes
- YaraLexer

## venv\Lib\site-packages\pygments\lexers\zig.py

### Classes
- ZigLexer

## venv\Lib\site-packages\pygments\modeline.py

### Functions
- get_filetype_from_line
- get_filetype_from_buffer

## venv\Lib\site-packages\pygments\plugin.py

### Functions
- iter_entry_points
- find_plugin_lexers
- find_plugin_formatters
- find_plugin_styles
- find_plugin_filters

## venv\Lib\site-packages\pygments\regexopt.py

### Functions
- commonprefix
- make_charset
- regex_opt_inner
- regex_opt

## venv\Lib\site-packages\pygments\scanner.py

### Classes
- EndOfText
- Scanner

## venv\Lib\site-packages\pygments\sphinxext.py

### Classes
- PygmentsDoc

### Functions
- setup

## venv\Lib\site-packages\pygments\style.py

### Classes
- StyleMeta
- Style

## venv\Lib\site-packages\pygments\styles\__init__.py

### Functions
- get_style_by_name
- get_all_styles

## venv\Lib\site-packages\pygments\styles\_mapping.py

## venv\Lib\site-packages\pygments\styles\abap.py

### Classes
- AbapStyle

## venv\Lib\site-packages\pygments\styles\algol.py

### Classes
- AlgolStyle

## venv\Lib\site-packages\pygments\styles\algol_nu.py

### Classes
- Algol_NuStyle

## venv\Lib\site-packages\pygments\styles\arduino.py

### Classes
- ArduinoStyle

## venv\Lib\site-packages\pygments\styles\autumn.py

### Classes
- AutumnStyle

## venv\Lib\site-packages\pygments\styles\borland.py

### Classes
- BorlandStyle

## venv\Lib\site-packages\pygments\styles\bw.py

### Classes
- BlackWhiteStyle

## venv\Lib\site-packages\pygments\styles\coffee.py

### Classes
- CoffeeStyle

## venv\Lib\site-packages\pygments\styles\colorful.py

### Classes
- ColorfulStyle

## venv\Lib\site-packages\pygments\styles\default.py

### Classes
- DefaultStyle

## venv\Lib\site-packages\pygments\styles\dracula.py

### Classes
- DraculaStyle

## venv\Lib\site-packages\pygments\styles\emacs.py

### Classes
- EmacsStyle

## venv\Lib\site-packages\pygments\styles\friendly.py

### Classes
- FriendlyStyle

## venv\Lib\site-packages\pygments\styles\friendly_grayscale.py

### Classes
- FriendlyGrayscaleStyle

## venv\Lib\site-packages\pygments\styles\fruity.py

### Classes
- FruityStyle

## venv\Lib\site-packages\pygments\styles\gh_dark.py

### Classes
- GhDarkStyle

## venv\Lib\site-packages\pygments\styles\gruvbox.py

### Classes
- GruvboxDarkStyle
- GruvboxLightStyle

## venv\Lib\site-packages\pygments\styles\igor.py

### Classes
- IgorStyle

## venv\Lib\site-packages\pygments\styles\inkpot.py

### Classes
- InkPotStyle

## venv\Lib\site-packages\pygments\styles\lightbulb.py

### Classes
- LightbulbStyle

## venv\Lib\site-packages\pygments\styles\lilypond.py

### Classes
- LilyPondStyle

## venv\Lib\site-packages\pygments\styles\lovelace.py

### Classes
- LovelaceStyle

## venv\Lib\site-packages\pygments\styles\manni.py

### Classes
- ManniStyle

## venv\Lib\site-packages\pygments\styles\material.py

### Classes
- MaterialStyle

## venv\Lib\site-packages\pygments\styles\monokai.py

### Classes
- MonokaiStyle

## venv\Lib\site-packages\pygments\styles\murphy.py

### Classes
- MurphyStyle

## venv\Lib\site-packages\pygments\styles\native.py

### Classes
- NativeStyle

## venv\Lib\site-packages\pygments\styles\nord.py

### Classes
- NordStyle
- NordDarkerStyle

## venv\Lib\site-packages\pygments\styles\onedark.py

### Classes
- OneDarkStyle

## venv\Lib\site-packages\pygments\styles\paraiso_dark.py

### Classes
- ParaisoDarkStyle

## venv\Lib\site-packages\pygments\styles\paraiso_light.py

### Classes
- ParaisoLightStyle

## venv\Lib\site-packages\pygments\styles\pastie.py

### Classes
- PastieStyle

## venv\Lib\site-packages\pygments\styles\perldoc.py

### Classes
- PerldocStyle

## venv\Lib\site-packages\pygments\styles\rainbow_dash.py

### Classes
- RainbowDashStyle

## venv\Lib\site-packages\pygments\styles\rrt.py

### Classes
- RrtStyle

## venv\Lib\site-packages\pygments\styles\sas.py

### Classes
- SasStyle

## venv\Lib\site-packages\pygments\styles\solarized.py

### Classes
- SolarizedDarkStyle
- SolarizedLightStyle

### Functions
- make_style

## venv\Lib\site-packages\pygments\styles\staroffice.py

### Classes
- StarofficeStyle

## venv\Lib\site-packages\pygments\styles\stata_dark.py

### Classes
- StataDarkStyle

## venv\Lib\site-packages\pygments\styles\stata_light.py

### Classes
- StataLightStyle

## venv\Lib\site-packages\pygments\styles\tango.py

### Classes
- TangoStyle

## venv\Lib\site-packages\pygments\styles\trac.py

### Classes
- TracStyle

## venv\Lib\site-packages\pygments\styles\vim.py

### Classes
- VimStyle

## venv\Lib\site-packages\pygments\styles\vs.py

### Classes
- VisualStudioStyle

## venv\Lib\site-packages\pygments\styles\xcode.py

### Classes
- XcodeStyle

## venv\Lib\site-packages\pygments\styles\zenburn.py

### Classes
- ZenburnStyle

## venv\Lib\site-packages\pygments\token.py

### Classes
- _TokenType

### Functions
- is_token_subtype
- string_to_tokentype

## venv\Lib\site-packages\pygments\unistring.py

### Functions
- combine
- allexcept
- _handle_runs

## venv\Lib\site-packages\pygments\util.py

### Classes
- ClassNotFound
- OptionError
- Future
- UnclosingTextIOWrapper

### Functions
- get_choice_opt
- get_bool_opt
- get_int_opt
- get_list_opt
- docstring_headline
- make_analysator
- shebang_matches
- doctype_matches
- html_doctype_matches
- looks_like_xml
- surrogatepair
- format_lines
- duplicates_removed
- guess_decode
- guess_decode_from_terminal
- terminal_encoding

## venv\Lib\site-packages\pytest\__init__.py

## venv\Lib\site-packages\pytest\__main__.py

## venv\Lib\site-packages\pytest_cov\__init__.py

### Classes
- CoverageError
- PytestCovWarning
- CovDisabledWarning
- CovReportWarning
- CentralCovContextWarning
- DistCovError

## venv\Lib\site-packages\pytest_cov\engine.py

### Classes
- BrokenCovConfigError
- _NullFile
- CovController
- Central
- DistMaster
- DistWorker

### Functions
- _ensure_topdir

## venv\Lib\site-packages\pytest_cov\plugin.py

### Classes
- StoreReport
- CovPlugin
- TestContextPlugin

### Functions
- validate_report
- validate_fail_under
- validate_context
- pytest_addoption
- _prepare_cov_source
- pytest_load_initial_conftests
- no_cover
- cov
- pytest_configure

## venv\Lib\site-packages\pytest_env\__init__.py

## venv\Lib\site-packages\pytest_env\plugin.py

### Classes
- Entry

### Functions
- pytest_addoption
- pytest_load_initial_conftests
- _apply_env_files
- _apply_entries
- pytest_report_header
- _format_actions
- _find_toml_config
- _config_source
- _load_toml_config
- _load_env_files
- _load_values
- _parse_toml_config

## venv\Lib\site-packages\pytest_env\version.py

## venv\Lib\site-packages\ruff\__init__.py

## venv\Lib\site-packages\ruff\__main__.py

### Functions
- _run

## venv\Lib\site-packages\ruff\_find_ruff.py

### Classes
- RuffNotFound

### Functions
- find_ruff_bin
- _module_path
- _matching_parents
- _join
- _user_scheme

## venv\Lib\site-packages\shiboken6\__init__.py

## venv\Lib\site-packages\shiboken6\_config.py

## venv\Lib\site-packages\shiboken6\_git_shiboken_module_version.py

## venv\Lib\site-packages\typing_extensions.py

### Classes
- _SpecialForm
- _ExtensionsSpecialForm
- _DefaultMixin
- _TypeVarLikeMeta
- _EllipsisDummy

### Functions
- _caller
- IntVar
- _get_protocol_attrs
- _set_default
- _set_module
- _create_concatenate_alias
- _concatenate_getitem
- _unpack_args
- _has_generic_or_protocol_as_origin
- _is_unpacked_typevartuple

## zennity-engine-game.worktrees\copilot-greeting-integration\__init__.py

## zennity-engine-game.worktrees\copilot-greeting-integration\demos\demo_2d.py

### Classes
- PlayerController
- CameraFollow2D
- Game2DScene

### Functions
- create_player_surface
- create_platform_surface

## zennity-engine-game.worktrees\copilot-greeting-integration\demos\demo_3d.py

### Classes
- Spinner3D
- FreeCameraController3D
- Game3DScene

### Functions
- ensure_pyramid_obj

## zennity-engine-game.worktrees\copilot-greeting-integration\demos\editor_3d.py

### Classes
- GuiButton
- OrbitCameraController
- EditorScene

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\__init__.py

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\assets.py

### Classes
- Mesh
- Assets

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\audio.py

### Classes
- Audio

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\component.py

### Classes
- Component
- Transform

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\core.py

### Classes
- Scene
- Engine

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\editor_utils.py

### Functions
- point_in_polygon
- create_pyramid_mesh
- create_sphere_mesh

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\game_object.py

### Classes
- GameObject

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\graphics\__init__.py

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\graphics\camera2d.py

### Classes
- Camera2D

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\graphics\math3d.py

### Functions
- translation_matrix
- scale_matrix
- rotation_matrix
- projection_matrix
- view_matrix
- project_vertices

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\graphics\renderer2d.py

### Classes
- SpriteRenderer
- TextRenderer
- Particle
- ParticleSystem

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\graphics\renderer3d.py

### Classes
- Camera3D
- MeshRenderer3D

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\input.py

### Classes
- Input

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\lifecycle.py

### Functions
- reset_engine_state

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\physics\__init__.py

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\physics\collision.py

### Classes
- BoxCollider2D

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\physics\rigidbody.py

### Classes
- Rigidbody2D

## zennity-engine-game.worktrees\copilot-greeting-integration\engine\scene_io.py

### Functions
- serialize_scene_objects
- save_scene_file
- load_scene_file
- create_object_from_data
- count_shapes

## zennity-engine-game.worktrees\copilot-greeting-integration\scripts\behavior_bloco_2.py

### Functions
- start
- update

## zennity-engine-game.worktrees\copilot-greeting-integration\scripts\oscillate.py

### Functions
- update

## zennity-engine-game.worktrees\copilot-greeting-integration\scripts\pulse.py

### Functions
- update

## zennity-engine-game.worktrees\copilot-greeting-integration\scripts\rotate.py

### Functions
- update

## zennity-engine-game.worktrees\copilot-greeting-integration\tests\conftest.py

### Functions
- pygame_headless
- reset_engine_state

## zennity-engine-game.worktrees\copilot-greeting-integration\tests\test_editor_utils.py

### Functions
- test_point_in_polygon_inside_square
- test_point_in_polygon_outside_square
- test_point_in_polygon_horizontal_edge_does_not_crash
- test_create_pyramid_mesh_has_expected_topology
- test_create_sphere_mesh_has_faces

## zennity-engine-game.worktrees\copilot-greeting-integration\tests\test_game_object.py

### Classes
- CounterComponent

### Functions
- test_game_object_propagates_scene_to_components
- test_destroy_clears_children_and_components
- test_transform_world_position_with_parent
- test_get_component_returns_first_match

## zennity-engine-game.worktrees\copilot-greeting-integration\tests\test_lifecycle.py

### Functions
- test_reset_engine_state_clears_colliders
- test_reset_engine_state_clears_camera_singletons
- test_reset_engine_state_clears_asset_caches
- test_destroy_removes_collider_from_registry

## zennity-engine-game.worktrees\copilot-greeting-integration\tests\test_physics.py

### Classes
- _PhysicsScene

### Functions
- _setup_box
- test_rigidbody_falls_with_gravity
- test_rigidbody_lands_on_static_platform
- test_box_collider_overlap_resolution_direction

## zennity-engine-game.worktrees\copilot-greeting-integration\tests\test_serialization.py

### Functions
- _make_object
- test_serialize_uses_mesh_type_not_name_heuristics
- test_save_and_load_roundtrip
- test_count_shapes
- test_load_scene_file_invalid_json

## zennity-engine-game\__init__.py

## zennity-engine-game\assets\scripts\__init__.py

## zennity-engine-game\assets\scripts\animator.py

### Classes
- Animator

## zennity-engine-game\assets\scripts\camera_follow.py

### Classes
- CameraFollow

## zennity-engine-game\assets\scripts\collectible.py

### Classes
- Collectible

## zennity-engine-game\assets\scripts\enemy_ai.py

### Classes
- EnemyAI

## zennity-engine-game\assets\scripts\health.py

### Classes
- Health

## zennity-engine-game\assets\scripts\player_controller.py

### Classes
- PlayerController

## zennity-engine-game\assets\scripts\projectile.py

### Classes
- Projectile

## zennity-engine-game\assets\scripts\timer_component.py

### Classes
- TimerComponent

## zennity-engine-game\conftest.py

### Classes
- _FakeSurface

### Functions
- pytest_configure
- _pygame_init
- fake_surface_class
- screen
- empty_scene
- simple_go
- reset_pygame_mocks

## zennity-engine-game\demos\demo_2d.py

### Classes
- PlayerController
- CameraFollow2D
- Game2DScene

### Functions
- create_player_surface
- create_platform_surface

## zennity-engine-game\demos\demo_3d.py

### Classes
- Spinner3D
- FreeCameraController3D
- Game3DScene

### Functions
- ensure_pyramid_obj

## zennity-engine-game\demos\demo_animator.py

### Classes
- AnimatorDemoScene

### Functions
- _draw_player_frame
- _make_spritesheet
- _make_extra_frames
- _make_tile_surface
- _build_tilemap

## zennity-engine-game\demos\demo_particles.py

### Classes
- ParticlesDemoScene

## zennity-engine-game\demos\demo_physics.py

### Classes
- DemoScene

## zennity-engine-game\demos\demo_platformer.py

### Classes
- RectSprite
- PlayerSprite
- CoinComponent
- PlatformerScene

### Functions
- _make_tileset
- _make_tilemap

## zennity-engine-game\demos\demo_scene_manager.py

### Classes
- SplashScene
- TitleScene
- PauseScene
- GameScene
- GameOverScene

### Functions
- _font
- _center_text

## zennity-engine-game\demos\demo_tilemap.py

### Classes
- TilemapDemoScene

### Functions
- _cleanup_tmp_tileset
- _make_procedural_tileset
- _build_map

## zennity-engine-game\demos\demo_tilemap_physics.py

### Classes
- PhysicsDemoScene

### Functions
- _make_tileset
- _build_map

## zennity-engine-game\demos\demo_ui.py

### Classes
- UIDemoScene

## zennity-engine-game\demos\editor_3d.py

## zennity-engine-game\editor\__init__.py

## zennity-engine-game\editor\core\event_bus.py

## zennity-engine-game\editor\core\exporter.py

### Functions
- export_project

## zennity-engine-game\editor\core\serializer.py

### Functions
- serialize_game_object
- deserialize_game_object
- save_scene_to_file
- load_scene_from_file

## zennity-engine-game\editor\main.py

### Functions
- patch_logger
- load_stylesheet
- main

## zennity-engine-game\editor\models\asset_model.py

### Classes
- AssetModel

## zennity-engine-game\editor\models\scene_model.py

### Classes
- SceneModel

## zennity-engine-game\editor\viewmodels\asset_viewmodel.py

### Classes
- AssetViewModel

## zennity-engine-game\editor\viewmodels\scene_viewmodel.py

### Classes
- SceneViewModel

## zennity-engine-game\editor\widgets\asset_browser_dock.py

### Classes
- AssetBrowserDock

## zennity-engine-game\editor\widgets\code_editor_dock.py

### Classes
- CodeEditorDock

## zennity-engine-game\editor\widgets\collapsible_section.py

### Classes
- CollapsibleSection

## zennity-engine-game\editor\widgets\component_widgets.py

### Classes
- TransformComponentWidget
- MeshRendererWidget
- ColliderComponentWidget
- RigidBodyComponentWidget
- ScriptComponentWidget

### Functions
- _f
- _dsb
- _row_label
- _axis_header

## zennity-engine-game\editor\widgets\console_dock.py

### Classes
- ConsoleDock

## zennity-engine-game\editor\widgets\hierarchy_dock.py

### Classes
- HierarchyDock

## zennity-engine-game\editor\widgets\inspector_dock.py

### Classes
- InspectorDock

## zennity-engine-game\editor\widgets\profiler_dock.py

### Classes
- PerformanceChartWidget
- ProfilerDock

## zennity-engine-game\editor\widgets\viewport_tab_bar.py

### Classes
- ViewportTabBar
- _GameViewport
- ViewportContainer

### Functions
- _btn_style

## zennity-engine-game\editor\widgets\viewport_widget.py

### Classes
- ViewportWidget

## zennity-engine-game\editor\windows\main_window.py

### Classes
- MainWindow

## zennity-engine-game\editor\windows\preferences_dialog.py

### Classes
- PreferencesDialog

## zennity-engine-game\editor_legacy\__init__.py

## zennity-engine-game\editor_legacy\camera_controller.py

### Classes
- OrbitCameraController

## zennity-engine-game\editor_legacy\code_editor.py

### Classes
- CodeEditor

## zennity-engine-game\editor_legacy\editor_2d.py

### Classes
- Editor2DScene

### Functions
- _screen_size

## zennity-engine-game\editor_legacy\gui.py

### Classes
- GuiButton
- SectionHeader
- Divider
- Badge

## zennity-engine-game\editor_legacy\history.py

### Classes
- History

### Functions
- _snap_obj
- _get_color
- _snap_scene

## zennity-engine-game\editor_legacy\launcher.py

### Classes
- LauncherScene

## zennity-engine-game\editor_legacy\layout.py

### Classes
- Layout

## zennity-engine-game\editor_legacy\layout_constants.py

## zennity-engine-game\editor_legacy\mesh_factory.py

### Functions
- create_pyramid_mesh
- create_sphere_mesh
- create_plane_mesh
- create_capsule_mesh

## zennity-engine-game\editor_legacy\physics_sim.py

### Classes
- PhysicsSim

### Functions
- _half_extents
- _aabb_overlap

## zennity-engine-game\editor_legacy\scene.py

### Classes
- EditorScene

### Functions
- _point_in_polygon

## zennity-engine-game\editor_legacy\script_manager.py

### Classes
- ScriptManager

## zennity-engine-game\editor_legacy\theme.py

### Functions
- alpha_blend
- grid_color

## zennity-engine-game\editor_legacy\widgets\__init__.py

## zennity-engine-game\editor_legacy\widgets\panel_base.py

### Classes
- PanelBase
- _ClipContext

## zennity-engine-game\engine\__init__.py

## zennity-engine-game\engine\animation\__init__.py

## zennity-engine-game\engine\animation\animator.py

### Classes
- Animator

## zennity-engine-game\engine\animation\clip.py

### Classes
- AnimationEvent
- AnimationClip

## zennity-engine-game\engine\animation\spritesheet.py

### Classes
- SpriteSheet

## zennity-engine-game\engine\application.py

### Classes
- Application

## zennity-engine-game\engine\assets.py

### Classes
- Mesh
- Assets

## zennity-engine-game\engine\audio.py

### Classes
- AudioManager

## zennity-engine-game\engine\component.py

## zennity-engine-game\engine\component_registry.py

### Classes
- _ComponentRegistryMeta
- ComponentRegistry

## zennity-engine-game\engine\core.py

## zennity-engine-game\engine\core\__init__.py

## zennity-engine-game\engine\core\application.py

## zennity-engine-game\engine\core\component.py

### Classes
- Component
- Transform

## zennity-engine-game\engine\core\engine.py

### Classes
- Engine

### Functions
- _builtin_physics_system

## zennity-engine-game\engine\core\event_bus.py

## zennity-engine-game\engine\core\game_object.py

## zennity-engine-game\engine\core\logger.py

## zennity-engine-game\engine\core\scene.py

### Classes
- Scene

## zennity-engine-game\engine\core\scene_manager.py

### Classes
- SceneManager

## zennity-engine-game\engine\core\system.py

## zennity-engine-game\engine\core\time.py

## zennity-engine-game\engine\event_bus.py

### Classes
- EventBus

## zennity-engine-game\engine\game_object.py

### Classes
- GameObject

## zennity-engine-game\engine\graphics\__init__.py

## zennity-engine-game\engine\graphics\camera.py

### Classes
- Camera

## zennity-engine-game\engine\graphics\camera2d.py

### Classes
- Camera2D

## zennity-engine-game\engine\graphics\math3d.py

### Functions
- translation_matrix
- scale_matrix
- rotation_matrix
- projection_matrix
- view_matrix
- project_vertices

## zennity-engine-game\engine\graphics\particles.py

### Classes
- Particle
- ParticleSystem

## zennity-engine-game\engine\graphics\renderer.py

### Classes
- SpriteRenderer

## zennity-engine-game\engine\graphics\renderer2d.py

### Classes
- SpriteRenderer
- TextRenderer
- Particle
- ParticleSystem

## zennity-engine-game\engine\graphics\renderer3d.py

### Classes
- Camera3D
- MeshRenderer3D

## zennity-engine-game\engine\input.py

### Classes
- Input

## zennity-engine-game\engine\logger.py

### Classes
- Logger
- _TaggedLogger

## zennity-engine-game\engine\physics\__init__.py

### Functions
- __getattr__

## zennity-engine-game\engine\physics\collider.py

### Classes
- CollisionInfo
- BoxCollider
- CircleCollider

## zennity-engine-game\engine\physics\collision.py

### Classes
- BoxCollider2D

### Functions
- check_collision

## zennity-engine-game\engine\physics\rigidbody.py

### Classes
- RigidBody

## zennity-engine-game\engine\physics\rigidbody3d.py

### Classes
- RigidBody3D

## zennity-engine-game\engine\physics\tilemap_collider.py

### Classes
- TilemapCollider

## zennity-engine-game\engine\scene_manager.py

## zennity-engine-game\engine\system.py

### Classes
- SystemPriority
- System
- SystemRegistry

## zennity-engine-game\engine\tilemap\__init__.py

## zennity-engine-game\engine\tilemap\tilemap.py

### Classes
- TileLayer
- TileMap
- TilemapRenderer

## zennity-engine-game\engine\tilemap\tilemap_loader.py

### Classes
- TileMapLoader

## zennity-engine-game\engine\tilemap\tileset.py

### Classes
- TileData
- Tileset

## zennity-engine-game\engine\time.py

### Classes
- Time

## zennity-engine-game\engine\transitions.py

### Classes
- TransitionPhase
- Transition
- FadeTransition
- SlideDirection
- SlideTransition
- WipeTransition
- CrossfadeTransition

### Functions
- _linear
- _ease_in
- _ease_out
- _ease_in_out

## zennity-engine-game\engine\ui\__init__.py

## zennity-engine-game\engine\ui\base.py

### Classes
- Anchor
- Pivot
- UIElement

## zennity-engine-game\engine\ui\button.py

### Classes
- Button

## zennity-engine-game\engine\ui\canvas.py

### Classes
- UICanvas

## zennity-engine-game\engine\ui\image.py

### Classes
- UIImage

## zennity-engine-game\engine\ui\label.py

### Classes
- Label

## zennity-engine-game\engine\ui\panel.py

### Classes
- Panel

## zennity-engine-game\engine\ui\progress_bar.py

### Classes
- ProgressBar

## zennity-engine-game\engine\ui\ui_manager.py

### Classes
- UIManager

## zennity-engine-game\engine\window.py

### Classes
- Window

## zennity-engine-game\scripts\behavior_bloco_1.py

### Functions
- start
- update

## zennity-engine-game\scripts\behavior_bloco_2.py

### Functions
- start
- update

## zennity-engine-game\scripts\builtin_destroy_on_collision.py

### Functions
- start
- update

## zennity-engine-game\scripts\builtin_follow_player.py

### Functions
- start
- update

## zennity-engine-game\scripts\builtin_jump.py

### Functions
- start
- update

## zennity-engine-game\scripts\builtin_rotate.py

### Functions
- start
- update

## zennity-engine-game\scripts\builtin_wasd.py

### Functions
- start
- update

## zennity-engine-game\scripts\oscillate.py

### Functions
- update

## zennity-engine-game\scripts\pulse.py

### Functions
- update

## zennity-engine-game\scripts\rotate.py

### Functions
- update

## zennity-engine-game\tests\__init__.py

## zennity-engine-game\tests\animation\__init__.py

## zennity-engine-game\tests\animation\conftest.py

## zennity-engine-game\tests\animation\test_animation.py

### Classes
- TestAnimationEvent
- TestAnimationClip
- TestAnimatorInit
- TestAnimatorUpdate
- TestAnimatorEvents
- TestAnimatorTransitions
- TestAnimatorPushFrame
- TestAnimatorState

### Functions
- make_surface
- make_frames
- make_animator

## zennity-engine-game\tests\animation\test_animator.py

### Classes
- TestInit
- TestAddClip
- TestPlay
- TestStart
- TestUpdateFrameAdvance
- TestOnFinish
- TestTransitions
- TestAnimationEvents
- TestStateQueries

### Functions
- _frames
- _clip
- _animator_with_go
- _animator

## zennity-engine-game\tests\animation\test_clip.py

### Classes
- TestAnimationEvent
- TestAnimationClipInit
- TestFlipH
- TestFrameCount
- TestDuration
- TestAddEvent
- TestRepr

### Functions
- reset_flip
- _frames
- _clip

## zennity-engine-game\tests\conftest.py

## zennity-engine-game\tests\core\__init__.py

## zennity-engine-game\tests\core\test_application.py

### Classes
- TestSingleton
- TestServiceLocator
- TestBuiltins
- TestRepr
- TestConvenienceProperties

### Functions
- reset_application
- _make_app
- _stop_patches

## zennity-engine-game\tests\core\test_component.py

### Classes
- TestComponentInit
- TestComponentLifecycle
- TestComponentProperties
- TestTransformInit
- TestTransformSetters
- TestTransformTranslate
- TestTransformRotate
- TestTransformModelMatrix
- TestTransformRepr

## zennity-engine-game\tests\core\test_event_bus.py

### Classes
- TestSubscribe
- TestUnsubscribe
- TestEmit
- TestOnce
- TestEmitDeferred
- TestClear
- TestInspection
- TestInstanceAlias
- TestEdgeCases

### Functions
- reset_bus

## zennity-engine-game\tests\core\test_game_object.py

### Classes
- TestIdentity
- TestTransform
- TestAddComponent
- TestGetComponent
- TestRemoveComponent
- TestHierarchy
- TestUpdate
- TestDraw
- TestDestroy
- TestScenePropagation

### Functions
- make_component
- fake_scene

## zennity-engine-game\tests\core\test_input.py

### Classes
- TestGetKey
- TestGetKeyDown
- TestGetKeyUp
- TestMousePosition
- TestMouseButton
- TestAxes
- TestUpdate
- TestInputEdgeCases

### Functions
- _make_keys

## zennity-engine-game\tests\core\test_scene.py

### Classes
- TestSceneInit
- TestAddGameObject
- TestRemoveGameObject
- TestFind
- TestUpdate
- TestDraw
- TestLifecycleHooks
- TestEngineRef

### Functions
- make_go
- make_tracked_go

## zennity-engine-game\tests\core\test_scene_manager.py

### Classes
- _FakePhase
- _FakeScene
- _FakeTransition
- TestSingleton
- TestBind
- TestLoad
- TestPush
- TestPop
- TestUpdate
- TestDraw
- TestHandleEvent
- TestCallbacks
- TestRepr

### Functions
- clean_sm
- sm
- fake_engine

## zennity-engine-game\tests\core\test_time.py

### Classes
- TestDefaults
- TestTick
- TestDtCap
- TestScale
- TestPaused
- TestElapsed
- TestSlowMo
- TestAliases
- TestCurrent
- TestRepr

### Functions
- make_time

## zennity-engine-game\tests\core\test_transform.py

### Classes
- TestTransformSetters
- TestTransformMethods
- TestTransformRepr
- TestComponentLifecycle

## zennity-engine-game\tests\core\test_window.py

### Classes
- TestDefaults
- TestSetTitle
- TestOnResize
- TestToggleFullscreen
- TestFlip
- TestResolutionClamping

### Functions
- _make_surface
- _make_display_info
- make_window

## zennity-engine-game\tests\graphics\__init__.py

## zennity-engine-game\tests\graphics\test_camera2d.py

### Classes
- TestInit
- TestMakeMain
- TestUpdateFollow
- TestBounds
- TestWorldToScreen
- TestScreenToWorld

### Functions
- _make_go
- _make_cam
- reset_main

## zennity-engine-game\tests\graphics\test_renderer.py

### Classes
- _FakeSurface
- TestInit
- TestSurfaceProperty
- TestDrawNoCam
- TestDrawWithCam

### Functions
- _make_surface
- reset_camera
- _make_go
- _renderer

## zennity-engine-game\tests\physics\test_collider.py

### Classes
- TestCollisionInfo
- TestBoxColliderInit
- TestBoxColliderLifecycle
- TestBoxColliderRect
- TestBoxCheckAllBasic
- TestBoxCheckAllTrigger
- TestBoxResolve
- TestCircleColliderInit
- TestCircleColliderCenter
- TestCircleCheckAllBasic
- TestCircleCheckAllTrigger
- TestCircleResolve

### Functions
- _make_transform
- _make_rb
- _make_go
- _box
- _circle
- _clean_registries

## zennity-engine-game\tests\physics\test_rigidbody.py

### Classes
- TestRigidBodyInit
- TestAddForce
- TestAddImpulse
- TestSetVelocityStop
- TestUpdateGravity
- TestUpdateExternalForces
- TestUpdateDrag
- TestUpdateKinematic
- TestGrounded

### Functions
- _make_transform
- _make_go
- _rb

## zennity-engine-game\tests\test_assets.py

### Classes
- _FakeSurface
- TestMeshInit
- TestGetImage
- TestLoadSpriteSheet
- TestGetSound
- TestPlayMusic
- TestGetFont
- TestGetMesh
- TestCreateCubeMesh

### Functions
- clean_cache

## zennity-engine-game\tests\test_audio.py

### Classes
- _FakeMusic
- _FakeSound
- TestInit
- TestPlayMusic
- TestStopMusic
- TestPauseResumeMusic
- TestMusicVolume
- TestSfx
- TestMasterVolume
- TestGlobalControl
- TestUnloadCache

### Functions
- _build_mixer_stub
- reset_audio
- exists_true
- exists_false

## zennity-engine-game\tests\test_component_registry.py

### Classes
- Health
- Speed
- UniqueComp
- TestRegistryRegister
- TestRegistryResolve
- TestRegistryCreate
- TestComponentEnabled
- TestComponentUnique
- TestComponentSerialize
- TestTransformSerialize
- TestGameObjectSerialize

### Functions
- clean_registry

## zennity-engine-game\tests\test_event_bus.py

### Classes
- TestSubscribe
- TestUnsubscribe
- TestEmit
- TestOnce
- TestEmitDeferred
- TestClear
- TestRetrocompatInstance
- TestEdgeCases

### Functions
- bus

## zennity-engine-game\tests\test_game_object.py

### Classes
- _Counter
- _Crasher
- _TypeA
- _TypeB
- TestInit
- TestComponents
- TestLifecycle
- TestHierarchy
- TestRepr

### Functions
- _go
- _screen

## zennity-engine-game\tests\test_input.py

### Classes
- _FakeKeys
- TestGetKey
- TestGetKeyDown
- TestGetKeyUp
- TestMouse
- TestAxes
- TestUpdate

### Functions
- _build_pygame_stub
- reset_input
- _press
- _release

## zennity-engine-game\tests\test_logger.py

### Classes
- TestLevelConstants
- TestSetLevel
- TestMessageFormat
- TestSilence
- TestFileOutput
- TestTaggedLogger

### Functions
- reset_logger
- _inject_file

## zennity-engine-game\tests\test_time.py

### Classes
- _FakeClock
- TestInit
- TestTick
- TestScaledDelta
- TestElapsed
- TestPauseUnpause
- TestDtCap
- TestCurrent
- TestRepr

### Functions
- _build_pygame_stub
- reset_current
- t
- _tick

## zennity-engine-game\tests\test_transitions.py

### Classes
- _FakeSurface
- TestEasing
- TestTransitionBase
- TestFadeTransition
- TestSlideTransition
- TestWipeTransition
- TestCrossfadeTransition
- TestPhaseLifecycle

### Functions
- _pygame
- _advance
- _run_to_swap
- _run_to_done
- _fake_snap

## zennity-engine-game\tests\tilemap\__init__.py

## zennity-engine-game\tests\tilemap\conftest.py

## zennity-engine-game\tests\tilemap\test_tilemap.py

### Classes
- _FakeSurface
- _FakeRect
- TestTileLayerInit
- TestTileLayerGetSetGid
- TestTileMapInit
- TestTileMapTilesets
- TestTileMapLayers
- TestCoordinates
- TestIsSolidAt
- TestGetSolidRectsInRegion
- TestBakeAndInvalidate
- TestDraw
- TestTilemapRenderer

### Functions
- _layer
- _map
- _tileset

## zennity-engine-game\tests\ui\__init__.py

## zennity-engine-game\tests\ui\test_button.py

### Classes
- _FakeRect
- _FakeTextSurf
- _FakeFont
- _FakeSurface
- TestButtonInit
- TestNaturalSize
- TestHandleEventMouseMotion
- TestHandleEventMouseDown
- TestHandleEventMouseUp
- TestUpdate
- TestLerpColor
- TestDrawSelf

### Functions
- reset_draw
- _screen
- _btn
- _event

## zennity-engine-game\tests\ui\test_label.py

### Classes
- _FakeSurf
- _FakeFont
- _FakeScreen
- TestLabelInit
- TestSetText
- TestRebuild
- TestNaturalSize
- TestDrawSelf

### Functions
- reset_font_mock
- _screen
- _lbl

## zennity-engine-game\tests\ui\test_progress_bar.py

### Classes
- _FakeRect
- _FakeSurf
- _FakeFont
- _FakeScreen
- TestInit
- TestRatio
- TestSetValue
- TestUpdate
- TestDrawSelf

### Functions
- reset_mocks
- _screen
- _bar

## zennity-engine-game\tests\ui\test_ui_base.py

### Classes
- _FakeRect
- _FakeSurface
- TestAnchorEnum
- TestPivotEnum
- TestUIElementInit
- TestHierarchy
- TestGetRect
- TestContainsPoint
- TestVisibility
- TestHandleEvent
- TestUpdate
- TestRepr

### Functions
- _screen
- _elem

