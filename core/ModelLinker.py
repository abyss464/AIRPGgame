from openai import OpenAI, APIError, APIConnectionError
from typing import List, Dict, Any, Optional

# 导入我们之前写的配置管理器
from manager.model_config_manager import ModelConfigManager


class ModelLinker:
    """
    一个高层封装，用于简化与大语言模型的对话补全交互。
    它可以直接使用完整的API参数，或通过ModelConfigManager指定的服务商名称进行调用。
    """

    def __init__(self, config_manager: ModelConfigManager):
        """
        初始化ModelLinker。

        Args:
            config_manager (ModelConfigManager): 一个ModelConfigManager的实例。
        """
        if not isinstance(config_manager, ModelConfigManager):
            raise TypeError("config_manager 必须是 ModelConfigManager 的一个实例。")
        self.manager = config_manager

    def create_completion(self,
                          messages: List[Dict[str, str]],
                          provider_name: Optional[str] = None,
                          model: Optional[str] = None,
                          **kwargs: Any) -> Optional[str]:
        """
        执行一次对话补全。

        可以通过两种方式调用：
        1. 托管模式: 提供 `provider_name`，将从配置中加载参数。
           - `model` (可选): 如果提供，将覆盖该服务商的默认模型。
           - `**kwargs` (可选): 其他API参数 (如 temperature, max_tokens) 将覆盖配置中的默认值。

        2. 直接模式: 不提供 `provider_name`，但必须在 `**kwargs` 中提供 `api_key`, `base_url` 和 `model`。

        Args:
            messages (List[Dict[str, str]]): 对话消息列表，遵循OpenAI格式。
            provider_name (Optional[str]): 要使用的服务商名称。
            model (Optional[str]): 要使用的模型名称。
            **kwargs (Any): 其他传递给OpenAI API的参数。

        Returns:
            Optional[str]: 模型生成的回复内容，如果出错则返回None。
        """
        client_config = {}
        api_params = {}

        if provider_name:
            # --- 托管模式 ---
            print(f"正在使用托管模式，服务商: '{provider_name}'")
            provider_params = self.manager.get_request_params(provider_name, model_override=model)

            if not provider_params:
                print(f"错误: 无法获取服务商 '{provider_name}' 的配置。")
                return None

            # 提取客户端配置和API参数
            client_config['api_key'] = provider_params.pop('api_key', None)
            client_config['base_url'] = provider_params.pop('base_url', None)

            # 合并参数：kwargs中的参数优先级更高
            api_params = {**provider_params, **kwargs}
        else:
            # --- 直接模式 ---
            print("正在使用直接模式。")
            if not all(k in kwargs for k in ['api_key', 'base_url', 'model']):
                print("错误: 在直接模式下，kwargs中必须提供 'api_key', 'base_url' 和 'model'。")
                return None

            client_config['api_key'] = kwargs.pop('api_key')
            client_config['base_url'] = kwargs.pop('base_url')
            api_params = kwargs

        # 确保 final_model 存在
        final_model = api_params.get('model')
        if not final_model:
            print("错误: 最终未能确定要使用的模型。")
            return None

        print(f"将要使用的模型: {final_model}")
        print(f"API Base URL: {client_config['base_url']}")

        try:
            # 初始化OpenAI客户端
            client = OpenAI(
                api_key=client_config['api_key'],
                base_url=client_config['base_url']
            )

            # 发起API请求
            response = client.chat.completions.create(
                messages=messages,
                **api_params
            )

            # 提取并返回结果
            content = response.choices[0].message.content
            return content.strip() if content else ""

        except APIConnectionError as e:
            print(f"API连接错误: 无法连接到 {client_config['base_url']}. 请检查地址和网络。")
            print(f"详细信息: {e.__cause__}")
            return None
        except APIError as e:
            print(f"API返回错误: {e.status_code} - {e.message}")
            return None
        except Exception as e:
            print(f"发生未知错误: {e}")
            return None

