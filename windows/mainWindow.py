import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTextEdit, QPushButton, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt, QSize, Signal, QObject
from PySide6.QtGui import QIcon, QFont

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

        # --- 新增：状态变量 ---
        # 用于跟踪左侧面板是否已经最大化
        self.is_left_panel_expanded = False
        # 用于存储分裂器在收起前的状态
        self.splitter_state = None

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

        # --- 新增：用于放置展开按钮的顶部栏 ---
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.expand_button = QPushButton("↗")
        self.expand_button.setObjectName("ExpandButton")
        self.expand_button.setFixedSize(30, 30)
        self.expand_button.setToolTip("展开侧边栏")

        # 添加一个伸缩项将按钮推到右侧
        top_bar_layout.addStretch(1)
        top_bar_layout.addWidget(self.expand_button)

        # 将顶部栏添加到左侧面板的布局中
        left_layout.addLayout(top_bar_layout)
        # --- 新增结束 ---

        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(10)
        self.card_layout.setAlignment(Qt.AlignTop)

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

        # 将 splitter 提升为实例变量 self.splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(self.output_box)
        self.splitter.setSizes([int(self.width() * 3 / 8), int(self.width() * 5 / 8)])
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 5)
        self.splitter.handle(1).setDisabled(True)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.splitter)  # 使用 self.splitter

        # 连接信号
        self.settings_button.clicked.connect(self.open_settings_window)
        self.expand_button.clicked.connect(self.toggle_left_panel_expansion)

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

            /* --- 新增：展开/收起按钮的样式 --- */
            #ExpandButton {
                background-color: transparent;
                color: #abb2bf;
                border: none;
                border-radius: 4px; /* 轻微圆角 */
                font-size: 20px;
                font-weight: bold;
            }
            #ExpandButton:hover { background-color: #4f5666; }
            #ExpandButton:pressed { background-color: #5a6275; }

        """)

    def toggle_left_panel_expansion(self):
        """
        切换左侧面板的展开和收起状态。
        """
        if self.is_left_panel_expanded:
            # --- 当前是展开状态，需要收起 ---
            # 1. 恢复右侧输出框的可见性
            self.output_box.show()
            # 2. 恢复分裂器的尺寸
            if self.splitter_state:
                self.splitter.setSizes(self.splitter_state)
            # 3. 更改按钮图标和提示文本
            self.expand_button.setText("↗")
            self.expand_button.setToolTip("展开侧边栏")
            # 4. 更新状态
            self.is_left_panel_expanded = False
        else:
            self.splitter_state = self.splitter.sizes()
            self.output_box.hide()
            self.expand_button.setText("↙")
            self.expand_button.setToolTip("收起侧边栏")
            self.is_left_panel_expanded = True

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
        # 为了演示，如果 settingWindow 不存在，则不做任何事
        try:
            if self.settings_window is None:
                self.settings_window = settingWindow.SettingWindow(self)
            self.settings_window.show()
            self.settings_window.activateWindow()
        except (NameError, AttributeError):
            print("settingWindow 模块未导入或不存在，无法打开设置窗口。")
            self.append_output("错误：无法打开设置窗口。")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()

    # 添加一个示例卡片，以便观察布局
    from PySide6.QtWidgets import QLabel


    # 模拟一个卡片
    class InfoCard(QWidget):
        def __init__(self, title, parent=None):
            super().__init__(parent)
            self.setObjectName("InfoCard")
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(f"这是一个标题为 '{title}' 的卡片"))
            layout.addWidget(QLabel("一些内容..."))
            layout.addWidget(QLabel("更多内容..."))
            self.setMinimumHeight(100)  # 给卡片一个最小高度


    window.add_card(InfoCard("角色A"))
    window.add_card(InfoCard("角色B"))
    window.append_output("程序启动成功。")
    window.append_output("点击左上角的 '↗' 按钮可以展开/收起侧边栏。")

    window.show()
    sys.exit(app.exec())
