"""
抓取指定用户的最新内容
"""
import json
from datetime import timedelta, datetime
import time

from media_platform.twitter.crawler import TwitterCrawler
from media_platform.twitter.service import UserService, ContentServie
from media_platform.twitter.exception import APICALLERROR
from models.twitter import XUser
from database import get_db, get_redis
from tools.message import send_msg
from ai_toolkit.help import model_client_factory, system_message, user_message
from ai_toolkit.prompt_manager import PromptManager
from tools.utils import logger
from tools.time import format_datetime

redis = get_redis()
db = get_db()

crawler = TwitterCrawler(db, redis)
user_service = UserService(db)
content_service = ContentServie(db)


def get_latest_content_by_rest_id(user_list: [XUser]):
    logger.debug("调用get_latest_content_by_rest_id")

    notify_message = {}  # 暂存最新博主的信息

    for user in user_list:
        cache_key = f"last_content_{user.rest_id}"
        x_created_at = redis.get(cache_key)
        # x_created_at = None

        # 获取最新的内容
        contents = content_service.get_latest_by_user_id(user.rest_id, x_created_at)
        if len(contents) == 0:
            logger.debug(f"{user.name}没有最新的内容")
            continue

        redis.set(cache_key, str(contents[0].x_created_at))

        # 保存用户数据信息
        notify_message[user.name] = {"data": []}
        for con in contents:
            notify_message[user.name]['data'].append({
                "content": con.content,
                'publish_date': format_datetime(con.x_created_at),
                'url': f'https://x.com/{user.name}/status/{con.rest_id}'
            })

    return notify_message


def ai_summary(content, ai_type, model, prompt):
    logger.debug("调用ai_summary")

    if len(content) == 0:
        logger.info('没有最新内容')
        return ''

    notify_content = json.dumps(content)

    # AI配置
    prompt_model = PromptManager()
    prompts = prompt_model.get_prompt(prompt)
    message_list = [
        system_message(prompts),
    ]

    try:
        message_list.append(user_message(notify_content))

        ai_client = model_client_factory(ai_type)
        response = ai_client.chat(message_list, model)
        notify_content = response.choices[0].message.content
    except Exception as e:
        logger.warning(f"调用大模型{ai_type}-{model}错误.{str(e)}")
        raise APICALLERROR("调用大模型错误")

    rs = send_msg(notify_content)
    logger.info(f"发送信息结果：{str(rs)}")


def main():
    group_list = user_service.get_watch_group()

    for group in group_list:
        logger.debug(f"执行{group.group_name}组用户的内容")
        rest_ids = group.user_ids["user_ids"]
        user_list = user_service.get_user_by_restIds(rest_ids)
        content = get_latest_content_by_rest_id(user_list)

        # 调用ai总结发送通知消息
        try:
            ai_summary(content, group.ai_type, group.ai_model, group.ai_prompt)
        except APICALLERROR as e:
            continue

        # 设置下次执行时间
        group.last_execution_time = datetime.now() + timedelta(minutes=group.interval)

        db.commit()


if __name__ == '__main__':
    while True:
        main()
        time.sleep(10)