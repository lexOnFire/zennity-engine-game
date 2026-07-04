import sys
from PySide6.QtWidgets import QApplication
from editor.phase1_editor import ZennityPhase1Editor
from editor.premium_theme import PREMIUM_QSS

app = QApplication(sys.argv)
app.setStyleSheet(PREMIUM_QSS)
window = ZennityPhase1Editor()
window.show()
app.exec()
