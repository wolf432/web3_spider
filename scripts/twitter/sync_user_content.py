"""
同步用户表里的最新数据
"""
import traceback

from media_platform.twitter.crawler import TwitterCrawler
from media_platform.twitter.service import UserService, ContentServie
from media_platform.twitter.exception import RateLimitError, TokenWaitError
from database import get_db, get_redis
from tools.utils import logger
from tools.time import random_wait
from tools.message import send_msg_error

redis = get_redis()
db = get_db()

crawler = TwitterCrawler(db, redis)
user_service = UserService(db)
content_service = ContentServie(db)

# 通知缓存，防止一定时间内一直发送
cache_key = 'sync_user_notify'


def main():
    # 获取用户列表
    user_list = user_service.get_user_monitored_list()
    if len(user_list) == 0:
        logger.info('[script.twitter.sync_user_content] 没有需要监控的账号')

    for user in user_list:
        logger.info(f"[script.twitter.sync_user_content] 开始获取{user.name}的内容")
        try:
            page = 200 if user.full == 2 else 1
            crawler.sync_content_by_name(user.name, page)
            if user.full == 2:
                user_service.set_full(user.id)
        except (TokenWaitError, RateLimitError) as e:
            logger.error(f'[script.twitter.sync_user_content] 所有Token都不可用，等待15分钟后再请求,{str(e)}')
            random_wait(900, 1000)
        except Exception as e:
            if redis.get(cache_key):
                send_msg_error(f'推特sysc_user_content脚本出错：{e}')
                redis.set(cache_key,1, 1200)

            stack_trace = traceback.format_exc()
            logger.error(f'[script.twitter.sync_user_content]{stack_trace}')
            continue


if __name__ == '__main__':
    while True:
        main()
        random_wait(300, 600)
