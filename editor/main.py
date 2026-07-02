import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream

# Garante que o diretório raiz esteja no path para imports relativos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from editor.windows.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    """Lê e aplica o arquivo QSS do tema escuro."""
    theme_path = os.path.join(os.path.dirname(__file__), "themes", "dark_theme.qss")
    file = QFile(theme_path)
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        app.setStyleSheet(stream.readAll())
        file.close()
    else:
        print(f"[WARNING] Não foi possível carregar a folha de estilo em: {theme_path}")


def main() -> None:
    """Função principal que inicializa o loop do Qt Application."""
    app = QApplication(sys.argv)
    
    # Aplica o tema escuro Unreal
    load_stylesheet(app)
    
    # Instancia a janela principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
