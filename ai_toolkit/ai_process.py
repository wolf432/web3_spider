"""
ai对数据进行处理
"""
import json
from urllib.parse import urlparse

from ai_toolkit.help import image_base64, image_message, get_ai_manager
from ai_toolkit.prompt_manager import PromptManager
from ai_toolkit import help

class AIProcess:
    """
    封装了要使用ai处理的操作
    """

    def __init__(self, big_model: str, model_name: str):
        """
        :big_model: 要使用的ai大模型，openai、zhipu
        :model_name: 要使用的模型名
        """
        self._big_model = big_model
        self._model_name = model_name
        self._ai_client = get_ai_manager(self._big_model, self._model_name)
        self._prompt_manager = PromptManager()

    def change_big_model(self, big_model: str, model_name: str):
        self._ai_client.use_big_model(big_model, model_name)

    def ai_describe_image(self, image_path: str, prompt: str = '描述下图片的内容'):
        """
        返回图片的描述
        : image_path: 图片地址，本地路径或网络url地址
        : prompt: 提示词
        """
        # 判断image_path是url还是文件
        is_url = urlparse(image_path)
        if all([is_url.scheme, is_url.netloc]):
            img_base = image_path
        else:
            img_base = image_base64(image_path, self._big_model)

        messages = [
            image_message(img_base, prompt)
        ]

        try:
            response = self._ai_client.chat_image(messages, model=self._model_name)
            return response.choices[0].message.content
        except Exception as e:
            return None

    def ai_extract_tags(self, title:str, content: str):
        """
        使用大模型根据标题和内容提取出标签
        """
        prompt = self._prompt_manager.get_prompt('qtc_article_tag.md')
        messages = [
            help.system_message(prompt),
            help.user_message(json.dumps({'title':title,'summary':content}))
        ]

        try:
            return self._ai_client.chat(messages)
        except Exception as e:
            raise Exception()

    def ai_text_to_vector(self, content: list):
        """
        把文章转换为向量
        """
        return self._ai_client.embedding(content)

    def ai_article_segmentation(self,content: str):
        """
        对文章进行分割
        """
        prompt = self._prompt_manager.get_prompt('article_segmentation.md')

        messages = [
            help.system_message(prompt),
            help.user_message(content)
        ]

        return self._ai_client.chat(messages=messages,response_format='json_object')

    def ai_article_answer(self, question:str, knowledge: str):
        prompt = self._prompt_manager.get_prompt('article_answer.md',question=question,knowledge=knowledge)

        messages = [
            help.user_message(prompt),
        ]

        return self._ai_client.chat(messages=messages)