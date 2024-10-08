"""
同步分类的脚本
"""

from database import get_db, get_redis
from media_platform.quantclass.crawler import QuantClassCrawler
from media_platform.quantclass.field import QuantCategory
from media_platform.quantclass.service import CategoryService
from tools.utils import logger

db = get_db()
redis = get_redis()

crawler = QuantClassCrawler(db, redis)

categories = crawler.get_categories()
category_service = CategoryService(db, redis)


for cate in categories:
    logger.debug(f'开始添加:{cate["attributes"]["name"]}')
    category_service.add(
        QuantCategory(
            name=cate['attributes']['name'],
            id=cate['attributes']['id'],
            created_at=cate['attributes']['created_at'],
        )
    )
    if len(cate['attributes']['children']) > 0:
        for ch in cate['attributes']['children']:
            logger.debug(f'开始添加:{ch["name"]}')
            category_service.add(
                QuantCategory(
                    name=ch['name'],
                    id=ch['id'],
                    created_at=ch['created_at'],
                    pid=ch['parentid'],
                )
            )
