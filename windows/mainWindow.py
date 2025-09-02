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
        self.setGeometry(100, 100, 1600, 900)
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
        central_widget.setObjectName("CentralWidget")
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
        left_layout.addLayout(top_bar_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("CardScrollArea")
        # 移除滚动区域的边框，让它看起来更无缝
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        self.card_container = QWidget()
        # 让卡片容器的背景透明，这样左侧面板的圆角才能透出来
        self.card_container.setStyleSheet("background-color: transparent;")
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 10, 0, 10)  # 给卡片上下留点空间
        self.card_layout.setSpacing(10)
        self.card_layout.setAlignment(Qt.AlignTop)  # 让卡片从顶部开始排列

        # 将 card_container 设置为 scroll_area 的内容控件
        scroll_area.setWidget(self.card_container)

        # 将 scroll_area 添加到左侧布局中，而不是 card_container
        left_layout.addWidget(scroll_area)

        # left_layout.addStretch(1)

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
            QMainWindow, QWidget#CentralWidget  {
                background-color: #282c34;
                color: #abb2bf;
            }

            /* 左侧面板的圆角矩形样式 */
            #LeftPanel {
                background-color: #3a3f4b;
                border-radius: 15px;
            }

            /* --- 新增：卡片滚动区域的样式 --- */
            #CardScrollArea {
                border: none;
                background-color: #30353f; /* 比左侧面板稍微亮一点的颜色 */
                border-radius: 10px;
                padding: 5px;
            }

            /* --- 卡片的通用样式 --- */
            QWidget#InfoCard {
                background-color: #2c313a;
                border-radius: 8px;
                border: 1px solid #21252b;
                padding: 8px;
                margin: 2px;
            }
            
            .InfoCard {
                background-color: #2c313a;
                border-radius: 8px;
                border: 1px solid #21252b;
                padding: 8px;
                margin: 2px;
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

            /* --- 新增：美化滚动条 --- */
            QScrollBar:vertical {
                border: none;
                background: #3a3f4b; /* 滚动条背景色 */
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #5a6275; /* 滑块颜色 */
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6b7389; /* 悬停时滑块颜色 */
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px; /* 隐藏上下箭头 */
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

            #ExpandButton {
                background-color: transparent;
                color: #abb2bf;
                border: none;
                border-radius: 4px;
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
        # --- 修改 4: 插入卡片到伸缩项之前 ---
        # self.card_layout.addWidget(card) # 旧代码
        # count()-1 是因为最后一个item是addStretch
        card.setObjectName("InfoCard")
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

