import json
import math
from sqlalchemy.orm import Session
from sqlalchemy import update
from redis import Redis

from models import quantclass
from tools.utils import to_dict, logger
from tools.encrypt import calculate_md5
from media_platform.quantclass.field import QuantCategory


class CategoryService:

    def __init__(self, db: Session, redis: Redis):
        self._db = db
        self._redis = redis
        self.cache_ex = 86400 * 14

    @staticmethod
    def get_cache_keys(fun: str, key: str):
        return f'qtc_categories_{fun}_{key}'

    def get_by_name(self, name: str) -> quantclass.QtcCategories | None:
        """
        根据分类名返回数据
        """
        cache_key = self.get_cache_keys('get_by_name', calculate_md5(name))
        cache_info: str = self._redis.get(cache_key)
        if cache_info:
            info_json = json.loads(cache_info)
            return quantclass.QtcCategories(**info_json)
        info = self._db.query(quantclass.QtcCategories).where(quantclass.QtcCategories.name == name).first()
        if info is not None:
            json_str = json.dumps(to_dict(info))
            self._redis.set(cache_key, json_str, self.cache_ex)
        return info

    def get_by_id(self, cid: int) -> quantclass.QtcCategories | None:
        """
        根据分类id返回数据
        """
        cache_key = self.get_cache_keys('get_by_id', str(cid))
        cache_info: str = self._redis.get(cache_key)
        if cache_info:
            info_json = json.loads(cache_info)
            return quantclass.QtcCategories(**info_json)
        info = self._db.query(quantclass.QtcCategories).where(quantclass.QtcCategories.id == cid).first()
        if info is not None:
            json_str = json.dumps(to_dict(info))
            self._redis.set(cache_key, json_str, self.cache_ex)
        return info

    def add(self, field: QuantCategory):
        """
        添加分类的数据
        """
        if self.get_by_name(field.name) is not None:
            return True

        self._db.add(quantclass.QtcCategories(
            id=field.id,
            name=field.name,
            pid=field.pid,
            created_at=field.created_at
        ))
        self._db.commit()
        return True


class ArticleSummaryService:
    def __init__(self, db: Session, redis: Redis):
        self._db = db
        self._redis = redis
        self.cache_ex = 86400 * 14

    @staticmethod
    def get_cache_keys(fun: str, key: str):
        return f'qtc_article_summary_{fun}_{key}'

    def add(self, fields: [quantclass.QtcArticleSummary]):
        """
        添加文章简介列表的数据
        """
        try:
            for field in fields:
                info = self.get_by_aid(field.aid)
                if info is None:
                    # 新增
                    self._db.add(field)
                else:
                    # 更新
                    stmt = (update(quantclass.QtcArticleSummary)
                    .where(quantclass.QtcArticleSummary.aid == field.aid)
                    .values(
                        view_count=field.view_count,
                        vote_count=field.vote_count,
                        is_essence=field.is_essence,
                        summary=field.summary,
                        title=field.title,
                    )
                    )
                    self._db.execute(stmt)
                self._db.commit()
        except Exception as e:
            logger.error(f'添加文章数据失败。{e}')
            return False

        return True

    def get_by_aid(self, aid: int) -> quantclass.QtcArticleSummary | None:
        """
        根据文章id返回数据
        """
        cache_key = self.get_cache_keys('get_by_aid', str(aid))
        cache_info: str = self._redis.get(cache_key)
        if cache_info:
            info_json = json.loads(cache_info)
            return quantclass.QtcArticleSummary(**info_json)
        info = self._db.query(quantclass.QtcArticleSummary).where(quantclass.QtcArticleSummary.aid == aid).first()
        if info is not None:
            json_str = json.dumps(to_dict(info))
            self._redis.set(cache_key, json_str, self.cache_ex)
        return info

    def get_not_fetch(self, page: int = 1, limit: int = 50):
        """
        没有抓取内容的加精的数据
        """
        query = self._db.query(quantclass.QtcArticleSummary).where(quantclass.QtcArticleSummary.is_essence == 2,quantclass.QtcArticleSummary.fetch==1)
        amount = query.count()
        page_total = math.ceil(amount / limit)
        start_page = (page - 1) * limit
        if page > page_total:
            return 0, None

        data = query.order_by(quantclass.QtcArticleSummary.id.desc()).offset(
            start_page).limit(limit).all()
        return page_total, data

    def set_fetch(self, aid:int):
        """
        设置内容已抓取
        """
        stmt = update(quantclass.QtcArticleSummary).where(quantclass.QtcArticleSummary.aid==aid).values(fetch=2)
        self._db.execute(stmt)
        self._db.commit()


class ArticleContentService:
    def __init__(self, db: Session):
        self._db = db

    def get_by_aid(self, aid: int) -> quantclass.QtcArticleContent | None:
        """
        根据文章id返回数据
        """
        return self._db.query(quantclass.QtcArticleContent).where(quantclass.QtcArticleContent.aid == aid).first()

    def add(self, field: quantclass.QtcArticleContent):
        """
        添加文章内容,如果内容已存在则更新
        """
        info = self.get_by_aid(field.aid)
        if info is not None:
            info.content = field.content
        else:
            self._db.add(quantclass.QtcArticleContent(
                aid=field.aid,
                content=field.content,
            ))
        self._db.commit()
        return True
