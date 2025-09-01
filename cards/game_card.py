# game_card.py (Final Correct Version)
import sys
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox,
                               QPlainTextEdit, QLineEdit, QHBoxLayout, QApplication)
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor

from core.GameController import GameController


class GameCard(QWidget):
    return_to_menu_requested = Signal()
    send_log = Signal(str)

    # 【核心-1】: 定义用于启动游戏的自定义信号
    request_start_game = Signal(str)
    request_load_game = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # --- UI组件和布局 (保持不变) ---
        self.combo_workflows = QComboBox()
        self.btn_new_game = QPushButton("开始新游戏")
        self.btn_load_game = QPushButton("继续游戏")
        self.log_console = QPlainTextEdit();
        self.log_console.setReadOnly(True)
        self.input_line = QLineEdit();
        self.input_line.setPlaceholderText("等待游戏指示...")
        self.btn_send_input = QPushButton("发送")
        self.btn_return_menu = QPushButton("返回主菜单")
        setup_layout = QHBoxLayout();
        setup_layout.addWidget(QLabel("选择流程:"));
        setup_layout.addWidget(self.combo_workflows, 1);
        setup_layout.addWidget(self.btn_new_game);
        setup_layout.addWidget(self.btn_load_game)
        self.setup_widget = QWidget();
        self.setup_widget.setLayout(setup_layout)
        input_layout = QHBoxLayout();
        input_layout.addWidget(self.input_line, 1);
        input_layout.addWidget(self.btn_send_input)
        self.input_widget = QWidget();
        self.input_widget.setLayout(input_layout)
        main_layout = QVBoxLayout(self);
        main_layout.addWidget(self.setup_widget);
        main_layout.addWidget(self.log_console, 1);
        main_layout.addWidget(self.input_widget);
        main_layout.addWidget(self.btn_return_menu)

        self.game_thread: QThread | None = None
        self.controller: GameController | None = None

        temp_controller = GameController()
        self.populate_workflows(temp_controller.workflows)
        del temp_controller

        self.connect_ui_signals()
        self.set_ui_mode('setup')

    def populate_workflows(self, workflows):
        self.combo_workflows.clear()
        if not workflows:
            self.combo_workflows.addItem("未找到工作流文件");
            self.btn_new_game.setEnabled(False);
            self.btn_load_game.setEnabled(False)
        else:
            for wf_data in workflows.values(): self.combo_workflows.addItem(wf_data.get("name", "未命名流程"))
            self.btn_new_game.setEnabled(True);
            self.btn_load_game.setEnabled(True)

    def connect_ui_signals(self):
        self.btn_new_game.clicked.connect(self.start_new_game)
        self.btn_load_game.clicked.connect(self.start_loaded_game)
        self.btn_send_input.clicked.connect(self.submit_input)
        self.input_line.returnPressed.connect(self.submit_input)
        self.btn_return_menu.clicked.connect(self.request_return)

    def set_ui_mode(self, mode: str):
        if mode == 'setup':
            self.setup_widget.setVisible(True);
            self.input_widget.setEnabled(False);
            self.input_line.setPlaceholderText("等待游戏指示...");
            self.btn_return_menu.setText("返回主菜单")
        elif mode == 'ingame':
            self.setup_widget.setVisible(False);
            self.input_widget.setEnabled(False);
            self.input_line.clear();
            self.btn_return_menu.setText("强制返回主菜单")

    def _start_game_session(self, is_new_game, workflow_name, **kwargs):
        if self.game_thread is not None:
            print("警告: 一个游戏会话已在进行中，请等待其结束。");
            return

        self.log_console.clear()
        self.set_ui_mode('ingame')

        self.game_thread = QThread()
        self.controller = GameController()
        self.controller.moveToThread(self.game_thread)

        # 【核心-2】: 在创建时连接所有需要的信号
        self.controller.ai_response.connect(self.append_log_ai)
        self.controller.input_requested.connect(self.handle_input_request)
        self.controller.game_finished.connect(self.game_thread.quit)
        self.game_thread.finished.connect(self.on_game_session_finished)

        # 连接自定义的启动信号到控制器的槽
        if is_new_game:
            self.request_start_game.connect(self.controller.run)
        else:
            self.request_load_game.connect(self.controller.load_and_run)

        # 启动线程的事件循环
        self.game_thread.start()

        # 【核心-3】: 在线程启动后，通过发射信号来启动游戏逻辑
        if is_new_game:
            self.request_start_game.emit(workflow_name)
        else:
            self.request_load_game.emit(workflow_name, kwargs.get("slot", "autosave"))

    def start_new_game(self):
        workflow_name = self.combo_workflows.currentText()
        if workflow_name and "未找到" not in workflow_name:
            self._start_game_session(is_new_game=True, workflow_name=workflow_name)

    def start_loaded_game(self):
        workflow_name = self.combo_workflows.currentText()
        if workflow_name and "未找到" not in workflow_name:
            self._start_game_session(is_new_game=False, workflow_name=workflow_name, slot="autosave")

    def submit_input(self):
        if self.controller:
            text = self.input_line.text()
            if text:
                self.append_log_player(text)
                self.controller.submit_user_input(text)
                self.input_widget.setEnabled(False);
                self.input_line.clear();
                self.input_line.setPlaceholderText("等待游戏指示...")

    def on_game_session_finished(self):
        print("游戏会话线程已结束，正在清理资源...")

        # 断开所有连接，防止旧信号影响新会话
        if self.controller:
            try:
                self.request_start_game.disconnect(self.controller.run)
            except (TypeError, RuntimeError):
                pass
            try:
                self.request_load_game.disconnect(self.controller.load_and_run)
            except (TypeError, RuntimeError):
                pass
            self.controller.deleteLater()
            self.controller = None

        if self.game_thread:
            self.game_thread.deleteLater()
            self.game_thread = None

        self.set_ui_mode('setup')
        temp_controller = GameController();
        self.populate_workflows(temp_controller.workflows);
        del temp_controller

    def handle_input_request(self, prompt: str):
        self.input_widget.setEnabled(True);
        self.input_line.setPlaceholderText(prompt);
        self.input_line.setFocus()

    def request_return(self):
        if self.controller:
            self.controller.stop_game()
        elif self.game_thread and self.game_thread.isRunning():
            self.game_thread.quit()
        self.return_to_menu_requested.emit()

    def append_log_formatted(self, text, color, prefix):
        log_entry = f"{prefix} {text}" if prefix else text
        cursor = self.log_console.textCursor()
        cursor.movePosition(QTextCursor.End)
        text_format = QTextCharFormat();
        text_format.setForeground(QColor(color))
        display_text = f"\n{log_entry}\n" if prefix == "[游戏]" else f"{log_entry}\n"
        cursor.setCharFormat(text_format)
        cursor.insertText(display_text)
        self.log_console.ensureCursorVisible()

    def append_log_ai(self, text: str):
        self.send_log.emit(f"[游戏] {text}")
        self.append_log_formatted(text, 'black', '[游戏]')

    def append_log_player(self, text: str):
        self.append_log_formatted(text, 'blue', '[玩家]')

    def closeEvent(self, event):
        self.request_return();
        if self.game_thread: self.game_thread.wait(1000)
        super().closeEvent(event)
