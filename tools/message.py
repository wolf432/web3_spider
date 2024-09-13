import requests
from config import settings
from tools import utils

url = 'http://msg.linan87.cn'
header = {
    "Authorization": settings.MESSAGE_TOKEN
}


def send_msg(content: str) -> bool:
    """
    发送消息给第三方
    """
    data = {'content': content}
    try:
        response = requests.post(url + '/message', headers=header, json=data)
        if response.status_code == 200:
            return True
    except Exception as e:
        utils.logger.error(f"发送信息失败:{str(e)}")
        return False
