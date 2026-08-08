# PHASE 3E: AUDITORIA COMPLETA DE EXECUTORES

Total de executores: 95
Data: zennity-engine-game

## Resumo por Classificação

- LEGACY_COMPATIBILITY: 2
- PURE_NODE_SHOULD_HAVE_NO_EXECUTOR: 5
- UNKNOWN: 88

## Multi-output potencial: 53

## Detalhes por Executor

### add_transition

- File: state_machine_nodes.py
- Function: execute_add_transition
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### animate_value

- File: animation_nodes.py
- Function: execute_animate_value
- Classification: UNKNOWN
- Return patterns:
  - [animating]
  - [failure]
  - [finished]

### apply_force

- File: physics_nodes.py
- Function: execute_apply_force
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### bind_ui_to_blackboard

- File: ui_nodes.py
- Function: execute_bind_ui_to_blackboard
- Classification: UNKNOWN
- Return patterns:
  - [next]

### bind_ui_to_variable

- File: ui_binding_nodes.py
- Function: execute_bind_ui_to_variable
- Classification: LEGACY_COMPATIBILITY
- Return patterns:
  - [exec_failure, next]
  - [exec_not_found, next]
  - [exec_success, next]

### call_subgraph

- File: misc_nodes.py
- Function: execute_call_subgraph
- Classification: UNKNOWN
- Return patterns:
  - [next]

### camera_follow

- File: camera_nodes.py
- Function: execute_camera_follow
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [following]

### camera_look_at

- File: camera_nodes.py
- Function: execute_camera_look_at
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [looking]

### camera_set_zoom

- File: camera_nodes.py
- Function: execute_camera_set_zoom
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### camera_shake

- File: camera_nodes.py
- Function: execute_camera_shake
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [shaking]

### camera_stop_follow

- File: camera_nodes.py
- Function: execute_camera_stop_follow
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### change_state

- File: state_machine_nodes.py
- Function: execute_change_state
- Classification: UNKNOWN
- Return patterns:
  - [changed]
  - [failure]
  - [invalid_transition]

### clone_object

- File: prefab_nodes.py
- Function: execute_clone_object
- Classification: UNKNOWN
- Return patterns:
  - [limit_reached]
  - [next]

### close_dialog

- File: dialog_nodes.py
- Function: execute_close_dialog
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### compare_number

- File: event_nodes.py
- Function: execute_compare_number
- Classification: UNKNOWN
- Return patterns:
  - [<?unknown>]

### compare_text

- File: event_nodes.py
- Function: execute_compare_text
- Classification: UNKNOWN
- Return patterns:
  - [<?unknown>]

### cooldown

- File: flow_nodes.py
- Function: execute_cooldown
- Classification: UNKNOWN
- Return patterns:
  - [blocked]
  - [next]

### create_object

- File: prefab_nodes.py
- Function: execute_create_object
- Classification: UNKNOWN
- Return patterns:
  - [limit_reached]
  - [next]

### create_particle_system

- File: particle_nodes.py
- Function: execute_create_particle_system
- Classification: UNKNOWN
- Return patterns:
  - [created]
  - [failure]

### create_prefab

- File: prefab_nodes.py
- Function: execute_create_prefab
- Classification: UNKNOWN
- Return patterns:
  - [limit_reached]
  - [next]

### create_state_machine

- File: state_machine_nodes.py
- Function: execute_create_state_machine
- Classification: UNKNOWN
- Return patterns:
  - [created]
  - [failure]

### create_ui_button

- File: dynamic_ui_nodes.py
- Function: execute_create_ui_button
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### create_ui_image

- File: dynamic_ui_nodes.py
- Function: execute_create_ui_image
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### create_ui_label

- File: dynamic_ui_nodes.py
- Function: execute_create_ui_label
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### create_ui_progress_bar

- File: dynamic_ui_nodes.py
- Function: execute_create_ui_progress_bar
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### delete_save

- File: save_load_nodes.py
- Function: execute_delete_save
- Classification: UNKNOWN
- Return patterns:
  - [deleted]
  - [failure]

### destroy_after_time

- File: actions_nodes.py
- Function: execute_destroy_after_time
- Classification: UNKNOWN
- Return patterns:
  - [next]

### destroy_object

- File: actions_nodes.py
- Function: execute_destroy_object
- Classification: PURE_NODE_SHOULD_HAVE_NO_EXECUTOR
- Return patterns:
  - []

### destroy_ui_widget

- File: dynamic_ui_nodes.py
- Function: execute_destroy_ui_widget
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### detect_pinch

- File: input_advanced_nodes.py
- Function: execute_detect_pinch
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [no_pinch]
  - [pinched]

### detect_swipe

- File: input_advanced_nodes.py
- Function: execute_detect_swipe
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [no_swipe]
  - [swiped]

### detect_touch

- File: input_advanced_nodes.py
- Function: execute_detect_touch
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [no_touch]
  - [touched]

### distance_to_point

- File: pathfinding_nodes.py
- Function: execute_distance_to_point
- Classification: UNKNOWN
- Return patterns:
  - [calculated]
  - [failure]

### emit_event

- File: misc_nodes.py
- Function: execute_emit_event
- Classification: UNKNOWN
- Return patterns:
  - [next]

### emit_particles

- File: particle_nodes.py
- Function: execute_emit_particles
- Classification: UNKNOWN
- Return patterns:
  - [emitting]
  - [failure]

### find_path

- File: pathfinding_nodes.py
- Function: execute_find_path
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [found]

### follow_path

- File: pathfinding_nodes.py
- Function: execute_follow_path
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [finished]
  - [following]

### get_continuous_motion

- File: movement_nodes.py
- Function: execute_get_continuous_motion
- Classification: UNKNOWN
- Return patterns:
  - [next]

### get_progress_bar_value

- File: dynamic_ui_nodes.py
- Function: execute_get_progress_bar_value
- Classification: PURE_NODE_SHOULD_HAVE_NO_EXECUTOR
- Return patterns:

### get_state

- File: state_machine_nodes.py
- Function: execute_get_state
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [got_state]

### get_ui_widget_property

- File: dynamic_ui_nodes.py
- Function: execute_get_ui_widget_property
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### get_variable

- File: misc_nodes.py
- Function: execute_get_variable
- Classification: UNKNOWN
- Return patterns:
  - [next]

### has_save

- File: save_load_nodes.py
- Function: execute_has_save
- Classification: UNKNOWN
- Return patterns:
  - [exists]
  - [failure]
  - [not_exists]

### if_else

- File: flow_nodes.py
- Function: execute_if_else
- Classification: UNKNOWN
- Return patterns:
  - [<?unknown>]

### is_grounded

- File: event_nodes.py
- Function: execute_is_grounded
- Classification: UNKNOWN
- Return patterns:
  - [<?unknown>]

### is_in_state

- File: state_machine_nodes.py
- Function: execute_is_in_state
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [in_state]
  - [not_in_state]

### is_key_pressed

- File: input_advanced_nodes.py
- Function: execute_is_key_pressed
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [not_pressed]
  - [pressed]

### jump

- File: movement_nodes.py
- Function: execute_jump
- Classification: UNKNOWN
- Return patterns:
  - [next]

### key_held

- File: event_nodes.py
- Function: execute_key_held
- Classification: UNKNOWN
- Return patterns:
  - [<?unknown>]

### key_pressed

- File: event_nodes.py
- Function: execute_key_pressed
- Classification: UNKNOWN
- Return patterns:
  - [<?unknown>]

### load_game

- File: save_load_nodes.py
- Function: execute_load_game
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [loaded]
  - [no_save]

### log_message

- File: actions_nodes.py
- Function: execute_log_message
- Classification: UNKNOWN
- Return patterns:
  - [next]

### modify_collider

- File: physics_nodes.py
- Function: execute_modify_collider
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### modify_rigidbody

- File: physics_nodes.py
- Function: execute_modify_rigidbody
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### move

- File: movement_nodes.py
- Function: execute_move
- Classification: UNKNOWN
- Return patterns:
  - [next]

### move_by

- File: movement_nodes.py
- Function: execute_move_by
- Classification: UNKNOWN
- Return patterns:
  - [next]

### once

- File: flow_nodes.py
- Function: execute_once
- Classification: UNKNOWN
- Return patterns:
  - [blocked]
  - [next]

### patrol_axis

- File: movement_nodes.py
- Function: execute_patrol_axis
- Classification: UNKNOWN
- Return patterns:
  - [next]

### play_animation

- File: actions_nodes.py
- Function: execute_play_animation
- Classification: UNKNOWN
- Return patterns:
  - [next]

### play_animation_asset

- File: actions_nodes.py
- Function: execute_play_animation_asset
- Classification: UNKNOWN
- Return patterns:
  - [next]

### play_sound

- File: actions_nodes.py
- Function: execute_play_sound
- Classification: UNKNOWN
- Return patterns:
  - [next]

### play_sound_fade

- File: audio_advanced_nodes.py
- Function: execute_play_sound_fade
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [playing]

### remove_component

- File: components_nodes.py
- Function: execute_remove_component
- Classification: UNKNOWN
- Return patterns:
  - [next]

### restart_scene

- File: flow_nodes.py
- Function: execute_restart_scene
- Classification: PURE_NODE_SHOULD_HAVE_NO_EXECUTOR
- Return patterns:
  - []

### rotate

- File: actions_nodes.py
- Function: execute_rotate
- Classification: UNKNOWN
- Return patterns:
  - [next]

### save_game

- File: save_load_nodes.py
- Function: execute_save_game
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [saved]

### sequence

- File: misc_nodes.py
- Function: execute_sequence
- Classification: PURE_NODE_SHOULD_HAVE_NO_EXECUTOR
- Return patterns:

### set_active

- File: actions_nodes.py
- Function: execute_set_active
- Classification: UNKNOWN
- Return patterns:
  - [next]

### set_dialog_choice

- File: dialog_nodes.py
- Function: execute_set_dialog_choice
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### set_hud

- File: misc_nodes.py
- Function: execute_set_hud
- Classification: UNKNOWN
- Return patterns:
  - [next]

### set_pitch

- File: audio_advanced_nodes.py
- Function: execute_set_pitch
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### set_position

- File: actions_nodes.py
- Function: execute_set_position
- Classification: UNKNOWN
- Return patterns:
  - [next]

### set_sprite

- File: actions_nodes.py
- Function: execute_set_sprite
- Classification: UNKNOWN
- Return patterns:
  - [next]

### set_ui_progress_bar

- File: ui_nodes.py
- Function: execute_set_ui_progress_bar
- Classification: UNKNOWN
- Return patterns:
  - [next]

### set_ui_text

- File: ui_nodes.py
- Function: execute_set_ui_text
- Classification: UNKNOWN
- Return patterns:
  - [next]

### set_ui_visible

- File: ui_nodes.py
- Function: execute_set_ui_visible
- Classification: UNKNOWN
- Return patterns:
  - [next]

### set_variable

- File: misc_nodes.py
- Function: execute_set_variable
- Classification: UNKNOWN
- Return patterns:
  - [next]

### set_volume

- File: audio_advanced_nodes.py
- Function: execute_set_volume
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### show_dialog

- File: dialog_nodes.py
- Function: execute_show_dialog
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [showing]

### start_behavior_tree

- File: actions_nodes.py
- Function: execute_start_behavior_tree
- Classification: UNKNOWN
- Return patterns:
  - [next]

### start_continuous_motion

- File: movement_nodes.py
- Function: execute_start_continuous_motion
- Classification: UNKNOWN
- Return patterns:
  - [next]

### start_texture_scroll

- File: actions_nodes.py
- Function: execute_start_texture_scroll
- Classification: UNKNOWN
- Return patterns:
  - [next]

### stop_all_sounds

- File: audio_advanced_nodes.py
- Function: execute_stop_all_sounds
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### stop_animation

- File: actions_nodes.py
- Function: execute_stop_animation
- Classification: UNKNOWN
- Return patterns:
  - [next]

### stop_continuous_motion

- File: movement_nodes.py
- Function: execute_stop_continuous_motion
- Classification: UNKNOWN
- Return patterns:
  - [next]

### stop_particles

- File: particle_nodes.py
- Function: execute_stop_particles
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [stopped]

### stop_path

- File: pathfinding_nodes.py
- Function: execute_stop_path
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [stopped]

### stop_texture_scroll

- File: actions_nodes.py
- Function: execute_stop_texture_scroll
- Classification: UNKNOWN
- Return patterns:
  - [next]

### subgraph_return

- File: misc_nodes.py
- Function: execute_subgraph_return
- Classification: PURE_NODE_SHOULD_HAVE_NO_EXECUTOR
- Return patterns:
  - []

### update_continuous_motion

- File: movement_nodes.py
- Function: execute_update_continuous_motion
- Classification: UNKNOWN
- Return patterns:
  - [next]

### update_ui_binding

- File: ui_binding_nodes.py
- Function: execute_update_ui_binding
- Classification: LEGACY_COMPATIBILITY
- Return patterns:
  - [exec_failure, next]
  - [exec_not_found, next]
  - [exec_success, next]

### update_ui_widget_property

- File: dynamic_ui_nodes.py
- Function: execute_update_ui_widget_property
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]

### wait_dialog_choice

- File: dialog_nodes.py
- Function: execute_wait_dialog_choice
- Classification: UNKNOWN
- Return patterns:
  - [chosen]
  - [failure]
  - [waiting]

### wait_key_release

- File: input_advanced_nodes.py
- Function: execute_wait_key_release
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [released]
  - [timeout]
  - [waiting]

### wait_until_condition

- File: animation_nodes.py
- Function: execute_wait_until_condition
- Classification: UNKNOWN
- Return patterns:
  - [failure]
  - [success]
  - [timeout]
  - [waiting]

