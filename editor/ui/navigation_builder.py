
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QPushButton, QSplitter, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget
)

def build_navigation_panels(window):
    hierarchy = QTreeWidget()
    window.hierarchy_tree = hierarchy
    hierarchy.setObjectName("HierarchyTree")
    hierarchy.setHeaderHidden(True)
    root = QTreeWidgetItem(["MainScene"])
    environment = QTreeWidgetItem(["Environment"])
    environment.addChildren([QTreeWidgetItem(["DirectionalLight"]), QTreeWidgetItem(["Terrain"])])
    root.addChildren([environment, QTreeWidgetItem(["Chao"]), QTreeWidgetItem(["Player"]), QTreeWidgetItem(["Enemies"])])
    hierarchy.addTopLevelItem(root)
    hierarchy.expandAll()

    assets = QTreeWidget()
    window.assets_tree = assets
    assets.setObjectName("AssetsTree")
    assets.setHeaderHidden(True)
    asset_root = QTreeWidgetItem(["Assets"])
    asset_root.addChildren([QTreeWidgetItem(["Scenes"]), QTreeWidgetItem(["Logic"]), QTreeWidgetItem(["Animations"]), QTreeWidgetItem(["Textures"]), QTreeWidgetItem(["Audio"])])
    assets.addTopLevelItem(asset_root)
    assets.expandAll()

    create_panel = QWidget()
    create_layout = QVBoxLayout(create_panel)
    create_layout.setContentsMargins(6, 6, 6, 6)
    window.create_buttons = {}
    for label, kind in (
        ("Empty Object", "Empty"), ("Sprite 2D", "Sprite"),
        ("Player 2D", "Player"), ("Platform 2D", "Platform"),
        ("Enemy 2D", "Enemy"), ("Trigger 2D", "Trigger"),
        ("Camera 2D", "Camera"),
    ):
        button = QPushButton(label)
        button.setObjectName("CreatePresetButton")
        window.create_buttons[kind] = button
        create_layout.addWidget(button)
    create_layout.addStretch(1)

    hierarchy_tabs = QTabWidget()
    hierarchy_tabs.setObjectName("NavigationTabs")
    hierarchy_tabs.addTab(hierarchy, "Hierarchy")
    hierarchy_tabs.addTab(create_panel, "Criar")

    prefab_tree = QTreeWidget()
    window.prefab_tree = prefab_tree
    prefab_tree.setObjectName("PrefabsTree")
    prefab_tree.setHeaderHidden(True)
    prefab_tree.addTopLevelItem(QTreeWidgetItem(["Prefabs disponíveis no projeto"] ))
    asset_tabs = QTabWidget()
    asset_tabs.setObjectName("AssetTabs")
    asset_tabs.addTab(assets, "Assets")
    asset_tabs.addTab(prefab_tree, "Adicionar Prefabs")

    left = QSplitter(Qt.Vertical)
    left.setChildrenCollapsible(False)
    left.addWidget(hierarchy_tabs)
    left.addWidget(asset_tabs)
    left.setSizes([300, 420])
    left.setMinimumWidth(240)

    return left
