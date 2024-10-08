from sqlalchemy.orm import Session
from redis import Redis
from datetime import datetime

from media_platform.quantclass.client import QuantClassClient
from models.quantclass import QtcArticleSummary
from media_platform.quantclass.exception import AUTHENError
from tools.utils import logger


class QuantClassCrawler():

    def __init__(self, db: Session, redis: Redis):
        self._client = QuantClassClient(db, redis)

    def get_article_by_list(self, page: int = 1, pre_page: int = 20, category_id: int = 0, essence: int = 0, days: int = 0):
        """
        获取文章列表
        """
        response = self._client.api_get_article_list(page, pre_page, category_id, essence, days)
        summary = []
        for info in response['pageData']:
            thread = info['thread']
            summary.append(
                QtcArticleSummary(
                    aid=thread['pid'],
                    title=thread['title'],
                    summary=thread['summary'].replace('\n', ''),
                    category_id=thread['categoryId'],
                    add_time=datetime.fromisoformat(thread['createdAt']),
                    author_id=info['user']['pid'],
                    view_count=thread['viewCount'],
                    vote_count=thread['voteCount'],
                    is_essence=1 if thread['isEssence'] else 0,
                )
            )
        return {
            'total_page': response['totalPage'],
            'page_length': response['pageLength'],
            'summary': summary,
        }

    def get_article_detail_by_id(self, article_id: int, headers:dict):
        """
        获取指定文章的数据
        """
        article = self._client.api_get_article_detail(article_id, headers)
        return article['firstPost']['content']

    def get_categories(self):
        """
        获取所有分类数据
        """
        return self._client.api_get_categories()

    def is_login(self,headers:dict):
        try:
            self._client.api_is_login(headers)
            return True
        except AUTHENError as e:
            logger.error('登录信息错误')
            return False
