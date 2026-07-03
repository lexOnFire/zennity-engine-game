import sys
import os
import datetime
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream

# Garante que o diretório raiz esteja no path para imports relativos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from editor.windows.main_window import MainWindow
from engine.logger import Logger
from editor.core.event_bus import EventBus, EVENT_LOG_ADDED


def patch_logger() -> None:
    """Monkey-patch no Logger da engine para encaminhar mensagens de log ao EventBus."""
    orig_log = Logger._log
    
    @classmethod
    def patched_log(cls, level: int, message: str, tag: str | None, **kwargs) -> None:
        # Executa a chamada original (grava no terminal/arquivo)
        orig_log(level, message, tag, **kwargs)
        
        # Repassa de forma assíncrona ao EventBus do editor
        try:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            label = cls._LABELS.get(level, "?????")
            tag_str = f" [{tag}]" if tag else ""
            extras = (" | " + " ".join(f"{k}={v}" for k, v in kwargs.items())) if kwargs else ""
            plain = f"[{now}] [{label}]{tag_str} {message}{extras}"
            
            level_name = "info"
            if level == cls.WARNING:
                level_name = "warning"
            elif level == cls.ERROR:
                level_name = "error"
            elif level == cls.DEBUG:
                level_name = "debug"
                
            EventBus.emit(EVENT_LOG_ADDED, message=plain, type=level_name)
        except Exception:
            pass

    Logger._log = patched_log


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
    
    # Aplica patches e carrega recursos
    patch_logger()
    load_stylesheet(app)
    
    # Envia o primeiro log de inicialização do sistema
    Logger.info("Zennity Engine Editor v0.1.0 inicializado com sucesso.")
    
    # Instancia a janela principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
