"""
抓取文章列表的内容
"""
import argparse

from database import get_db, get_redis
from tools.utils import logger
from tools.time import random_wait
from models.quantclass import QtcArticleSummary
from media_platform.quantclass.crawler import QuantClassCrawler
from media_platform.quantclass.service import ArticleSummaryService, CategoryService
from media_platform.quantclass.exception import DataFetchError

db = get_db()
redis = get_redis()
crawler = QuantClassCrawler(db, redis)
summary_service = ArticleSummaryService(db, redis)
category_service = CategoryService(db, redis)


def fetch_data_by_cid(cid: int, cname: str, days: int):
    page = 1
    max_loop = 100  # 最大循环次数
    while max_loop > 0:
        article_list = crawler.get_article_by_list(page, 50, cid, 0, days)
        logger.info(f'获取分类:{cname},第{page}/{article_list["total_page"]}页的文章列表')

        if article_list['page_length'] == 0:
            logger.info(f'cid={cid}数据抓取完毕!')
            return ''
        write_database(article_list['summary'])

        page += 1
        max_loop -= 1
        random_wait(2, 4)


def write_database(data: [QtcArticleSummary]):
    amount = len(data)
    logger.debug(f'文章内容写入数据库：{amount}')
    result = summary_service.add(data)
    if result is False:
        logger.error(f'文章内容插入失败')


def main(cid_arr, days):
    for cid in cid_arr:
        try:
            if cid == 0:
                cname = '全部数据'
            else:
                # 获取分类信息
                cate_info = category_service.get_by_id(cid)
                cname = cate_info.name
                if cate_info is None:
                    logger.error(f'{cid}未知的分类id')
                    continue
            # 获取数据
            fetch_data_by_cid(cid, cname, days)
        except DataFetchError as e:
            logger.error(f'获取cid={cid}得到错误。{e}')


if __name__ == '__main__':
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(description="这是一个传入数组参数的Python脚本示例")

    # 添加数组类型的参数，使用 nargs='+' 表示接受一个或多个参数
    parser.add_argument('--cid', type=int, nargs='+', default=[0], help='传入要抓取的分类id')
    parser.add_argument('--days', type=int, default=0, help='传入要抓取几天内的数据，0表示抓取所有数据')

    # 解析参数
    args = parser.parse_args()

    if args.days == 0:
        logger.info(f'抓取分类{args.cid},抓取全量数据的数据')
    else:
        logger.info(f'抓取分类{args.cid},抓取{args.days}天内的数据')

    main(args.cid, args.days)
