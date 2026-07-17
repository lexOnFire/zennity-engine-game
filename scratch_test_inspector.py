import sys
import os
import time

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap

sys.path.insert(0, os.path.abspath('.'))

from editor.isolated_editor_main import IsolatedEditorWindow

def run_test():
    app = QApplication.instance() or QApplication(sys.argv)
    
    # We pass None for viewport process and dummy queues
    class DummyQueue:
        def put(self, *args, **kwargs): pass
        def get(self, *args, **kwargs): return None
        def empty(self): return True
        
    window = IsolatedEditorWindow(None, DummyQueue(), DummyQueue())
    window.show()
    
    def on_timeout():
        # Select player
        window._selected_name = "Player"
        window._update_inspector("Player")
        
        # Take screenshot of the entire window
        QApplication.processEvents()
        
        pixmap = window.grab()
        pixmap.save(r"C:\Users\alexs\.gemini\antigravity\brain\36f15d82-13b2-4e62-8e38-053b34e7a329\test_output_inspector.png")
        print("Screenshot saved.")
        
        QApplication.quit()
        
    QTimer.singleShot(1000, on_timeout)
    sys.exit(app.exec())

if __name__ == '__main__':
    run_test()
