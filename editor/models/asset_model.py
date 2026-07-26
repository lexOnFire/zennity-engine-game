import os
from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import QDir, Qt


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
        self.setNameFilters(["*.py", "*.png", "*.jpg", "*.json", "*.wav", "*.ogg", "*.obj", "*.zprefab", "*.zscene", "*.zmat"])
        self.setNameFilterDisables(False)  # Oculta arquivos que não batem com o filtro

    def get_assets_root_path(self) -> str:
        """Retorna o caminho absoluto do diretório Assets do projeto."""
        return self.rootPath()

    def data(self, index, role: int = Qt.ItemDataRole.DisplayRole):
        """Sobrescreve a renderização de dados para fornecer Thumbnails dinâmicas."""
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DecorationRole:
            path = self.filePath(index)
            if self.isDir(index):
                return super().data(index, role)

            ext = os.path.splitext(path)[1].lower()
            if ext in [".png", ".jpg", ".tga"]:
                # Aqui usaríamos um sistema de cache otimizado (lru_cache) em produção
                # Para simplificar na implementação inicial, carregamos diretamente
                from PySide6.QtGui import QPixmap, QIcon
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    # Escala mantendo proporção para melhor UX
                    scaled = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    return QIcon(scaled)

        return super().data(index, role)
