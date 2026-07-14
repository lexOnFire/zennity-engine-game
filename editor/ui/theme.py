"""Geração e aplicação do tema central do editor."""
from __future__ import annotations

from typing import Any

from .tokens import DEFAULT_TOKENS, EditorThemeTokens


_QSS_TEMPLATE = r"""
QMainWindow { background: $BG; }
QWidget {
    color: $TEXT;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: $FONT_SIZEpx;
    selection-background-color: $ACCENT_SOFT;
    selection-color: $TEXT;
}
QWidget:disabled { color: $TEXT_DISABLED; }

QMenuBar {
    background: $BG;
    border-bottom: 1px solid $BORDER;
    padding: $SPACING_XSpx $SPACING_SMpx;
}
QMenuBar::item { border-radius: $RADIUS_SMALLpx; padding: 5px 10px; }
QMenuBar::item:selected { background: $SURFACE_HOVER; }
QMenu {
    background: $SURFACE_RAISED;
    border: 1px solid $BORDER_STRONG;
    border-radius: $RADIUSpx;
    padding: 5px;
}
QMenu::item { border-radius: $RADIUS_SMALLpx; padding: 7px 24px; }
QMenu::item:selected { background: $ACCENT_SOFT; }
QMenu::separator { background: $BORDER; height: 1px; margin: 5px 8px; }

QToolBar#CommandBar {
    background: $SURFACE;
    border: none;
    border-bottom: 1px solid $BORDER;
    spacing: $SPACING_XSpx;
    padding: 5px $SPACING_SMpx;
}
QToolBar#CommandBar::separator { background: $BORDER; width: 1px; margin: 4px 5px; }
QToolBar#CommandBar QToolButton { qproperty-iconSize: 17px 17px; }
QToolButton, QPushButton {
    background: $SURFACE_RAISED;
    border: 1px solid $BORDER;
    border-radius: $RADIUSpx;
    color: $TEXT;
    min-height: $CONTROL_HEIGHTpx;
    padding: 3px 10px;
}
QToolButton:hover, QPushButton:hover { background: $SURFACE_HOVER; border-color: $BORDER_STRONG; }
QToolButton:pressed, QPushButton:pressed { background: $ACCENT_SOFT; border-color: $ACCENT; }
QToolButton:checked, QPushButton:checked { background: $ACCENT_SOFT; border-color: $ACCENT; color: #ffffff; }
QToolButton:disabled, QPushButton:disabled { background: $SURFACE; border-color: $BORDER; color: $TEXT_DISABLED; }
QToolButton[uiRole="play"] { color: $SUCCESS; }
QToolButton[uiRole="pause"] { color: $WARNING; }
QToolButton[uiRole="stop"] { color: $DANGER; }
QPushButton[uiRole="primary"] { background: $ACCENT; border-color: $ACCENT; color: #ffffff; font-weight: 600; }
QPushButton[uiRole="primary"]:hover { background: $ACCENT_HOVER; }
QPushButton[uiRole="danger"], QToolButton[uiRole="danger"] { background: transparent; border: none; color: $DANGER; min-height: 18px; padding: 1px 4px; }
QPushButton[uiRole="dangerAction"] { background: $DANGER_SOFT; border-color: $DANGER; color: #ffffff; }
QPushButton[uiRole="dangerAction"]:hover { background: $DANGER; border-color: $DANGER; }
QPushButton[uiRole="icon"], QToolButton[uiRole="icon"] { background: transparent; border: none; min-height: 18px; padding: 1px 4px; }

QTabWidget::pane { background: $SURFACE; border: 1px solid $BORDER; top: -1px; }
QTabBar::tab {
    background: $BG;
    border: 1px solid transparent;
    border-bottom: 1px solid $BORDER;
    color: $TEXT_MUTED;
    min-width: 68px;
    padding: 7px 12px;
}
QTabBar::tab:hover { background: $SURFACE_HOVER; color: $TEXT; }
QTabBar::tab:selected { background: $SURFACE; border-color: $BORDER; border-bottom-color: $SURFACE; color: $TEXT; }
QTabWidget#SceneGameTabs QTabBar::tab:selected { color: $ACCENT_HOVER; font-weight: 600; }
QTabWidget#BottomPanelTabs QTabBar::tab { min-width: 82px; padding: 6px 12px; }

QWidget#AnimationWorkspace, QWidget#ConsolePanel, QFrame#ProfilerPanel {
    background: $SURFACE;
}
QWidget#AnimationToolbar, QWidget#ConsoleToolbar {
    background: $SURFACE_RAISED;
    border: 1px solid $BORDER;
    border-radius: $RADIUSpx;
}
QLabel#WorkspaceTitle { color: $TEXT; font-size: 15px; font-weight: 700; }
QLabel#WorkspaceContext { color: $ACCENT_HOVER; font-weight: 600; }
QLabel#WorkspaceStatus, QLabel#PanelHint { color: $TEXT_MUTED; }
QLabel#WorkspaceStatus[uiState="saved"] { color: $SUCCESS; }
QLabel#WorkspaceStatus[uiState="dirty"] { color: $WARNING; }
QFrame#AnimationLibraryPanel, QWidget#AnimationPropertiesPanel {
    background: $BG;
    border: 1px solid $BORDER;
    border-radius: $RADIUSpx;
}
QLabel#PanelSectionTitle {
    color: $TEXT_MUTED;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}
QTreeWidget#AnimationLibraryTree { background: $INPUT_BG; border: none; }
QWidget#AnimationPreviewPanel { background: $SURFACE; }
QFrame#AnimationTimelinePanel {
    background: $SURFACE_RAISED;
    border: 1px solid $BORDER;
    border-radius: $RADIUSpx;
}
QLabel#AnimationFrameCounter { color: $TEXT_MUTED; font-family: "Cascadia Mono", "Consolas", monospace; }
QScrollArea#AnimationPropertiesScroll { background: $SURFACE; border: none; }
QScrollArea#AnimationPropertiesScroll > QWidget > QWidget { background: $SURFACE; }
QLabel#AnimationPreview {
    background: $INPUT_BG;
    border: 1px solid $BORDER;
    border-radius: $RADIUSpx;
    color: $TEXT_DISABLED;
}
QLabel#AnimationPreview[uiState="empty"] { border-style: dashed; }
QLabel#AnimationPreview[uiState="error"] { border-color: $DANGER; color: $DANGER; }
QPushButton[uiRole="play"] { color: $SUCCESS; }
QPlainTextEdit#ConsoleOutput, QTextEdit#ConsoleOutput {
    background: $INPUT_BG;
    border: 1px solid $BORDER;
    border-radius: $RADIUSpx;
    color: $TEXT;
    font-family: "Cascadia Mono", "Consolas", monospace;
    padding: 6px;
}
QLabel#ProfilerMetric {
    color: $TEXT;
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-weight: 600;
}
QWidget#ProfilerMetrics { background: transparent; }
QWidget#ProfilerChart { background: $INPUT_BG; border-radius: $RADIUSpx; }

QDialog#BuildReportDialog { background: $BG; }
QFrame#BuildSummary {
    background: $SURFACE_RAISED;
    border: 1px solid $BORDER_STRONG;
    border-radius: $RADIUSpx;
}
QLabel#BuildStatus { font-size: 18px; font-weight: 700; }
QLabel#BuildStatus[uiState="success"] { color: $SUCCESS; }
QLabel#BuildStatus[uiState="error"] { color: $DANGER; }
QLabel#BuildDestination { color: $TEXT; font-family: "Cascadia Mono", "Consolas", monospace; }
QLabel#BuildDetails { color: $TEXT_MUTED; }
QTabWidget#BuildReportTabs QTreeWidget, QTabWidget#BuildReportTabs QPlainTextEdit { border: none; }

QDialog#ComponentPickerDialog, QDialog#ProjectValidationDialog, QDialog#PreferencesDialog {
    background: $BG;
}
QLabel#DialogTitle { color: $TEXT; font-size: 15px; font-weight: 700; }
QLabel#DialogDescription { color: $TEXT_MUTED; padding: 6px 2px; }
QTreeWidget#ComponentPickerTree, QTreeWidget#ValidationIssues { border-radius: $RADIUSpx; }
QFrame#ValidationSummary {
    background: $SURFACE_RAISED;
    border: 1px solid $BORDER_STRONG;
    border-radius: $RADIUSpx;
}
QLabel#ValidationStatus { font-size: 18px; font-weight: 700; }
QLabel#ValidationStatus[uiState="success"] { color: $SUCCESS; }
QLabel#ValidationStatus[uiState="error"] { color: $DANGER; }
QLabel#ValidationDetails { color: $TEXT_MUTED; }

QWidget#EmptyState { background: $SURFACE; }
QLabel#EmptyStateGlyph { color: $TEXT_DISABLED; font-size: 24px; }
QLabel#EmptyStateTitle { color: $TEXT_MUTED; font-size: 13px; font-weight: 600; }
QLabel#EmptyStateDescription { color: $TEXT_DISABLED; }

QWidget#AssetPreviewPanel { background: $SURFACE; }
QLabel#AssetPreviewThumbnail {
    background: $INPUT_BG;
    border: 1px solid $BORDER;
    border-radius: $RADIUSpx;
    color: $TEXT_MUTED;
    font-size: 14px;
}
QLabel#AssetPreviewThumbnail[uiState="empty"] {
    border: 1px dashed $BORDER_STRONG;
    color: $TEXT_DISABLED;
}
QLabel#AssetPreviewDetails { color: $TEXT; padding: 2px 4px; }

QDockWidget { background: $SURFACE; color: $TEXT_MUTED; font-weight: 600; }
QDockWidget::title { background: $SURFACE; border-bottom: 1px solid $BORDER; padding: 7px 9px; text-align: left; }
QWidget#EditorPanel, QWidget#InspectorPanel, QFrame#PremiumPanel { background: $SURFACE; }
QWidget#InspectorToolbar { background: $SURFACE_RAISED; border: 1px solid $BORDER; border-radius: $RADIUSpx; }
QLabel#InspectorToolbarTitle { color: $TEXT_MUTED; font-weight: 700; }
QLabel#InspectorObjectName { color: $TEXT; font-size: 14px; font-weight: 700; }

QTreeWidget, QTreeView, QListView, QTableView, QPlainTextEdit, QTextEdit, QTextBrowser {
    background: $INPUT_BG;
    border: 1px solid $BORDER;
    color: $TEXT;
    outline: none;
}
QTreeWidget::item, QTreeView::item { border-radius: $RADIUS_SMALLpx; min-height: 22px; padding: 3px 5px; }
QTreeWidget::item:hover, QTreeView::item:hover { background: $SURFACE_HOVER; }
QTreeWidget::item:selected, QTreeView::item:selected { background: $ACCENT_SOFT; color: #ffffff; }
QTreeWidget#HierarchyTree, QTreeWidget#AssetsTree { border: none; }

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: $INPUT_BG;
    border: 1px solid $BORDER;
    border-radius: $RADIUS_SMALLpx;
    color: $TEXT;
    min-height: $CONTROL_HEIGHTpx;
    padding: 2px 7px;
}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover { border-color: $BORDER_STRONG; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: $ACCENT; }
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled { background: $BG; color: $TEXT_DISABLED; }
QComboBox QAbstractItemView { background: $SURFACE_RAISED; border: 1px solid $BORDER_STRONG; selection-background-color: $ACCENT_SOFT; }
QCheckBox { color: $TEXT_MUTED; spacing: 6px; }
QCheckBox::indicator { width: 14px; height: 14px; }

QWidget#InspectorComponentHeader {
    background: $SURFACE_RAISED;
    border: 1px solid $BORDER;
    border-radius: $RADIUS_SMALLpx;
    min-height: 28px;
}
QWidget#InspectorComponentHeader:hover { border-color: $BORDER_STRONG; }
QWidget#InspectorComponentBody {
    background: $SURFACE;
    border-left: 1px solid $BORDER;
    border-right: 1px solid $BORDER;
    border-bottom: 1px solid $BORDER;
}
QLabel#InspectorComponentTitle { color: $TEXT; font-weight: 600; }
QLabel#InspectorPropertyLabel { color: $TEXT_MUTED; min-width: 58px; }
QPushButton#InspectorAddComponentButton { margin: 7px 38px 9px 38px; }
QPushButton#InspectorAddComponentButton:hover { border-color: $ACCENT; }
QScrollArea#InspectorScrollArea { background: $SURFACE; border: none; }

QSplitter::handle { background: $BG; }
QSplitter::handle:hover { background: $ACCENT_SOFT; }
QSplitter::handle:horizontal { width: 4px; }
QSplitter::handle:vertical { height: 4px; }
QScrollBar:vertical { background: $BG; border: none; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: $BORDER_STRONG; border-radius: 4px; min-height: 28px; margin: 2px; }
QScrollBar::handle:vertical:hover { background: $TEXT_MUTED; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: $BG; border: none; height: 10px; }
QScrollBar::handle:horizontal { background: $BORDER_STRONG; border-radius: 4px; min-width: 28px; margin: 2px; }

QStatusBar { background: $BG; border-top: 1px solid $BORDER; color: $TEXT_MUTED; min-height: 23px; }
QStatusBar::item { border: none; }
QToolTip { background: $SURFACE_RAISED; border: 1px solid $BORDER_STRONG; color: $TEXT; padding: 5px; }
"""


def build_editor_stylesheet(tokens: EditorThemeTokens = DEFAULT_TOKENS) -> str:
    values = {
        "BG": tokens.bg, "SURFACE": tokens.surface, "SURFACE_RAISED": tokens.surface_raised,
        "SURFACE_HOVER": tokens.surface_hover, "INPUT_BG": tokens.input_bg,
        "BORDER": tokens.border, "BORDER_STRONG": tokens.border_strong,
        "TEXT": tokens.text, "TEXT_MUTED": tokens.text_muted, "TEXT_DISABLED": tokens.text_disabled,
        "ACCENT": tokens.accent, "ACCENT_HOVER": tokens.accent_hover, "ACCENT_SOFT": tokens.accent_soft,
        "SUCCESS": tokens.success, "WARNING": tokens.warning, "DANGER": tokens.danger,
        "DANGER_SOFT": tokens.danger_soft,
        "RADIUS_SMALL": str(tokens.radius_small), "RADIUS": str(tokens.radius),
        "SPACING_XS": str(tokens.spacing_xs), "SPACING_SM": str(tokens.spacing_sm),
        "FONT_SIZE": str(tokens.font_size), "CONTROL_HEIGHT": str(tokens.control_height),
    }
    stylesheet = _QSS_TEMPLATE
    for name in sorted(values, key=len, reverse=True):
        value = values[name]
        stylesheet = stylesheet.replace(f"${name}", value)
    return stylesheet


EDITOR_QSS = build_editor_stylesheet()


def apply_editor_theme(app: Any) -> None:
    from PySide6.QtGui import QFont

    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(EDITOR_QSS)


def polish_editor_widgets(window: Any) -> None:
    """Migra widgets legados para roles do Design System sem recriá-los."""
    from PySide6.QtWidgets import QAbstractButton, QWidget

    for attribute in ("hierarchy_tree", "assets_tree", "prefab_tree"):
        widget = getattr(window, attribute, None)
        if widget is not None:
            widget.setObjectName({
                "hierarchy_tree": "HierarchyTree",
                "assets_tree": "AssetsTree",
                "prefab_tree": "PrefabsTree",
            }[attribute])
    named_attributes = {
        "btn_collapse_dock": ("InspectorPanelControl", "icon"),
        "btn_float_dock": ("InspectorPanelControl", "icon"),
        "btn_dock_dock": ("InspectorPanelControl", "icon"),
        "btn_collapse_transform": ("InspectorFoldoutButton", "icon"),
        "btn_collapse_renderer": ("InspectorFoldoutButton", "icon"),
        "btn_collapse_audio": ("InspectorFoldoutButton", "icon"),
        "btn_collapse_rigidbody": ("InspectorFoldoutButton", "icon"),
        "btn_collapse_collider": ("InspectorFoldoutButton", "icon"),
        "btn_collapse_camera": ("InspectorFoldoutButton", "icon"),
        "btn_collapse_ui": ("InspectorFoldoutButton", "icon"),
        "btn_delete_renderer": ("InspectorDangerButton", "danger"),
        "btn_delete_audio": ("InspectorDangerButton", "danger"),
        "btn_del_rb": ("InspectorDangerButton", "danger"),
        "btn_del_col": ("InspectorDangerButton", "danger"),
        "btn_delete_camera": ("InspectorDangerButton", "danger"),
        "btn_delete_ui": ("InspectorDangerButton", "danger"),
        "add_component_button": ("InspectorAddComponentButton", "primary"),
    }
    for attribute, (object_name, role) in named_attributes.items():
        widget = getattr(window, attribute, None)
        if widget is not None:
            widget.setObjectName(object_name)
            widget.setProperty("uiRole", role)
            widget.setStyleSheet("")

    managed_names = {
        "InspectorComponentHeader", "InspectorComponentBody", "InspectorCheckBox",
        "InspectorNumberField", "InspectorTextField", "InspectorCombo",
        "InspectorAddComponentButton", "InspectorRemoveComponentButton",
        "InspectorObjectName", "InspectorScriptSelector", "InspectorScrollArea",
        "InspectorPanel", "InspectorToolbar", "InspectorToolbarTitle",
        "AnimationWorkspace", "AnimationToolbar", "AnimationLibraryPanel",
        "AnimationLibraryTree", "AnimationPreview", "AnimationPropertiesPanel",
        "ConsolePanel", "ConsoleToolbar", "ConsoleOutput", "ProfilerPanel",
        "ProfilerMetrics", "ProfilerMetric", "ProfilerChart", "BottomPanelTabs",
        "EmptyState", "EmptyStateGlyph", "EmptyStateTitle", "EmptyStateDescription",
        "AssetPreviewPanel", "AssetPreviewThumbnail", "AssetPreviewDetails",
    }
    for widget in window.findChildren(QWidget):
        if widget.objectName() in managed_names:
            widget.setStyleSheet("")
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    role_by_tooltip = {"Play": "play", "Pause": "pause", "Stop": "stop"}
    for button in window.findChildren(QAbstractButton):
        role = role_by_tooltip.get(button.toolTip())
        if role:
            button.setProperty("uiRole", role)
        if button.objectName() in {"InspectorFoldoutButton", "InspectorPanelControl"}:
            button.setProperty("uiRole", "icon")
        elif button.objectName() == "InspectorDangerButton":
            button.setProperty("uiRole", "danger")
        button.style().unpolish(button)
        button.style().polish(button)
    window.update()
