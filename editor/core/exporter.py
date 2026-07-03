import os
import shutil
from typing import List
from engine.game_object import GameObject
from editor.core.serializer import save_scene_to_file


def export_project(dest_dir: str, root_objects: List[GameObject]) -> str:
    """
    Exporta a cena ativa do jogo e empacota as dependências da engine
    em uma pasta standalone pronta para ser jogada.
    """
    os.makedirs(dest_dir, exist_ok=True)
    
    # 1. Salva a cena ativa como 'scene.zscene' no diretório de exportação
    scene_path = os.path.join(dest_dir, "scene.zscene")
    save_scene_to_file(scene_path, root_objects)
    
    # 2. Copia as dependências da Zennity Engine (pasta 'engine')
    src_engine = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "engine"))
    dest_engine = os.path.join(dest_dir, "engine")
    if os.path.exists(src_engine):
        if os.path.exists(dest_engine):
            shutil.rmtree(dest_engine)
        shutil.copytree(src_engine, dest_engine)
        
    # 3. Copia a pasta de assets se houver
    src_assets = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
    dest_assets = os.path.join(dest_dir, "assets")
    if os.path.exists(src_assets):
        if os.path.exists(dest_assets):
            shutil.rmtree(dest_assets)
        shutil.copytree(src_assets, dest_assets)
        
    # 4. Copia a pasta de scripts de comportamento se houver
    src_scripts = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
    dest_scripts = os.path.join(dest_dir, "scripts")
    if os.path.exists(src_scripts):
        if os.path.exists(dest_scripts):
            shutil.rmtree(dest_scripts)
        shutil.copytree(src_scripts, dest_scripts)
        
    # 5. Copia o ScriptManager legado para o root para gerenciar scripts standalone
    src_sm = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "editor_legacy", "script_manager.py"))
    dest_sm = os.path.join(dest_dir, "script_manager.py")
    if os.path.exists(src_sm):
        shutil.copy2(src_sm, dest_sm)
        
    # 6. Cria o launcher standalone 'main_standalone.py'
    launcher_content = """import sys
import os
import pygame
import numpy as np

# Adiciona pasta local ao path para imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Inicializa dependências
from engine.core import Application
from engine.core.scene import Scene
from engine.core.serializer import load_scene_from_file

def main():
    # Inicializa a Zennity Engine de Produção
    app = Application(800, 600, "Zennity Engine - Standalone Game")
    
    # Cria a cena principal
    game_scene = Scene("GameScene")
    
    # Carrega os GameObjects do arquivo .zscene exportado
    scene_file = os.path.join(os.path.dirname(__file__), "scene.zscene")
    if os.path.exists(scene_file):
        try:
            # Monkey-patch temporário no serializer para importar localmente
            import serializer
            loaded_objs = serializer.load_scene_from_file(scene_file)
            for obj in loaded_objs:
                game_scene.add_game_object(obj)
        except Exception as e:
            print(f"[ERROR] Falha ao carregar cena do jogo: {e}")
            
    # Registra o ScriptManager no loop de simulação
    try:
        import script_manager
        
        # Sistema de update standalone para atualizar comportamentos físicos/lógicos
        def update_system(scene, dt):
            script_manager.ScriptManager.update_all(scene.game_objects, dt)
            
        app.engine.add_update_system(update_system)
        
        # Roda o start de todos os scripts
        for obj in game_scene.game_objects:
            if getattr(obj, "script_path", ""):
                # Ajusta path local
                script_manager.ScriptManager.load(obj)
    except Exception as e:
        print(f"[WARNING] O gerenciador de scripts falhou ao inicializar: {e}")
        
    # Inicia o jogo
    app.run(game_scene)

if __name__ == "__main__":
    main()
"""
    launcher_path = os.path.join(dest_dir, "main_standalone.py")
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(launcher_content)
        
    # 7. Copia o próprio serializer.py para a pasta local para permitir desserialização local
    src_sz = os.path.abspath(os.path.join(os.path.dirname(__file__), "serializer.py"))
    dest_sz = os.path.join(dest_dir, "serializer.py")
    if os.path.exists(src_sz):
        shutil.copy2(src_sz, dest_sz)
        
    # 8. Cria os scripts de execução rápida jogar.bat e jogar.sh
    bat_path = os.path.join(dest_dir, "jogar.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write("@echo off\npython main_standalone.py\npause\n")
        
    sh_path = os.path.join(dest_dir, "jogar.sh")
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\npython3 main_standalone.py\n")
    # Dá permissão de execução no sh
    try:
        os.chmod(sh_path, 0o755)
    except Exception:
        pass
        
    return dest_dir
