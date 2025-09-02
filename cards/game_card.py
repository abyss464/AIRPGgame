import sys
import os
import json
from PySide6.QtCore import Signal, QThread, Qt, QObject
from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox,
                               QPlainTextEdit, QHBoxLayout, QApplication, QFormLayout,
                               QFrame)
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor, QKeyEvent, QFont

from core.GameController import GameController
from core.ModelLinker import ModelLinker
from manager.model_config_manager import ModelConfigManager

class ExpandingInput(QPlainTextEdit):
    send_requested = Signal()
    FIXED_LINES = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        font_metrics = self.fontMetrics()
        single_line_height = font_metrics.height()
        margins = self.contentsMargins()
        vertical_padding = margins.top() + margins.bottom() + self.frameWidth() * 2
        fixed_height = single_line_height * self.FIXED_LINES + vertical_padding
        self.setFixedHeight(fixed_height)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            event.accept()
            self.send_requested.emit()
        else:
            super().keyPressEvent(event)


# 【核心修改】: 使用真实的 ModelLinker 来处理属性文件
class AttributeWorker(QThread):
    finished = Signal(dict, str)  # 发送处理结果(字典)和可能的错误信息

    def __init__(self, file_path: str, model_linker: ModelLinker, parent: QObject | None = None):
        super().__init__(parent)
        self.file_path = file_path
        self.model_linker = model_linker

        # ---【请根据您的配置修改】---
        # 定义用于属性规范化的模型。建议使用一个速度快、成本低的强大模型。
        self.NORMALIZATION_PROVIDER = "openai"  # 例如: "openai", "deepseek", "ollama"
        self.NORMALIZATION_MODEL = "gpt-3.5-turbo"  # 例如: "gpt-3.5-turbo", "deepseek-coder"
        # -----------------------------

    def run(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 1. 尝试直接解析为JSON
            try:
                data = json.loads(content)
                self.finished.emit(data, "")
                return  # 成功解析，任务完成
            except json.JSONDecodeError:
                # 2. 如果不是JSON，则视为自然语言，调用AI进行规范化
                print(f"内容非JSON，将使用AI进行规范化: {self.NORMALIZATION_PROVIDER}/{self.NORMALIZATION_MODEL}")

                system_prompt = (
                    "你是一个数据提取与格式化助手。"
                    "你的任务是将用户提供的关于游戏角色的自然语言描述，转换成一个结构清晰的JSON对象。"
                    "请对属性进行逻辑分组，例如将力量、敏捷等归入 'attributes' 或 '能力' 键下。"
                    "确保输出的是一个格式完全正确的、可以直接被程序解析的JSON对象，不要在JSON对象前后添加任何额外的解释性文字、代码块标记(```json)或注释。"
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]

                try:
                    # 调用真实的模型链接器
                    ai_response_str = self.model_linker.create_completion(
                        messages=messages,
                        provider_name=self.NORMALIZATION_PROVIDER,
                        model=self.NORMALIZATION_MODEL
                    )

                    # 3. 解析AI的响应
                    try:
                        normalized_data = json.loads(ai_response_str)
                        self.finished.emit(normalized_data, "")
                    except json.JSONDecodeError:
                        # AI返回的不是有效的JSON
                        error_msg = f"AI模型返回了无效的JSON格式数据。\n响应内容: {ai_response_str[:200]}..."
                        self.finished.emit({}, error_msg)

                except Exception as e:
                    # API调用失败
                    error_msg = f"调用AI模型时发生错误: {e}"
                    self.finished.emit({}, error_msg)

        except FileNotFoundError:
            self.finished.emit({}, f"错误: 找不到属性文件\n'{self.file_path}'")
        except Exception as e:
            self.finished.emit({}, f"处理属性文件时发生严重错误: {e}")


# 【无变化】: 动态属性面板
class AttributePane(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)

        title = QLabel("角色属性")
        font = title.font()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)

        self.main_layout.addWidget(title)

        self.content_widget = QWidget()
        self.form_layout = QFormLayout(self.content_widget)
        self.form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.form_layout.setLabelAlignment(Qt.AlignRight)

        self.main_layout.addWidget(self.content_widget)

        self.clear_attributes()

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())

    def _populate_layout(self, layout, data):
        for key, value in data.items():
            key_label = QLabel(f"{key}:")

            if isinstance(value, dict):
                group_frame = QFrame()
                group_frame.setFrameShape(QFrame.StyledPanel)
                group_layout = QVBoxLayout(group_frame)
                group_title = QLabel(key)
                font = group_title.font();
                font.setBold(True)
                group_title.setFont(font)
                group_layout.addWidget(group_title)
                sub_form_layout = QFormLayout()
                sub_form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
                self._populate_layout(sub_form_layout, value)
                group_layout.addLayout(sub_form_layout)
                layout.addRow(group_frame)
            elif isinstance(value, list):
                value_text = "\n".join(f"- {item}" for item in value)
                value_label = QLabel(value_text)
                value_label.setWordWrap(True)
                layout.addRow(key_label, value_label)
            else:
                value_label = QLabel(str(value))
                value_label.setWordWrap(True)
                layout.addRow(key_label, value_label)

    def update_attributes(self, data: dict, error_message: str = ""):
        self._clear_layout(self.form_layout)
        if error_message:
            self.form_layout.addRow(QLabel(error_message))
        elif not data:
            self.form_layout.addRow(QLabel("无可用属性信息。"))
        else:
            self._populate_layout(self.form_layout, data)

    def clear_attributes(self):
        self.update_attributes({}, "")
        self.form_layout.addRow(QLabel("等待游戏开始以加载属性..."))


# 【GameCard】: 集成AI调用逻辑
class GameCard(QWidget):
    return_to_menu_requested = Signal()
    send_log = Signal(str, str)
    request_start_game = Signal(str)
    request_load_game = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # --- 模型管理器和链接器 ---
        try:
            self.modelmanager = ModelConfigManager()
            self.model_linker = ModelLinker(self.modelmanager)
        except Exception as e:
            print(f"错误：无法初始化AI模型管理器: {e}")
            # 在这种情况下，可以禁用需要AI的功能，或显示错误信息
            # 为简单起见，我们假设它总是成功
            self.model_linker = None

        # --- UI组件 ---
        self.combo_workflows = QComboBox()
        self.btn_new_game = QPushButton("开始新游戏")
        self.btn_load_game = QPushButton("继续游戏")
        self.log_console = QPlainTextEdit()
        self.log_console.setReadOnly(True)
        self.input_line = ExpandingInput()
        self.input_line.setPlaceholderText("等待游戏指示... (Shift+Enter 换行)")
        self.btn_send_input = QPushButton("发送")
        self.btn_return_menu = QPushButton("返回主菜单")
        self.attribute_pane = AttributePane()

        # --- 布局 ---
        setup_layout = QHBoxLayout()
        setup_layout.addWidget(QLabel("选择流程:"))
        setup_layout.addWidget(self.combo_workflows, 1)
        setup_layout.addWidget(self.btn_new_game)
        setup_layout.addWidget(self.btn_load_game)
        self.setup_widget = QWidget()
        self.setup_widget.setLayout(setup_layout)

        # 输入区域（输入框和发送按钮垂直排列）
        input_layout = QVBoxLayout()
        input_layout.addWidget(self.input_line)  # 输入框在上方
        input_layout.addWidget(self.btn_send_input)  # 发送按钮在下方
        input_layout.setContentsMargins(0, 0, 0, 0)  # 设置边距为0，使布局更紧凑
        self.input_widget = QWidget()
        self.input_widget.setLayout(input_layout)

        # 下方面板整体布局 (移除了log_console)
        right_panel_layout = QVBoxLayout()
        right_panel_layout.addWidget(self.input_widget)  # 现在输入区域会占据更多空间
        right_panel = QWidget()
        right_panel.setLayout(right_panel_layout)

        # 上下分栏主布局
        content_layout = QVBoxLayout()
        # 1. 添加属性面板，并设置伸缩因子为 3，使其可拉伸并占据更多空间
        content_layout.addWidget(self.attribute_pane, 10)
        # 2. 添加输入区域，设置伸缩因子为 1，保持合理的输入区域大小
        content_layout.addWidget(right_panel, 1)

        # 整体布局
        # --- 创建新的顶部栏 ---
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(self.btn_return_menu)  # 将按钮放在最左边
        top_bar_layout.addStretch()  # 添加伸缩项，占据所有剩余空间，将按钮推向左侧
        top_bar_layout.setContentsMargins(0, 5, 0, 5)  # 轻微调整垂直边距，使其美观

        # --- 重组整体布局 ---
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_bar_layout)  # 1. 添加新的顶部栏
        main_layout.addWidget(self.setup_widget)  # 2. 添加流程选择/开始游戏的区域
        main_layout.addLayout(content_layout)  # 3. 添加包含属性和输入的主内容区域

        # --- 状态和连接 ---
        self.game_thread: QThread | None = None
        self.controller: GameController | None = None
        self.attribute_worker: AttributeWorker | None = None

        try:
            temp_controller = GameController()
            self.populate_workflows(temp_controller.workflows)
            del temp_controller
        except Exception:
            print("警告: GameController 未找到，无法填充工作流。")
            self.populate_workflows({})

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
        self.input_line.send_requested.connect(self.submit_input)
        self.btn_return_menu.clicked.connect(self.request_return)

    def set_ui_mode(self, mode: str):
        if mode == 'setup':
            self.setup_widget.setVisible(True)
            self.input_widget.setEnabled(False)
            self.input_line.setPlaceholderText("等待游戏指示...")
            self.btn_return_menu.setText("返回主菜单")
            self.attribute_pane.clear_attributes()
        elif mode == 'ingame':
            self.setup_widget.setVisible(False)
            self.input_widget.setEnabled(False)
            self.input_line.clear()
            self.btn_return_menu.setText("强制返回主菜单")

    def _start_game_session(self, is_new_game, workflow_name, **kwargs):
        if self.game_thread is not None:
            print("警告: 一个游戏会话已在进行中，请等待其结束。")
            return

        self.log_console.clear()
        self.set_ui_mode('ingame')

        self.load_attributes(workflow_name)

        self.game_thread = QThread()
        self.controller = GameController()
        self.controller.moveToThread(self.game_thread)
        self.controller.ai_response.connect(self.append_log_ai)
        self.controller.input_requested.connect(self.handle_input_request)
        self.controller.game_finished.connect(self.game_thread.quit)
        self.game_thread.finished.connect(self.on_game_session_finished)

        if is_new_game:
            self.request_start_game.connect(self.controller.run)
            self.game_thread.started.connect(lambda: self.request_start_game.emit(workflow_name))
        else:
            slot = kwargs.get("slot", "autosave")
            self.request_load_game.connect(self.controller.load_and_run)
            self.game_thread.started.connect(lambda: self.request_load_game.emit(workflow_name, slot))

        self.game_thread.start()

    def load_attributes(self, workflow_name: str):
        if not self.model_linker:
            self.attribute_pane.update_attributes({}, "错误: AI模型链接器未初始化。")
            return

        attribute_file = os.path.join("aifiles", workflow_name, "character_sheet.txt")
        self.attribute_pane.update_attributes({}, "正在加载并解析属性...")

        if os.path.exists(attribute_file):
            self.attribute_worker = AttributeWorker(attribute_file, self.model_linker)  # 传递linker
            self.attribute_worker.finished.connect(self.attribute_pane.update_attributes)
            self.attribute_worker.finished.connect(self.attribute_worker.deleteLater)
            self.attribute_worker.start()
        else:
            self.attribute_pane.update_attributes({}, f"未找到属性文件:\n{attribute_file}")

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
            text = self.input_line.toPlainText().strip()
            if text:
                self.send_log.emit(f"[玩家] {text}", "player")
                self.controller.submit_user_input(text)
                self.input_widget.setEnabled(False)
                self.input_line.clear()
                self.input_line.setPlaceholderText("等待游戏指示...")

    def on_game_session_finished(self):
        print("游戏会话线程已结束，正在清理资源...")
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
        try:
            temp_controller = GameController()
            self.populate_workflows(temp_controller.workflows)
            del temp_controller
        except Exception:
            pass

    def handle_input_request(self, prompt: str):
        self.input_widget.setEnabled(True)
        self.input_line.setPlaceholderText(f"{prompt} (Shift+Enter 换行)")
        self.input_line.setFocus()

    def request_return(self):
        if self.controller:
            self.controller.stop_game()
        if self.game_thread and self.game_thread.isRunning():
            self.game_thread.quit()
            self.game_thread.wait(500)
        self.return_to_menu_requested.emit()

    def append_log_formatted(self, text, color, prefix):
        cursor = self.log_console.textCursor()
        cursor.movePosition(QTextCursor.End)
        text_format = QTextCharFormat();
        text_format.setForeground(QColor(color))
        cursor.insertText("\n", QTextCharFormat())
        cursor.setCharFormat(text_format)
        cursor.insertText(f"{prefix} {text}" if prefix else text)
        self.log_console.ensureCursorVisible()

    def append_log_ai(self, text: str):
        self.send_log.emit(f"[游戏] {text}", "ai")
        self.append_log_formatted(text, 'black', '[游戏]')

    def append_log_player(self, text: str):
        self.append_log_formatted(text, 'blue', '[玩家]')

    def closeEvent(self, event):
        self.request_return()
        super().closeEvent(event)
