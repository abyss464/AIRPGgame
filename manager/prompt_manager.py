# prompt_manager.py

import json
import os
from typing import List, Dict, Optional, Literal

# 定义合法的提示词类型，使用 Literal 类型注解可以获得 IDE 的智能提示和静态检查
PromptType = Literal["goal", "core_content", "prohibitions", "response_structure"]
PROMPT_TYPES: List[PromptType] = ["goal", "core_content", "prohibitions", "response_structure"]


class PromptManager:
    """
    一个用于创建、管理和存储系统提示词的类。
    所有提示词都将持久化到一个 JSON 文件中。
    """

    def __init__(self, file_path: str = "prompts.json"):
        """
        初始化提示词管理器。

        Args:
            file_path (str): 用于存储提示词的 JSON 文件的路径。
        """
        self.file_path = file_path
        # 使用字典来存储提示词，键为提示词的唯一名称
        self.prompts: Dict[str, Dict] = {}
        self.load_prompts()

    def load_prompts(self) -> bool:
        """
        从 JSON 文件加载提示词到内存中。
        如果文件不存在，则会静默失败，等待第一次保存时创建。

        Returns:
            bool: 如果加载成功返回 True，否则返回 False。
        """
        if not os.path.exists(self.file_path):
            return False
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.prompts = json.load(f)
            return True
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading prompts file: {e}")
            return False

    def save_prompts(self) -> bool:
        """
        将内存中的所有提示词保存到 JSON 文件中。

        Returns:
            bool: 如果保存成功返回 True，否则返回 False。
        """
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, ensure_ascii=False, indent=4)
            return True
        except IOError as e:
            print(f"Error saving prompts file: {e}")
            return False

    def add_prompt(self, name: str, prompt_type: PromptType, content: str, description: str = "") -> bool:
        """
        添加一个新的提示词。如果同名提示词已存在，它将被覆盖。

        Args:
            name (str): 提示词的唯一名称 (例如, 'fantasy_gm_base')。
            prompt_type (PromptType): 提示词的类型 ('goal', 'core_content', 'prohibitions', 'response_structure')。
            content (str): 提示词的具体文本内容。
            description (str, optional): 对该提示词的简短描述。默认为 ""。

        Returns:
            bool: 如果添加成功返回 True，否则返回 False。
        """
        if prompt_type not in PROMPT_TYPES:
            print(f"Error: Invalid prompt type '{prompt_type}'. Must be one of {PROMPT_TYPES}")
            return False

        self.prompts[name] = {
            "type": prompt_type,
            "content": content,
            "description": description
        }
        return True

    def delete_prompt(self, name: str) -> bool:
        """
        根据名称删除一个提示词。

        Args:
            name (str): 要删除的提示词的名称。

        Returns:
            bool: 如果删除成功返回 True，如果提示词不存在则返回 False。
        """
        if name in self.prompts:
            del self.prompts[name]
            return True
        return False

    def update_prompt_attribute(self, name: str, attribute: str, value: str) -> bool:
        """
        更新一个已存在提示词的单个属性（例如 'content' 或 'type'）。

        Args:
            name (str): 要更新的提示词的名称。
            attribute (str): 要更新的属性 ('type', 'content', 'description')。
            value (str): 新的属性值。

        Returns:
            bool: 如果更新成功返回 True，否则返回 False。
        """
        if name not in self.prompts:
            print(f"Error: Prompt '{name}' not found.")
            return False

        if attribute == "type" and value not in PROMPT_TYPES:
            print(f"Error: Invalid prompt type '{value}'.")
            return False

        if attribute not in ["type", "content", "description"]:
            print(f"Error: Invalid attribute '{attribute}'.")
            return False

        self.prompts[name][attribute] = value
        return True

    def get_prompt(self, name: str) -> Optional[Dict]:
        """
        根据名称获取一个提示词的详细信息。

        Args:
            name (str): 提示词的名称。

        Returns:
            Optional[Dict]: 如果找到则返回提示词的字典，否则返回 None。
        """
        return self.prompts.get(name)

    def list_prompts(self) -> List[str]:
        """
        获取所有已存储提示词的名称列表。

        Returns:
            List[str]: 所有提示词名称的列表。
        """
        return list(self.prompts.keys())

    def get_prompts_by_type(self, prompt_type: PromptType) -> Dict[str, Dict]:
        """
        获取特定类型的所有提示词。

        Args:
            prompt_type (PromptType): 要筛选的提示词类型。

        Returns:
            Dict[str, Dict]: 包含所有匹配类型提示词的字典。
        """
        if prompt_type not in PROMPT_TYPES:
            return {}
        return {
            name: data for name, data in self.prompts.items()
            if data.get("type") == prompt_type
        }
