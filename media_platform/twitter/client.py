import requests
import json
from sqlalchemy.orm import Session
from redis import Redis

from base.base_crawler import AbstractApiClient
from media_platform.twitter.exception import *
from media_platform.twitter.field import UserInfo, CookieIdentity
from media_platform.twitter.help import extract_value_from_url, get_headers
from media_platform.twitter.exception import TokenWaitError
from models.twitter import CookiePool
from tools import utils
from tools import time


class TwitterClient(AbstractApiClient):
    # 需要登录用户cookie的接口
    API_LIMITS = {
        'UserTweets': 50,
        'TweetDetail': 150,
        'Following': 493
    }
    cookie_pool_prefix = 'twitter_cookie_pool_'  # cookie缓存池队列名前缀

    def __init__(self,
                 db: Session,
                 redis: Redis,
                 timeout=30,
                 proxies=None,
                 ):
        self.proxies = proxies
        self.timeout = timeout
        self._redis = redis
        self._db = db

        self._init_cookie_pool()

    def _init_cookie_pool(self):
        """
        初始化cookie池的缓存
        :return:
        """
        utils.logger.info("初始化cookie池")
        pools = self._db.query(CookiePool).where(CookiePool.identity_type == CookieIdentity.USER.value,
                                                 CookiePool.use_status == 1).all()
        if len(pools) == 0:
            raise Exception("没有可用的cookie")

        for (api, limit) in self.API_LIMITS.items():
            cache_key = self.cookie_pool_prefix + api

            if self._redis.llen(cache_key) > 0:
                utils.logger.debug(f'{api}队列缓存池不用初始化')
                continue

            self._redis.delete(cache_key)
            for pool in pools:
                cookie = {
                    "id": pool.id,
                    "cto": pool.value['cto'],
                    "auth_token": pool.value['auth_token'],
                    'limit': limit,
                    'limit_reset': 0
                }
                self._redis.lpush(cache_key, json.dumps(cookie))

    def get_by_header(self, url, params: dict | None = None):
        """
        根据请求的url来设置cookie
        :param url: url
        :param params: 参数
        :return:
        """
        api_name = extract_value_from_url(url)
        if not self.API_LIMITS.get(api_name):
            utils.logger.error(f"请求{api_name}接口不存在")
            raise APINOTFOUNDERROR("api 不存在")
        cache_key = self.cookie_pool_prefix + api_name

        queue_len = self._redis.llen(cache_key)
        current_time = time.current_unixtime()
        cookie = {}

        while queue_len > 0:
            cache_value = self._redis.lpop(cache_key)
            if cache_value is None:
                raise RateLimitError("没有可用的cookie")

            cookie = json.loads(cache_value)

            if cookie['limit'] > 0 or current_time > cookie['limit_reset']:
                break

            queue_len -= 1
            self._redis.lpush(cache_key, cache_value)
            cookie = {}

        if not cookie:
            raise TokenWaitError('等待15分钟后刷新再使用')

        _headers = get_headers()
        _headers["cookie"] = f"auth_token={cookie['auth_token']};ct0={cookie['cto']}"
        _headers["x-csrf-token"] = cookie['cto']

        response = self.request(method="GET", url=f"{url}", params=params, headers=_headers)

        cookie['limit'] = int(response.headers.get('x-rate-limit-remaining', cookie['limit']))
        cookie['limit_reset'] = int(response.headers.get('x-rate-limit-reset', 0))
        self._redis.lpush(cache_key, json.dumps(cookie))
        return response

    def request(self, method, url, **kwargs):
        """
        GET、POST统一请求方法，根据http状态码会抛出异常
        :param method: GET或POST方法
        :param url: 请求url
        :param kwargs: 参数
        :return:
        """
        response = None

        if method == "GET":
            response = requests.request(method, url, **kwargs)
        elif method == "POST":
            response = requests.request(method, url, **kwargs)

        if response.status_code == 200:
            return response

        if response.status_code == 429:
            utils.logger.error(f"访问次数受限，等待刷新时间后再用: {response.text}")
            raise RateLimitError(response.text)

        if response.status_code == 403:
            utils.logger.error(f"token 过期: {response.text}")
            raise TokenExpiredError(response.text)

        if response.status_code == 401:
            utils.logger.error(f"认证失败，请检查cookie是否正确: {response.text}")
            raise TokenExpiredError(response.text)

        utils.logger.error(f"请求数据失败: {response.text}")
        raise DataFetchError(response.text)

    def get(self, url: str, params: dict | None = None, headers: dict | None = None):
        """
        GET请求
        :param url: 请求地址
        :param params: 参数
        :param headers: http头参数
        :return:
        """
        return self.request(method="GET", url=f"{url}", params=params, headers=headers)

    def post(self, url: str, data: dict, headers: dict | None = None):
        """
        POST请求
        :param url: 请求地址
        :param data: 参数
        :param headers: http头参数
        :return:
        """
        return self.request(method="POST", url=f"{url}", data=data, headers=headers)

    def api_user_by_screen_name(self, user: str, headers: dict):
        """
        获取指定账号的基础信息
        :param headers: header信息
        :param user: 用户名，@后面的用户名
        :return: UserInfo
        """
        variables = '{"screen_name":"' + user + '","withSafetyModeUserFields":true}'
        features = '{"hidden_profile_subscriptions_enabled":true,"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_is_identity_verified_enabled":true,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"responsive_web_twitter_article_notes_tab_enabled":true,"subscriptions_feature_can_gift_premium":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}'
        fieldToggles = '{"withAuxiliaryUserLabels":false}'
        url = f'https://twitter.com/i/api/graphql/Yka-W8dz7RaEuQNkroPkYw/UserByScreenName?variables={variables}&features={features}&fieldToggles={fieldToggles}'
        response = self.get(url, headers=headers)

        headers = response.headers
        data = response.json()["data"]["user"]["result"]
        legacy = response.json()["data"]["user"]["result"]["legacy"]

        x_created_at = time.convert_to_ymd(legacy['created_at'])

        return UserInfo(
            rest_id=data["rest_id"],
            name=legacy["screen_name"],
            rate_limit_reset=headers["x-rate-limit-remaining"],
            limit_remaining=response.headers["x-rate-limit-reset"],
            followers_count=legacy["followers_count"],
            friends_count=legacy["friends_count"],
            statuses_count=legacy["statuses_count"],
            description=legacy["description"],
            x_created_at=x_created_at,
            full_name=legacy["name"],
        )

    def api_user_tweets(self, user_id: int, next_course: str | None = None):
        """
        获取指定用户的内容
        接口访问限制：50/15分钟
        :param user_id: 用户id
        :param next_course: 向下翻页的定位值
        :return:
        """
        utils.logger.debug(f"调用api_user_tweets接口查询user_id={str(user_id)}")

        variables_json = {
            "userId": user_id,
            "count": 20,
            "includePromotedContent": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True,
            "cursor": ""
        }
        if next_course is not None:
            variables_json["cursor"] = next_course
        variables = json.dumps(variables_json)
        features = '{"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}'
        fieldToggles = '{"withArticlePlainText":false}'
        url = f'https://api.x.com/graphql/E3opETHurmVJflFsUBVuUQ/UserTweets?variables={variables}&features={features}&fieldToggles={fieldToggles}'

        # response = self.get(url, headers=headers)
        response = self.get_by_header(url)

        result = response.json()

        instructions = result["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"]

        # 获取时间数据列表
        entries = []
        for timeline in instructions:
            if timeline["type"] == "TimelineAddEntries":
                entries = timeline["entries"]

        data = self._get_content_by_timeline(entries, user_id)

        utils.logger.debug(
            f'调用api_user_tweets接口剩余次数:{response.headers["x-rate-limit-remaining"]},刷新时间:{response.headers["x-rate-limit-reset"]}')
        return {
            "data": data["data"],
            "limit-remaining": response.headers["x-rate-limit-remaining"],  # 访问剩余次数
            "x-rate-limit-reset": response.headers["x-rate-limit-reset"],  # 刷新时间
            "next_cursor": data["next_cursor"],
        }

    def _get_content_by_timeline(self, contents, user_id: int):
        """
        细节列表页中的数据
        :param contents:
        :return:
        """
        list = []
        next_cursor = ''  # 向下翻页的值
        for v in contents:
            if v["content"]["entryType"] == "TimelineTimelineModule":  # 有多个数据
                # 忽略推荐关注人的数据
                if v["entryId"].startswith("who-to-follow"):
                    continue

                if v["content"]["items"][0]["item"]["itemContent"]["tweet_results"]["result"]['__typename'] == 'Tweet':
                    result = v["content"]["items"][0]["item"]["itemContent"]["tweet_results"]["result"]
                else:
                    result = v["content"]["items"][0]["item"]["itemContent"]["tweet_results"]["result"]['tweet']

                legacy = result["legacy"]
                rest_id = result["rest_id"]
                views = result["views"]
                if views["state"] == "Enabled":
                    views_count = 0
                else:
                    views_count = views['count']

                list.append({
                    "content": legacy["full_text"],
                    "created_at": time.convert_to_ymd(legacy["created_at"]),
                    "favorite_count": legacy["favorite_count"],  # 喜欢数
                    "reply_count": legacy["reply_count"],  # 评论数
                    "retweet_count": legacy["retweet_count"],  # 转帖数
                    "views_count": views_count,  # 查看数
                    "id": int(rest_id),  # 帖子id
                    "user_id": int(user_id),  # 帖子id
                    "retweeted_id": 0,  # 转发帖原帖id
                })
            elif v["content"]["entryType"] == "TimelineTimelineItem":  # 转帖
                core = v["content"]["itemContent"]["tweet_results"]["result"].get('core', -1)
                if core == -1:
                    continue
                legacy = v["content"]["itemContent"]["tweet_results"]["result"]["legacy"]
                views = v["content"]["itemContent"]["tweet_results"]["result"]["views"]
                if views["state"] == "Enabled":
                    views_count = 0
                else:
                    views_count = views["count"]

                # 获取转发帖子的id
                retweeted_id = 0
                if legacy.get("quoted_status_id_str"):
                    retweeted_id = legacy["quoted_status_id_str"]
                elif legacy.get("retweeted_status_result"):
                    retweeted_id = legacy["retweeted_status_result"]["result"]["rest_id"]

                list.append({
                    "content": legacy["full_text"],
                    "created_at": time.convert_to_ymd(legacy["created_at"]),
                    "favorite_count": legacy["favorite_count"],  # 喜欢数
                    "reply_count": legacy["reply_count"],  # 评论数
                    "retweet_count": legacy["retweet_count"],  # 转帖数
                    "views_count": views_count,  # 查看数
                    "id": int(legacy["id_str"]),  # 帖子id
                    "user_id": int(user_id),  # 用户id
                    "retweeted_id": retweeted_id,
                })
            elif v["content"]["entryType"] == "TimelineTimelineCursor" and v["content"]["cursorType"] == "Bottom":
                next_cursor = v["content"]["value"]

        return {
            "data": list,
            "next_cursor": next_cursor
        }

    def api_tweet_detail_text(self, tweet_id: int, headers: dict):
        """
        获取指定帖子的内容，不获取回复
        访问限制：150/15分钟
        :param tweet_id:
        :param headers:
        :return:
        """
        utils.logger.debug(f"api_tweet_detail_text接口调用，tweet_id={tweet_id}")

        variables = '{"focalTweetId":"' + str(
            tweet_id) + '","with_rux_injections":false,"rankingMode":"Relevance","includePromotedContent":true,"withCommunity":true,"withQuickPromoteEligibilityTweetFields":true,"withBirdwatchNotes":true,"withVoice":true}'
        features = '{"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}'
        fieldToggles = '{"withArticleRichContentState":true,"withArticlePlainText":false,"withGrokAnalyze":false,"withDisallowedReplyControls":false}'
        url = f'https://x.com/i/api/graphql/QuBlQ6SxNAQCt6-kBiCXCQ/TweetDetail?variables={variables}&features={features}&fieldToggles={fieldToggles}'
        # response = self.get(url, headers=headers)
        response = self.get_by_header(url)

        result = response.json()
        instructions = result["data"]["threaded_conversation_with_injections_v2"]["instructions"]

        entries = []
        text = ''
        for val in instructions:
            if val["type"] == "TimelineAddEntries":
                entries = val["entries"]
                break
        for entry in entries:
            if entry["content"]["entryType"] != "TimelineTimelineItem":
                continue
            if entry["content"]["itemContent"]["itemType"] != "TimelineTweet":
                continue

            result = entry["content"]["itemContent"]["tweet_results"]["result"]

            if result.get('note_tweet'):

                text = entry["content"]["itemContent"]["tweet_results"]["result"]["note_tweet"]["note_tweet_results"][
                    "result"]["text"]
            else:
                text = entry["content"]["itemContent"]["tweet_results"]["result"]['legacy']['full_text']

        utils.logger.debug(
            f'调用api_tweet_detail_text接口剩余次数:{response.headers["x-rate-limit-remaining"]},刷新时间:{response.headers["x-rate-limit-reset"]}')

        return {
            "text": text,
            "rate_limit_reset": response.headers["x-rate-limit-remaining"],
            "limit_remaining": response.headers["x-rate-limit-reset"],
        }

    def api_following(self, user_id: int, cursor: str | None = None):
        utils.logger.debug(f"api_following接口调用，user_id={user_id}")

        variables_json = {
            "userId": user_id,
            "count": 20,
            "includePromotedContent": False
        }
        if cursor is not None:
            variables_json["cursor"] = cursor
        variables = json.dumps(variables_json)
        url = f'https://x.com/i/api/graphql/7oQrdmth4zE3EtD42ZxgOA/Following?variables={variables}&features=%7B%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22responsive_web_graphql_exclude_directive_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22communities_web_enable_tweet_community_results_fetch%22%3Atrue%2C%22c9s_tweet_anatomy_moderator_badge_enabled%22%3Atrue%2C%22articles_preview_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22responsive_web_twitter_article_tweet_consumption_enabled%22%3Atrue%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22creator_subscriptions_quote_tweet_preview_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Atrue%2C%22rweb_video_timestamps_enabled%22%3Atrue%2C%22longform_notetweets_rich_text_read_enabled%22%3Atrue%2C%22longform_notetweets_inline_media_enabled%22%3Atrue%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D'
        response = self.get_by_header(url)

        result = response.json()
        instructions = result["data"]["user"]["result"]["timeline"]["timeline"]["instructions"]

        entries = []
        for val in instructions:
            if val["type"] == "TimelineAddEntries":
                entries = val["entries"]
                break

        user_list = []
        bottom = ""  # 向下翻页
        for entry in entries:
            if entry["content"]["entryType"] == "TimelineTimelineCursor" and entry["content"]["cursorType"] == "Bottom":
                bottom = entry["content"]["value"]

            if entry["content"]["entryType"] != "TimelineTimelineItem":
                continue

            user_results = entry["content"]["itemContent"]["user_results"]
            if len(user_results) == 0:
                continue

            result = user_results["result"]
            legacy = result["legacy"]
            user_list.append(
                UserInfo(
                    rest_id=result["rest_id"],
                    name=legacy["screen_name"],
                    followers_count=legacy["followers_count"],
                    friends_count=legacy["friends_count"],
                    statuses_count=legacy["statuses_count"],
                    description=legacy["description"],
                    x_created_at=time.convert_to_ymd(legacy["created_at"]),
                    full_name=legacy["name"],
                    rate_limit_reset=0,
                    limit_remaining=0,
                )
            )
        utils.logger.debug(
            f'调用api_following接口剩余次数:{response.headers["x-rate-limit-remaining"]},刷新时间:{response.headers["x-rate-limit-reset"]}')
        return {
            "list": user_list,
            "bottom": bottom,
            "rate_limit_reset": response.headers["x-rate-limit-remaining"],
            "limit_remaining": response.headers["x-rate-limit-reset"],
        }

    def api_search(self, keyword: str):
        """
        按照关键字搜索
        """
        url = f'https://x.com/i/api/graphql/UN1i3zUiCWa-6r-Uaho4fw/SearchTimeline?variables={"rawQuery":"{keyword}","count":20,"querySource":"typed_query","product":"Top"}&features={"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}'
        response = self.get_by_header(url)

        result = response.json()
