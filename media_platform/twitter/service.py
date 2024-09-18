"""
数据库数据的操作封装
"""
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import update, delete

from models.twitter import CookiePool, XUser, TweetSummaries, WatchXUser
from tools.time import current_unixtime
from media_platform.twitter.field import UserInfo
from media_platform.twitter.exception import NoData, DataAddError
from tools.utils import logger
from media_platform.twitter.help import get_header_by_guest


class UserService():

    def __init__(self, db: Session):
        self._db = db

    def update_user_info(self, user_info: UserInfo):
        """
        根据UserInfo类型更新用户数据
        :param user_info:
        :return:
        """
        existing_user = self._db.query(XUser).where(XUser.name == user_info.name).first()

        if existing_user:
            # 获取 UserInfo 模型的所有字段（排除继承自 Request_Limit 或 BaseModel 的字段）
            user_info_fields = user_info.__fields__.keys()

            for field in user_info_fields:
                # 检查 XUser 中是否存在与 UserInfo 相同的字段
                if hasattr(existing_user, field):
                    # 动态设置 XUser 对应字段的值
                    setattr(existing_user, field, getattr(user_info, field))

            # 提交更改
            self._db.commit()
        else:
            raise NoData(f"没有找到要跟新的数据,{user_info.name}")

    def add_all(self, user_list: [UserInfo]):
        """
        批量添加用户数据
        :param user_list:
        :return:
        """
        data = []
        logger.info("开始批量添加推特用户")
        for user in user_list:
            exists = self.get_user_by_restId(user.rest_id)
            if exists is not None:
                continue
            data.append(
                XUser(**user.dict(exclude={"limit_remaining", "rate_limit_reset"}))
            )
        if len(data) == 0:
            logger.info("没有要提交的推特用户")
            return True
        self._db.bulk_save_objects(data)
        self._db.commit()
        logger.info(f"批量添加推特用户成功.{len(data)}")

    def get_user_list_latest(self):
        """
        获取用户列表，按id从大到小排序
        :return: [XUser]
        """
        return self._db.query(XUser).order_by(XUser.id.desc()).all()

    def get_user_monitored_list(self):
        """
        获取需要监控内容的用户列表
        :return: [XUser]
        """
        return self._db.query(XUser).where(XUser.is_monitored == 2).all()

    def get_user_amount(self):
        """
        获取用户总数据
        :return: int
        """
        return self._db.query(XUser).order_by(XUser.id.desc()).count()

    def get_user_by_name(self, name: str):
        """
        根据用户名获取数据
        :return: [XUser]
        """
        return self._db.query(XUser).where(XUser.name == name).first()

    def get_user_by_restId(self, rest_id: int):
        """
        用户twit的id获取数据
        :return: [XUser]
        """
        return self._db.query(XUser).where(XUser.rest_id == rest_id).first()

    def get_user_by_restIds(self, rest_ids: [int]):
        """
        根据用户twitter的id批量获取数据
        :return: [XUser]
        """
        return self._db.query(XUser).where(XUser.rest_id.in_(rest_ids)).all()

    def get_watch_group(self):
        """
        获取所有监控分组数据
        """
        now = datetime.now()
        return self._db.query(WatchXUser).where(now >= WatchXUser.last_execution_time).order_by(WatchXUser.interval.asc()).all()


class CookieService():

    def __init__(self, db: Session):
        self._db = db

    def get_cookie_by_id(self, id: int):
        """
        获取指定id的cookie
        :param id: 表的主键id
        :return: CookiePool
        """
        cookie = self._db.query(CookiePool).where(CookiePool.id == id).order_by(CookiePool.expired.asc()).one()
        if not cookie:
            raise NoData("没有该条数据")
        return cookie

    def get_cookie(self, guest=1):
        """
        获取cookie
        :param guest: 1-获取游客，2-获取登录用户
        :return: dict
        """
        now = current_unixtime()
        cookie = self._db.query(CookiePool).where(CookiePool.identity_type == guest, CookiePool.expired >= now,
                                                  CookiePool.amount > 0, CookiePool.use_status == 1).first()
        if not cookie:
            return {}
        return cookie

    def get_cookie_with_header(self, guest=1):
        """
        获取设置好cookie头的数据
        :param guest: 1-获取游客，2-获取登录用户
        :return: dict
        """
        now = current_unixtime()
        cookie = self._db.query(CookiePool).where(CookiePool.identity_type == guest, CookiePool.expired >= now,
                                                  CookiePool.amount > 0, CookiePool.use_status == 1).first()
        if not cookie:
            raise NoData("没有可用cookie")
        return {
            'header': get_header_by_guest(cookie.value),
            'cookie_id': cookie.id
        }

    def get_cookie_amount(self, guest=1):
        """
        获取cookie可用的数量
        :param guest: 1-获取游客，2-获取登录用户
        :return: dict
        """
        now = current_unixtime()
        return self._db.query(CookiePool).where(CookiePool.identity_type == guest, CookiePool.expired >= now,
                                                CookiePool.amount > 0, CookiePool.use_status == 1).count()

    def get_available_amount(self, guest: int):
        now = current_unixtime()
        return self._db.query(CookiePool).where(CookiePool.identity_type == guest, CookiePool.expired >= now,
                                                CookiePool.amount > 0, CookiePool.use_status == 1).count()

    def set_cookie_invalid(self, ids: [int]):
        """
        修改数据位无效
        :param ids:
        :return:
        """
        stmt = update(CookiePool).values(use_status=2).where(CookiePool.id.in_(ids))
        self._db.execute(stmt)
        self._db.commit()

    def add_all(self, data: [CookiePool]):
        """
        批量添加cookie数据
        :param data:
        :return:
        """
        try:
            self._db.add_all(data)
            self._db.commit()
        except Exception as e:
            logger.error(f"添加cookie失败")
            raise DataAddError("cookie")

    def remove_not_available(self):
        """
        删除无用的cookie数据
        :return:
        """
        now = current_unixtime()
        stmt = delete(CookiePool).where((CookiePool.identity_type == 1) & (
                (CookiePool.expired < now) | (CookiePool.amount < 0) | (CookiePool.use_status == 2)))
        self._db.execute(stmt)
        self._db.commit()
        logger.info("删除无用cookie")


class ContentServie():
    def __init__(self, db: Session):
        self._db = db

    def get_info_by_id(self, rest_id: int):
        """
        获取指定id的数据
        :param rest_id:
        :return: CookiePool
        """
        info = self._db.query(TweetSummaries).where(TweetSummaries.rest_id == rest_id).first()
        if not info:
            raise NoData("没有该条数据")
        return info

    def add_all(self, data: [TweetSummaries]):
        """
        批量添加特推列表数据，如果数据存在则更新喜欢等数据
        :param data:
        :return:
        """
        for val in data:
            try:
                info = self.get_info_by_id(val.rest_id)
                info.like_count = val.like_count
                info.reply_count = val.reply_count
                info.views_count = val.views_count
                info.retweet_count = val.retweet_count
                info.x_created_at = val.x_created_at
            except NoData:
                self._db.add(val)
            except Exception as e:
                logger.error(f"添加内容失败: message:{str(e)}")
                raise DataAddError("summaries add_all")
        self._db.commit()

    def get_latest_by_user_id(self, user_id: int, date: datetime | None = None, limit: int = 3):
        """
        获取指定用户最新的内容，最多返回3条
        :param date: 发布时间，按照发布时间来获取最新的数据，如果没有则返回最新的10条数据
        :param user_id: twitter的用户id
        :param limit: 返回数据数量
        :return: []
        """
        query = self._db.query(TweetSummaries)
        if date is None:
            query = query.where(TweetSummaries.user_id == user_id)
        else:
            query = query.where(TweetSummaries.user_id == user_id, TweetSummaries.x_created_at > date)

        return query.order_by(TweetSummaries.x_created_at.desc()).limit(limit).all()
