import requests
from config import settings
from tools import utils

url = 'http://msg.linan87.cn'


def send_msg_twitter(content: str) -> bool:
    """
    发送消息给twitter提示群
    """
    data = {'content': content}
    header = {"Authorization": settings.MESSAGE_TOKEN}
    try:
        response = requests.post(url + '/message', headers=header, json=data)
        if response.status_code == 200:
            return True
    except Exception as e:
        utils.logger.error(f"发送信息失败:{str(e)}")
        return False


def send_msg_error(content: str) -> bool:
    """
    发送错误信息给运维提示群
    """
    data = {'content': content}
    header = {
        "Authorization": settings.MESSAGE_ERROR_TOKEN
    }
    try:
        response = requests.post(url + '/message', headers=header, json=data)
        if response.status_code == 200:
            return True
    except Exception as e:
        utils.logger.error(f"发送信息失败:{str(e)}")
        return False
