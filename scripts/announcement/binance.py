"""
抓取币安的公告
"""
import time
import json
from urllib.parse import quote
import requests
import traceback
from datetime import datetime

from database import get_redis
from tools.time import today_unix_time, convert_timestamp_to_date, random_wait
from tools.message import send_msg_article

# https://www.okx.com/zh-hans/web3/discover/cryptopedia  web3活动公告

redis = get_redis()

log_prefix = '[scripts.announcement.binance'

cate_arr = {
    48: '数字货币及交易对上新',
    49: '币安最新动态'
}

info_url = 'https://www.binance.com/zh-CN/support/announcement'  # 详情页的基础url


def add_cache(cache_key, value):
    if not redis.exists(cache_key):
        redis.expire(cache_key, 86400)
    redis.sadd(cache_key, value)


def exists(cache_key, value):
    return redis.sismember(cache_key, value)


def get_binance_page_info(catalogId, _today_time):
    """
    获取币安的公告
    """
    cache_key = f'get_binance_page_info{_today_time}'

    cname = quote(cate_arr[catalogId])
    de_list = []
    try:
        # 头信息
        headers = {
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
            'lang': 'zh-CN',
            'referer': f'https://www.binance.com/zh-CN/support/announcement/{cname}?c=48&navId=48&hl=zh-CN',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        }
        # 构造请求数据
        params = (('catalogId', catalogId), ('pageNo', '1'), ('pageSize', '20'), ('type', 1))
        # 请求公告链接
        response = requests.get('https://www.binance.com/bapi/composite/v1/public/cms/article/list/query',
                                params=params, timeout=10, headers=headers)
        response.raise_for_status()  # 等待网络请求成功
        # 判断请求是否成功
        if response.json()["success"]:
            data = response.json()["data"]["catalogs"][0]["articles"]

            # 遍历最新的公告数据
            for item in data:
                # 判断是否为当天的最新公告
                if item['releaseDate'] > _today_time:
                    if exists(cache_key, item['id']):
                        continue

                    add_cache(cache_key, item['id'])
                    title = item['title'].replace(' ', '')
                    de_list.append(
                        {
                            'title': title,
                            'url': f'{info_url}/{title}-{item["code"]}',
                            'publish_date': convert_timestamp_to_date(item['releaseDate'], '%Y-%m-%d %H:%M'),
                            'category': cate_arr[catalogId]
                        }
                    )
    except:
        print('页面接口解析出错', traceback.format_exc())

    return de_list


def binance(_today_time):
    markdown = "https://www.binance.com/zh-CN/support/announcement"
    for cate, cname in cate_arr.items():
        markdown += f"{cname}\n"
        data = get_binance_page_info(cate, _today_time)
        if len(data) == 0:
            continue

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

        binance(today_time)
        random_wait(60, 120)
