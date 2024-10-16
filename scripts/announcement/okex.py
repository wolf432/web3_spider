"""
抓取币安的公告
"""
import time
import json
import requests
import traceback
from datetime import datetime

from database import get_redis
from tools.encrypt import calculate_md5
from tools.time import today_unix_time, convert_timestamp_to_date, random_wait, current_unixtime
from tools.message import send_msg_article
from tools.utils import logger

# https://www.okx.com/zh-hans/web3/discover/cryptopedia  web3活动公告

redis = get_redis()

log_prefix = '[scripts.announcement.binance'


def add_cache(cache_key, value):
    if not redis.exists(cache_key):
        redis.expire(cache_key, 86400)
    redis.sadd(cache_key, value)


def exists(cache_key, value):
    return redis.sismember(cache_key, value)


def get_okex_page_info(_today_time):
    """
    获取OKex的公告
    """
    cache_key = f'get_okex_page_info{_today_time}'
    de_list = []
    try:
        # 头信息
        headers = {
            'referer': 'https://www.okx.com/zh-hans/help/section/announcements-latest-announcements',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            "x-locale": "zh_CN"
        }
        now = current_unixtime() * 1000
        # 请求公告链接
        response = requests.get(f'https://www.okx.com/v2/support/home/web?t={now}', timeout=10, headers=headers)
        response.raise_for_status()  # 等待网络请求成功
        # 判断请求是否成功
        if int(response.json()["error_code"]) == 0:
            data = response.json()["data"]["notices"]

            # 遍历最新的公告数据
            for item in data:
                # 判断是否为当天的最新公告
                if item['publishDate'] > _today_time:
                    cache_value = calculate_md5(item['title'])
                    if exists(cache_key, cache_value):
                        continue

                    # add_cache(cache_key, cache_value)
                    de_list.append(
                        {
                            'title': item['title'],
                            'url': item['shareLink'],
                            'publish_date': convert_timestamp_to_date(item['publishDate'], '%Y-%m-%d %H:%M'),
                        }
                    )
    except:
        print('页面接口解析出错', traceback.format_exc())

    return de_list


def main(_today_time):
    markdown = "https://www.okx.com/zh-hans/help/section/announcements-latest-announcements\n"
    data = get_okex_page_info(_today_time)
    if len(data) == 0:
        logger.info('Okx没有新的公告')
        return

    for info in data:
        markdown += f"{info['title']} \n"
    send_msg_article(markdown)


if __name__ == '__main__':
    while True:
        dt = datetime.fromtimestamp(time.time())
        # 当天的YMD
        today = dt.strftime("%Y%m%d")
        # 当天的时间戳
        today_time = today_unix_time() * 1000
        main(today_time)

        random_wait(60, 120)
