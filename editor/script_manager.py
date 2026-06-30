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
        result = ["Nenhum"]
        if os.path.exists(ScriptManager.SCRIPTS_DIR):
            for f in sorted(os.listdir(ScriptManager.SCRIPTS_DIR)):
                if f.endswith(".py"):
                    result.append(os.path.join(ScriptManager.SCRIPTS_DIR, f))
        return result

    @staticmethod
    def load(obj: "GameObject") -> None:
        path = getattr(obj, "script_path", "")
        if not path or not os.path.exists(path):
            return
        try:
            spec   = importlib.util.spec_from_file_location(f"_script_{id(obj)}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            obj.script_module = module
            if hasattr(module, "start"):
                module.start(obj)
        except Exception as e:
            print(f"[ScriptManager] Erro ao carregar '{path}': {e}")

    @staticmethod
    def update(obj: "GameObject", dt: float) -> None:
        mod = getattr(obj, "script_module", None)
        if mod and hasattr(mod, "update"):
            try:
                mod.update(obj, dt)
            except Exception as e:
                print(f"[ScriptManager] Erro no update de '{obj.name}': {e}")

    @staticmethod
    def unload(obj: "GameObject") -> None:
        """Remove o módulo e atributos temporários do objeto.

        Atributos em PERSISTENT são mantidos intactos entre Play/Stop para que
        o editor retome o estado correto. _phys_vel é REMOVIDO aqui (não
        preservado) porque PhysicsSim.attach_rigidbody o recria com o valor
        correto de initial_velocity_y a cada Play.
        """
        PERSISTENT = {
            "name", "transform", "components", "scene",
            "mesh_type", "is_static", "use_physics",
            "initial_velocity_y", "script_path", "active",
            "parent", "children",
            "tag",          # ← preservar tag definida no inspetor
        }
        for key in list(obj.__dict__.keys()):
            if key not in PERSISTENT:
                try:
                    delattr(obj, key)
                except AttributeError:
                    pass

    @staticmethod
    def create_template(obj: "GameObject") -> str:
        os.makedirs(ScriptManager.SCRIPTS_DIR, exist_ok=True)
        name = obj.name.lower().replace(" ", "_")
        path = os.path.join(ScriptManager.SCRIPTS_DIR, f"behavior_{name}.py")
        if not os.path.exists(path):
            content = (
                f"# Script de Comportamento para o objeto: {obj.name}\n"
                "# Voce pode editar este arquivo para programar o comportamento em tempo de execucao.\n"
                "import pygame\n"
                "import numpy as np\n\n"
                "def start(obj):\n"
                "    # Executado uma unica vez ao iniciar a simulacao (PLAY)\n"
                "    print(f'Iniciando comportamento de {obj.name}!')\n"
                "    obj.script_time = 0.0\n\n"
                "def update(obj, dt):\n"
                "    # Executado a cada frame durante a simulacao (PLAY)\n"
                "    obj.script_time = getattr(obj, 'script_time', 0.0) + dt\n\n"
                "    # Exemplo: Rotacao suave no eixo Y\n"
                "    obj.transform.rotation[1] = (obj.transform.rotation[1] + 45.0 * dt) % 360\n\n"
                "    # Exemplo de movimentacao:\n"
                "    # velocidade = 5.0\n"
                "    # teclas = pygame.key.get_pressed()\n"
                "    # if teclas[pygame.K_LEFT]:\n"
                "    #     obj.transform.position[0] -= velocidade * dt\n"
                "    # if teclas[pygame.K_RIGHT]:\n"
                "    #     obj.transform.position[0] += velocidade * dt\n"
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[ScriptManager] Script criado: {path}")
        return path
