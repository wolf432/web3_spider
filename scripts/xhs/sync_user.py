"""
同步用户表中的用户的数据
"""
from database import get_db, get_redis
from media_platform.xhs.crawler import XHSCrawler
from media_platform.xhs.service import UserService
from models.xhs import XHSUser, XhsUserSnapshot
from tools.cookie_pool import get_cookie_by_platform, set_cookie_invalid
from tools.utils import logger
from tools.time import random_wait
from media_platform.xhs.help import chinese_to_number

redis = get_redis()
db = get_db()

cookie_pool = get_cookie_by_platform('xhs')
if len(cookie_pool) == 0:
    logger.error('[xsh.sysc_user]没有可用的cookie，退出脚本')
    exit()

for cookie in cookie_pool:
    try:
        web_session = cookie.value['web_session']
        crawler = XHSCrawler(web_session, db, redis)
        break
    except Exception as e:
        set_cookie_invalid('xhs', [cookie.id])
        logger.error(f'[xsh.sysc_user]初始化浏览器失败，退出脚本.{e}')
        exit()

user_service = UserService(db, redis)
page_number = 1
while True:
    total_page, user_list = user_service.get_by_page(page_number, 20)
    if user_list is None:
        logger.info('[xhs.sync_user]获取用户数据出错。返回None')
        exit()
    if len(user_list) == 0:
        logger.info('[xhs.sync_user]没有用户数据')
        exit()

    for user in user_list:
        user_info = crawler.user_info_by_api(user.user_id)

        if user_info is None:
            continue

        tag_list = {}
        if len(user_info['tags']) > 0:
            tag_list = user_info['tags'].split(',')

        fans = chinese_to_number(user_info['fans'])

        # 更新用户表
        user_service.add_user(XHSUser(
            user_id=user.user_id,
            nickname=user_info['nickname'],
            location=user_info['location'],
            desc=user_info['desc'],
            fans=fans,
            tag_list=tag_list
        ))
        # 添加用户快照
        user_service.add_snapshot(XhsUserSnapshot(
            user_id=user.user_id,
            fans=fans
        ))

        random_wait(1, 3)

    page_number += 1
