import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from editor.ui.property_editors import FoldoutWidget

app = QApplication(sys.argv)
win = QMainWindow()
central = QWidget()
layout = QVBoxLayout(central)
win.setCentralWidget(central)

foldout = FoldoutWidget("Transform")
foldout.content_layout.addWidget(QLabel("Content 1"))
foldout.content_layout.addWidget(QLabel("Content 2"))

COLLAPSED_STATES = {}
original_toggle = foldout.toggle
def new_toggle():
    print("new_toggle called!")
    original_toggle()
    COLLAPSED_STATES["Transform"] = not foldout._is_expanded

foldout.toggle = new_toggle
foldout.toggle_btn.clicked.disconnect()
foldout.toggle_btn.clicked.connect(foldout.toggle)

layout.addWidget(foldout)
layout.addStretch(1)

win.show()

print("Before toggle:")
print("Foldout size:", foldout.size())

# Simulate click signal
foldout.toggle_btn.click()

print("\nAfter toggle:")
print("Foldout size:", foldout.size())
print("COLLAPSED_STATES:", COLLAPSED_STATES)

print("\nAfter toggle:")
print("Foldout size:", foldout.size())
print("Header size:", foldout.header.size())

sys.exit(0)
