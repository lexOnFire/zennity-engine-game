"""
Zennity Engine — Editor 3D

Ponto de entrada. Toda a lógica foi refatorada para editor/.
Rodar: python demos/editor_3d.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.core import Engine
from editor.scene import EditorScene

if __name__ == "__main__":
    engine = Engine(width=1000, height=600, title="Zennity Engine — Editor 3D")
    engine.run(EditorScene())
