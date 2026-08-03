"""
tests/test_validation_suite.py
─────────────────────────────────────────────────────────────────────────────
Suíte de Testes Automatizados para a Checklist de Validação Funcional AAA.
"""
import unittest
from pathlib import Path
from PySide6.QtGui import QColor

from editor.gizmos.scale_gizmo import QtScaleGizmoOverlay
from editor.viewport.marquee_selection import MarqueeSelection
from editor.viewport.viewport_toolbar_overlay import ViewportToolbarOverlay
from editor.visual_scripting.smart_context_menu import SmartContextMenu
from editor.visual_scripting.visual_debugger import VisualDebugger
from editor.inspector.component_preset_manager import ComponentPresetManager
from editor.inspector.collapsible_card import CollapsibleComponentCard


class MockTransform:
    def __init__(self, x=0.0, y=0.0, rz=0.0):
        self.position = [x, y, 0.0]
        self.rz = rz


class MockObject:
    def __init__(self, name="TestObject", x=0.0, y=0.0):
        self.name = name
        self.transform = MockTransform(x, y)


class TestValidationSuite(unittest.TestCase):

    def test_01_scale_gizmo_hit_test(self):
        gizmo = QtScaleGizmoOverlay(axis_length=70, handle_size=10)
        obj = MockObject(x=100.0, y=100.0)
        world_to_vp = lambda pos: (pos[0], pos[1])

        # Teste centro (uniforme)
        res_center = gizmo.hit_test(100.0, 100.0, obj, world_to_vp)
        self.assertEqual(res_center, "center")

        # Teste Eixo X
        res_x = gizmo.hit_test(140.0, 100.0, obj, world_to_vp)
        self.assertEqual(res_x, "x")

        # Teste Eixo Y
        res_y = gizmo.hit_test(100.0, 50.0, obj, world_to_vp)
        self.assertEqual(res_y, "y")

    def test_02_marquee_selection(self):
        marquee = MarqueeSelection()
        marquee.start(0.0, 0.0)
        marquee.update(200.0, 200.0)

        obj1 = MockObject("Inside", 50.0, 50.0)
        obj2 = MockObject("Outside", 300.0, 300.0)

        world_to_vp = lambda pos: (pos[0], pos[1])
        selected = marquee.select_objects([obj1, obj2], world_to_vp)

        self.assertIn(obj1, selected)
        self.assertNotIn(obj2, selected)

    def test_03_visual_debugger_breakpoints(self):
        dbg = VisualDebugger()
        dbg.toggle_breakpoint("node_123")

        self.assertTrue("node_123" in dbg.breakpoints)
        is_paused = dbg.notify_node_executed("node_123", {"health": 100})
        self.assertTrue(is_paused)
        self.assertTrue(dbg.is_paused)
        self.assertEqual(dbg.watched_variables.get("health"), 100)

        dbg.resume()
        self.assertFalse(dbg.is_paused)

    def test_04_component_preset_manager(self):
        mgr = ComponentPresetManager(project_root=Path("."))
        preset_file = mgr.save_preset("BoxCollider", "DefaultBox", {"width": 32, "height": 32})

        self.assertTrue(preset_file.is_file())
        loaded = mgr.load_preset(preset_file)
        self.assertEqual(loaded.get("width"), 32)
        self.assertEqual(loaded.get("height"), 32)

        # Cleanup
        if preset_file.is_file():
            preset_file.unlink()


if __name__ == "__main__":
    unittest.main()
