
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

def build_bottom_panels(window, left):

    console_panel = QWidget()
    console_panel.setObjectName("ConsolePanel")
    console_layout = QVBoxLayout(console_panel)
    console_layout.setContentsMargins(6, 6, 6, 6)
    console_layout.setSpacing(5)
    console_toolbar = QWidget()
    console_toolbar.setObjectName("ConsoleToolbar")
    console_filters = QHBoxLayout(console_toolbar)
    console_filters.setContentsMargins(6, 3, 6, 3)
    window.console_level_checks = {}
    for level in ("INFO", "WARNING", "ERROR"):
        check = QCheckBox(level)
        check.setChecked(True)
        window.console_level_checks[level] = check
        console_filters.addWidget(check)
    console_filters.addStretch(1)
    window.console_clear_button = QPushButton("Limpar")
    window.console_clear_button.setFixedHeight(22)
    console_filters.addWidget(window.console_clear_button)
    console_layout.addWidget(console_toolbar)

    console = QPlainTextEdit()
    window.console_output = console
    console.setObjectName("ConsoleOutput")
    console.setReadOnly(True)
    console_layout.addWidget(console)
    window.profiler_label = QLabel("FPS: --\nObjetos: 0\nModo: EDIT")
    window.profiler_label.setObjectName("ProfilerMetric")
    window.profiler_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    profiler = QFrame()
    profiler.setObjectName("ProfilerPanel")
    profiler_layout = QVBoxLayout(profiler)
    profiler_layout.setContentsMargins(10, 10, 10, 10)
    profiler_layout.addWidget(window.profiler_label)
    profiler_layout.addStretch(1)

    console_tabs = QTabWidget()
    console_tabs.setObjectName("BottomPanelTabs")
    console_tabs.addTab(console_panel, "Console")
    console_tabs.addTab(
        EmptyStateWidget("Nenhuma saída disponível", "Mensagens do runtime aparecerão aqui.", "▤"),
        "Saída",
    )
    console_tabs.addTab(
        EmptyStateWidget("Depurador inativo", "Inicie o Play Mode para acompanhar a execução.", "◇"),
        "Depurador",
    )

    # Asset Preview aprimorado (Layout Horizontal: Imagem/Ícone à Esquerda, Detalhes à Direita)
    preview = QWidget()
    preview.setObjectName("AssetPreviewPanel")
    preview_layout = QHBoxLayout(preview)
    preview_layout.setContentsMargins(10, 10, 10, 10)
    preview_layout.setSpacing(15)

    # Container da miniatura (lado esquerdo)
    window.preview_label = QLabel("Selecione um asset\npara visualizar")
    window.preview_label.setObjectName("AssetPreviewThumbnail")
    window.preview_label.setProperty("uiState", "empty")
    window.preview_label.setAlignment(Qt.AlignCenter)
    window.preview_label.setMinimumSize(128, 104)
    window.preview_label.setMaximumWidth(180)
    window.preview_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    preview_layout.addWidget(window.preview_label)

    # Container dos metadados (lado direito)
    window.preview_details_label = QLabel()
    window.preview_details_label.setObjectName("AssetPreviewDetails")
    window.preview_details_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    window.preview_details_label.setWordWrap(True)
    window.preview_details_label.setText("<b>Nenhum asset selecionado</b><br><br>Selecione uma imagem, script, cena ou áudio na árvore de Assets para ver as informações detalhadas e pré-visualizar.")
    preview_layout.addWidget(window.preview_details_label, 1)

    console_row = QSplitter(Qt.Horizontal)
    console_row.addWidget(console_tabs)
    console_row.addWidget(profiler)
    console_row.setSizes([650, 240])

    center = QSplitter(Qt.Vertical)
    center.setChildrenCollapsible(False)
    center.addWidget(window.center_container)
    center.addWidget(console_row)
    center.addWidget(preview)
    center.setSizes([560, 150, 150])

    main = QSplitter(Qt.Horizontal)
    main.setChildrenCollapsible(False)
    main.addWidget(left)
    main.addWidget(center)
    main.setStretchFactor(1, 1)
    main.setSizes([270, 1170])
    window.main_splitter = main
    window.setCentralWidget(main)

