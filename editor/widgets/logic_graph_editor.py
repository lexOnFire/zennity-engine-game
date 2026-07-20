"""Workspace visual para criar e editar assets ``.zlogic``."""

from __future__ import annotations

import json
import unicodedata
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from .logic_graph.items import (
    LogicPortItem, LogicEdgeItem, LogicGroupResizeHandle, LogicGroupItem,
    LogicCommentItem, LogicFlipControl, LogicCollapseControl, LogicResizeHandle,
    LogicNodeItem
)
from .logic_graph.views import LogicGraphView, LogicMiniMapView
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPainterPathStroker, QPen, QBrush
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QComboBox,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from editor.ui.icons import editor_icon
from editor.widgets.logic_asset_picker import LogicAssetPickerDialog
from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    UNIQUE_EVENT_TYPES,
    consolidate_logic_events,
    create_logic_node,
    default_logic_graph,
    load_logic_graph,
    merge_logic_fragment,
    normalize_logic_graph,
    node_port_definitions,
    save_logic_graph,
    subgraph_interface,
    validate_logic_graph,
)
from engine.logic.blackboard import coerce_variable_value, save_blackboard_asset
from engine.logic.code_preview import node_code_preview
from engine.logic.recipes import build_logic_recipe, find_logic_recipes, logic_recipe
from engine.prefabs.prefab_asset import load_prefab_asset, resolve_prefab_parameters


CATEGORY_COLORS = {
    "Eventos": QColor("#d66ba0"),
    "Movimento": QColor("#4c9aff"),
    "Posição": QColor("#3fb6a8"),
    "Ação": QColor("#ae7df0"),
    "Lógica": QColor("#f0a64b"),
    "Condição": QColor("#50c878"),
    "Objetos": QColor("#47b8c8"),
    "Variáveis": QColor("#d5b84b"),
    "Subgrafos": QColor("#b48ead"),
    "Matemática": QColor("#e07a5f"),
    "Texto": QColor("#81b29a"),
    "Personalizado": QColor("#7f8b9c"),
}

PORT_COLORS = {
    "flow": QColor("#d9dde7"),
    "number": QColor("#58a6ff"),
    "bool": QColor("#50c878"),
    "text": QColor("#e6b85c"),
    "object": QColor("#47b8c8"),
    "movement": QColor("#ff8c69"),
    "any": QColor("#ae7df0"),
}

NODE_DESCRIPTIONS = {
    "event_collision_enter": "Executa quando este objeto começa uma colisão física.",
    "event_collision_exit": "Executa quando os objetos deixam de colidir.",
    "event_trigger_enter": "Executa ao entrar em um collider marcado como área/trigger.",
    "event_trigger_exit": "Executa ao sair de uma área/trigger.",
    "event_timer": "Espera a quantidade de segundos e pode repetir automaticamente.",
    "event_key_pressed": "Executa uma única vez no instante em que a tecla é apertada.",
    "event_object_created": "Executa quando este grafo cria uma instância; o novo objeto vira o alvo implícito.",
    "create_object": "Cria uma cópia profunda e independente; ações conectadas depois recebem automaticamente o novo objeto.",
    "get_tag": "Lê a Tag do objeto conectado, útil para identificar colisões e triggers.",
    "get_prefab_parameter": "Lê um valor exposto recebido quando esta instância do Prefab foi criada.",
    "create_prefab": "Cria um Prefab com overrides opcionais; câmera, áudio e lógica só são copiados quando autorizados.",
    "clone_object": "Duplica um objeto existente durante o Play Mode.",
    "destroy_after_time": "Agenda o descarte do alvo sem bloquear o restante do fluxo.",
    "add_component": "Adiciona e configura um componente no objeto alvo.",
    "remove_component": "Remove um componente opcional do objeto alvo.",
    "once": "Libera o fluxo somente na primeira execução.",
    "cooldown": "Libera o fluxo novamente após o intervalo configurado.",
    "restart_scene": "Restaura a cena ao estado capturado no início do Play Mode.",
    "get_position": "Lê as coordenadas X e Y atuais do objeto.",
    "move_by": "Move X e Y continuamente em unidades por segundo, sem exigir teclado.",
    "start_continuous_motion": "Inicia uma velocidade que continua ativa depois que a tecla é solta.",
    "update_continuous_motion": "Altera a velocidade desejada de um movimento já iniciado.",
    "pause_continuous_motion": "Pausa somente o movimento indicado, usando desaceleração quando configurada.",
    "resume_continuous_motion": "Continua um movimento pausado sem criar outro.",
    "stop_continuous_motion": "Interrompe o movimento indicado; identificador vazio mantém compatibilidade e para todos do alvo.",
    "get_continuous_motion": "Consulta velocidade, módulo e estado de um movimento durante o Play.",
    "key_pressed": "Verdadeiro somente no primeiro frame em que a tecla é apertada.",
    "key_held": "Verdadeiro durante todo o tempo em que a tecla fica segurada.",
    "compare_text": "Compara textos ignorando diferenças entre letras maiúsculas e minúsculas.",
    "patrol_axis": "Move entre dois limites e inverte automaticamente a direção ao alcançá-los.",
    "set_sprite": "Troca a imagem principal do objeto durante o Play Mode.",
    "start_texture_scroll": "Repete e desloca a imagem dentro do plano sem mover collider ou Transform.",
    "stop_texture_scroll": "Interrompe o deslocamento da imagem do plano.",
    "play_animation_asset": "Carrega e toca diretamente um arquivo de animação .zanim.",
    "stop_animation": "Interrompe a animação atual do objeto.",
    "set_position": "Move imediatamente o objeto para uma posição X e Y.",
    "rotate": "Acrescenta graus à rotação atual do objeto.",
    "set_active": "Mostra/ativa ou oculta/desativa o objeto.",
    "destroy_object": "Desativa o objeto durante o Play Mode.",
    "log_message": "Escreve uma mensagem no console do editor.",
    "add_number": "Soma dois números.",
    "subtract_number": "Subtrai B de A.",
    "multiply_number": "Multiplica dois números.",
    "divide_number": "Divide A por B e avisa se B for zero.",
    "absolute_number": "Remove o sinal negativo de um número.",
    "clamp_number": "Mantém o número entre um mínimo e um máximo.",
    "random_number": "Gera um número aleatório dentro do intervalo.",
    "delta_time": "Tempo transcorrido desde o último frame.",
    "join_text": "Junta dois valores em um único texto.",
    "to_text": "Converte número, booleano ou objeto em texto.",
}

PROPERTY_LABELS = {
    "seconds": "Segundos", "repeat": "Repetir", "minimum": "Mínimo", "maximum": "Máximo",
    "degrees": "Graus", "active": "Ativo", "text": "Texto", "value": "Valor",
    "default": "Valor inicial", "type": "Tipo", "name": "Nome", "path": "Arquivo",
    "speed": "Velocidade", "force": "Força", "condition": "Condição",
    "width": "Largura", "height": "Altura", "color": "Cor", "texture": "Imagem",
    "tag": "Tag", "relative": "Posição relativa", "inherit_source": "Copiar objeto original",
    "inherit_logic": "Copiar Logic Graphs também",
    "override_position": "Sobrescrever posição",
    "override_rotation": "Sobrescrever rotação",
    "override_scale": "Sobrescrever tamanho",
    "include_camera": "Copiar câmera do Prefab",
    "include_audio": "Copiar áudio do Prefab",
    "include_logic": "Copiar lógica do Prefab",
    "lifetime": "Destruir após (s, 0 = nunca)",
    "max_instances": "Máximo de instâncias (0 = ilimitado)",
    "max_distance": "Distância máxima (0 = ilimitada)",
    "use_pool": "Reutilizar por pool",
    "speed_x": "Velocidade X", "speed_y": "Velocidade Y",
    "repeat_x": "Repetir no eixo X", "repeat_y": "Repetir no eixo Y",
    "parallax": "Intensidade do parallax", "reset": "Voltar à origem",
    "send_to_background": "Enviar para camada Background",
    "movement": "Identificador do movimento",
    "space": "Espaço (global/local)",
    "acceleration": "Aceleração",
    "deceleration": "Desaceleração",
    "smooth": "Parada suave",
}

NODE_PROPERTY_LABELS = {
    "move_by": {"x": "Velocidade X", "y": "Velocidade Y"},
    "start_continuous_motion": {"x": "Velocidade permanente X", "y": "Velocidade permanente Y"},
    "update_continuous_motion": {"x": "Nova velocidade X", "y": "Nova velocidade Y"},
    "set_position": {"x": "Posição X", "y": "Posição Y"},
    "patrol_axis": {"axis": "Eixo", "minimum": "Limite mínimo", "maximum": "Limite máximo", "speed": "Velocidade"},
    "create_object": {"x": "Posição X", "y": "Posição Y"},
    "create_prefab": {
        "x": "Posição X", "y": "Posição Y", "rotation": "Rotação",
        "width": "Largura", "height": "Altura",
    },
}


from .logic_graph.editor_mixins import (
    LogicGraphPaletteMixin, LogicGraphRuntimeViewMixin, LogicGraphCanvasMixin,
    LogicGraphPropertiesMixin, LogicGraphPersistenceMixin,
)


class LogicGraphEditor(
    LogicGraphPaletteMixin, LogicGraphRuntimeViewMixin, LogicGraphCanvasMixin,
    LogicGraphPropertiesMixin, LogicGraphPersistenceMixin, QWidget,
):
    message = Signal(str, str)
    asset_changed = Signal()
    debug_command = Signal(str)
    play_requested = Signal()
    stop_requested = Signal()
    MAGNET_RADIUS_PIXELS = 42.0

    def __init__(self, project_root: str | Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LogicWorkspace")
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.current_path: Path | None = None
        self.graph = default_logic_graph()
        self.node_items: dict[str, LogicNodeItem] = {}
        self.edge_items: list[LogicEdgeItem] = []
        self.group_items: dict[str, LogicGroupItem] = {}
        self.comment_items: dict[str, LogicCommentItem] = {}
        self._connection_origin: LogicPortItem | None = None
        self._connection_candidate: LogicPortItem | None = None
        self._connection_preview: QGraphicsPathItem | None = None
        self._runtime_trace_active = False
        self._palette_category = "Movimento"
        self._blackboard_selected_name = ""
        self._dirty = False
        self._updating_properties = False
        self._history: list[dict[str, Any]] = []
        self._history_index = -1
        self._restoring_history = False
        self._history_timer = QTimer(self)
        self._history_timer.setSingleShot(True)
        self._history_timer.setInterval(180)
        self._history_timer.timeout.connect(self._capture_history)
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(700)
        self._autosave_timer.timeout.connect(self._autosave)
        self._build_ui()
        self._connect_ui()
        self.set_graph(self.graph)

    def _build_ui(self) -> None:
        from .logic_graph.ui_builder import build_logic_graph_ui

        build_logic_graph_ui(self)
    def _connect_ui(self) -> None:
        self.category_combo.currentTextChanged.connect(self._category_changed)
        self.node_search.textChanged.connect(lambda _text: self._refresh_palette())
        self.palette.itemDoubleClicked.connect(self._add_palette_item)
        self.recipe_search.textChanged.connect(lambda text: self._refresh_recipes(text))
        self.recipe_list.currentItemChanged.connect(self._recipe_selection_changed)
        self.recipe_list.itemDoubleClicked.connect(lambda _item: self._insert_selected_recipe())
        self.recipe_apply_button.clicked.connect(self._insert_selected_recipe)
        self.subgraph_list.itemDoubleClicked.connect(self._add_subgraph_asset)
        self.scene.selectionChanged.connect(self._selection_changed)
        self.property_tree.itemChanged.connect(self._property_changed)
        self.property_tree.itemDoubleClicked.connect(self._choose_exposed_property_asset)
        self.property_asset_button.clicked.connect(self._choose_selected_node_asset)
        self.new_button.clicked.connect(self.new_graph)
        self.new_subgraph_button.clicked.connect(self.new_subgraph)
        self.open_button.clicked.connect(self.open_dialog)
        self.save_button.clicked.connect(self.save)
        self.save_as_button.clicked.connect(lambda: self.save(save_as=True))
        self.demo_button.clicked.connect(self.open_demo)
        self.play_button.clicked.connect(self.request_play)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.fit_button.clicked.connect(self.fit_graph)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        self.add_group_button.clicked.connect(self.add_group)
        self.add_comment_button.clicked.connect(self.add_comment)
        self.organize_button.clicked.connect(self.organize_graph)
        self.align_button.clicked.connect(self.align_selected)
        self.distribute_button.clicked.connect(self.distribute_selected)
        self.breakpoint_button.clicked.connect(self.toggle_selected_breakpoint)
        self.continue_debug_button.clicked.connect(lambda: self.debug_command.emit("continue"))
        self.step_debug_button.clicked.connect(lambda: self.debug_command.emit("step"))
        self.restart_debug_button.clicked.connect(lambda: self.debug_command.emit("restart"))
        self.breakpoint_condition_edit.editingFinished.connect(self._update_breakpoint_condition)
        self.add_watch_button.clicked.connect(self._add_watch)
        self.remove_watch_button.clicked.connect(self._remove_watch)
        self.watch_expression_edit.returnPressed.connect(self._add_watch)
        self.blackboard_tree.itemSelectionChanged.connect(self._select_blackboard_variable)
        self.blackboard_tree.itemDoubleClicked.connect(lambda _item, _column: self._add_blackboard_node("get_variable"))
        self.blackboard_save_button.clicked.connect(self._save_blackboard_variable)
        self.blackboard_remove_button.clicked.connect(self._remove_blackboard_variable)
        self.blackboard_get_button.clicked.connect(lambda: self._add_blackboard_node("get_variable"))
        self.blackboard_set_button.clicked.connect(lambda: self._add_blackboard_node("set_variable"))
        self.connect_button.clicked.connect(self.connect_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.target_type.currentIndexChanged.connect(lambda _index: (self.mark_dirty(), self._refresh_target_hints()))
        self.target_value.textChanged.connect(lambda _text: (self.mark_dirty(), self._refresh_target_hints()))
        self.graph_enabled_check.toggled.connect(lambda _checked: self.mark_dirty())

    @staticmethod
