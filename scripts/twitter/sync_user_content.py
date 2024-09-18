"""
同步用户表里的最新数据
"""
import traceback

from media_platform.twitter.crawler import TwitterCrawler
from media_platform.twitter.service import UserService
from media_platform.twitter.exception import RateLimitError, TokenWaitError
from media_platform.twitter.service import ContentServie
from database import get_db, get_redis
from tools.utils import logger

redis = get_redis()
db = get_db()

crawler = TwitterCrawler(db, redis)
user_service = UserService(db)
content_service = ContentServie(db)

# 获取用户列表
user_list = user_service.get_user_monitored_list()
if user_list is None:
    logger.info('没有需要监控的账号')
    exit()

for user in user_list:
    logger.info(f"开始获取{user.name}的内容")
    try:
        crawler.sync_content_by_name(user.name)
    except (TokenWaitError, RateLimitError) as e:
        logger.error(f'所有Token都不可用，等待15分钟后再请求,{str(e)}')
        exit()
    except Exception as e:
        stack_trace = traceback.format_exc()
        logger.error(stack_trace)
        continue