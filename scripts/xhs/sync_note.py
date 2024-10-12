"""
根据关键词抓取笔记
"""

import random
import time

from database import get_db, get_redis
from media_platform.xhs.crawler import XHSCrawler
from media_platform.xhs.service import NoteService, UserService
from media_platform.xhs.field import SearchSortType, SearchNoteType
from tools.cookie_pool import get_cookie_by_platform, set_cookie_invalid
from tools.utils import logger
from tools.time import random_wait

redis = get_redis()
db = get_db()

random_wait(300, 700)
exec_cache_key = 'xhs_sync_note_exec'
if redis.get(exec_cache_key):
    logger.debug("[xsh.sync_note] 已经同步过数据了，不在同步")

cookie_pool = get_cookie_by_platform('xhs')
if len(cookie_pool) == 0:
    logger.error('[xsh.sync_note]没有可用的cookie，退出脚本')
    exit()

for cookie in cookie_pool:
    try:
        crawler = XHSCrawler(cookie.value, db, redis)
        break
    except Exception as e:
        set_cookie_invalid('xhs', [cookie.id])
        logger.error(f'[xsh.sync_note]初始化浏览器失败，退出脚本.{e}')
        exit()

user_service = UserService(db, redis)
note_serivce = NoteService(db, redis)

keywords = [
    {"keyword": "家居", "page_size": 10},
    {"keyword": "奶油风", "page_size": 10},
    {"keyword": "奶油原木风", "page_size": 10},
    {"keyword": "装修", "page_size": 10},
    {"keyword": "小户型", "page_size": 10},
]

for value in keywords:
    logger.info(f"开始同步关键词{value['keyword']},一共同步{value['page_size']}页")
    result = crawler.search_by_api(value['keyword'], value['page_size'],SearchNoteType.IMAGE,SearchSortType.GENERAL)
    if result is None:
        logger.error('[xsh.sync_note]搜索笔记数据为空，脚本停止运行')

    logger.debug(f"[xsh.sync_note]同步用户数据，一共{len(result['user_fields'])}条数据需要同步")
    for user in result['user_fields']:
        user_service.add_user(user)

    logger.debug(f"[xsh.sync_note]获取笔记详情,一共{len(result['note_ids'])}条数据需要同步")

    for note in result['note_ids']:
        logger.info(f"[xsh.sync_note]获取{note['id']}笔记，点赞数{note['liked_count']}")

        # 进行一个策略的过滤
        # 点赞数小于300的笔记不抓取
        if note['liked_count'] < 500:
            logger.info(f"[xsh.sync_note]获取{note['id']}过滤，点赞数{note['liked_count']},不足300.")
            continue

        field = crawler.note_detail_by_api(note['id'], note['xsec_token'], 'pc_search', value['keyword'])
        if field is None:
            logger.warning(f"[xsh.sync_note]{note['id']}笔记获取失败.")
            continue

        note_serivce.add_note(field)
        pause_duration = random.uniform(1, 5)
        time.sleep(pause_duration)

    time.sleep(random.uniform(5, 10))

redis.set(exec_cache_key, 1, 3600 * 4)