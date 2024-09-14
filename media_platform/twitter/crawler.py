import math
import time
from datetime import datetime
from sqlalchemy.orm import Session
from redis import Redis

from models.twitter import CookiePool
from media_platform.twitter.field import CookieIdentity
from media_platform.twitter.client import TwitterClient
from media_platform.twitter import help
from media_platform.twitter.exception import NoData, RateLimitError, DataAddError
from tools.utils import logger
from media_platform.twitter.service import UserService, CookieService, ContentServie
from models.twitter import TweetSummaries


class TwitterCrawler():

    def __init__(self, db: Session, redis: Redis, timeout=30):
        self._user_service = UserService(db)
        self._cookie_service = CookieService(db)
        self._content_service = ContentServie(db)

        self._client = TwitterClient(db, redis, timeout)

    def get_content_by_name(self, name: str, limit: int = 20):
        """
        获取指定用户的推特内容列表
        :param limit: 获取内容的条数
        :param name: 用户名
        :return:
        """
        user = self._user_service.get_user_by_name(name)
        result = []
        next_course = None
        while limit > 0:
            content = self._client.api_user_tweets(user.rest_id, next_course=next_course)
            next_course = content['next_cursor']
            for data in content["data"]:
                if limit < 1:
                    break
                result.append(data)
                limit -= 1
        return result

    def sync_content_by_name(self, name: str, limit: int = 20):
        """
        同步指定用户的文章到数据库
        :param name: 用户名
        :param limit: 同步数量
        :return:
        """
        content_list = self.get_content_by_name(name, limit)
        logger.info(f"开始同步{name}的推特内容.")
        # 排重
        data = []
        for con in content_list:
            data.append(
                TweetSummaries(
                    content=con["content"],
                    reply_count=con["reply_count"],
                    retweet_count=con["retweet_count"],
                    views_count=con["views_count"],
                    like_count=con["favorite_count"],
                    x_created_at=con["created_at"],
                    user_id=con["user_id"],
                    rest_id=con["id"],
                )
            )
        try:
            self._content_service.add_all(data)
        except DataAddError as e:
            logger.error(f"添加推特列表内容失败:{str(e)}")
            return ''

        logger.info(f"{name}的推特内容同步完成.同步了{len(data)}条数据")

    def get_detail_content(self, tweet_id: int):
        """
        获取指定帖子的内容
        :param tweet_id:
        :return:
        """
        cookie = self._cookie_service.get_cookie(CookieIdentity.USER.value)
        if not cookie:
            raise RateLimitError("没有可用的cookie")

        headers = help.get_user_cookie(cookie.value)

        result = self._client.api_tweet_detail_text(tweet_id, headers)
        return result

    def sync_following(self, user_id: int):
        """
        获取指定用户的关注列表
        访问限制 500/15分钟
        :param user_id:
        :return:
        """
        cookie = self._cookie_service.get_cookie(CookieIdentity.USER.value)
        if not cookie:
            raise RateLimitError("没有可用的cookie")

        cursor = None
        while True:
            result = self._client.api_following(user_id, cursor)
            self._user_service.add_all(result['list'])

            cursor = result["bottom"]
            if int(cursor.split("|")[0]) == 0:
                break

    def sync_user_info(self):
        """
        同步用户的基础信息
        一个游客cookie请求限制：95/15分钟
        :return:
        """
        cookie_amount = self._cookie_service.get_cookie_amount()
        user_amount = self._user_service.get_user_amount()
        user_ceil = math.ceil(user_amount / 95)
        if cookie_amount < user_ceil:
            self.sync_cookie_pool(user_ceil - cookie_amount)

        header_data = self._cookie_service.get_cookie_with_header()
        current_time = datetime.now()

        user_list = self._user_service.get_user_list_latest()
        for user in user_list:
            # 检查上次跟新时间，1小时内不再更新
            updated_at = user.updated_at  if user.updated_at else 0
            if updated_at != 0:
                time_difference = current_time - updated_at
                difference = time_difference.total_seconds()
            else:
                difference = 3601
            if difference < 3600:
                logger.info(f"{user.name}更新没超过1小时，不更新.")
                continue

            logger.info(f"更新{user.name}的基础信息.")
            try:
                user_info = self._client.api_user_by_screen_name(user.name, headers=header_data["header"])

                if user_info.rate_limit_reset < 1:
                    self._cookie_service.set_cookie_invalid([header_data["cookie_id"]])
                    header_data = self._cookie_service.get_cookie_with_header()

                self._user_service.update_user_info(user_info)
            except RateLimitError as e:
                logger.warning(f"更新次数太多被限制，等待1分钟后再请求。message:{str(e)}")
                time.sleep(600)
            except Exception as e:
                logger.warning(f"更新{user.name}失败, message:{str(e)}")

    def sync_cookie_pool(self, limit: int = 5):
        """
        维护游客的cookie池
        :param limit:维持可用cookie数量
        :return: void
        """
        self._cookie_service.remove_not_available()
        amount = self._cookie_service.get_available_amount(CookieIdentity.GUEST.value)
        if amount >= limit:
            logger.info(f"可用的游客cookie充足,不用更新.amount={amount}")
            return True
        amount = limit - amount
        logger.info(f"开始获取{amount}个游客cookie")

        new_cookie_pool: [CookiePool] = []
        try:
            for i in range(amount):
                guest_cookie = help.get_guest_cookie(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.3")

                new_cookie_pool.append(
                    CookiePool(
                        value=guest_cookie['cookies'],
                        expired=guest_cookie['expired'],
                        identity_type=CookieIdentity.GUEST.value
                    )
                )

            self._cookie_service.add_all(new_cookie_pool)
        except Exception as e:
            logger.error(f"添加游客cookie失败.messsage:{str(e)}")
            return False

        logger.info(f"插入{amount}个游客cookie成功.")
