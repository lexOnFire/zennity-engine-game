import re

with open('editor/widgets/viewport_widget.py', 'r', encoding='utf-8') as f:
    orig = f.read()

# Insert import
c = orig.replace(
    'from editor.viewmodels.scene_viewmodel import SceneViewModel',
    'from editor.viewmodels.scene_viewmodel import SceneViewModel\nfrom editor.runtime.legacy_scene_adapter import LegacySceneAdapter'
)

# spawn_object
c = re.sub(
    r'if hasattr\(self\.active_scene, "spawn_object"\):\s+self\.active_scene\.spawn_object\(([^)]+)\)',
    r'LegacySceneAdapter.spawn_object(self.active_scene, \1)',
    c
)

# delete_selected
c = re.sub(
    r'if hasattr\(self\.active_scene, "delete_selected"\):\s+self\.active_scene\.delete_selected\(\)',
    r'LegacySceneAdapter.delete_selected(self.active_scene)',
    c
)

# duplicate_selected
c = re.sub(
    r'if hasattr\(self\.active_scene, "duplicate_selected"\):\s+self\.active_scene\.duplicate_selected\(\)',
    r'LegacySceneAdapter.duplicate_selected(self.active_scene)',
    c
)

# draw
c = c.replace('self.active_scene.draw(self.pg_surface)', 'LegacySceneAdapter.draw(self.active_scene, self.pg_surface)')

# handle_event
c = c.replace('self.active_scene.handle_event(pg_ev)', 'LegacySceneAdapter.handle_event(self.active_scene, pg_ev)')

with open('editor/widgets/viewport_widget.py', 'w', encoding='utf-8') as f:
    f.write(c)
