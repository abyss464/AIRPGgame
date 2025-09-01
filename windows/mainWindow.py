import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTextEdit, QPushButton, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt, QSize, Signal, QObject
from PySide6.QtGui import QIcon, QFont

# 导入设置窗口类
import windows.settingWindow as settingWindow



class MainWindow(QMainWindow):
    """
    应用程序的主窗口。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RPG")
        self.setGeometry(100, 100, 1200, 800)
        self.settings_window = None

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """初始化用户界面布局和控件。"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        left_panel = QWidget()
        left_panel.setObjectName("LeftPanel")

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)

        self.card_container = QWidget()
        # 为这个容器创建一个垂直布局
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(10)  # 卡片之间的垂直间距
        self.card_layout.setAlignment(Qt.AlignTop)  # 确保卡片从顶部开始排列

        left_layout.addWidget(self.card_container)

        left_layout.addStretch(1)

        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName("SettingsButton")
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setToolTip("打开设置")
        left_layout.addWidget(self.settings_button, 0, Qt.AlignBottom | Qt.AlignLeft)

        self.output_box = QTextEdit()
        self.output_box.setObjectName("OutputBox")
        self.output_box.setReadOnly(True)
        font = QFont("Consolas", 11)
        self.output_box.setFont(font)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.output_box)
        splitter.setSizes([int(self.width() * 3 / 8), int(self.width() * 5 / 8)])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 5)
        splitter.handle(1).setDisabled(True)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(splitter)

        self.settings_button.clicked.connect(self.open_settings_window)

    def apply_styles(self):
        """应用QSS样式表美化界面。"""
        self.setStyleSheet("""
            /* 主窗口和中央控件背景色 */
            QMainWindow, QWidget {
                background-color: #282c34;
                color: #abb2bf; /* 为所有子控件设置一个默认前景色 */
            }

            /* 左侧面板的圆角矩形样式 */
            #LeftPanel {
                background-color: #3a3f4b;
                border-radius: 15px;
            }

            /* --- 新增：卡片的通用样式 --- */
            #InfoCard {
                background-color: #2c313a;
                border-radius: 8px;
                border: 1px solid #21252b;
            }

            /* 右侧代码输出框样式 */
            #OutputBox {
                background-color: #21252b;
                border: 1px solid #181a1f;
                border-radius: 8px;
                padding: 10px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 14px;
            }

            QSplitter::handle:horizontal {
                background-color: #282c34;
            }

            #SettingsButton {
                background-color: transparent;
                color: #abb2bf;
                border: none;
                border-radius: 20px;
                font-size: 24px;
                padding-bottom: 2px;
            }
            #SettingsButton:hover { background-color: #4f5666; }
            #SettingsButton:pressed { background-color: #5a6275; }
        """)

    # --- 公共函数/槽函数 ---

    def add_card(self, card: QWidget):
        """
        向左侧面板添加一个卡片控件。

        Args:
            card (QWidget): 一个预先创建好的卡片实例 (例如 CharacterInfoCard)。
        """
        self.card_layout.addWidget(card)

    def clear_cards(self):
        """从布局中移除所有控件，但不删除它们。"""
        while self.card_layout.count():
            child = self.card_layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.setParent(None)

    def append_output(self, text: str):
        self.output_box.append(text)
        self.output_box.verticalScrollBar().setValue(self.output_box.verticalScrollBar().maximum())

    def clear_output(self):
        self.output_box.clear()

    def open_settings_window(self):
        """打开设置窗口。"""
        if self.settings_window is None:
            self.settings_window = settingWindow.SettingWindow(self)
        self.settings_window.show()
        self.settings_window.activateWindow()
