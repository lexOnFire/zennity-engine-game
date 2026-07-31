"""Widget de Visual Profiler para análise de performance de runtime."""
from __future__ import annotations

from typing import Any
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QScrollArea, QFrame, QPushButton
)
from editor.core.event_bus import EventBus
from editor.runtime.execution_analysis_framework import ExecutionAnalysisFramework


class ProfilerCategoryWidget(QFrame):
    def __init__(self, name: str, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.name = name
        self.setStyleSheet(f"""
            QFrame {{
                background: #101621;
                border: 1px solid #232d3d;
                border-radius: 6px;
                padding: 4px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self.name_label = QLabel(name)
        self.name_label.setFixedWidth(80)
        self.name_label.setStyleSheet("color: #a0aec0; font-weight: bold; font-size: 11px; border: none; background: transparent;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background: #171f2d;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        
        self.value_label = QLabel("0.0 ms")
        self.value_label.setFixedWidth(60)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setStyleSheet("color: #e2e8f0; font-family: Consolas; font-size: 11px; border: none; background: transparent;")

        layout.addWidget(self.name_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.value_label)

    def update_value(self, value_ms: float, max_ms: float = 16.6) -> None:
        self.value_label.setText(f"{value_ms:.2f} ms")
        pct = min(100, int((value_ms / max_ms) * 100))
        self.progress_bar.setValue(pct)


class VisualProfilerWidget(QWidget):
    """Exibe métricas de execução em tempo real da viewport isolada."""

    COLORS = {
        "physics": "#f56565",
        "scripts": "#48bb78",
        "animation": "#4299e1",
        "audio": "#ed64a6",
        "rendering": "#ecc94b",
        "overhead": "#a0aec0",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("VisualProfilerWidget")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📊 Análise de Performance do Runtime")
        title.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 13px;")
        
        self.fps_label = QLabel("FPS: -- | Frame: -- ms")
        self.fps_label.setStyleSheet("color: #4fd1c5; font-family: Consolas; font-weight: bold; font-size: 12px;")
        
        self.btn_reset = QPushButton("Resetar Métricas")
        self.btn_reset.setFixedWidth(120)
        self.btn_reset.clicked.connect(self._reset_metrics)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background: #2d3748; color: #e2e8f0; border-radius: 4px; padding: 4px; border: 1px solid #4a5568;
            }
            QPushButton:hover { background: #4a5568; }
        """)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.fps_label)
        header_layout.addWidget(self.btn_reset)
        
        main_layout.addLayout(header_layout)
        
        # Categories Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.categories_container = QWidget()
        self.categories_container.setStyleSheet("background: transparent;")
        self.categories_layout = QVBoxLayout(self.categories_container)
        self.categories_layout.setContentsMargins(0, 0, 0, 0)
        self.categories_layout.setSpacing(4)
        
        self.scroll_area.setWidget(self.categories_container)
        main_layout.addWidget(self.scroll_area)
        
        # Summary
        self.summary_label = QLabel("Aguardando execução...")
        self.summary_label.setStyleSheet("color: #718096; font-size: 11px; font-style: italic;")
        main_layout.addWidget(self.summary_label)
        
        self.category_widgets: dict[str, ProfilerCategoryWidget] = {}
        
        self._setup_categories()
        
        # Polling
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._poll_metrics)
        self.update_timer.start(100)  # 10 FPS de refresh de UI
        
        # Subscrever para logs de evento explícito
        EventBus.subscribe("runtime_metrics", self._on_runtime_metrics)

    def _setup_categories(self) -> None:
        for cat, color in self.COLORS.items():
            widget = ProfilerCategoryWidget(cat.capitalize(), color)
            self.category_widgets[cat] = widget
            self.categories_layout.addWidget(widget)
        self.categories_layout.addStretch()

    def _reset_metrics(self) -> None:
        eaf = ExecutionAnalysisFramework.instance()
        for k in eaf.profiler_categories:
            eaf.profiler_categories[k] = 0.0
        self._poll_metrics()

    def _poll_metrics(self) -> None:
        eaf = ExecutionAnalysisFramework.instance()
        total_ms = 0.0
        for cat, widget in self.category_widgets.items():
            val = eaf.profiler_categories.get(cat, 0.0)
            widget.update_value(val)
            total_ms += val
            
        # Calcula FPS aproximado pelo tempo total dos frames registrados, ou pelo dado explícito
        if total_ms > 0:
            fps = 1000.0 / total_ms
            # Limit to 1000 FPS display max
            fps = min(fps, 999.9)
            self.fps_label.setText(f"FPS: {fps:.0f} | Frame: {total_ms:.2f} ms")
        
        self.summary_label.setText(f"{len(eaf.execution_history)} execuções registradas em nós.")

    def _on_runtime_metrics(self, **kwargs: Any) -> None:
        """Event from viewport/runtime with specific metrics."""
        fps = kwargs.get("fps", 0)
        frame_time = kwargs.get("frame_time_ms", 0.0)
        if fps > 0:
            self.fps_label.setText(f"FPS: {fps:.0f} | Frame: {frame_time:.2f} ms")
        
        cats = kwargs.get("categories", {})
        eaf = ExecutionAnalysisFramework.instance()
        for k, v in cats.items():
            eaf.profiler_categories[k] = float(v)
