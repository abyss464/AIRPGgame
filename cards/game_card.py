from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel

class GameCard(QWidget):
    return_to_menu_requested = Signal()
    send_log = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("游戏正在进行中...")
        button = QPushButton("返回主菜单")
        layout.addWidget(label)
        layout.addWidget(button)
        button.clicked.connect(self.return_to_menu_requested.emit)
