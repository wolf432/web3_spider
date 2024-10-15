from zhipuai import ZhipuAI

from ai_toolkit.models.base_model import BaseModel


class ChatGlmModel(BaseModel):
    """
        ChatGlmModel是实现智普AI，API的具体实现类，继承了BaseModel。它实现了聊天功能
        文档：https://open.bigmodel.cn/dev/api/normal-model/glm-4
    """

    def __init__(self, api_key):
        self._client = ZhipuAI(api_key=api_key)

    def chat(self, messages: list, model: str = 'glm-4-plus', **kwargs):
        try:
            stream = kwargs.get("stream", False)
            response = self._client.chat.completions.create(
                # -------------------------------常用请求参数---------------------------------
                # 上下文
                # role，表示角色，有三个取值：
                #   1. 'system'，系统扮演角色，比如：你是一个中国资深的营养师为用户提供健康的、减脂方案
                #   2. 'user'，用户，表示用户输入的信息
                #   3. 'assistant'，助手消息
                #   4. ‘tool’ 工具调用
                messages=messages,
                # 要调用的模型编码,glm-4-plus、glm-4-0520、glm-4 、glm-4-air、glm-4-airx、glm-4-long 、 glm-4-flash
                model=model,

                # 模型输出的最大token数，最大输出为4095，默认值为1024
                max_tokens=kwargs.get("max_tokens", 4095),

                # 采样温度，控制输出的随机性，必须为正数取值范围是：[0.0, 1.0]，默认值为0.95。
                temperature=kwargs.get("temperature", 0.3),

                # 该参数在使用同步调用时应设置为false或省略。表示模型在生成所有内容后一次性返回所有内容。默认值为false。
                # 如果设置为true，模型将通过标准Event Stream逐块返回生成的内容。
                # 当Event Stream结束时，将返回一个data: [DONE]消息。出
                stream=stream,

                # 模型可以调用的工具。
                tools=kwargs.get("tools", None),

                # -------------------------------不常用请求参数---------------------------------

                # 用户的 ID，用于 GPT 可以监控以及检测某个用户是否对该 api 进行滥用，不常用。
                user_id=kwargs.get("user_id", 'user_id')
            )
            if stream:
                return response
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"调用智普的chat出错。{str(e)}")

    def chat_image(self, messages: list, **kwargs):
        """
        对图片进行问答
        文档：https://open.bigmodel.cn/dev/api/normal-model/glm-4v
        """
        try:
            response = self._client.chat.completions.create(
                # -------------------------------常用请求参数---------------------------------
                # 上下文
                messages=messages,
                # 要调用的模型编码,glm-4v-plus 、glm-4v
                model='glm-4v-plus',

                # 采样温度，控制输出的随机性，必须为正数取值范围是：[0.0, 1.0]，默认值为0.95。
                temperature=kwargs.get("temperature", 0.3),

                # 该参数在使用同步调用时应设置为false或省略。表示模型在生成所有内容后一次性返回所有内容。默认值为false。
                # 如果设置为true，模型将通过标准Event Stream逐块返回生成的内容。
                # 当Event Stream结束时，将返回一个data: [DONE]消息。出
                stream=kwargs.get("stream", False),
            )
            return response
        except Exception as e:
            raise Exception(f"调用智普的chat出错。{str(e)}")

    def embedding(self, content: list):
        """
        内容转换成向量
        """
        response = self._client.embeddings.create(
            model='embedding-3',
            input=content
        )
        return response
