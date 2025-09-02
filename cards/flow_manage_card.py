from functools import partial

# 1. 导入两个核心逻辑类
from manager.json_flow_manager import JsonWorkflowManager
from manager.prompt_manager import PromptManager, PROMPT_TYPES
from manager.model_config_manager import ModelConfigManager

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QInputDialog, QMessageBox, QFormLayout, QLineEdit,
    QTextEdit, QCheckBox, QSplitter, QTreeView, QStackedWidget, QDialog,
    QComboBox, QAbstractItemView, QDialogButtonBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction


# --- 常量定义 ---
ITEM_TYPE_ROLE = Qt.UserRole + 1
ITEM_ID_ROLE = Qt.UserRole + 2
ITEM_PARENT_IDS_ROLE = Qt.UserRole + 3


class AddPromptDialog(QDialog):
    """
    一个用于添加新提示词的专用对话框。
    允许用户输入名称、选择类型、填写描述和内容。
    """

    def __init__(self, prompt_types, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加新提示词")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(prompt_types)
        self.desc_edit = QLineEdit()
        self.content_edit = QTextEdit()
        self.content_edit.setAcceptRichText(False)  # 通常提示词是纯文本

        form_layout.addRow("名称 (唯一):", self.name_edit)
        form_layout.addRow("类型:", self.type_combo)
        form_layout.addRow("描述:", self.desc_edit)
        form_layout.addRow("内容:", self.content_edit)

        layout.addLayout(form_layout)

        # 标准的 OK/Cancel 按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def accept(self):
        # 在接受对话框前，进行基本校验
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "提示词名称不能为空。")
            self.name_edit.setFocus()
            return
        # 校验通过，调用父类的accept
        super().accept()

    def get_data(self):
        """返回用户输入的数据字典"""
        return {
            "name": self.name_edit.text().strip(),
            "type": self.type_combo.currentText(),
            "description": self.desc_edit.text(),
            "content": self.content_edit.toPlainText()
        }

class PromptManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("全局提示词管理器")
        self.setMinimumSize(800, 600)
        self.manager = PromptManager('prompts.json')
        main_layout = QVBoxLayout(self)
        toolbar_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加新提示词")
        self.del_btn = QPushButton("删除选中项")
        self.add_btn.clicked.connect(self._add_prompt)
        self.del_btn.clicked.connect(self._delete_prompt)
        toolbar_layout.addWidget(self.add_btn)
        toolbar_layout.addWidget(self.del_btn)
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_model = QStandardItemModel()
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree_view.setModel(self.tree_model)
        self.tree_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.tree_view.doubleClicked.connect(self._on_tree_item_double_clicked)
        splitter.addWidget(self.tree_view)
        self.details_panel = QWidget()
        self.details_layout = QFormLayout(self.details_panel)
        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        self.type_combo = QComboBox()
        self.type_combo.addItems(PROMPT_TYPES)
        self.desc_edit = QLineEdit()
        self.content_edit = QTextEdit()
        self.save_btn = QPushButton("保存更改")
        self.save_btn.clicked.connect(self._save_prompt_details)
        self.details_layout.addRow("名称 (唯一):", self.name_edit)
        self.details_layout.addRow("类型:", self.type_combo)
        self.details_layout.addRow("描述:", self.desc_edit)
        self.details_layout.addRow("内容:", self.content_edit)
        self.details_layout.addRow(self.save_btn)
        splitter.addWidget(self.details_panel)
        splitter.setSizes([250, 550])
        self._populate_tree()
        self._on_selection_changed()

    def _populate_tree(self):
        self.tree_model.clear()
        root = self.tree_model.invisibleRootItem()
        type_items = {}
        for p_type in PROMPT_TYPES: type_item = QStandardItem(p_type.replace('_', ' ').title()); type_item.setData(
            "category", ITEM_TYPE_ROLE); type_item.setEditable(False); root.appendRow(type_item); type_items[
            p_type] = type_item
        for name, data in self.manager.prompts.items(): prompt_item = QStandardItem(name); prompt_item.setData("prompt",
                                                                                                               ITEM_TYPE_ROLE); prompt_item.setData(
            name, ITEM_ID_ROLE); parent_item = type_items.get(data.get("type")); (
                    parent_item and parent_item.appendRow(prompt_item))
        self.tree_view.expandAll()

    def _get_selected_prompt_name(self):
        indexes = self.tree_view.selectedIndexes();
        item = self.tree_model.itemFromIndex(indexes[0]) if indexes else None;
        return item.data(ITEM_ID_ROLE) if item and item.data(ITEM_TYPE_ROLE) == "prompt" else None

    def _on_selection_changed(self):
        prompt_name = self._get_selected_prompt_name();
        is_prompt_selected = prompt_name is not None
        self.details_panel.setEnabled(is_prompt_selected);
        self.del_btn.setEnabled(is_prompt_selected)
        if is_prompt_selected:
            prompt_data = self.manager.get_prompt(prompt_name); self.name_edit.setText(
                prompt_name); self.type_combo.setCurrentText(prompt_data.get("type", "")); self.desc_edit.setText(
                prompt_data.get("description", "")); self.content_edit.setText(prompt_data.get("content", ""))
        else:
            self.name_edit.clear(); self.desc_edit.clear(); self.content_edit.clear(); self.type_combo.setCurrentIndex(
                -1)

    def _add_prompt(self):
        """
        使用自定义的 AddPromptDialog 来添加新提示词，提供更好的用户体验。
        """
        dialog = AddPromptDialog(PROMPT_TYPES, self)

        # 以模态方式显示对话框，并检查返回值
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            name = data["name"]

            # 唯一性校验
            if self.manager.get_prompt(name):
                QMessageBox.warning(self, "错误", f"名称 '{name}' 已存在，请使用其他名称。")
                return  # 提前返回，不进行后续操作

            # 添加到管理器
            self.manager.add_prompt(
                name,
                data["type"],
                data["content"],
                data["description"]
            )

            # 保存并刷新UI
            if self.manager.save_prompts():
                # 重新填充树
                self._populate_tree()
                # 自动选中新添加的项，提升用户体验
                self._select_item_by_name(name)
                QMessageBox.information(self, "成功", f"提示词 '{name}' 已成功添加。")

    # 在 _populate_tree 方法之后，_add_prompt 方法之前添加
    def _select_item_by_name(self, name):
        """在树中查找并选中指定名称的项"""
        # 使用 MatchRecursive 在整个模型中递归查找
        items = self.tree_model.findItems(name, Qt.MatchExactly | Qt.MatchRecursive)
        for item in items:
            # 确保找到的是一个 prompt 项，而不是同名的类别项
            if item.data(ITEM_TYPE_ROLE) == "prompt":
                index = self.tree_model.indexFromItem(item)
                # 设置为当前选中项
                self.tree_view.setCurrentIndex(index)
                return # 找到后即可退出

    def _on_tree_item_double_clicked(self, index):
        self.tree_view.selectionModel().clearSelection()

    def _delete_prompt(self):
        prompt_name = self._get_selected_prompt_name()
        if prompt_name: reply = QMessageBox.question(self, "确认删除", f"确定删除 '{prompt_name}' 吗？",
                                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No); (
                    reply == QMessageBox.Yes and self.manager.delete_prompt(
                prompt_name) and self.manager.save_prompts() and self._populate_tree())

    def _save_prompt_details(self):
        prompt_name = self.name_edit.text()
        if prompt_name: self.manager.update_prompt_attribute(prompt_name, "type",
                                                             self.type_combo.currentText()); self.manager.update_prompt_attribute(
            prompt_name, "description", self.desc_edit.text()); self.manager.update_prompt_attribute(prompt_name,
                                                                                                     "content",
                                                                                                     self.content_edit.toPlainText()); self.manager.save_prompts(); QMessageBox.information(
            self, "成功", "已保存。"); self._populate_tree()

class PromptBuilderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent);
        self.setWindowTitle("提示词构造器");
        self.setMinimumSize(900, 600);
        self.manager = PromptManager('prompts.json');
        self.final_prompt_text = ""
        main_layout = QVBoxLayout(self);
        splitter = QSplitter(Qt.Horizontal);
        main_layout.addWidget(splitter)
        left_widget = QWidget();
        left_layout = QVBoxLayout(left_widget);
        left_layout.addWidget(QLabel("<b>可用提示词 (可多选)</b>"));
        self.tree_view = QTreeView();
        self.tree_view.setHeaderHidden(True);
        self.tree_model = QStandardItemModel();
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection);
        self.tree_view.selectionModel().selectionChanged.connect(self._update_preview);
        left_layout.addWidget(self.tree_view);
        splitter.addWidget(left_widget)
        right_widget = QWidget();
        right_layout = QVBoxLayout(right_widget);
        right_layout.addWidget(QLabel("<b>组合预览</b>"));
        self.preview_edit = QTextEdit();
        self.preview_edit.setReadOnly(True);
        right_layout.addWidget(self.preview_edit);
        splitter.addWidget(right_widget);
        splitter.setSizes([300, 600])
        button_layout = QHBoxLayout();
        button_layout.addStretch();
        ok_btn = QPushButton("确定");
        cancel_btn = QPushButton("取消");
        ok_btn.clicked.connect(self.accept);
        cancel_btn.clicked.connect(self.reject);
        button_layout.addWidget(ok_btn);
        button_layout.addWidget(cancel_btn);
        main_layout.addLayout(button_layout)
        self._populate_tree()

    def _populate_tree(self):
        self.tree_model.clear();
        root = self.tree_model.invisibleRootItem();
        type_items = {}
        for p_type in PROMPT_TYPES: type_item = QStandardItem(p_type.replace('_', ' ').title()); type_item.setData(
            "category", ITEM_TYPE_ROLE); type_item.setEditable(False); root.appendRow(type_item); type_items[
            p_type] = type_item
        for name, data in self.manager.prompts.items(): prompt_item = QStandardItem(name); prompt_item.setData("prompt",
                                                                                                               ITEM_TYPE_ROLE); prompt_item.setData(
            name, ITEM_ID_ROLE); parent_item = type_items.get(data.get("type")); (
                    parent_item and parent_item.appendRow(prompt_item))
        self.tree_view.expandAll()

    def _update_preview(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if not selected_indexes: self.preview_edit.clear(); self.final_prompt_text = ""; return
        selected_names = {self.tree_model.itemFromIndex(index).data(ITEM_ID_ROLE) for index in selected_indexes if
                          self.tree_model.itemFromIndex(index).data(ITEM_TYPE_ROLE) == "prompt"}
        sorted_prompts = {ptype: [] for ptype in PROMPT_TYPES}
        for name in selected_names: prompt_data = self.manager.get_prompt(name); (
                    prompt_data and sorted_prompts[prompt_data['type']].append(prompt_data['content']))
        preview_parts = [];
        final_parts = []
        for ptype, contents in sorted_prompts.items():
            if contents: preview_parts.extend(
                [f"--- {ptype.upper().replace('_', ' ')} ---\n", *contents, "\n"]); final_parts.extend(contents)
        self.preview_edit.setText("\n".join(preview_parts));
        self.final_prompt_text = "\n\n".join(final_parts)

    def get_final_prompt(self) -> str:
        return self.final_prompt_text


class HierarchicalFlowManagerUI(QWidget):
    send_log = Signal(str)
    return_to_menu_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # 假设 JsonWorkflowManager 类已在前面定义
        self.manager = JsonWorkflowManager('workflows.json')
        self.model_manager = ModelConfigManager()

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 全局工具栏
        global_toolbar_layout = QHBoxLayout()
        self.return_btn = QPushButton("🔙 返回主菜单")
        self.return_btn.clicked.connect(self.return_to_menu_requested.emit)
        global_toolbar_layout.addWidget(self.return_btn)
        self.manage_prompts_btn = QPushButton("📚 管理提示词库")
        self.manage_prompts_btn.clicked.connect(self._open_global_prompt_manager)
        global_toolbar_layout.addWidget(self.manage_prompts_btn)
        global_toolbar_layout.addStretch()
        main_layout.addLayout(global_toolbar_layout)

        # 流程专用工具栏
        workflow_toolbar_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加流程")
        self.del_btn = QPushButton("删除选中项")
        self.add_btn.clicked.connect(self._add_item)
        self.del_btn.clicked.connect(self._delete_item)
        workflow_toolbar_layout.addWidget(self.add_btn)
        workflow_toolbar_layout.addWidget(self.del_btn)
        workflow_toolbar_layout.addStretch()
        main_layout.addLayout(workflow_toolbar_layout)

        # 主区域 (树 + 详情)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree_view.doubleClicked.connect(self._handle_tree_double_click)
        self.tree_model = QStandardItemModel()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.tree_view)

        self.details_panel = QWidget()
        self.details_layout = QVBoxLayout(self.details_panel)
        self.details_layout.setAlignment(Qt.AlignTop)
        self.stacked_widget = QStackedWidget()
        self._setup_details_widgets()
        self.details_layout.addWidget(self.stacked_widget)
        splitter.addWidget(self.details_panel)
        splitter.setSizes([350, 650])

        self._populate_tree()
        self._on_selection_changed()

    def _open_global_prompt_manager(self):
        dialog = PromptManagerDialog(self)
        dialog.exec()

    def _handle_tree_double_click(self, index):
        if index.isValid():
            self.tree_view.selectionModel().clearSelection()

    def _setup_details_widgets(self):
        # 0: Empty Widget
        self.empty_widget = QLabel("← 请在左侧选择一个项目进行查看或编辑")
        self.empty_widget.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(self.empty_widget)

        # 1: Workflow Details
        self.wf_details_widget = QWidget()
        wf_layout = QFormLayout(self.wf_details_widget)
        self.wf_name_edit = QLineEdit()
        self.wf_desc_edit = QTextEdit()
        wf_save_btn = QPushButton("保存更改")
        wf_layout.addRow("名称:", self.wf_name_edit)
        wf_layout.addRow("描述:", self.wf_desc_edit)
        wf_layout.addRow(wf_save_btn)
        self.stacked_widget.addWidget(self.wf_details_widget)
        wf_save_btn.clicked.connect(partial(self._save_details, "workflow"))

        # 2: Node Details
        self.node_details_widget = QWidget()
        node_layout = QFormLayout(self.node_details_widget)
        self.node_name_edit = QLineEdit()
        self.node_loop_check = QCheckBox("无限循环此节点内的所有步骤")

        # --- 新增Node条件循环控件 ---
        self.node_loop_condition_check = QCheckBox("循环直至条件满足")
        self.node_loop_condition_label = QLabel("条件:")
        self.node_loop_condition_edit = QLineEdit()
        self.node_loop_condition_check.toggled.connect(self._toggle_node_condition_widgets)
        # --- 结束新增 ---

        node_save_btn = QPushButton("保存更改")
        node_layout.addRow("名称:", self.node_name_edit)
        node_layout.addRow(self.node_loop_check)

        # --- 新增Node条件循环布局 ---
        node_layout.addRow(self.node_loop_condition_check)
        node_layout.addRow(self.node_loop_condition_label, self.node_loop_condition_edit)
        # --- 结束新增 ---

        node_layout.addRow(node_save_btn)
        self.stacked_widget.addWidget(self.node_details_widget)
        node_save_btn.clicked.connect(partial(self._save_details, "node"))

        # 3: Step Details
        self.step_details_widget = QWidget()
        step_layout = QFormLayout(self.step_details_widget)
        self.step_name_edit = QLineEdit()
        prompt_header_layout = QHBoxLayout()
        prompt_header_layout.addWidget(QLabel("提示词(Prompt):"))
        prompt_header_layout.addStretch()
        self.build_prompt_btn = QPushButton("🔨 构建提示词")
        self.build_prompt_btn.clicked.connect(self._open_prompt_builder)
        prompt_header_layout.addWidget(self.build_prompt_btn)
        self.step_prompt_edit = QTextEdit()
        self.step_provider_combo = QComboBox()
        self.step_model_combo = QComboBox()
        self.step_provider_combo.currentTextChanged.connect(self._update_step_model_combo)
        self.step_read_file_edit = QLineEdit()
        self.step_save_file_edit = QLineEdit()
        self.step_use_user_context_check = QCheckBox()
        self.step_use_context_check = QCheckBox()
        self.step_output_console_check = QCheckBox()
        self.step_parallel_check = QCheckBox()
        self.step_save_context_check = QCheckBox()

        # --- 新增Step条件循环控件 ---
        self.step_loop_condition_check = QCheckBox("循环直至条件满足")
        self.step_loop_condition_label = QLabel("条件:")
        self.step_loop_condition_edit = QLineEdit()
        self.step_loop_condition_check.toggled.connect(self._toggle_step_condition_widgets)
        # --- 结束新增 ---

        step_save_btn = QPushButton("保存更改")
        step_layout.addRow("名称:", self.step_name_edit)
        step_layout.addRow(prompt_header_layout)
        step_layout.addRow(self.step_prompt_edit)
        step_layout.addRow("服务商:", self.step_provider_combo)
        step_layout.addRow("模型:", self.step_model_combo)
        step_layout.addRow("从文件读入:", self.step_read_file_edit)
        step_layout.addRow("存入指定文件:", self.step_save_file_edit)
        step_layout.addRow("允许用户输入:", self.step_use_user_context_check)
        step_layout.addRow("使用上下文:", self.step_use_context_check)
        step_layout.addRow("保存输出到上下文:", self.step_save_context_check)
        step_layout.addRow("并行执行:", self.step_parallel_check)
        step_layout.addRow("输出至控制台:", self.step_output_console_check)

        # --- 新增Step条件循环布局 ---
        step_layout.addRow(self.step_loop_condition_check)
        step_layout.addRow(self.step_loop_condition_label, self.step_loop_condition_edit)
        # --- 结束新增 ---

        step_layout.addRow(step_save_btn)
        self.stacked_widget.addWidget(self.step_details_widget)
        step_save_btn.clicked.connect(partial(self._save_details, "step"))

        # 初始化隐藏条件控件
        self._toggle_node_condition_widgets(False)
        self._toggle_step_condition_widgets(False)

    # --- 新增的槽函数 ---
    def _toggle_node_condition_widgets(self, checked):
        """根据复选框状态显示或隐藏Node的条件输入框"""
        self.node_loop_condition_label.setVisible(checked)
        self.node_loop_condition_edit.setVisible(checked)

    def _toggle_step_condition_widgets(self, checked):
        """根据复选框状态显示或隐藏Step的条件输入框"""
        self.step_loop_condition_label.setVisible(checked)
        self.step_loop_condition_edit.setVisible(checked)

    # --- 结束新增 ---

    def _update_step_provider_combo(self):
        current_provider = self.step_provider_combo.currentText()
        self.step_provider_combo.blockSignals(True)
        self.step_provider_combo.clear()
        providers = self.model_manager.list_providers()
        if providers:
            self.step_provider_combo.addItems(providers)
            if current_provider in providers:
                self.step_provider_combo.setCurrentText(current_provider)
        self.step_provider_combo.blockSignals(False)
        self._update_step_model_combo(self.step_provider_combo.currentText())

    def _update_step_model_combo(self, provider_name: str):
        current_model = self.step_model_combo.currentText()
        self.step_model_combo.clear()
        if provider_name:
            models = self.model_manager.list_available_models(provider_name)
            if models:
                self.step_model_combo.addItems(models)
                if current_model in models:
                    self.step_model_combo.setCurrentText(current_model)

    def _open_prompt_builder(self):
        dialog = PromptBuilderDialog(self)
        if dialog.exec():
            self.step_prompt_edit.setText(dialog.get_final_prompt())
            self.send_log.emit("使用构造器更新了提示词。")

    def _populate_tree(self):
        _, selected_id, _ = self._get_selected_item_info()
        self.tree_model.clear()
        root = self.tree_model.invisibleRootItem()
        item_to_reselect = None
        for wf_id, wf_data in self.manager.data.items():
            wf_item = QStandardItem(wf_data.get("name", "未命名流程"))
            wf_item.setData("workflow", ITEM_TYPE_ROLE)
            wf_item.setData(wf_id, ITEM_ID_ROLE)
            root.appendRow(wf_item)
            if wf_id == selected_id: item_to_reselect = wf_item
            for node_id, node_data in wf_data.get("nodes", {}).items():
                node_name = node_data.get("name", "未命名节点")
                # --- 修改：更新循环状态的显示文本 ---
                loop_text = ""
                if node_data.get("loop_until_condition_met", False):
                    loop_text = " (条件循环)"
                elif node_data.get("loop", False):
                    loop_text = " (无限循环)"
                node_item = QStandardItem(f"{node_name}{loop_text}")
                # --- 结束修改 ---
                node_item.setData("node", ITEM_TYPE_ROLE)
                node_item.setData(node_id, ITEM_ID_ROLE)
                node_item.setData({"wf_id": wf_id}, ITEM_PARENT_IDS_ROLE)
                wf_item.appendRow(node_item)
                if node_id == selected_id: item_to_reselect = node_item
                for step_data in node_data.get("steps", []):
                    step_id = step_data.get("step_id")
                    step_name = step_data.get("name", "未命名步骤")
                    # --- 新增：为Step也添加循环状态显示 ---
                    loop_text = ""
                    if step_data.get("loop_until_condition_met", False):
                        loop_text = " (条件循环)"
                    step_item = QStandardItem(f"{step_name}{loop_text}")
                    # --- 结束新增 ---
                    step_item.setData("step", ITEM_TYPE_ROLE)
                    step_item.setData(step_id, ITEM_ID_ROLE)
                    step_item.setData({"wf_id": wf_id, "node_id": node_id}, ITEM_PARENT_IDS_ROLE)
                    node_item.appendRow(step_item)
                    if step_id == selected_id: item_to_reselect = step_item
        self.tree_view.expandAll()
        if item_to_reselect: self.tree_view.setCurrentIndex(self.tree_model.indexFromItem(item_to_reselect))

    def _get_selected_item_info(self):
        indexes = self.tree_view.selectedIndexes()
        if not indexes: return None, None, None
        item = self.tree_model.itemFromIndex(indexes[0])
        return (item.data(ITEM_TYPE_ROLE), item.data(ITEM_ID_ROLE), item.data(ITEM_PARENT_IDS_ROLE)) if item else (
        None, None, None)

    def _on_selection_changed(self):
        self._update_ui_state()
        self._update_details_panel()

    def _update_ui_state(self):
        item_type, _, _ = self._get_selected_item_info()
        self.del_btn.setEnabled(item_type is not None)
        if item_type == "workflow":
            self.add_btn.setText("添加节点")
            self.add_btn.setEnabled(True)
        elif item_type == "node":
            self.add_btn.setText("添加流节点")
            self.add_btn.setEnabled(True)
        elif item_type == "step":
            self.add_btn.setText("添加...")
            self.add_btn.setEnabled(False)
        else:
            self.add_btn.setText("添加流程")
            self.add_btn.setEnabled(True)

    def _update_details_panel(self):
        item_type, item_id, parent_ids = self._get_selected_item_info()
        if not item_type or not item_id:
            self.stacked_widget.setCurrentIndex(0)
            return

        data = None
        if item_type == "workflow":
            data = self.manager.get_workflow(item_id)
        elif item_type == "node" and parent_ids:
            wf_data = self.manager.get_workflow(parent_ids["wf_id"])
            data = wf_data.get('nodes', {}).get(item_id) if wf_data else None
        elif item_type == "step" and parent_ids:
            wf_data = self.manager.get_workflow(parent_ids["wf_id"])
            node_data = wf_data.get('nodes', {}).get(parent_ids["node_id"]) if wf_data else None
            data = next((s for s in node_data.get('steps', []) if s.get('step_id') == item_id),
                        None) if node_data else None

        if not data:
            self.stacked_widget.setCurrentIndex(0)
            return

        if item_type == "workflow":
            self.wf_name_edit.setText(data.get("name", ""))
            self.wf_desc_edit.setText(data.get("description", ""))
            self.stacked_widget.setCurrentIndex(1)
        elif item_type == "node":
            self.node_name_edit.setText(data.get("name", ""))
            self.node_loop_check.setChecked(data.get("loop", False))
            # --- 新增：加载Node条件循环数据 ---
            is_cond_loop = data.get("loop_until_condition_met", False)
            self.node_loop_condition_check.setChecked(is_cond_loop)
            self.node_loop_condition_edit.setText(data.get("loop_condition", ""))
            self._toggle_node_condition_widgets(is_cond_loop)  # 更新控件可见性
            # --- 结束新增 ---
            self.stacked_widget.setCurrentIndex(2)
        elif item_type == "step":
            self.step_name_edit.setText(data.get("name", ""))
            self.step_prompt_edit.setText(data.get("prompt", ""))
            self.step_read_file_edit.setText(data.get("read_from_file") or "")
            self.step_save_file_edit.setText(data.get("save_to_file") or "")
            self.step_use_user_context_check.setChecked(data.get("use_user_context", True))
            self.step_use_context_check.setChecked(data.get("use_context", False))
            self.step_output_console_check.setChecked(data.get("output_to_console", False))
            self.step_parallel_check.setChecked(data.get("parallel_execution", True))
            self.step_save_context_check.setChecked(data.get("save_to_context", True))

            # --- 新增：加载Step条件循环数据 ---
            is_cond_loop = data.get("loop_until_condition_met", False)
            self.step_loop_condition_check.setChecked(is_cond_loop)
            self.step_loop_condition_edit.setText(data.get("loop_condition", ""))
            self._toggle_step_condition_widgets(is_cond_loop)  # 更新控件可见性
            # --- 结束新增 ---

            self._update_step_provider_combo()
            self.step_provider_combo.setCurrentText(data.get("provider", ""))
            self._update_step_model_combo(data.get("provider", ""))
            self.step_model_combo.setCurrentText(data.get("model", ""))
            self.stacked_widget.setCurrentIndex(3)

    def _add_item(self):
        item_type, item_id, parent_ids = self._get_selected_item_info()
        if item_type == "workflow":
            name, ok = QInputDialog.getText(self, "添加节点", "节点名称:")
        elif item_type == "node":
            name, ok = QInputDialog.getText(self, "添加流节点", "流节点(Step)名称:")
        else:
            name, ok = QInputDialog.getText(self, "添加流程", "流程名称:")
        if ok and name:
            if item_type == "workflow":
                self.manager.add_node(item_id, name)
            elif item_type == "node":
                self.manager.add_step(parent_ids["wf_id"], item_id, {"name": name})
            else:
                self.manager.create_workflow(name)
        self._populate_tree()

    def _delete_item(self):
        item_type, item_id, parent_ids = self._get_selected_item_info()
        if item_type:
            reply = QMessageBox.question(self, "确认删除", f"确定删除 '{item_type}' 吗？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if item_type and reply == QMessageBox.Yes:
            if item_type == "workflow":
                self.manager.delete_workflow(item_id)
            elif item_type == "node":
                self.manager.delete_node(parent_ids["wf_id"], item_id)
            elif item_type == "step":
                self.manager.delete_step(parent_ids["wf_id"], parent_ids["node_id"], item_id)
            self._populate_tree()
            self.stacked_widget.setCurrentIndex(0)

    def _save_details(self, item_to_save):
        item_type, item_id, parent_ids = self._get_selected_item_info()
        if item_type == item_to_save:
            if item_type == "workflow":
                self.manager.edit_workflow(item_id, name=self.wf_name_edit.text(),
                                           description=self.wf_desc_edit.toPlainText())
            elif item_type == "node":
                # --- 修改：在保存时加入新的条件循环字段 ---
                self.manager.edit_node(
                    parent_ids["wf_id"],
                    item_id,
                    name=self.node_name_edit.text(),
                    loop=self.node_loop_check.isChecked(),
                    loop_until_condition_met=self.node_loop_condition_check.isChecked(),
                    loop_condition=self.node_loop_condition_edit.text() if self.node_loop_condition_check.isChecked() else ""
                )
                # --- 结束修改 ---
            elif item_type == "step":
                # --- 修改：在保存时加入新的条件循环字段 ---
                updates = {
                    "name": self.step_name_edit.text(),
                    "prompt": self.step_prompt_edit.toPlainText(),
                    "provider": self.step_provider_combo.currentText(),
                    "model": self.step_model_combo.currentText(),
                    "read_from_file": self.step_read_file_edit.text() or None,
                    "save_to_file": self.step_save_file_edit.text() or None,
                    "use_user_context": self.step_use_user_context_check.isChecked(),
                    "use_context": self.step_use_context_check.isChecked(),
                    "output_to_console": self.step_output_console_check.isChecked(),
                    "parallel_execution": self.step_parallel_check.isChecked(),
                    "save_to_context": self.step_save_context_check.isChecked(),
                    "loop_until_condition_met": self.step_loop_condition_check.isChecked(),
                    "loop_condition": self.step_loop_condition_edit.text() if self.step_loop_condition_check.isChecked() else ""
                }
                self.manager.edit_step(parent_ids["wf_id"], parent_ids["node_id"], item_id, updates)
                # --- 结束修改 ---

            self.send_log.emit(f"更新了 {item_type}: {item_id}")
            self._populate_tree()
