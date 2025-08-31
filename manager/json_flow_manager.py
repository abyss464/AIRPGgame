import json
import uuid
import os
from typing import Dict, Any, List, Optional


class JsonWorkflowManager:
    """
    一个用于管理、创建、编辑和删除多层级工作流程的类。
    所有数据都存储在一个JSON文件中。

    结构:
    - Workflows (流程)
      - Nodes (节点), 节点层面可设置是否循环
        - Steps (流节点/AI对话)
    """

    def __init__(self, file_path: str):
        """
        初始化管理器。

        :param file_path: 用于存储工作流程的JSON文件路径。
        """
        self.file_path = file_path
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """从JSON文件加载数据。如果文件不存在，则返回一个空字典。"""
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_data(self) -> None:
        """将当前数据保存到JSON文件。"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def _generate_id() -> str:
        """生成一个唯一的ID。"""
        return str(uuid.uuid4())

    # --- 流程 (Workflow) 管理 ---

    def create_workflow(self, name: str, description: str = "") -> str:
        """
        创建一个新的流程。

        :param name: 流程名称。
        :param description: 流程描述。
        :return: 新创建的流程的ID。
        """
        workflow_id = self._generate_id()
        self.data[workflow_id] = {
            "name": name,
            "description": description,
            "nodes": {}
        }
        self._save_data()
        print(f"流程 '{name}' (ID: {workflow_id}) 已创建。")
        return workflow_id

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        根据ID删除一个流程。

        :param workflow_id: 要删除的流程ID。
        :return: 如果成功删除则返回 True，否则返回 False。
        """
        if workflow_id in self.data:
            del self.data[workflow_id]
            self._save_data()
            print(f"流程 ID: {workflow_id} 已删除。")
            return True
        print(f"错误: 未找到流程 ID: {workflow_id}。")
        return False

    def edit_workflow(self, workflow_id: str, name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """
        编辑一个已存在的流程。

        :param workflow_id: 要编辑的流程ID。
        :param name: 新的流程名称 (可选)。
        :param description: 新的流程描述 (可选)。
        :return: 如果成功编辑则返回 True，否则返回 False。
        """
        if workflow_id in self.data:
            if name is not None:
                self.data[workflow_id]['name'] = name
            if description is not None:
                self.data[workflow_id]['description'] = description
            self._save_data()
            print(f"流程 ID: {workflow_id} 已更新。")
            return True
        print(f"错误: 未找到流程 ID: {workflow_id}。")
        return False

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取单个流程的详细信息。"""
        return self.data.get(workflow_id)

    def list_workflows(self) -> List[Dict[str, str]]:
        """列出所有流程的基本信息（ID和名称）。"""
        return [{"id": wf_id, "name": wf.get("name")} for wf_id, wf in self.data.items()]

    # --- 节点 (Node) 管理 ---

    def add_node(self, workflow_id: str, node_name: str, loop: bool = False) -> Optional[str]:
        """
        向指定流程中添加一个新节点。

        :param workflow_id: 流程ID。
        :param node_name: 新节点的名称。
        :param loop: 节点是否循环执行。
        :return: 新节点的ID，如果流程不存在则返回 None。
        """
        if workflow_id not in self.data:
            print(f"错误: 未找到流程 ID: {workflow_id}。")
            return None

        node_id = self._generate_id()
        self.data[workflow_id]['nodes'][node_id] = {
            "name": node_name,
            "loop": loop,  # 在节点层面添加循环属性
            "steps": []
        }
        self._save_data()
        print(f"在流程 {workflow_id} 中添加了节点 '{node_name}' (ID: {node_id}), 循环: {loop}。")
        return node_id

    def delete_node(self, workflow_id: str, node_id: str) -> bool:
        """从流程中删除一个节点。"""
        if workflow_id in self.data and node_id in self.data[workflow_id]['nodes']:
            del self.data[workflow_id]['nodes'][node_id]
            self._save_data()
            print(f"节点 ID: {node_id} 已从流程 {workflow_id} 中删除。")
            return True
        print(f"错误: 未找到流程 {workflow_id} 或节点 {node_id}。")
        return False

    def edit_node(self, workflow_id: str, node_id: str, name: Optional[str] = None,
                  loop: Optional[bool] = None) -> bool:
        """
        编辑一个节点的属性（名称、是否循环）。

        :param workflow_id: 流程ID。
        :param node_id: 节点ID。
        :param name: 新的节点名称 (可选)。
        :param loop: 新的循环设置 (可选)。
        :return: 如果成功编辑则返回 True，否则返回 False。
        """
        if workflow_id in self.data and node_id in self.data[workflow_id]['nodes']:
            node = self.data[workflow_id]['nodes'][node_id]
            updated = False
            if name is not None:
                node['name'] = name
                updated = True
            if loop is not None:
                node['loop'] = loop
                updated = True

            if updated:
                self._save_data()
                print(f"节点 ID: {node_id} 已更新。")
                return True
            return False  # 没有提供更新项

        print(f"错误: 未找到流程 {workflow_id} 或节点 {node_id}。")
        return False

    # --- 流节点 (Step) 管理 ---

    def add_step(self, workflow_id: str, node_id: str, step_details: Dict[str, Any]) -> Optional[str]:
        """
        向指定节点中添加一个新步骤 (AI对话)。

        :param workflow_id: 流程ID。
        :param node_id: 节点ID。
        :param step_details: 包含步骤所有配置的字典。
        :return: 新步骤的ID，如果流程或节点不存在则返回 None。
        """
        if workflow_id not in self.data or node_id not in self.data[workflow_id]['nodes']:
            print(f"错误: 未找到流程 {workflow_id} 或节点 {node_id}。")
            return None

        step_id = self._generate_id()

        # 默认模板中已移除 loop 字段
        new_step = {
            "step_id": step_id,
            "name": "新AI对话步骤",
            "prompt": "",
            "input_value": "",
            "use_context": True,
            "provider": "default",
            "model": "default",
            "read_from_file": None,
            "save_to_file": None,
            "output_to_console": False
        }
        new_step.update(step_details)

        self.data[workflow_id]['nodes'][node_id]['steps'].append(new_step)
        self._save_data()
        print(f"在节点 {node_id} 中添加了步骤 '{new_step['name']}' (ID: {step_id})。")
        return step_id

    def delete_step(self, workflow_id: str, node_id: str, step_id: str) -> bool:
        """从节点中删除一个步骤。"""
        if workflow_id not in self.data or node_id not in self.data[workflow_id]['nodes']:
            print(f"错误: 未找到流程 {workflow_id} 或节点 {node_id}。")
            return False

        steps = self.data[workflow_id]['nodes'][node_id]['steps']
        original_len = len(steps)
        self.data[workflow_id]['nodes'][node_id]['steps'] = [s for s in steps if s.get('step_id') != step_id]

        if len(self.data[workflow_id]['nodes'][node_id]['steps']) < original_len:
            self._save_data()
            print(f"步骤 ID: {step_id} 已从节点 {node_id} 中删除。")
            return True

        print(f"错误: 在节点 {node_id} 中未找到步骤 ID: {step_id}。")
        return False

    def edit_step(self, workflow_id: str, node_id: str, step_id: str, updates: Dict[str, Any]) -> bool:
        """
        编辑一个已存在的步骤。

        :param workflow_id: 流程ID。
        :param node_id: 节点ID。
        :param step_id: 要编辑的步骤ID。
        :param updates: 包含要更新的字段和新值的字典。
        :return: 如果成功编辑则返回 True，否则返回 False。
        """
        if workflow_id not in self.data or node_id not in self.data[workflow_id]['nodes']:
            print(f"错误: 未找到流程 {workflow_id} 或节点 {node_id}。")
            return False

        steps = self.data[workflow_id]['nodes'][node_id]['steps']
        for step in steps:
            if step.get('step_id') == step_id:
                step.update(updates)
                self._save_data()
                print(f"步骤 ID: {step_id} 已更新。")
                return True

        print(f"错误: 在节点 {node_id} 中未找到步骤 ID: {step_id}。")
        return False
