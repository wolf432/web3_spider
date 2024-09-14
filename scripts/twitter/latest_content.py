"""
抓取指定用户的最新内容
"""
import logging
import traceback

from media_platform.twitter.crawler import TwitterCrawler
from media_platform.twitter.service import UserService
from media_platform.twitter.exception import RateLimitError, TokenWaitError
from media_platform.twitter.service import ContentServie
from database import get_db, get_redis
from tools.message import send_msg
from ai_toolkit.help import model_client_factory, system_message, user_message
from ai_toolkit.prompt_manager import PromptManager

# AI配置
ai_client = model_client_factory('zhipu')
prompt_model = PromptManager()
prompts = prompt_model.get_prompt('filter_market_noise.md')
message_list = [
    system_message(prompts),
]

redis = get_redis()
db = get_db()

crawler = TwitterCrawler(db, redis)
user_service = UserService(db)
content_service = ContentServie(db)

notify_message = []  # 暂存最新博主的信息

user_list = [
    'Phyrex_Ni', 'jason_chen998','0xDeMoo','VitalikButerin','33357xyz',
    'tinyxiong_eth','nake13','VV_watch'
]
for name in user_list:
    logging.info(f"开始获取{name}的内容")
    try:
        user = user_service.get_user_by_name(name)
        if user is None:
            logging.error(f"{name}不存在")
            continue

        user_rest_id = user.rest_id
        crawler.sync_content_by_name(name)
    except (TokenWaitError, RateLimitError) as e:
        logging.error(f'所有Token都不可用，等待15分钟后再请求,{str(e)}')
        exit()
    except Exception as e:
        stack_trace = traceback.format_exc()
        logging.error(stack_trace)
        continue

    cache_key = f"last_content_{user_rest_id}"
    x_created_at = redis.get(cache_key)
    # x_created_at = None

    # 获取最新的内容
    contents = content_service.get_latest_by_user_id(user_rest_id, x_created_at)
    if len(contents) == 0:
        logging.info(f"{name}没有最新的内容")
        continue

    redis.set(cache_key, str(contents[0].x_created_at))

    notify_message.append(f'\n========={name}博主的最新内容：==========\n')
    for con in contents:
        text = f"""
        {con.content}
        发布时间:{con.x_created_at}
        详细链接：f'https://x.com/status/{name}/{con.rest_id}'
        """
        notify_message.append(text)

if len(notify_message) > 0:
    notify_content = "".join(notify_message)
    try:
        message_list.append(user_message(notify_content))
        response = ai_client.chat(message_list, 'GLM-4-Plus')
        notify_content = response.choices[0].message.content
    except Exception as e:
        logging.warning(f"调用大模型错误.{str(e)}")

    rs = send_msg(notify_content)
    logging.info(f"发送信息结果：{str(rs)}")