import base64
import os
import math

from config import settings
from ai_toolkit.ai_manager import AIManager
from ai_toolkit import exception
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


def image_message(image_base: str, content: str):
    return {"role": "user", "content": [
        {
            "type": 'image_url',
            "image_url": {"url": image_base}
        },
        {
            "type": "text",
            "text": content
        }
    ]}


def image_text_message(content: str):
    return {"role": "user", "content": [
        {
            "type": "text",
            "text": content
        }
    ]}


def get_image_format(file_path):
    # 定义常见图片格式的文件签名
    image_signatures = {
        b'\xFF\xD8\xFF\xDB': 'JPEG',
        b'\xFF\xD8\xFF\xE0': 'JPEG',
        b'\xFF\xD8\xFF\xEE': 'JPEG',
        b'\xFF\xD8\xFF\xE1': 'JPEG',
        b'\x89PNG\r\n\x1A\n': 'PNG',
        b'GIF87a': 'GIF',
        b'GIF89a': 'GIF',
        b'%PDF-': 'PDF',
        b'BM': 'BMP',
        b'II*\x00': 'TIFF',
        b'MM\x00*': 'TIFF',
    }

    # 读取文件的前几个字节
    with open(file_path, 'rb') as file:
        file_header = file.read(8)

    # 遍历文件签名字典，匹配图片格式
    for signature, format_name in image_signatures.items():
        if file_header.startswith(signature):
            return format_name

    return 'png'


def image_base64(img_path: str, big_model: str = 'zhipu'):
    """
    把图片转换为Base64
    """
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"[ai_tookit.help.image_base64] 图片不存在 {img_path}不存在.")

    # 获取图片大小，防止超过大模型的限制
    file_size = os.path.getsize(img_path)
    if file_size > 5242880:
        raise exception.FileTooLargeError("图片不能超过5M")

    format_name = get_image_format(img_path)
    img_format = ['PNG','JPG','JPEG']
    if big_model == 'openai':
        img_format += ['GIF','WEBP']
    # 检查图片格式是否支持
    if format_name not in img_format:
        raise exception.UnsupportedFileFormatError(f"大模型不支持{format_name}格式的图片")
    with open(img_path, 'rb') as img_file:
        img_base = base64.b64encode(img_file.read()).decode('utf-8')
        return img_base if big_model == 'zhipu' else f"data:image/{format_name};base64,{img_base}"


def model_client_factory(model_name: str):
    """
    返回指定大模型的客户端实例
    """
    if model_name == 'openai':
        return OpenAIModel(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
    if model_name == 'zhipu':
        return ChatGlmModel(api_key=settings.ZHIPU_API_KEY)

    raise Exception(f"不支持的大模型客户端：{model_name}")


def get_ai_manager(big_model: str = '', model_name: str = ''):
    # 创建AIManager实例
    ai_manager = AIManager()

    # 注册OpenAI模型
    openai_model = OpenAIModel(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
    ai_manager.register_model("openai", openai_model)

    # 注册智普模型
    zhipu_model = ChatGlmModel(api_key=settings.ZHIPU_API_KEY)
    ai_manager.register_model("zhipu", zhipu_model)

    if big_model != '' and model_name != '':
        ai_manager.use_big_model(big_model, model_name)
    return ai_manager
