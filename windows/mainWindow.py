import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTextEdit, QPushButton, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt, QSize, Signal, QObject
from PySide6.QtGui import QIcon, QFont, QColor, QTextCharFormat, QTextCursor, QTextBlock

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
        self.is_left_panel_expanded = False
        self.splitter_state = None

        self.last_ai_message_start_block = -1
        self.last_ai_message_block_count = 0
        self._setup_text_formats()

        self.init_ui()
        self.apply_styles()

    def _setup_text_formats(self):
        """一次性创建所有文本格式，提高效率"""
        # 玩家输入的格式 (亮蓝色)
        self.player_format = QTextCharFormat()
        self.player_format.setForeground(QColor("#61afef"))
        self.player_format.setFont(QFont("Consolas", 11))

        # AI回复的格式 - 最新/明亮 (亮紫色, 粗体)
        self.ai_bright_format = QTextCharFormat()
        self.ai_bright_format.setForeground(QColor("#c678dd"))
        bright_font = QFont("Consolas", 11, QFont.Bold)
        self.ai_bright_format.setFont(bright_font)

        # AI回复的格式 - 旧/暗淡 (暗淡的灰色文本，非紫色，以示区别)
        self.ai_dim_format = QTextCharFormat()
        self.ai_dim_format.setForeground(QColor("#7f848e"))  # 使用暗灰色
        self.ai_dim_format.setFont(QFont("Consolas", 11))

        # 默认/系统消息格式 (绿色)
        self.system_format = QTextCharFormat()
        self.system_format.setForeground(QColor("#98c379"))
        self.system_format.setFont(QFont("Consolas", 11))

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

    def append_output(self, text: str, color_key: str):
        """向主输出面板追加带特定颜色和高亮逻辑的文本"""

        # 步骤 1: 将之前的AI消息变暗
        # 如果新消息是 'ai' 并且我们记录了上一个AI消息的范围
        if color_key == 'ai' and self.last_ai_message_start_block != -1:
            doc = self.output_box.document()
            # 遍历上一个AI消息的所有块
            for i in range(self.last_ai_message_block_count):
                block_num = self.last_ai_message_start_block + i
                block = doc.findBlockByNumber(block_num)
                if block.isValid():
                    # 创建一个指向该块的临时光标并应用暗淡格式
                    temp_cursor = QTextCursor(block)
                    temp_cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                    temp_cursor.setCharFormat(self.ai_dim_format)

        # 步骤 2: 准备在文档末尾插入新消息
        cursor = self.output_box.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 如果输出框不为空，则先插入一个新段落，确保消息间有间距
        if not self.output_box.toPlainText() == "":
            cursor.insertBlock()

        # 步骤 3: 根据 color_key 选择要应用的格式
        if color_key == 'ai':
            current_format = self.ai_bright_format
        elif color_key == 'player':
            current_format = self.player_format
        else:  # 'system'或其他
            current_format = self.system_format

        # 步骤 4: 插入带格式的新文本
        cursor.setCharFormat(current_format)

        # --- 关键修改：记录插入前的块编号 ---
        start_block_num = cursor.blockNumber()

        cursor.insertText(text)

        # --- 关键修改：记录插入后的块编号，并计算块数量 ---
        end_block_num = cursor.blockNumber()
        block_count = end_block_num - start_block_num + 1

        # 步骤 5: 如果刚插入的是AI消息，更新追踪器
        if color_key == 'ai':
            self.last_ai_message_start_block = start_block_num
            self.last_ai_message_block_count = block_count
        else:
            # 如果是玩家或系统消息，重置追踪器
            self.last_ai_message_start_block = -1
            self.last_ai_message_block_count = 0

        # 步骤 6: 确保视图滚动到底部 (更可靠的方法)
        v_scrollbar = self.output_box.verticalScrollBar()
        v_scrollbar.setValue(v_scrollbar.maximum())

    def clear_output(self):
        self.output_box.clear()
        self.last_ai_message_start_block = -1
        self.last_ai_message_block_count = 0

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

