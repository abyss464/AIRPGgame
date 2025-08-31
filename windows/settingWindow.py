import sys
import json
from PySide6.QtWidgets import (
    QApplication, QVBoxLayout, QListWidget,
    QLineEdit, QFormLayout, QTextEdit, QMessageBox,
    QListWidgetItem, QFrame, QComboBox
)

from manager.model_config_manager import ModelConfigManager

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import Qt, QPoint


class CustomTitleBar(QWidget):
    """自定义标题栏，支持关闭和有限范围的拖动。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.parent_window = parent  # parent_window is the SettingWindow

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)

        self.title_label = QLabel("模型服务商配置")
        self.title_label.setStyleSheet("color: #E0E0E0; font-size: 16px; font-weight: bold;")

        layout.addWidget(self.title_label)
        layout.addStretch()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # self.parent_window is SettingWindow
            self.parent_window.start_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.parent_window.start_pos

            unconstrained_pos = self.parent_window.pos() + delta

            # 3. 获取边界（主窗口）
            main_window = self.parent_window.parent()
            if not main_window:
                # 如果没有父窗口，则不进行限制
                self.parent_window.move(unconstrained_pos)
                self.parent_window.start_pos = event.globalPosition().toPoint()
                event.accept()
                return

            min_x = 0
            min_y = 0
            max_x = main_window.width() - self.parent_window.width()
            max_y = main_window.height() - self.parent_window.height()

            # 5. "钳制"（Clamp）期望位置，使其在允许范围内
            final_pos = unconstrained_pos
            if final_pos.x() < min_x: final_pos.setX(min_x)
            if final_pos.x() > max_x: final_pos.setX(max_x)
            if final_pos.y() < min_y: final_pos.setY(min_y)
            if final_pos.y() > max_y: final_pos.setY(max_y)

            self.parent_window.move(final_pos)

            self.parent_window.start_pos = event.globalPosition().toPoint()
            event.accept()


class SettingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = ModelConfigManager()
        self.start_pos = QPoint()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("模型服务商配置")
        self.setMinimumSize(800, 800)
        self.resize(800, 800)

        self.init_ui()
        self.load_providers_list()
        self._set_dark_theme()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        container = QFrame(self)
        container.setObjectName("container")
        main_layout.addWidget(container)

        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(0, 0, 0, 10)
        content_layout.setSpacing(10)

        self.title_bar = CustomTitleBar(self)
        content_layout.addWidget(self.title_bar)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #4A4A4A;")
        content_layout.addWidget(line)

        workspace_layout = QHBoxLayout()
        workspace_layout.setContentsMargins(15, 10, 15, 10)
        workspace_layout.setSpacing(15)
        content_layout.addLayout(workspace_layout)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        left_panel.addWidget(QLabel("服务商列表"))
        self.provider_list = QListWidget()
        self.provider_list.currentItemChanged.connect(self.on_provider_selected)
        left_panel.addWidget(self.provider_list)

        left_button_layout = QHBoxLayout()
        self.add_button = QPushButton("➕ 新增")
        self.add_button.clicked.connect(self.prepare_add_provider)
        self.remove_button = QPushButton("➖ 删除")
        self.remove_button.clicked.connect(self.remove_provider)
        left_button_layout.addWidget(self.add_button)
        left_button_layout.addWidget(self.remove_button)
        left_panel.addLayout(left_button_layout)
        workspace_layout.addLayout(left_panel, stretch=1)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("详细配置"))
        self.form_layout = QFormLayout()
        self.form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.form_layout.setLabelAlignment(Qt.AlignRight)

        self.name_input = QLineEdit()
        self.base_url_input = QLineEdit()
        self.default_model_input = QLineEdit()
        self.provider_type_input = QLineEdit("openai")
        self.other_params_input = QTextEdit()
        self.other_params_input.setAcceptRichText(False)
        self.other_params_input.setPlaceholderText("请输入JSON格式的额外参数...")

        # <-- 2. Replace QListWidget with QComboBox -->
        self.available_models_combobox = QComboBox()
        self.available_models_combobox.setPlaceholderText("请先获取模型列表")
        # <-- 3. Connect signal to the new slot -->
        self.available_models_combobox.currentTextChanged.connect(self.on_model_selected)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.toggle_api_key_button = QPushButton("显示")
        self.toggle_api_key_button.setFixedWidth(60)
        self.toggle_api_key_button.setObjectName("visibilityButton")
        self.toggle_api_key_button.setCheckable(True)
        self.toggle_api_key_button.clicked.connect(self.toggle_api_key_visibility)

        api_key_layout = QHBoxLayout()
        api_key_layout.setContentsMargins(0, 0, 0, 0)
        api_key_layout.setSpacing(5)
        api_key_layout.addWidget(self.api_key_input)
        api_key_layout.addWidget(self.toggle_api_key_button)

        self.form_layout.addRow("名称 (Name):", self.name_input)
        self.form_layout.addRow("API Key:", api_key_layout)
        self.form_layout.addRow("Base URL:", self.base_url_input)
        # <-- 4. Use the new QComboBox in the layout -->
        self.form_layout.addRow("可用模型列表:", self.available_models_combobox)
        self.form_layout.addRow("默认模型:", self.default_model_input)
        self.form_layout.addRow("服务商类型:", self.provider_type_input)
        self.form_layout.addRow("其他参数 (JSON):", self.other_params_input)
        right_panel.addLayout(self.form_layout)

        right_button_layout = QHBoxLayout()
        self.fetch_button = QPushButton("🔄 获取模型列表")
        self.fetch_button.clicked.connect(self.fetch_models)
        self.save_button = QPushButton("💾 保存更改")
        self.save_button.clicked.connect(self.save_provider)
        self.close_button_main = QPushButton("关闭")
        self.close_button_main.clicked.connect(self.close)

        right_button_layout.addStretch()
        right_button_layout.addWidget(self.fetch_button)
        right_button_layout.addWidget(self.save_button)
        right_button_layout.addWidget(self.close_button_main)
        right_panel.addLayout(right_button_layout)
        workspace_layout.addLayout(right_panel, stretch=3)

        self.set_details_enabled(False)

    def _set_dark_theme(self):
        self.setStyleSheet("""
            /* ... (previous styles are the same) ... */
            #container { background-color: #2D2D2D; border: 1px solid #4A4A4A; border-radius: 8px; }
            QLabel { color: #E0E0E0; font-size: 14px; }

            /* <-- 5. Add QComboBox to the styled widgets list --> */
            QLineEdit, QTextEdit, QListWidget, QComboBox {
                background-color: #3C3C3C;
                color: #F0F0F0;
                border: 1px solid #5A5A5A;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-height: 28px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border-color: #007ACC; }

            /* <-- 6. Add specific styles for QComboBox dropdown --> */
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #5A5A5A;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow { image: url(down_arrow.png); } /* Optional: for a custom arrow icon */
            QComboBox QAbstractItemView { /* Style for the dropdown list itself */
                background-color: #3C3C3C;
                border: 1px solid #5A5A5A;
                selection-background-color: #007ACC;
                color: #F0F0F0;
                padding: 4px;
            }

            QPushButton { background-color: #555555; color: #FFFFFF; border: 1px solid #6A6A6A; border-radius: 4px; padding: 10px 16px; font-size: 14px; }
            QPushButton:hover { background-color: #686868; border-color: #888888; }
            QPushButton:pressed { background-color: #4A4A4A; }
            QPushButton:disabled { background-color: #404040; color: #888888; border-color: #555555; }
            #visibilityButton { padding: 8px; }
            #visibilityButton:checked { background-color: #007ACC; border-color: #005A9E; }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background-color: #007ACC; color: white; }
            /* ... (scrollbar styles are the same) ... */
        """)

    # <-- 7. New slot method to handle model selection -->
    def on_model_selected(self, model_name: str):
        """When a model is selected from the combobox, update the default model field."""
        # Check if the signal is not blocked and the text is valid
        if not self.available_models_combobox.signalsBlocked() and model_name:
            self.default_model_input.setText(model_name)

    def toggle_api_key_visibility(self, checked):
        if checked:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
            self.toggle_api_key_button.setText("隐藏")
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.toggle_api_key_button.setText("显示")

    def load_providers_list(self):
        self.provider_list.clear()
        providers = self.manager.list_providers()
        if providers:
            self.provider_list.addItems(providers)
            self.provider_list.setCurrentRow(0)
        else:
            self.clear_details()
            self.set_details_enabled(False)

    def on_provider_selected(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
        if not current_item:
            self.clear_details()
            self.set_details_enabled(False)
            return

        self.set_details_enabled(True)
        provider_name = current_item.text()
        provider_data = self.manager.get_provider(provider_name)

        if provider_data:
            self.name_input.setText(provider_data.get('name', ''))
            self.api_key_input.setText(provider_data.get('api_key', ''))
            self.base_url_input.setText(provider_data.get('base_url', ''))
            self.default_model_input.setText(provider_data.get('default_model', ''))
            self.provider_type_input.setText(provider_data.get('provider_type', 'openai'))

            other_params = provider_data.get('other_params', {})
            self.other_params_input.setText(json.dumps(other_params, indent=4) if other_params else '')

            # <-- 8. Update logic to populate QComboBox and set current item -->
            # Block signals to prevent on_model_selected from firing during setup
            self.available_models_combobox.blockSignals(True)
            self.available_models_combobox.clear()

            models = provider_data.get('available_models', [])
            if models:
                self.available_models_combobox.addItems(models)
                default_model = provider_data.get('default_model', '')
                if default_model in models:
                    self.available_models_combobox.setCurrentText(default_model)
                elif models:  # if default model not in list, select the first one
                    self.available_models_combobox.setCurrentIndex(0)

            # Unblock signals now that setup is complete
            self.available_models_combobox.blockSignals(False)
            # <-- End of modification -->

            self.toggle_api_key_button.setChecked(False)
            self.toggle_api_key_visibility(False)

    def prepare_add_provider(self):
        self.provider_list.clearSelection()
        self.clear_details()
        self.set_details_enabled(True)
        self.name_input.setFocus()

    def remove_provider(self):
        selected_item = self.provider_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "操作失败", "请先在左侧选择一个要删除的服务商。")
            return
        provider_name = selected_item.text()
        reply = QMessageBox.question(self, "确认删除", f"您确定要删除服务商 '{provider_name}' 吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.manager.remove_provider(provider_name):
                QMessageBox.information(self, "成功", f"服务商 '{provider_name}' 已被删除。")
                self.load_providers_list()
            else:
                QMessageBox.critical(self, "错误", "删除失败。")

    def save_provider(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "验证失败", "服务商名称不能为空。")
            return
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()
        default_model = self.default_model_input.text().strip()
        provider_type = self.provider_type_input.text().strip()
        other_params = {}
        try:
            other_params_text = self.other_params_input.toPlainText().strip()
            if other_params_text:
                other_params = json.loads(other_params_text)
            if not isinstance(other_params, dict):
                raise ValueError("JSON顶层必须是对象")
        except (json.JSONDecodeError, ValueError) as e:
            QMessageBox.critical(self, "格式错误", f"“其他参数”中的JSON格式不正确：\n{e}")
            return

        is_updating = self.manager.get_provider(name) is not None
        if is_updating:
            success = self.manager.update_provider(name=name, api_key=api_key, base_url=base_url,
                                                   default_model=default_model, provider_type=provider_type,
                                                   other_params=other_params)
        else:
            success = self.manager.add_provider(name=name, api_key=api_key, base_url=base_url,
                                                default_model=default_model, provider_type=provider_type,
                                                other_params=other_params)

        if success:
            QMessageBox.information(self, "成功", f"服务商 '{name}' 的配置已保存。")
            current_name = name
            self.load_providers_list()
            items = self.provider_list.findItems(current_name, Qt.MatchExactly)
            if items:
                self.provider_list.setCurrentItem(items[0])
        else:
            QMessageBox.critical(self, "错误", f"无法保存服务商 '{name}'。")

    def fetch_models(self):
        selected_item = self.provider_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "操作失败", "请先选择一个服务商。")
            return

        provider_name = self.name_input.text().strip()  # Use name from input field
        base_url = self.base_url_input.text().strip()
        api_key = self.api_key_input.text().strip()

        if not base_url or not api_key:
            QMessageBox.warning(self, "信息不完整", "获取模型需要有效的 Base URL 和 API Key。")
            return

        # Temporarily update the manager's in-memory config for the fetch call
        # This allows fetching models for a new or modified provider before saving
        temp_provider_config = {
            'name': provider_name,
            'base_url': base_url,
            'api_key': api_key
        }

        if self.manager.get_provider(provider_name):
            self.manager.update_provider(provider_name, base_url=base_url, api_key=api_key)
        else:
            self.manager.config['providers'].append(temp_provider_config)

        self.fetch_button.setText("获取中...")
        self.fetch_button.setEnabled(False)
        QApplication.processEvents()

        models = self.manager.fetch_and_update_models(provider_name)

        self.fetch_button.setText("🔄 获取模型列表")
        self.fetch_button.setEnabled(True)

        if not self.manager.get_provider(selected_item.text()):  # If it was a temporary provider, remove it
            self.manager.config['providers'] = [p for p in self.manager.config['providers'] if
                                                p['name'] != provider_name]

        if models is not None:
            QMessageBox.information(self, "成功", f"成功为 '{provider_name}' 获取了 {len(models)} 个模型。")
            self.on_provider_selected(self.provider_list.currentItem(), None)
        else:
            QMessageBox.critical(self, "失败", f"无法从 '{provider_name}' 获取模型列表。")

    def clear_details(self):
        self.name_input.clear()
        self.api_key_input.clear()
        self.base_url_input.clear()
        self.default_model_input.clear()
        self.provider_type_input.setText("openai")
        self.other_params_input.clear()
        # <-- 9. Update clear logic -->
        self.available_models_combobox.clear()

        self.toggle_api_key_button.setChecked(False)
        self.toggle_api_key_visibility(False)

    def set_details_enabled(self, enabled: bool):
        # <-- 10. Update widget list to toggle -->
        widgets_to_toggle = [
            self.name_input, self.api_key_input, self.base_url_input,
            self.default_model_input, self.provider_type_input,
            self.other_params_input, self.save_button, self.fetch_button,
            self.remove_button, self.toggle_api_key_button,
            self.available_models_combobox
        ]
        for w in widgets_to_toggle:
            w.setEnabled(enabled)

        if not enabled or self.provider_list.currentItem() is None:
            self.remove_button.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SettingWindow()
    window.show()
    sys.exit(app.exec())
