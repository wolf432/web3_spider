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
        self._use_model = ''
        self._big_model = ''

    def use_big_model(self, big_model: str, model_name: str):
        if not self.models.get(big_model):
            raise ValueError(f"大模型'{big_model}'没有注册到类中")
        self._big_model = big_model
        self._use_model = model_name

    def _check_params(self):
        """
        检查模型参数是否设置
        """
        if self._big_model == '' or self._use_model == '':
            raise ValueError('请设置要使用的大模型和调用的模型名')

    def register_model(self, model_name, model_instance):
        """
        注册一个新的AI模型到AIManager中。

        参数:
        model_name (str): 模型名称，用于标识模型。
        model_instance (BaseModel): 继承自BaseModel的模型实例。
        """
        self.models[model_name] = model_instance

    def chat(self, messages: list, **kwargs):
        """
        调用指定模型的chat方法。

        参数:
        model_name (str): 要调用的模型名称。
        prompt (str): 用户输入的文本。
        kwargs: 其他可选参数，例如max_tokens、temperature等。

        返回:
        str: 模型生成的文本响应。
        """
        self._check_params()
        model_instance = self.models.get(self._big_model)
        if not model_instance:
            raise ValueError(f"Model '{self._big_model}' is not registered.")
        return model_instance.chat(messages, self._use_model, **kwargs)

    def chat_image(self, messages: list, **kwargs):
        self._check_params()
        model_instance = self.models.get(self._big_model)
        if not model_instance:
            raise ValueError(f"Model '{self._big_model}' is not registered.")
        return model_instance.chat_image(messages, **kwargs)

    def embedding(self, content: list):
        self._check_params()
        model_instance = self.models.get(self._big_model)
        if not model_instance:
            raise ValueError(f"Model '{self._big_model}' is not registered.")
        return model_instance.embedding(content)
