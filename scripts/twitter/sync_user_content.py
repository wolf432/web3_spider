"""
同步用户表里的最新数据
"""
import traceback

from media_platform.twitter.crawler import TwitterCrawler
from media_platform.twitter.service import UserService,ContentServie
from media_platform.twitter.exception import RateLimitError, TokenWaitError
from database import get_db, get_redis
from tools.utils import logger

redis = get_redis()
db = get_db()

crawler = TwitterCrawler(db, redis)
user_service = UserService(db)
content_service = ContentServie(db)

# 记录更新过的缓存账号
cache_key = 'sync_user_content_'

# 获取用户列表
user_list = user_service.get_user_monitored_list()
if len(user_list) == 0:
    logger.info('没有需要监控的账号')

for user in user_list:
    logger.info(f"开始获取{user.name}的内容")
    tmp_cache_key = cache_key+str(user.rest_id)
    if redis.get(tmp_cache_key):
        logger.debug(f"{user.name}已经更新过，不需要在更新")
        continue
    try:
        page = 200 if user.full == 2 else 1
        crawler.sync_content_by_name(user.name,page)
        redis.set(tmp_cache_key, 1, 600)
        if user.full == 2:
            user_service.set_full(user.id)
    except (TokenWaitError, RateLimitError) as e:
        logger.error(f'所有Token都不可用，等待15分钟后再请求,{str(e)}')
        exit()
    except Exception as e:
        stack_trace = traceback.format_exc()
        logger.error(stack_trace)
        continue