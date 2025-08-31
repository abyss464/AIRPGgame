# context_builder.py

from typing import List, Dict, Optional
from manager.prompt_manager import PromptManager, PromptType

# 定义各类提示词在最终输出中的标题
TYPE_HEADERS: Dict[PromptType, str] = {
    "goal": "### 核心规则 ###",
    "core_content": "### 核心内容与世界观 (Core Content & Worldview) ###",
    "prohibitions": "### 禁止事项 (Prohibitions) ###",
    "response_structure": "### 回复结构 (Response Structure) ###"
}

# 定义默认的组合顺序
DEFAULT_CONSTRUCTION_ORDER: List[PromptType] = ["goal", "core_content", "prohibitions", "response_structure"]


class ContextBuilder:
    """
    根据用户的选择，从 PromptManager 动态构造一个完整的系统提示词。
    """

    def __init__(self, prompt_manager: PromptManager):
        """
        初始化提示词构造器。

        Args:
            prompt_manager (PromptManager): 一个 PromptManager 的实例，用于获取提示词数据。
        """
        if not isinstance(prompt_manager, PromptManager):
            raise TypeError("prompt_manager must be an instance of PromptManager")
        self.prompt_manager = prompt_manager

    def build(self, prompt_names: List[str], custom_order: Optional[List[PromptType]] = None) -> str:
        """
        根据给定的提示词名称列表，构建一个格式化的系统提示词字符串。

        Args:
            prompt_names (List[str]): 一个包含要使用的提示词名称的列表。
            custom_order (Optional[List[PromptType]], optional):
                一个可选的列表，用于指定提示词类型的组合顺序。
                如果为 None，则使用默认顺序。默认为 None。

        Returns:
            str: 组合并格式化后的完整系统提示词。
        """
        # 1. 确定组合顺序
        order = custom_order if custom_order else DEFAULT_CONSTRUCTION_ORDER

        # 2. 获取所有需要的提示词数据
        selected_prompts_data: Dict[str, Dict] = {}
        for name in prompt_names:
            prompt_data = self.prompt_manager.get_prompt(name)
            if prompt_data:
                selected_prompts_data[name] = prompt_data
            else:
                print(f"Warning: Prompt '{name}' not found in PromptManager and will be ignored.")

        # 3. 按顺序分类和组合提示词
        final_prompt_parts = []
        for prompt_type in order:
            # 找到所有属于当前类型的提示词内容
            contents_for_type = [
                data["content"] for data in selected_prompts_data.values()
                if data.get("type") == prompt_type
            ]

            # 如果该类型下有内容，则添加标题和内容
            if contents_for_type:
                # 添加标题
                header = TYPE_HEADERS.get(prompt_type, f"### {prompt_type.capitalize()} ###")
                final_prompt_parts.append(header)
                # 添加该类型下的所有提示词内容，用换行符连接
                final_prompt_parts.append("\n".join(f"- {item}" for item in contents_for_type))

        # 4. 将所有部分组合成最终的字符串
        return "\n\n".join(final_prompt_parts)

