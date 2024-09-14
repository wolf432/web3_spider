"""
抓取指定用户的最新内容
"""
import logging
import traceback

from media_platform.twitter.crawler import TwitterCrawler
from database import get_db, get_redis

redis = get_redis()
db = get_db()

crawler = TwitterCrawler(db, redis)

try:
    crawler.sync_user_info()
except Exception as e:
    stack_trace = traceback.format_exc()
    logging.error(f"同步用户数据失败。{str(e)}")
    logging.error(stack_trace)

