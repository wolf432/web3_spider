import ollama

from ai_toolkit.models.base_model import BaseModel


class OllamaModel(BaseModel):
    """
        Ollama是运行本地的大模型
        文档：
        - https://ollama.com/blog/python-javascript-libraries
        - https://github.com/ollama/ollama/blob/main/docs/api.md
    """
    def __init__(self):
        self._url = 'http://127.0.0.1:11434'

    def chat(self, messages: list, model_name: str = 'glm4:latest', **kwargs):
        """
        return:
        如果stream=True， 通过下面代码获取，和openai获取的不一样
        ···
        for chat in response:
            print(chat['message']['content'],end='')
        ···
        """
        try:
            stream = kwargs.get("stream", False)
            response = ollama.chat(
                model=model_name,
                messages=messages,
                stream=stream,
            )
            if stream:
                return response
            return response['message']['content']
        except Exception as e:
            raise Exception(f"调用Ollama的chat出错。{str(e)}")

    def chat_image(self, messages: list, **kwargs):
        pass
