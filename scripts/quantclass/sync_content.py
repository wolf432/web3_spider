"""
抓取文章列表的内容
"""

from database import get_db, get_redis
from tools.utils import logger
from tools.time import random_wait
from models.quantclass import QtcArticleContent
from media_platform.quantclass.crawler import QuantClassCrawler
from media_platform.quantclass.service import ArticleSummaryService, ArticleContentService
from models.cookie_pool import CookiePool
from media_platform.quantclass.exception import AUTHENError

db = get_db()
redis = get_redis()
crawler = QuantClassCrawler(db, redis)
summary_service = ArticleSummaryService(db, redis)
content_service = ArticleContentService(db)
cache_key = 'qtc_sync_content'


def fetch_data_by_aid(aid: int, title: str, headers: dict):
    logger.debug(f'开始获取：{title}，id={aid}')
    try:
        content = crawler.get_article_detail_by_id(aid, headers)
        content_service.add(
            QtcArticleContent(aid=aid, content=content)
        )
        summary_service.set_fetch(aid)
    except Exception as e:
        logger.error(f'获取{aid}文章内容失败,{e}')
    random_wait(60, 100)


def main(headers):
    if not crawler.is_login(headers):
        logger.error(f'认证信息错误')
        raise AUTHENError('认证信息错误')
    page = redis.get(cache_key)
    start_page = int(page) if page else 1
    while True:
        logger.debug(f'开始获取第{start_page}页数据')
        page_total, data = summary_service.get_not_fetch(start_page)
        # 通过接口获取数据
        for article in data:
            fetch_data_by_aid(article.aid, article.title, headers)
        start_page += 1
        if start_page > page_total or data is None:
            redis.delete(cache_key)
            return
        redis.set(cache_key, start_page, 86400)


if __name__ == '__main__':
    # 获取认证数据
    info = db.query(CookiePool).where(CookiePool.platform == 'qtc', CookiePool.use_status == 1).first()
    if info is None:
        logger.error('获取认证数据失败')
        exit()

    while True:
        try:
            main(info.value)
            random_wait(3000, 3600)
        except AUTHENError:
            exit()
        except Exception as e:
            logger.error(f'获取文章内容失败。{e}')
