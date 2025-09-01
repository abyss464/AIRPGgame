import json
import os
from typing import List, Dict, Any, Optional

import requests


class ModelConfigManager:
    """
    管理多个模型API服务商配置的类。
    支持增、删、改、查，设置默认服务商，以及动态获取模型列表。
    """

    def __init__(self, config_path: str = 'models_config.json'):
        """
        初始化配置管理器。

        Args:
            config_path (str): 配置文件的路径。
        """
        self.config_path = config_path
        self.config = self._load()

    def _load(self) -> Dict[str, Any]:
        """从文件加载配置，若文件不存在则创建空结构。"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                # 兼容旧的配置文件，确保新键存在
                if 'providers' not in config_data:
                    config_data['providers'] = []
                if 'default_provider_name' not in config_data:
                    config_data['default_provider_name'] = None
                return config_data
        except (FileNotFoundError, json.JSONDecodeError):
            # 初始化新的配置结构
            return {"default_provider_name": None, "providers": []}

    def _save(self):
        """将当前配置保存到文件。"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        print(f"配置已更新并保存到 '{self.config_path}'。")

    def _get_name_or_default(self, name: Optional[str]) -> Optional[str]:
        """内部辅助函数：如果 name 为 None，则返回默认服务商名称。"""
        if name is not None:
            return name

        default_name = self.get_default_provider_name()
        if default_name is None:
            print("错误: 未提供服务商名称，且没有设置默认服务商。")
            return None
        return default_name

    def _find_provider_index(self, name: str) -> Optional[int]:
        """根据名称查找服务商的索引，方便内部操作。"""
        for i, provider in enumerate(self.config.get('providers', [])):
            if provider.get('name') == name:
                return i
        return None

    # --- 新增和修改的核心功能 ---

    def set_default_provider(self, name: str) -> bool:
        """
        设置一个默认的服务商。

        Args:
            name (str): 要设置为默认的服务商的名称。

        Returns:
            bool: 成功设置返回 True，服务商不存在返回 False。
        """
        if self._find_provider_index(name) is None:
            print(f"错误: 找不到名为 '{name}' 的服务商，无法设置为默认。")
            return False

        self.config['default_provider_name'] = name
        self._save()
        print(f"已将 '{name}' 设置为默认服务商。")
        return True

    def get_default_provider_name(self) -> Optional[str]:
        """获取默认服务商的名称。"""
        return self.config.get('default_provider_name')

    def get_default_provider_model(self) -> Optional[str]:
        return self.get_default_model()


    def get_default_provider(self) -> Optional[Dict[str, Any]]:
        """获取默认服务商的完整配置信息。"""
        default_name = self.get_default_provider_name()
        if default_name:
            return self.get_provider(default_name)
        return None

    def remove_provider(self, name: str) -> bool:
        """
        根据名称删除一个服务商配置。
        如果被删除的是默认服务商，则会清除默认设置。

        Args:
            name (str): 要删除的服务商名称。

        Returns:
            bool: 成功删除返回 True，服务商不存在返回 False。
        """
        index = self._find_provider_index(name)
        if index is None:
            print(f"错误: 找不到名为 '{name}' 的服务商。")
            return False

        # 检查是否为默认服务商，如果是则清除
        if self.config.get('default_provider_name') == name:
            self.config['default_provider_name'] = None
            print(f"'{name}' 是默认服务商，已将其移除，现在没有默认服务商。")

        self.config['providers'].pop(index)
        self._save()
        return True

    # --- 对已有方法进行增强 ---

    def get_provider(self, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取指定服务商的完整配置信息。
        如果 name 为 None，则返回默认服务商的配置。
        """
        name_to_use = self._get_name_or_default(name)
        if name_to_use is None:
            return None

        index = self._find_provider_index(name_to_use)
        if index is not None:
            return self.config['providers'][index]
        print(f"错误: 找不到名为 '{name_to_use}' 的服务商。")
        return None

    def fetch_and_update_models(self, name: Optional[str] = None) -> Optional[List[str]]:
        """
        从服务商地址获取所有模型并存入列表。
        如果 name 为 None，则操作默认服务商。

        Args:
            name (str, optional): 服务商名称。如果为None，则使用默认服务商。

        Returns:
            Optional[List[str]]: 成功时返回获取到的模型名称列表，失败返回 None。
        """
        name_to_use = self._get_name_or_default(name)
        if name_to_use is None:
            return None

        index = self._find_provider_index(name_to_use)
        # 这里 index 不可能为 None，因为 _get_name_or_default 保证了名称存在
        # 但为保险起见可以加一个检查
        if index is None:
            print(f"错误: 找不到名为 '{name_to_use}' 的服务商。")
            return None

        provider = self.config['providers'][index]
        base_url = provider['base_url'].rstrip('/')
        api_key = provider['api_key']
        models_url = f"{base_url}/models"

        headers = {"Authorization": f"Bearer {api_key}"}

        print(f"正在从 {models_url} (服务商: {name_to_use}) 获取模型列表...")
        try:
            response = requests.get(models_url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            model_ids = sorted([model['id'] for model in data.get('data', [])])

            self.config['providers'][index]['available_models'] = model_ids
            self._save()
            print(f"成功为 '{name_to_use}' 获取了 {len(model_ids)} 个模型。")
            return model_ids

        except requests.exceptions.RequestException as e:
            print(f"错误: 获取模型列表失败。原因: {e}")
            return None

    def list_available_models(self, name: Optional[str] = None) -> Optional[List[str]]:
        """
        列出指定服务商所有已存储的可用模型。
        如果 name 为 None，则列出默认服务商的模型。
        """
        provider = self.get_provider(name)  # get_provider 已经支持默认
        if provider:
            return provider.get('available_models', [])
        # 如果 provider 不存在，get_provider 会打印错误信息
        return None

    def get_request_params(self, name: Optional[str] = None, model_override: Optional[str] = None) -> Optional[
        Dict[str, Any]]:
        """
        获取指定服务商实际使用时所需的参数字典。
        如果 name 为 None，则获取默认服务商的参数。
        """
        provider = self.get_provider(name)  # get_provider 已经支持默认
        if not provider:
            return None

        params = {
            "api_key": provider.get('api_key'),
            "base_url": provider.get('base_url'),
            "model": model_override or provider.get('default_model')
        }
        params.update(provider.get('other_params', {}))
        return params

    def get_default_model(self, name: Optional[str] = None) -> Optional[str]:
        """
        获取指定服务商的默认模型名称。
        如果 name 为 None，则获取【默认服务商】的默认模型。

        Args:
            name (str, optional): 服务商名称。如果为None，则使用默认服务商。

        Returns:
            Optional[str]: 成功时返回默认模型名称，失败则返回 None。
        """
        # 复用 get_provider 的逻辑，它已经完美处理了 name 为 None 的情况
        provider = self.get_provider(name)

        if provider:
            # 使用 .get() 方法更安全，以防 'default_model' 键不存在
            return provider.get('default_model')

        # 如果找不到服务商，get_provider 会打印错误信息，这里直接返回 None 即可
        return None

    def add_provider(self, name: str, api_key: str, base_url: str, default_model: str, provider_type: str = 'openai',
                     other_params: Optional[Dict[str, Any]] = None) -> bool:
        if self._find_provider_index(name) is not None:
            print(f"错误: 名为 '{name}' 的服务商已存在，无法添加。")
            return False

        new_provider = {"name": name, "provider_type": provider_type, "api_key": api_key, "base_url": base_url,
                        "default_model": default_model, "available_models": [],
                        "other_params": other_params if other_params else {}}
        self.config['providers'].append(new_provider)
        self._save()
        return True

    def list_providers(self) -> List[str]:
        return [p['name'] for p in self.config['providers']]

    def update_provider(self, name: str, **kwargs) -> bool:
        index = self._find_provider_index(name)
        if index is None:
            print(f"错误: 找不到名为 '{name}' 的服务商，无法更新。")
            return False

        valid_keys = {"name", "provider_type", "api_key", "base_url", "default_model", "available_models",
                      "other_params"}
        for key, value in kwargs.items():
            if key not in valid_keys:
                print(f"警告: 忽略无效参数 '{key}'。")
                continue
            if key == "name" and value != name and self._find_provider_index(value) is not None:
                print(f"错误: 新名称 '{value}' 已存在，无法更新。")
                return False
            self.config['providers'][index][key] = value

        self._save()
        return True

