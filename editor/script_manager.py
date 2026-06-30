"""Carregamento e execução dinâmica de scripts de comportamento."""
import os
import importlib.util
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.game_object import GameObject


class ScriptManager:
    """Gerencia scripts .py vinculados a GameObjects no modo Play."""

    SCRIPTS_DIR = "scripts"

    @staticmethod
    def list_scripts() -> List[str]:
        """Retorna ["Nenhum"] + caminhos de scripts em scripts/."""
        result = ["Nenhum"]
        if os.path.exists(ScriptManager.SCRIPTS_DIR):
            for f in sorted(os.listdir(ScriptManager.SCRIPTS_DIR)):
                if f.endswith(".py"):
                    result.append(os.path.join(ScriptManager.SCRIPTS_DIR, f))
        return result

    @staticmethod
    def load(obj: "GameObject") -> None:
        """Carrega e executa start() do script vinculado ao objeto."""
        path = getattr(obj, "script_path", "")
        if not path or not os.path.exists(path):
            return
        try:
            spec = importlib.util.spec_from_file_location(f"_script_{id(obj)}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            obj.script_module = module
            if hasattr(module, "start"):
                module.start(obj)
        except Exception as e:
            print(f"[ScriptManager] Erro ao carregar '{path}': {e}")

    @staticmethod
    def update(obj: "GameObject", dt: float) -> None:
        """Chama update() do módulo vinculado ao objeto."""
        mod = getattr(obj, "script_module", None)
        if mod and hasattr(mod, "update"):
            try:
                mod.update(obj, dt)
            except Exception as e:
                print(f"[ScriptManager] Erro no update de '{obj.name}': {e}")

    @staticmethod
    def unload(obj: "GameObject") -> None:
        """Remove o módulo e atributos temporários do objeto."""
        PERSISTENT = {
            "name", "transform", "components", "scene",
            "mesh_type", "is_static", "use_physics",
            "initial_velocity_y", "script_path", "active",
            "parent", "children",
        }
        for key in list(obj.__dict__.keys()):
            if key not in PERSISTENT:
                delattr(obj, key)

    @staticmethod
    def create_template(obj: "GameObject") -> str:
        """Cria um script template para o objeto e retorna o caminho."""
        os.makedirs(ScriptManager.SCRIPTS_DIR, exist_ok=True)
        name = obj.name.lower().replace(" ", "_")
        path = os.path.join(ScriptManager.SCRIPTS_DIR, f"behavior_{name}.py")
        if not os.path.exists(path):
            content = (
                f"# Script de Comportamento: {obj.name}\n"
                "import numpy as np\n\n"
                "def start(obj):\n"
                "    obj.script_time = 0.0\n\n"
                "def update(obj, dt):\n"
                "    obj.script_time = getattr(obj, 'script_time', 0.0) + dt\n"
                "    # Exemplo: rotação suave no eixo Y\n"
                "    obj.transform.rotation[1] = (obj.transform.rotation[1] + 45.0 * dt) % 360\n"
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[ScriptManager] Script criado: {path}")
        return path
