# PHASE 9 — UX ISSUES & AUTHORING HARDENING TRACKER

---

## 📌 RESOLVED ISSUES IN PHASE 9.1

### [ISSUE-01] Inspector Enum Property Controls & RigidBody BodyType UX
- **Severity:** P1
- **Subsystem:** Inspector Panel / Physics Components
- **Reproduction:** RigidBody inspector previously exposed `is_kinematic` as boolean and raw string properties without a dedicated dropdown selector.
- **Expected:** RigidBody property `Body Type` must present a canonical dropdown `[ Dynamic ▼ ]` with options `("Dynamic", "Kinematic", "Static")`.
- **Root Cause:** Absence of a generic `_enum_field` widget factory in `plugin_ui_utils.py` and missing `BODY_TYPES` contract on `RigidBody`.
- **Fix:**
  1. Implemented `_enum_field(value, choices, on_change)` in [`editor/inspector/plugin_ui_utils.py`](file:///c:/Users/alexs/OneDrive/Documentos/Nova%20pasta/zennity-engine-game/editor/inspector/plugin_ui_utils.py).
  2. Mapped `body_type` getter/setter and `BODY_TYPES` tuple in [`engine/physics/rigidbody.py`](file:///c:/Users/alexs/OneDrive/Documentos/Nova%20pasta/zennity-engine-game/engine/physics/rigidbody.py).
  3. Integrated `QComboBox` drop-down with Undo/Redo command manager support in [`editor/inspector/plugins/rigid_body_inspector_plugin.py`](file:///c:/Users/alexs/OneDrive/Documentos/Nova%20pasta/zennity-engine-game/editor/inspector/plugins/rigid_body_inspector_plugin.py).
  4. Handled unknown/invalid enum values safely without crashing.
- **Regression Test:** [`tests/editor/test_phase9_1_inspector_enum.py`](file:///c:/Users/alexs/OneDrive/Documentos/Nova%20pasta/zennity-engine-game/tests/editor/test_phase9_1_inspector_enum.py) (10/10 PASS).
- **Manual Acceptance Status:** **READY FOR USER ACCEPTANCE**
