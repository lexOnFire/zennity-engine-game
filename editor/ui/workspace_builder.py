
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDockWidget, QDoubleSpinBox,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPlainTextEdit, QPushButton, QScrollArea, QSlider, QSizePolicy,
    QSplitter, QTabWidget, QToolBar, QToolButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget
)
from editor.ui.icons import TOOLBAR_ICONS, component_title, editor_icon
from editor.ui.empty_state import EmptyStateWidget
from editor.widgets.logic_graph_editor import LogicGraphEditor
from editor.ui.detached_workspace import DetachedWorkspaceWindow


def _build_viewport_workspace(window):
    window.viewport_tabs = QTabWidget()
    window.viewport_tabs.setObjectName("SceneGameTabs")
    window.viewport_host = QFrame()
    window.viewport_host.setObjectName("IsolatedViewportHost")
    window.viewport_host.setFrameShape(QFrame.StyledPanel)
    window.viewport_host.setAttribute(Qt.WA_NativeWindow, True)

    # Em vez de colocar a viewport_host como widget da aba e perder o HWND parent ao alternar,
    # fazemos a viewport_tabs atuar apenas como seletor visual e inserimos o viewport_host diretamente
    # sob um container que o mantém ativo e visível.
    window.viewport_tabs.addTab(QWidget(), "Scene")
    window.viewport_tabs.addTab(QWidget(), "Game")


def _build_animation_header(window):
    window.animation_workspace = QWidget()
    window.animation_workspace.setObjectName("AnimationWorkspace")
    animation_layout = QVBoxLayout(window.animation_workspace)
    window._animation_layout = animation_layout
    animation_layout.setContentsMargins(8, 8, 8, 8)
    animation_layout.setSpacing(8)
    animation_header = QWidget()
    animation_header.setObjectName("AnimationHeader")
    animation_title_row = QHBoxLayout(animation_header)
    animation_title_row.setContentsMargins(14, 8, 14, 8)
    animation_title_row.setSpacing(12)
    animation_title = QLabel("ZENNITY  /  ANIMATION STUDIO")
    animation_title.setObjectName("WorkspaceTitle")
    window.animation_asset_label = QLabel("Novo clip — ainda não salvo")
    window.animation_asset_label.setObjectName("WorkspaceStatus")
    window.animation_object_label = QLabel("Nenhum objeto selecionado")
    window.animation_object_label.setObjectName("WorkspaceContext")
    animation_title_row.addWidget(animation_title)
    animation_title_row.addWidget(window.animation_asset_label)
    animation_title_row.addStretch(1)
    animation_title_row.addWidget(window.animation_object_label)
    animation_layout.addWidget(animation_header)

    animation_toolbar_widget = QWidget()
    animation_toolbar_widget.setObjectName("AnimationToolbar")
    animation_toolbar = QHBoxLayout(animation_toolbar_widget)
    animation_toolbar.setContentsMargins(6, 4, 6, 4)
    animation_toolbar.setSpacing(4)
    asset_tools_label = QLabel("ASSET")
    asset_tools_label.setObjectName("PanelSectionTitle")
    animation_toolbar.addWidget(asset_tools_label)
    window.animation_new_button = QToolButton()
    window.animation_open_button = QToolButton()
    window.animation_save_button = QToolButton()
    window.animation_save_as_button = QToolButton()
    window.animation_duplicate_button = QToolButton()
    window.animation_delete_button = QToolButton()
    for button, tooltip in (
        (window.animation_new_button, "Nova animação"),
        (window.animation_open_button, "Abrir animação"),
        (window.animation_save_button, "Salvar animação"),
        (window.animation_save_as_button, "Salvar animação como..."),
        (window.animation_duplicate_button, "Duplicar animação"),
        (window.animation_delete_button, "Excluir animação"),
    ):
        button.setToolTip(tooltip)
        button.setIconSize(QSize(16, 16))
        button.setProperty("uiRole", "icon")
    window.animation_apply_button = QPushButton("Aplicar ao selecionado")
    window.animation_apply_button.setObjectName("AnimationApplyButton")
    window.animation_demo_button = QPushButton("Testar no Player")
    window.animation_demo_button.setObjectName("AnimationDemoButton")
    window.animation_open_demo_button = QPushButton("Abrir Demo Animator")
    for button, icon_name in (
        (window.animation_new_button, "new"),
        (window.animation_open_button, "open"),
        (window.animation_save_button, "save"),
        (window.animation_save_as_button, "save"),
        (window.animation_duplicate_button, "duplicate"),
        (window.animation_delete_button, "delete"),
        (window.animation_apply_button, "apply"),
        (window.animation_demo_button, "play"),
        (window.animation_open_demo_button, "open"),
    ):
        button.setIcon(editor_icon(icon_name))
    window.animation_delete_button.setProperty("uiRole", "danger")
    window.animation_apply_button.setProperty("uiRole", "primary")
    window.animation_demo_button.setProperty("uiRole", "play")
    window.animation_open_demo_button.setProperty("uiRole", "primary")
    for button in (
        window.animation_new_button, window.animation_open_button,
        window.animation_save_button, window.animation_save_as_button,
        window.animation_duplicate_button, window.animation_delete_button,
    ):
        animation_toolbar.addWidget(button)
    animation_toolbar.addSpacing(10)
    object_tools_label = QLabel("OBJETO")
    object_tools_label.setObjectName("PanelSectionTitle")
    animation_toolbar.addWidget(object_tools_label)
    animation_toolbar.addWidget(window.animation_apply_button)
    animation_toolbar.addWidget(window.animation_demo_button)
    animation_toolbar.addWidget(window.animation_open_demo_button)
    animation_toolbar.addStretch(1)
    animation_layout.addWidget(animation_toolbar_widget)


def _build_animation_library(window):
    window.animation_content_splitter = QSplitter(Qt.Horizontal)
    window.animation_content_splitter.setObjectName("AnimationContentSplitter")
    window.animation_content_splitter.setChildrenCollapsible(False)

    library_panel = QFrame()
    library_panel.setObjectName("AnimationLibraryPanel")
    library_layout = QVBoxLayout(library_panel)
    library_layout.setContentsMargins(8, 8, 8, 8)
    library_title = QLabel("BIBLIOTECA")
    library_title.setObjectName("PanelSectionTitle")
    library_layout.addWidget(library_title)
    window.animation_library_tree = QTreeWidget()
    window.animation_library_tree.setObjectName("AnimationLibraryTree")
    window.animation_library_tree.setHeaderHidden(True)
    window.animation_library_tree.setMinimumWidth(140)
    window.animation_library_tree.setToolTip("Duplo clique para abrir uma animação salva")
    library_layout.addWidget(window.animation_library_tree, 1)
    library_hint = QLabel("Assets/Animations\nClips .zanim e controllers .zanimator")
    library_hint.setObjectName("PanelHint")
    library_layout.addWidget(library_hint)
    library_panel.setMinimumWidth(220)
    window.animation_content_splitter.addWidget(library_panel)

    preview_panel = QWidget()
    preview_panel.setObjectName("AnimationPreviewPanel")
    preview_panel.setMinimumWidth(220)
    window._animation_preview_panel = preview_panel

def _build_animation_preview(window):
    preview_panel = window._animation_preview_panel
    preview_column = QVBoxLayout(preview_panel)
    preview_column.setContentsMargins(8, 8, 8, 8)
    window.animator_preview = QLabel("Selecione um objeto com Animator 2D")
    window.animator_preview.setObjectName("AnimationPreview")
    window.animator_preview.setProperty("uiState", "empty")
    window.animator_preview.setAlignment(Qt.AlignCenter)
    window.animator_preview.setMinimumHeight(160)
    window.animator_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    preview_column.addWidget(window.animator_preview, 1)

    timeline_panel = QFrame()
    timeline_panel.setObjectName("AnimationTimelinePanel")
    timeline_layout = QVBoxLayout(timeline_panel)
    timeline_layout.setContentsMargins(8, 7, 8, 8)
    timeline_header = QHBoxLayout()
    timeline_title = QLabel("TIMELINE")
    timeline_title.setObjectName("PanelSectionTitle")
    timeline_header.addWidget(timeline_title)
    timeline_header.addStretch(1)
    window.animation_frame_label = QLabel("Frame 1 / 1")
    window.animation_frame_label.setObjectName("AnimationFrameCounter")
    timeline_header.addWidget(window.animation_frame_label)
    timeline_layout.addLayout(timeline_header)
    playback_row = QHBoxLayout()
    window.animation_first_frame_button = QPushButton("|◀")
    window.animation_previous_frame_button = QPushButton("◀")
    window.animation_play_button = QPushButton("⏸")
    window.animation_next_frame_button = QPushButton("▶")
    window.animation_last_frame_button = QPushButton("▶|")
    for button, icon_name in (
        (window.animation_first_frame_button, "first"),
        (window.animation_previous_frame_button, "previous"),
        (window.animation_play_button, "pause"),
        (window.animation_next_frame_button, "next"),
        (window.animation_last_frame_button, "last"),
    ):
        button.setText("")
        button.setIcon(editor_icon(icon_name))
    for button, tooltip in (
        (window.animation_first_frame_button, "Primeiro frame"),
        (window.animation_previous_frame_button, "Frame anterior"),
        (window.animation_play_button, "Reproduzir ou pausar prévia"),
        (window.animation_next_frame_button, "Próximo frame"),
        (window.animation_last_frame_button, "Último frame"),
    ):
        button.setToolTip(tooltip)
    for button in (
        window.animation_first_frame_button, window.animation_previous_frame_button,
        window.animation_play_button, window.animation_next_frame_button,
        window.animation_last_frame_button,
    ):
        button.setMaximumWidth(48)
        button.setProperty("uiRole", "icon")
        playback_row.addWidget(button)
    playback_row.addStretch(1)
    timeline_layout.addLayout(playback_row)
    window.animation_timeline = QSlider(Qt.Horizontal)
    window.animation_timeline.setRange(0, 0)
    window.animation_timeline.setToolTip("Arraste para visualizar qualquer quadro")
    timeline_layout.addWidget(window.animation_timeline)
    event_header = QHBoxLayout()
    event_header.addWidget(QLabel("EVENTOS POR FRAME"))
    event_header.addStretch(1)
    window.animation_add_event_button = QPushButton("+ Evento")
    window.animation_remove_event_button = QPushButton("− Evento")
    event_header.addWidget(window.animation_add_event_button)
    event_header.addWidget(window.animation_remove_event_button)
    timeline_layout.addLayout(event_header)
    window.animation_events_tree = QTreeWidget()
    window.animation_events_tree.setHeaderLabels(["Frame", "Evento", "Payload"])
    window.animation_events_tree.setMaximumHeight(105)
    window.animation_events_tree.setRootIsDecorated(False)
    timeline_layout.addWidget(window.animation_events_tree)
    current_clip_row = QHBoxLayout()
    current_clip_label = QLabel("Clip ativo")
    current_clip_label.setObjectName("PanelHint")
    current_clip_row.addWidget(current_clip_label)
    window._animation_preview_column = preview_column
    window._animation_timeline_panel = timeline_panel
    window._animation_timeline_layout = timeline_layout
    window._animation_current_clip_row = current_clip_row

def _build_animation_properties(window):
    window.animator_current_lbl = QLineEdit("Nenhum")
    window.animator_current_lbl.setReadOnly(True)
    window._animation_current_clip_row.addWidget(window.animator_current_lbl, 1)
    window._animation_timeline_layout.addLayout(window._animation_current_clip_row)
    window._animation_preview_column.addWidget(window._animation_timeline_panel)
    window.animation_content_splitter.addWidget(window._animation_preview_panel)

    window.animator_body = QWidget()
    window.animator_body.setObjectName("AnimationPropertiesPanel")
    animator_lay = QFormLayout(window.animator_body)
    animator_lay.setContentsMargins(10, 10, 10, 10)
    object_section_title = QLabel("OBJETO SELECIONADO")
    object_section_title.setObjectName("PanelSectionTitle")
    animator_lay.addRow(object_section_title)
    window.show_animator_chk = QCheckBox("Animator 2D ativo")
    animator_lay.addRow(window.show_animator_chk)
    window.btn_del_anim = QPushButton("Excluir Animator")
    window.btn_del_anim.setObjectName("AnimationDangerButton")
    window.btn_del_anim.setProperty("uiRole", "dangerAction")
    animator_lay.addRow(window.btn_del_anim)
    controller_section_title = QLabel("ANIMATOR CONTROLLER")
    controller_section_title.setObjectName("PanelSectionTitle")
    animator_lay.addRow(controller_section_title)
    window.animation_controller_combo = QComboBox()
    window.animation_controller_combo.addItem("Nenhum", "")
    animator_lay.addRow("Controller", window.animation_controller_combo)
    controller_actions = QWidget()
    controller_actions_layout = QHBoxLayout(controller_actions)
    controller_actions_layout.setContentsMargins(0, 0, 0, 0)
    window.animation_new_controller_button = QPushButton("Novo")
    window.animation_edit_controller_button = QPushButton("Editar")
    controller_actions_layout.addWidget(window.animation_new_controller_button)
    controller_actions_layout.addWidget(window.animation_edit_controller_button)
    animator_lay.addRow("Ações", controller_actions)
    window.animation_controller_summary = QLabel("Use um controller para criar estados e transições.")
    window.animation_controller_summary.setObjectName("PanelHint")
    window.animation_controller_summary.setWordWrap(True)
    animator_lay.addRow(window.animation_controller_summary)
    clip_runtime_section_title = QLabel("CLIP DIRETO")
    clip_runtime_section_title.setObjectName("PanelSectionTitle")
    animator_lay.addRow(clip_runtime_section_title)
    window.animator_clip_combo = QComboBox()
    animator_lay.addRow("Clip", window.animator_clip_combo)
    window.animator_speed_field = QDoubleSpinBox()
    window.animator_speed_field.setRange(0.0, 100.0)
    window.animator_speed_field.setValue(1.0)
    animator_lay.addRow("Velocidade", window.animator_speed_field)
    clip_actions = QWidget()
    clip_actions_layout = QHBoxLayout(clip_actions)
    clip_actions_layout.setContentsMargins(0, 0, 0, 0)
    window.animator_add_clip_button = QPushButton("+ Clip")
    window.animator_remove_clip_button = QPushButton("− Clip")
    clip_actions_layout.addWidget(window.animator_add_clip_button)
    clip_actions_layout.addWidget(window.animator_remove_clip_button)
    animator_lay.addRow("Clips", clip_actions)
    clip_section_title = QLabel("PROPRIEDADES DO CLIP")
    clip_section_title.setObjectName("PanelSectionTitle")
    animator_lay.addRow(clip_section_title)
    window.animator_sheet_combo = QComboBox()
    animator_lay.addRow("Sprite Sheet", window.animator_sheet_combo)
    window.animator_frame_width = QDoubleSpinBox()
    window.animator_frame_height = QDoubleSpinBox()
    window.animator_start_frame = QDoubleSpinBox()
    window.animator_frame_count = QDoubleSpinBox()
    for field, minimum, maximum in ((window.animator_frame_width, 1, 8192), (window.animator_frame_height, 1, 8192), (window.animator_start_frame, 0, 100000), (window.animator_frame_count, 1, 100000)):
        field.setRange(minimum, maximum)
        field.setDecimals(0)
        field.setKeyboardTracking(False)
    animator_lay.addRow("Largura do frame", window.animator_frame_width)
    animator_lay.addRow("Altura do frame", window.animator_frame_height)
    animator_lay.addRow("Frame inicial", window.animator_start_frame)
    animator_lay.addRow("Nº de frames", window.animator_frame_count)
    window.animator_fps_field = QDoubleSpinBox()
    window.animator_fps_field.setRange(0.1, 240.0)
    window.animator_fps_field.setValue(8.0)
    window.animator_fps_field.setKeyboardTracking(False)
    animator_lay.addRow("FPS", window.animator_fps_field)
    window.animator_loop_field = QCheckBox()
    window.animator_loop_field.setChecked(True)
    animator_lay.addRow("Repetir", window.animator_loop_field)
    properties_hint = QLabel("Escolha o Sprite Sheet e informe o tamanho de cada frame. Salve e aplique ao objeto selecionado.")
    properties_hint.setObjectName("PanelHint")
    properties_hint.setWordWrap(True)
    animator_lay.addRow(properties_hint)

    window.animation_properties_scroll = QScrollArea()
    window.animation_properties_scroll.setObjectName("AnimationPropertiesScroll")
    window.animation_properties_scroll.setWidgetResizable(True)
    window.animation_properties_scroll.setFrameShape(QFrame.NoFrame)
    window.animation_properties_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    window.animation_properties_scroll.setMinimumWidth(290)
    window.animation_properties_scroll.setWidget(window.animator_body)
    window.animation_content_splitter.addWidget(window.animation_properties_scroll)
    window.animation_content_splitter.setStretchFactor(0, 0)
    window.animation_content_splitter.setStretchFactor(1, 1)
    window.animation_content_splitter.setStretchFactor(2, 0)
    window.animation_content_splitter.setSizes([230, 700, 310])
    window._animation_layout.addWidget(window.animation_content_splitter, 1)

def _build_detached_workspaces(window):
    window.logic_workspace = LogicGraphEditor()
    window.animation_window = DetachedWorkspaceWindow("Zennity — Editor de Animação", window.animation_workspace, window)
    window.animation_window.resize(1320, 820)
    window.animation_window.setMinimumSize(980, 640)

    window.center_container = QWidget()
    layout = QVBoxLayout(window.center_container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(window.viewport_tabs)
    layout.addWidget(window.viewport_host)
    layout.setStretchFactor(window.viewport_host, 1)


def build_center_workspace(window):
    _build_viewport_workspace(window)
    _build_animation_header(window)
    _build_animation_library(window)
    _build_animation_preview(window)
    _build_animation_properties(window)
    _build_detached_workspaces(window)
