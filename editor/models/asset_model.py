import os
from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import QDir


class AssetModel(QFileSystemModel):
    """
    Modelo de dados que mapeia os diretórios e arquivos de recursos do projeto (Assets).
    Herda de QFileSystemModel para aproveitar o carregamento assíncrono do sistema.
    Componente 'Model' na arquitetura MVVM do editor.
    """
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        
        # Define diretório raiz padrão como a pasta 'Assets' na raiz do projeto
        root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Assets"))
        if not os.path.exists(root_path):
            os.makedirs(root_path, exist_ok=True)
            # Cria subdiretórios padrão para organização
            os.makedirs(os.path.join(root_path, "Textures"), exist_ok=True)
            os.makedirs(os.path.join(root_path, "Scripts"), exist_ok=True)
            os.makedirs(os.path.join(root_path, "Audio"), exist_ok=True)
            os.makedirs(os.path.join(root_path, "Scenes"), exist_ok=True)
            
        self.setRootPath(root_path)
        self.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        
        # Filtros de extensões suportadas pelo editor
        self.setNameFilters(["*.py", "*.png", "*.jpg", "*.json", "*.wav", "*.ogg", "*.obj"])
        self.setNameFilterDisables(False)  # Oculta arquivos que não batem com o filtro

    def get_assets_root_path(self) -> str:
        """Retorna o caminho absoluto do diretório Assets do projeto."""
        return self.rootPath()
