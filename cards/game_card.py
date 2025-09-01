# game_card.py
import sys
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox,
                               QPlainTextEdit, QLineEdit, QHBoxLayout, QApplication)
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor

from core.GameController import GameController


class GameCard(QWidget):
    return_to_menu_requested = Signal()
    send_log = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # --- UI组件定义 ---
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

        # 【修正-1】: 初始化时不创建线程和控制器
        self.game_thread: QThread | None = None
        self.controller: GameController | None = None

        # 使用临时控制器来填充初始UI，然后销毁它
        temp_controller = GameController()
        self.populate_workflows(temp_controller.workflows)
        del temp_controller

        # 只连接与UI直接相关的、不依赖于动态创建的 controller 的信号
        self.connect_ui_signals()
        self.set_ui_mode('setup')

    def populate_workflows(self, workflows):
        self.combo_workflows.clear()
        if not workflows:
            self.combo_workflows.addItem("未找到工作流文件")
            self.btn_new_game.setEnabled(False)
            self.btn_load_game.setEnabled(False)
        else:
            for wf_data in workflows.values():
                self.combo_workflows.addItem(wf_data.get("name", "未命名流程"))
            self.btn_new_game.setEnabled(True)
            self.btn_load_game.setEnabled(True)

    def connect_ui_signals(self):
        self.btn_new_game.clicked.connect(self.start_new_game)
        self.btn_load_game.clicked.connect(self.start_loaded_game)
        self.btn_send_input.clicked.connect(self.submit_input)
        self.input_line.returnPressed.connect(self.submit_input)
        self.btn_return_menu.clicked.connect(self.request_return)

    def set_ui_mode(self, mode: str):
        if mode == 'setup':
            self.setup_widget.setVisible(True)
            self.input_widget.setEnabled(False)
            self.input_line.setPlaceholderText("等待游戏指示...")
            self.btn_return_menu.setText("返回主菜单")
        elif mode == 'ingame':
            self.setup_widget.setVisible(False)
            self.input_widget.setEnabled(False)
            self.input_line.clear()
            self.btn_return_menu.setText("强制返回主菜单")

    def _start_game_session(self, start_method, workflow_name, **kwargs):
        """【修正-2】: 封装了创建和启动游戏会话的通用逻辑"""
        if self.game_thread is not None:
            print("警告: 一个游戏会话已在进行中，请等待其结束。")
            return

        self.log_console.clear()
        self.set_ui_mode('ingame')

        # 1. 为本次游戏创建全新的线程和控制器
        self.game_thread = QThread()
        self.controller = GameController()

        # 2. 将控制器移动到新线程
        self.controller.moveToThread(self.game_thread)

        # 3. 连接本次会话所需的所有信号
        self.controller.ai_response.connect(lambda text: self.append_log(text, "ai"))
        self.controller.input_requested.connect(self.handle_input_request)
        # 当游戏逻辑完成，让线程准备退出
        self.controller.game_finished.connect(self.game_thread.quit)
        # 当线程真正退出后，执行清理工作
        self.game_thread.finished.connect(self.on_game_session_finished)

        # 4. 连接线程的 started 信号来启动游戏逻辑（这是您原来有效的模式）
        self.game_thread.started.connect(lambda: start_method(workflow_name, **kwargs))

        # 5. 启动线程
        self.game_thread.start()

    def start_new_game(self):
        workflow_name = self.combo_workflows.currentText()
        if workflow_name and "未找到" not in workflow_name:
            self._start_game_session(
                start_method=lambda name: self.controller.run(name),
                workflow_name=workflow_name
            )

    def start_loaded_game(self):
        workflow_name = self.combo_workflows.currentText()
        if workflow_name and "未找到" not in workflow_name:
            self._start_game_session(
                start_method=lambda name, slot: self.controller.load_and_run(name, slot),
                workflow_name=workflow_name,
                # 可以在这里传递存档名等参数
                slot="autosave"
            )

    def submit_input(self):
        # 必须检查控制器是否存在
        if self.controller:
            text = self.input_line.text()
            if text:
                self.append_log(text, "player")
                # Qt会自动处理跨线程调用，将它排队
                self.controller.submit_user_input(text)
                self.input_widget.setEnabled(False)
                self.input_line.clear()
                self.input_line.setPlaceholderText("等待游戏指示...")

    def on_game_session_finished(self):
        """【修正-3】: 这是安全的游戏结束处理函数，替换了旧的 handle_game_finished"""
        print("游戏会话线程已结束，正在清理资源...")

        # 使用 deleteLater 安全地销毁对象
        if self.controller:
            self.controller.deleteLater()
            self.controller = None

        if self.game_thread:
            self.game_thread.deleteLater()
            self.game_thread = None

        # 重置UI到初始状态
        self.set_ui_mode('setup')

        # 如果需要，刷新工作流列表
        temp_controller = GameController()
        self.populate_workflows(temp_controller.workflows)
        del temp_controller

    def handle_input_request(self, prompt: str):
        """当控制器请求输入时，激活UI输入组件。"""
        self.input_widget.setEnabled(True)
        self.input_line.setPlaceholderText(prompt)
        self.input_line.setFocus()

    def handle_game_finished(self):
        # 这个方法现在是空的，因为所有逻辑都移到了 on_game_session_finished
        # 它只是为了防止旧的连接出错。实际上，我们可以直接把 controller.game_finished 连接到 thread.quit
        pass

    def request_return(self):
        if self.controller:
            # 请求控制器优雅地停止
            self.controller.stop_game()
        # 如果需要强制退出
        elif self.game_thread and self.game_thread.isRunning():
            self.game_thread.quit()

        self.return_to_menu_requested.emit()

    def append_log(self, text: str, log_type: str):
        # (此方法保持不变)
        prefix = ""
        color = 'black'

        if log_type == 'ai':
            prefix = "[游戏]"
            color = 'black'
            self.send_log.emit(f"{prefix} {text}")
        elif log_type == 'player':
            prefix = "[玩家]"
            color = 'blue'

        log_entry = f"{prefix} {text}"
        cursor = self.log_console.textCursor()
        cursor.movePosition(QTextCursor.End)
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))

        display_text = f"{log_entry}\n"
        if log_type == 'ai':
            display_text = f"\n{display_text}\n"

        cursor.setCharFormat(text_format)
        cursor.insertText(display_text)
        self.log_console.ensureCursorVisible()

    def closeEvent(self, event):
        """确保在关闭窗口时，如果游戏仍在运行，能干净地退出"""
        self.request_return()
        if self.game_thread:
            self.game_thread.wait(1000)  # 给点时间让线程退出
        super().closeEvent(event)

