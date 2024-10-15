import openai

from ai_toolkit.models.base_model import BaseModel


class OpenAIModel(BaseModel):
    """
        OpenAIModel是OpenAI API的具体实现类，继承了BaseModel。它实现了聊天功能
        文档：https://platform.openai.com/docs/api-reference/chat
    """

    def __init__(self, api_key: str, base_url: str = 'https://api.openai.com/v1'):
        """
            构造函数，初始化OpenAI API的API密钥。

            参数:
            api_key (str): OpenAI API的密钥。
            base_url(str): 如果使用的是代理需要填写代理给出的地址
        """
        self._openai = openai.OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

    def chat(self, messages: list, model: str = 'gpt-4o', **kwargs):

        try:
            stream = kwargs.get("stream", False)
            chat_completion = self._openai.chat.completions.create(
                # -------------------------------常用请求参数---------------------------------
                # 上下文
                # role，表示角色，有三个取值：
                #   1. 'system'，系统扮演角色，比如：你是一个中国资深的营养师为用户提供健康的、减脂方案
                #   2. 'user'，用户，表示用户输入的信息
                #   3. 'assistant'，系统回复，系统的答复用户询问的内容
                messages=messages,
                # 选定GPT的模型，这里只可以选择Chat相关（以gpt-3.5或gpt-4K开头）的模型，可以参考：https://platform.openai.com/docs/models/overview，也可以使用下边的'Models'接口
                model=model,

                # 生成的最大token数，注意：你输入的messages的token数 加上 max_tokens 要小于模型的最大上下文限制，否则会报错
                # 这里思考：为啥max_tokens + messages token 小于模型最大上下文，而不是max_tokens小于模型最大上下文？
                max_tokens=kwargs.get("max_tokens", 4096),

                # 采样温度，取值范围 0-2.0。控制 GPT 输出的随机性。数值越大随机性越高。
                # 如果你不想GPT的输出太过随机化，可以设计为0.2（比如知识库、智能客服场景），如果取值为2就会胡扯
                temperature=kwargs.get("temperature", 0.3),

                # 置信度，取值范围 0.0-1.0，默认为1。取值越小置信度越高，置信度越高 GPT 输出的内容越严谨、固定、且重复，相反会越随机
                # temperature与top_p不建议同时设置，更建议使用top_p来控制随机性，top_p=1即使很随机也不会出现胡扯的情况
                # top_p=1,

                # 每次输入生成多少条内容，每条内容都是独立的答复
                n=1,

                # 是否是流式输出。True表示流式输出，False表示非流式输出
                stream=stream,

                # 指定GPT的答复格式，取值为：text(默认) 或 json_object
                # 但是不太好的是，如果开启了这个功能的，你的prompt最后要加一句'以json格式输出'，
                response_format={"type": kwargs.get("response_format", 'text')},

                # 随机种子。在prompt相同的前提下，如果seed的值相同，那GPT的答复则相同。但目前还处于测试阶段，不稳定
                seed=1001,

                # 这两个参数是用于向GPT注册tools而使用的，具体的下边会介绍
                tools=kwargs.get("tools", None),
                # tool_choice=None,

                # -------------------------------不常用请求参数---------------------------------

                # 取值范围 -2.0 到 2.0 。用于控制模型生成常见词汇的倾向性。取值越大表示希望模型更倾向于生成不常见的词汇。
                # 如果你在写一个科幻故事，并希望模型能够引入一些不常见的词汇或概念，你可以增大 frequency_penalty 的值，反之亦然
                frequency_penalty=kwargs.get("frequency_penalty", 0.2),

                # 取值范围 -2.0 到 2.0 。presence_penalty 用于控制模型生成新的、未在前文中出现过的词汇的倾向性。
                # 取值越大表示更倾向生成新词。比如你在写一个故事，并希望模型能够引入新的角色或概念则设置越大，反之亦然。
                presence_penalty=kwargs.get("presence_penalty", 0.2),

                # 停止符，当GPT遇到相应的字符串后会停止生成。
                # string数组，最多四个，多了会报错
                # 几种可能得场景：让GPT只生成一句话或者一段话，那可以设置为["。"]或者["\n"]等
                # stop=["。"],

                # 用户的 ID，用于 GPT 可以监控以及检测某个用户是否对该 api 进行滥用，不常用。
                user=kwargs.get("user", 'user_id')
            )
            if stream:
                return chat_completion

            return chat_completion.choices[0].message.content
        except Exception as e:
            raise Exception(f"调用openai的chat出错。{str(e)}")

    def chat_image(self, messages: list, **kwargs):
        """
        对图片进行问答
        文档：https://platform.openai.com/docs/api-reference/chat/create
        """
        return self.chat(messages, 'gpt-4o')

    def embedding(self, content: list, model_name: str = 'text-embedding-3-small'):
        """
        内容转换成向量
        :content 要转行的内容
        :model_name: 要选择的模型，支持的有：text-embedding-3-small、text-embedding-3-large、ada v2
        """
        response = self._openai.embeddings.create(
            model='embedding-3',
            input=content
        )
        return response
