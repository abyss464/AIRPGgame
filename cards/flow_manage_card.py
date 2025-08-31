import sys
from functools import partial

# 1. 导入核心逻辑类
from json_flow_manager import JsonWorkflowManager

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QApplication,
    QMainWindow, QInputDialog, QMessageBox, QFormLayout, QLineEdit,
    QTextEdit, QCheckBox, QSplitter, QTreeView, QStackedWidget
)

# 自定义数据角色常量
ITEM_TYPE_ROLE = Qt.UserRole + 1
ITEM_ID_ROLE = Qt.UserRole + 2
ITEM_PARENT_IDS_ROLE = Qt.UserRole + 3


class HierarchicalFlowManagerUI(QWidget):
    return_to_menu_requested = Signal()
    send_log = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 2. 实例化导入的管理器
        self.manager = JsonWorkflowManager('workflows.json')

        main_layout = QVBoxLayout(self)

        # --- 工具栏 ---
        toolbar_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加流程")
        self.del_btn = QPushButton("删除选中项")
        self.add_btn.clicked.connect(self._add_item)
        self.del_btn.clicked.connect(self._delete_item)
        toolbar_layout.addWidget(self.add_btn)
        toolbar_layout.addWidget(self.del_btn)
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)

        # --- 主区域 (树 + 详情) ---
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧: 树视图
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_model = QStandardItemModel()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.tree_view)

        # 右侧: 详情面板
        self.details_panel = QWidget()
        self.details_layout = QVBoxLayout(self.details_panel)
        self.details_layout.setAlignment(Qt.AlignTop)
        self.stacked_widget = QStackedWidget()
        self._setup_details_widgets()
        self.details_layout.addWidget(self.stacked_widget)
        splitter.addWidget(self.details_panel)
        splitter.setSizes([350, 650])

        self._populate_tree()
        self._on_selection_changed()  # 初始化UI状态

    def _setup_details_widgets(self):
        """创建所有类型的详情面板并放入QStackedWidget"""
        # 0: 空白页
        self.empty_widget = QLabel("← 请在左侧选择一个项目进行查看或编辑")
        self.empty_widget.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(self.empty_widget)

        # 1: 流程详情页
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

        # 2: 节点详情页
        self.node_details_widget = QWidget()
        node_layout = QFormLayout(self.node_details_widget)
        self.node_name_edit = QLineEdit()
        self.node_loop_check = QCheckBox("循环执行此节点内的所有步骤")
        node_save_btn = QPushButton("保存更改")
        node_layout.addRow("名称:", self.node_name_edit)
        node_layout.addRow(self.node_loop_check)
        node_layout.addRow(node_save_btn)
        self.stacked_widget.addWidget(self.node_details_widget)
        node_save_btn.clicked.connect(partial(self._save_details, "node"))

        # 3: 流节点(Step)详情页
        self.step_details_widget = QWidget()
        step_layout = QFormLayout(self.step_details_widget)
        self.step_name_edit = QLineEdit()
        self.step_prompt_edit = QTextEdit()
        self.step_provider_edit = QLineEdit()
        self.step_model_edit = QLineEdit()
        self.step_read_file_edit = QLineEdit()
        self.step_save_file_edit = QLineEdit()
        self.step_use_context_check = QCheckBox()
        self.step_output_console_check = QCheckBox()
        step_save_btn = QPushButton("保存更改")
        step_layout.addRow("名称:", self.step_name_edit)
        step_layout.addRow("提示词(Prompt):", self.step_prompt_edit)
        step_layout.addRow("服务商:", self.step_provider_edit)
        step_layout.addRow("模型:", self.step_model_edit)
        step_layout.addRow("从文件读入:", self.step_read_file_edit)
        step_layout.addRow("存入指定文件:", self.step_save_file_edit)
        step_layout.addRow("使用上下文:", self.step_use_context_check)
        step_layout.addRow("输出至控制台:", self.step_output_console_check)
        step_layout.addRow(step_save_btn)
        self.stacked_widget.addWidget(self.step_details_widget)
        step_save_btn.clicked.connect(partial(self._save_details, "step"))

    def _populate_tree(self):
        """用manager中的数据完全重构树"""
        # 保存当前选中的ID，以便刷新后恢复
        _, selected_id, _ = self._get_selected_item_info()

        self.tree_model.clear()
        root = self.tree_model.invisibleRootItem()
        item_to_reselect = None

        for wf_id, wf_data in self.manager.data.items():
            wf_item = QStandardItem(wf_data.get("name", "未命名流程"))
            wf_item.setData("workflow", ITEM_TYPE_ROLE)
            wf_item.setData(wf_id, ITEM_ID_ROLE)
            root.appendRow(wf_item)
            if wf_id == selected_id:
                item_to_reselect = wf_item

            for node_id, node_data in wf_data.get("nodes", {}).items():
                node_name = node_data.get("name", "未命名节点")
                is_loop = " (循环)" if node_data.get("loop", False) else ""
                node_item = QStandardItem(f"{node_name}{is_loop}")
                node_item.setData("node", ITEM_TYPE_ROLE)
                node_item.setData(node_id, ITEM_ID_ROLE)
                node_item.setData({"wf_id": wf_id}, ITEM_PARENT_IDS_ROLE)
                wf_item.appendRow(node_item)
                if node_id == selected_id:
                    item_to_reselect = node_item

                for step_data in node_data.get("steps", []):
                    step_id = step_data.get("step_id")
                    step_item = QStandardItem(step_data.get("name", "未命名步骤"))
                    step_item.setData("step", ITEM_TYPE_ROLE)
                    step_item.setData(step_id, ITEM_ID_ROLE)
                    step_item.setData({"wf_id": wf_id, "node_id": node_id}, ITEM_PARENT_IDS_ROLE)
                    node_item.appendRow(step_item)
                    if step_id == selected_id:
                        item_to_reselect = step_item

        self.tree_view.expandAll()
        if item_to_reselect:
            index = self.tree_model.indexFromItem(item_to_reselect)
            self.tree_view.setCurrentIndex(index)

    def _get_selected_item_info(self):
        """获取当前选中项的类型、ID和父ID"""
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return None, None, None

        index = indexes[0]
        item = self.tree_model.itemFromIndex(index)
        if not item:  # Can happen if tree is being repopulated
            return None, None, None

        return item.data(ITEM_TYPE_ROLE), item.data(ITEM_ID_ROLE), item.data(ITEM_PARENT_IDS_ROLE)

    def _on_selection_changed(self):
        """当树中选择变化时，更新UI状态和详情面板"""
        self._update_ui_state()
        self._update_details_panel()

    def _update_ui_state(self):
        """根据当前选择更新按钮等控件的状态"""
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
        """根据选择更新右侧的详情显示"""
        item_type, item_id, parent_ids = self._get_selected_item_info()

        if not item_type or not item_id:
            self.stacked_widget.setCurrentIndex(0)
            return

        data = None
        if item_type == "workflow":
            data = self.manager.get_workflow(item_id)
            if data:
                self.wf_name_edit.setText(data.get("name", ""))
                self.wf_desc_edit.setText(data.get("description", ""))
                self.stacked_widget.setCurrentIndex(1)

        elif item_type == "node":
            wf_data = self.manager.get_workflow(parent_ids["wf_id"])
            if wf_data: data = wf_data.get('nodes', {}).get(item_id)
            if data:
                self.node_name_edit.setText(data.get("name", ""))
                self.node_loop_check.setChecked(data.get("loop", False))
                self.stacked_widget.setCurrentIndex(2)

        elif item_type == "step":
            wf_data = self.manager.get_workflow(parent_ids["wf_id"])
            if wf_data:
                node_data = wf_data.get('nodes', {}).get(parent_ids["node_id"])
                if node_data:
                    data = next((s for s in node_data.get('steps', []) if s.get('step_id') == item_id), None)
            if data:
                self.step_name_edit.setText(data.get("name", ""))
                self.step_prompt_edit.setText(data.get("prompt", ""))
                self.step_provider_edit.setText(data.get("provider", ""))
                self.step_model_edit.setText(data.get("model", ""))
                self.step_read_file_edit.setText(data.get("read_from_file") or "")
                self.step_save_file_edit.setText(data.get("save_to_file") or "")
                self.step_use_context_check.setChecked(data.get("use_context", False))
                self.step_output_console_check.setChecked(data.get("output_to_console", False))
                self.stacked_widget.setCurrentIndex(3)

        if not data:
            self.stacked_widget.setCurrentIndex(0)

    def _add_item(self):
        item_type, item_id, _ = self._get_selected_item_info()
        if item_type == "workflow":
            name, ok = QInputDialog.getText(self, "添加节点", "节点名称:")
            if ok and name: self.manager.add_node(item_id, name)
        elif item_type == "node":
            _, _, parent_ids = self._get_selected_item_info()
            name, ok = QInputDialog.getText(self, "添加流节点", "流节点(Step)名称:")
            if ok and name: self.manager.add_step(parent_ids["wf_id"], item_id, {"name": name})
        else:
            name, ok = QInputDialog.getText(self, "添加流程", "流程名称:")
            if ok and name: self.manager.create_workflow(name)
        self._populate_tree()

    def _delete_item(self):
        item_type, item_id, parent_ids = self._get_selected_item_info()
        if not item_type: return

        reply = QMessageBox.question(self, "确认删除", f"确定要删除选中的 '{item_type}' 吗？\n此操作不可撤销！",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
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
        if not item_type == item_to_save: return

        if item_type == "workflow":
            self.manager.edit_workflow(item_id, name=self.wf_name_edit.text(),
                                       description=self.wf_desc_edit.toPlainText())
        elif item_type == "node":
            self.manager.edit_node(parent_ids["wf_id"], item_id, name=self.node_name_edit.text(),
                                   loop=self.node_loop_check.isChecked())
        elif item_type == "step":
            updates = {
                "name": self.step_name_edit.text(),
                "prompt": self.step_prompt_edit.toPlainText(),
                "provider": self.step_provider_edit.text(),
                "model": self.step_model_edit.text(),
                "read_from_file": self.step_read_file_edit.text() or None,
                "save_to_file": self.step_save_file_edit.text() or None,
                "use_context": self.step_use_context_check.isChecked(),
                "output_to_console": self.step_output_console_check.isChecked()
            }
            self.manager.edit_step(parent_ids["wf_id"], parent_ids["node_id"], item_id, updates)

        self.send_log.emit(f"更新了 {item_type}: {item_id} 的信息")
        self._populate_tree()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 一个简单的暗色主题
    app.setStyleSheet("""
        QWidget { font-size: 14px; background-color: #2d2d2d; color: #f0f0f0; }
        QTreeView, QLineEdit, QTextEdit { background-color: #252525; border: 1px solid #444; }
        QTreeView::item:selected { background-color: #0078d7; }
        QPushButton { padding: 8px; background-color: #0078d7; border: none; border-radius: 4px; }
        QPushButton:hover { background-color: #0088f0; }
        QLabel { border: none; }
        QSplitter::handle { background-color: #444; }
    """)

    main_window = QMainWindow()
    flow_manager_widget = HierarchicalFlowManagerUI()
    flow_manager_widget.send_log.connect(lambda msg: print(f"UI_LOG: {msg}"))

    main_window.setCentralWidget(flow_manager_widget)
    main_window.setGeometry(100, 100, 1200, 800)
    main_window.setWindowTitle("模块化流程管理器")
    main_window.show()

    sys.exit(app.exec())
