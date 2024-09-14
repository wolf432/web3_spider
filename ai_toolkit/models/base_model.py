from abc import ABC, abstractmethod


class BaseModel(ABC):
    """
        BaseModel是一个抽象类，所有继承这个类的AI模型都必须实现这些方法。
        """
    @abstractmethod
    def chat(self, messages: list, model: str, **kwargs):
        pass
