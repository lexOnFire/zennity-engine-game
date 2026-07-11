import re

def main():
    files = [
        "editor/phase1_editor.py",
        "editor/inspector/phase1_inspector_bridge.py",
        "editor/runtime/command_manager.py"
    ]
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        c = content.replace(
            'scene = getattr(self.viewport, "active_scene", None)',
            'scene = self.editor_context.current_scene()'
        )
        c = c.replace(
            'scene = getattr(self.editor.viewport, "active_scene", None)',
            'scene = self.editor.editor_context.current_scene()'
        )
        c = c.replace(
            'scene = self.viewport.active_scene\n        if not scene:',
            'scene = self.editor_context.current_scene()\n        if not scene:'
        )
        c = c.replace(
            'scene = self.viewport.active_scene\n        if scene is None:',
            'scene = self.editor_context.current_scene()\n        if scene is None:'
        )

        with open(fpath, "w", encoding="utf-8") as f:
            f.write(c)

if __name__ == "__main__":
    main()
