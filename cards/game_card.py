# GameCard.py
import sys
from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox,
                               QPlainTextEdit, QLineEdit, QHBoxLayout, QApplication)
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor

# 导入修改后的GameController (这个文件保持不变)
from core.GameController import GameController


class GameCard(QWidget):
    return_to_menu_requested = Signal()
    # 1. 恢复了通往主控制台的 send_log 信号
    send_log = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.game_thread = QThread()
        self.controller = GameController()
        self.controller.moveToThread(self.game_thread)

        self.combo_workflows = QComboBox()
        self.btn_new_game = QPushButton("开始新游戏")
        self.btn_load_game = QPushButton("继续游戏")

        self.log_console = QPlainTextEdit()
        self.log_console.setReadOnly(True)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("等待游戏指示...")
        self.btn_send_input = QPushButton("发送")

        self.btn_return_menu = QPushButton("返回主菜单")

        # --- 布局管理 ---
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

        # 3. 将 GameController 的信号连接到统一的日志处理方法
        self.controller.log_message.connect(lambda text: self.append_log(text, "system"))
        self.controller.ai_response.connect(lambda text: self.append_log(text, "ai"))
        self.controller.input_requested.connect(self.handle_input_request)
        self.controller.game_finished.connect(self.handle_game_finished)

        self.game_thread.finished.connect(self.game_thread.deleteLater)
        self.game_thread.finished.connect(self.controller.deleteLater)

        self.btn_return_menu.clicked.connect(self.request_return)

    def set_ui_mode(self, mode: str):
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
        workflow_name = self.combo_workflows.currentText()
        if workflow_name:
            self.log_console.clear()
            self.game_thread.started.connect(lambda: self.controller.run(workflow_name))
            self.game_thread.start()
            self.set_ui_mode('ingame')

    def start_loaded_game(self):
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
        self.input_widget.setEnabled(True)
        self.input_line.setPlaceholderText(prompt)
        self.input_line.setFocus()

    def handle_game_finished(self):
        self.game_thread.quit()
        self.game_thread.wait()
        self.set_ui_mode('setup')
        self.__init__()  # 重新初始化以便下次游戏

    def request_return(self):
        if self.game_thread.isRunning():
            self.controller.stop_game()
            self.game_thread.quit()
            self.game_thread.wait(5000)
        self.return_to_menu_requested.emit()

    def append_log(self, text: str, log_type: str):
        """
        统一的日志处理方法。
        它既会更新自己的控制台，也会通过 send_log 信号将日志发送出去。
        - log_type: 'system', 'ai', 'player'
        """
        # 2. 准备要发送到主控制台的、带前缀的纯文本日志
        log_entry_for_signal = ""
        if log_type == 'system':
            log_entry_for_signal = f"[系统] {text}"
        elif log_type == 'ai':
            log_entry_for_signal = f"[游戏] {text}"
        elif log_type == 'player':
            log_entry_for_signal = f"[玩家] {text}"

        # 发射信号，供主窗口的控制台使用
        self.send_log.emit(log_entry_for_signal)

        # ---- 以下是更新 GameCard 内部控制台的逻辑 (使用富文本颜色) ----
        color_map = {'system': 'grey', 'ai': 'black', 'player': 'blue'}
        color = color_map.get(log_type, 'black')

        cursor = self.log_console.textCursor()
        cursor.movePosition(QTextCursor.End)

        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))

        # 为了美观，AI的回复前后加空行
        display_text = f"{log_entry_for_signal}\n"
        if log_type == 'ai':
            display_text = f"\n{display_text}\n"

        cursor.setCharFormat(text_format)
        cursor.insertText(display_text)
        self.log_console.ensureCursorVisible()

