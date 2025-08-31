import json
import os
from typing import List, Dict, Any, Optional

import requests


class ModelConfigManager:
    """
    管理多个模型API服务商配置的类。
    支持增、删、改、查，以及动态获取模型列表。
    """

    def __init__(self, config_path: str = 'models_config.json'):
        """
        初始化配置管理器。

        Args:
            config_path (str): 配置文件的路径。
        """
        self.config_path = config_path
        self.config = self._load()

    def _load(self) -> Dict[str, List[Dict[str, Any]]]:
        """从文件加载配置，若文件不存在则创建空结构。"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"providers": []}

    def _save(self):
        """将当前配置保存到文件。"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        print(f"配置已更新并保存到 '{self.config_path}'。")

    def _find_provider_index(self, name: str) -> Optional[int]:
        """根据名称查找服务商的索引，方便内部操作。"""
        for i, provider in enumerate(self.config['providers']):
            if provider.get('name') == name:
                return i
        return None

    def add_provider(self,
                     name: str,
                     api_key: str,
                     base_url: str,
                     default_model: str,
                     provider_type: str = 'openai',
                     other_params: Optional[Dict[str, Any]] = None) -> bool:
        """
        增加一个新的服务商配置。名称不可重复。

        Args:
            name (str): 唯一服务商名称标识。
            api_key (str): API密钥，将直接存储。
            base_url (str): API基础URL。
            default_model (str): 默认使用的模型。
            provider_type (str, optional): 服务商类型。默认为 'openai'。
            other_params (dict, optional): 其他自定义参数。

        Returns:
            bool: 成功添加返回 True，名称已存在则返回 False。
        """
        if self._find_provider_index(name) is not None:
            print(f"错误: 名为 '{name}' 的服务商已存在，无法添加。")
            return False

        new_provider = {
            "name": name,
            "provider_type": provider_type,
            "api_key": api_key,
            "base_url": base_url,
            "default_model": default_model,
            "available_models": [],  # 初始为空，待获取
            "other_params": other_params if other_params else {}
        }
        self.config['providers'].append(new_provider)
        self._save()
        return True

    def remove_provider(self, name: str) -> bool:
        """
        根据名称删除一个服务商配置。

        Args:
            name (str): 要删除的服务商名称。

        Returns:
            bool: 成功删除返回 True，服务商不存在返回 False。
        """
        index = self._find_provider_index(name)
        if index is None:
            print(f"错误: 找不到名为 '{name}' 的服务商。")
            return False

        self.config['providers'].pop(index)
        self._save()
        return True

    def list_providers(self) -> List[str]:
        """列出所有已配置的服务商名称。"""
        return [p['name'] for p in self.config['providers']]

    def get_provider(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定服务商的完整配置信息。"""
        index = self._find_provider_index(name)
        if index is not None:
            return self.config['providers'][index]
        return None

    def update_provider(self, name: str, **kwargs) -> bool:
        """
        修改指定服务商的单个或多个参数。

        Args:
            name (str): 要修改的服务商名称。
            **kwargs: 要更新的键值对，例如 `api_key="new_key"`, `default_model="gpt-4o"`。

        Returns:
            bool: 成功更新返回 True，服务商不存在返回 False。
        """
        index = self._find_provider_index(name)
        if index is None:
            print(f"错误: 找不到名为 '{name}' 的服务商，无法更新。")
            return False

        # 验证传入的参数是否是合法的字段
        valid_keys = {"name", "provider_type", "api_key", "base_url",
                      "default_model", "available_models", "other_params"}

        for key, value in kwargs.items():
            if key not in valid_keys:
                print(f"警告: 忽略无效参数 '{key}'。")
                continue
            if key == "name" and self._find_provider_index(value) is not None:
                print(f"错误: 新名称 '{value}' 已存在，无法更新。")
                return False
            self.config['providers'][index][key] = value

        self._save()
        return True

    def fetch_and_update_models(self, name: str) -> Optional[List[str]]:
        """
        从服务商地址获取所有模型并存入列表。
        此函数假设服务商提供一个与OpenAI兼容的 `/v1/models` 端点。

        Args:
            name (str): 服务商名称。

        Returns:
            Optional[List[str]]: 成功时返回获取到的模型名称列表，失败返回 None。
        """
        index = self._find_provider_index(name)
        if index is None:
            print(f"错误: 找不到名为 '{name}' 的服务商。")
            return None

        provider = self.config['providers'][index]
        base_url = provider['base_url'].rstrip('/')
        api_key = provider['api_key']
        models_url = f"{base_url}/models"

        headers = {"Authorization": f"Bearer {api_key}"}

        print(f"正在从 {models_url} 获取模型列表...")
        try:
            response = requests.get(models_url, headers=headers, timeout=10)
            response.raise_for_status()  # 如果状态码不是 2xx，则抛出异常

            data = response.json()
            model_ids = sorted([model['id'] for model in data.get('data', [])])

            self.config['providers'][index]['available_models'] = model_ids
            self._save()
            print(f"成功为 '{name}' 获取了 {len(model_ids)} 个模型。")
            return model_ids

        except requests.exceptions.RequestException as e:
            print(f"错误: 获取模型列表失败。原因: {e}")
            return None

    def list_available_models(self, name: str) -> Optional[List[str]]:
        """
        列出指定服务商所有已存储的可用模型。

        Args:
            name (str): 服务商名称。

        Returns:
            Optional[List[str]]: 模型列表，如果服务商不存在则返回 None。
        """
        provider = self.get_provider(name)
        if provider:
            return provider.get('available_models', [])
        print(f"错误: 找不到名为 '{name}' 的服务商。")
        return None

    def get_request_params(self, name: str, model_override: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取指定服务商实际使用时所需的参数字典。

        Args:
            name (str): 服务商名称。
            model_override (str, optional): 如果提供，将覆盖该服务商的默认模型。

        Returns:
            Optional[Dict[str, Any]]: 可直接用于API客户端的参数字典，服务商不存在则返回 None。
        """
        provider = self.get_provider(name)
        if not provider:
            print(f"错误: 找不到名为 '{name}' 的服务商。")
            return None

        # 基础参数
        params = {
            "api_key": provider.get('api_key'),
            "base_url": provider.get('base_url'),
            "model": model_override or provider.get('default_model')
        }

        # 合并其他自定义参数
        params.update(provider.get('other_params', {}))

        return params

