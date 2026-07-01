"""
Zennity Engine — Editor 3D

Ponto de entrada. Toda a lógica foi refatorada para editor/.
Rodar: python demos/editor_3d.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.core import Engine
from editor.launcher import LauncherScene

if __name__ == "__main__":
    engine = Engine(width=1400, height=800, title="Zennity Engine — Launcher & Workspace")
    engine.run(LauncherScene())
