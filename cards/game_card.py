# game_card.py
import sys
from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox,
                               QPlainTextEdit, QLineEdit, QHBoxLayout, QApplication)
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor

# 导入修改后的GameController
from core.GameController import GameController


class GameCard(QWidget):
    return_to_menu_requested = Signal()
    # 这个信号现在只用于向外（主窗口）转发AI的回复
    send_log = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.game_thread = QThread()
        self.controller = GameController()
        self.controller.moveToThread(self.game_thread)

        # --- UI组件定义 (保持不变) ---
        self.combo_workflows = QComboBox()
        self.btn_new_game = QPushButton("开始新游戏")
        self.btn_load_game = QPushButton("继续游戏")
        self.log_console = QPlainTextEdit()
        self.log_console.setReadOnly(True)
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("等待游戏指示...")
        self.btn_send_input = QPushButton("发送")
        self.btn_return_menu = QPushButton("返回主菜单")

        # --- 布局管理 (保持不变) ---
        setup_layout = QHBoxLayout()
        setup_layout.addWidget(QLabel("选择流程:"))
        setup_layout.addWidget(self.combo_workflows, 1)
        setup_layout.addWidget(self.btn_new_game)
        setup_layout.addWidget(self.btn_load_game)
        self.setup_widget = QWidget()
        self.setup_widget.setLayout(setup_layout)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_line, 1)
        input_layout.addWidget(self.btn_send_input)
        self.input_widget = QWidget()
        self.input_widget.setLayout(input_layout)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.setup_widget)
        main_layout.addWidget(self.log_console, 1)
        main_layout.addWidget(self.input_widget)
        main_layout.addWidget(self.btn_return_menu)

        self.populate_workflows()
        self.set_ui_mode('setup')
        self.connect_signals()

    def populate_workflows(self):
        # (此方法保持不变)
        workflows = self.controller.workflows
        if not workflows:
            self.combo_workflows.addItem("未找到工作流文件")
            self.btn_new_game.setEnabled(False)
            self.btn_load_game.setEnabled(False)
        else:
            for wf_data in workflows.values():
                self.combo_workflows.addItem(wf_data.get("name", "未命名流程"))

    def connect_signals(self):
        self.btn_new_game.clicked.connect(self.start_new_game)
        self.btn_load_game.clicked.connect(self.start_loaded_game)
        self.btn_send_input.clicked.connect(self.submit_input)
        self.input_line.returnPressed.connect(self.submit_input)

        # MODIFICATION: 移除了对 controller.log_message 的连接，因为它不再存在
        # self.controller.log_message.connect(lambda text: self.append_log(text, "system"))

        # 将 GameController 的 ai_response 信号连接到 append_log 方法
        self.controller.ai_response.connect(lambda text: self.append_log(text, "ai"))

        # 其他信号连接保持不变
        self.controller.input_requested.connect(self.handle_input_request)
        self.controller.game_finished.connect(self.handle_game_finished)
        self.game_thread.finished.connect(self.game_thread.deleteLater)
        self.game_thread.finished.connect(self.controller.deleteLater)
        self.btn_return_menu.clicked.connect(self.request_return)

    def set_ui_mode(self, mode: str):
        # (此方法保持不变)
        if mode == 'setup':
            self.setup_widget.setVisible(True)
            self.input_widget.setEnabled(False)
            self.btn_return_menu.setText("返回主菜单")
        elif mode == 'ingame':
            self.setup_widget.setVisible(False)
            self.input_widget.setEnabled(False)
            self.input_line.clear()
            self.btn_return_menu.setText("强制返回主菜单")

    def start_new_game(self):
        # (此方法保持不变)
        workflow_name = self.combo_workflows.currentText()
        if workflow_name:
            self.log_console.clear()
            self.game_thread.started.connect(lambda: self.controller.run(workflow_name))
            self.game_thread.start()
            self.set_ui_mode('ingame')

    def start_loaded_game(self):
        # (此方法保持不变)
        workflow_name = self.combo_workflows.currentText()
        if workflow_name:
            self.log_console.clear()
            self.game_thread.started.connect(lambda: self.controller.load_and_run(workflow_name))
            self.game_thread.start()
            self.set_ui_mode('ingame')

    def submit_input(self):
        text = self.input_line.text()
        if text:
            # 统一通过 append_log 处理玩家输入
            self.append_log(text, "player")
            self.controller.submit_user_input(text)
            self.input_widget.setEnabled(False)
            self.input_line.clear()
            self.input_line.setPlaceholderText("等待游戏指示...")

    def handle_input_request(self, prompt: str):
        # (此方法保持不变)
        self.input_widget.setEnabled(True)
        self.input_line.setPlaceholderText(prompt)
        self.input_line.setFocus()

    def handle_game_finished(self):
        # (此方法保持不变)
        self.game_thread.quit()
        self.game_thread.wait()
        self.set_ui_mode('setup')
        self.__init__()

    def request_return(self):
        # (此方法保持不变)
        if self.game_thread.isRunning():
            self.controller.stop_game()
            self.game_thread.quit()
            self.game_thread.wait(5000)
        self.return_to_menu_requested.emit()

    def append_log(self, text: str, log_type: str):
        """
        MODIFIED: 统一的日志处理方法。
        - 总是更新自己的控制台 (log_console)。
        - 只有当 log_type 是 'ai' 时，才通过 send_log 信号将日志发送出去。
        - log_type: 'ai', 'player'
        """
        prefix = ""
        color = 'black'

        # 定义不同日志类型的前缀和颜色
        if log_type == 'ai':
            prefix = "[游戏]"
            color = 'black'
        elif log_type == 'player':
            prefix = "[玩家]"
            color = 'blue'

        # 完整的日志条目，用于显示和发送
        log_entry = f"{prefix} {text}"

        # MODIFICATION: 仅在 log_type 为 'ai' 时发射信号
        # 这个信号是给主窗口的控制台使用的
        if log_type == 'ai':
            self.send_log.emit(log_entry)

        # ---- 以下是更新 GameCard 内部控制台的逻辑 (使用富文本颜色) ----
        cursor = self.log_console.textCursor()
        cursor.movePosition(QTextCursor.End)

        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))

        # 为了美观，AI的回复前后加空行
        display_text = f"{log_entry}\n"
        if log_type == 'ai':
            display_text = f"\n{display_text}\n"

        cursor.setCharFormat(text_format)
        cursor.insertText(display_text)
        self.log_console.ensureCursorVisible()

