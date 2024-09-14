from config import settings
from ai_toolkit.models.chatglm_model import ChatGlmModel
from ai_toolkit.models.openai_model import OpenAIModel


def system_message(content: str):
    return {"role": "system", "content": content}


def user_message(content: str):
    return {"role": "user", "content": content}


def tool_message(content: str, call_id: str):
    return {"role": "tool", "content": content, "tool_call_id": call_id}


def assistant_message(content: str):
    return {"role": "assistant", "content": content}


def model_client_factory(model_name: str):
    """
    返回指定大模型的客户端实例
    """
    if model_name == 'openai':
        return OpenAIModel(api_key=settings.OPENAI_API_KEY,base_url=settings.OPENAI_BASE_URL)
    if model_name == 'zhipu':
        return ChatGlmModel(api_key=settings.ZHIPU_API_KEY)

    raise Exception(f"不支持的大模型客户端：{model_name}")