from ai_toolkit.models.openai_model import OpenAIModel
from ai_toolkit.models.chatglm_model import ChatGlmModel


class AIManager:
    """
    AIManager类负责管理和调用不同的AI模型。
    它提供chat和generate_image两个统一的接口，隐藏了不同模型实现的差异。
    """

    def __init__(self):
        """
        初始化AIManager，创建一个空字典用于存储模型实例。
        """
        self.models = {}

    def register_model(self, model_name, model_instance):
        """
        注册一个新的AI模型到AIManager中。

        参数:
        model_name (str): 模型名称，用于标识模型。
        model_instance (BaseModel): 继承自BaseModel的模型实例。
        """
        self.models[model_name] = model_instance

    def chat(self, model_name, messages: list, model: str, **kwargs):
        """
        调用指定模型的chat方法。

        参数:
        model_name (str): 要调用的模型名称。
        prompt (str): 用户输入的文本。
        kwargs: 其他可选参数，例如max_tokens、temperature等。

        返回:
        str: 模型生成的文本响应。
        """
        model_instance = self.models.get(model_name)
        if not model_instance:
            raise ValueError(f"Model '{model_name}' is not registered.")
        return model_instance.chat(messages, model, **kwargs)


# 使用示例
if __name__ == "__main__":
    # 创建AIManager实例
    ai_manager = AIManager()

    # 注册OpenAI模型
    openai_model = OpenAIModel(api_key="your-openai-api-key")
    ai_manager.register_model("openai", openai_model)

    # 注册智普模型
    anthropic_model = ChatGlmModel(api_key="your-anthropic-api-key")
    ai_manager.register_model("anthropic", anthropic_model)

    # 调用聊天功能
    response = ai_manager.chat("openai", "Hello, how are you?")
    print(response)  # 输出AI模型的响应

