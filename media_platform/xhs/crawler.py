import json
import random
import time
import urllib.parse
from DrissionPage import ChromiumOptions, ChromiumPage
from sqlalchemy.orm import Session
from redis import Redis

from media_platform.xhs.client import XHSClient
from media_platform.xhs.service import UserService, NoteService
from tools.utils import logger
from media_platform.xhs.exception import DataFetchError
from media_platform.xhs.field import SearchSortType, SearchNoteType
from media_platform.xhs.help import chinese_to_number
from models.xhs import XHSNote, XHSUser
from tools.time import convert_timestamp_to_date, random_wait


class XHSCrawler():
    context_page: ChromiumPage
    xhs_client: XHSClient

    def __init__(self, cookie_str: str, db: Session, redis: Redis):
        co = ChromiumOptions()
        # 设置无头
        co.headless()
        co.set_argument('--no-sandbox')  # 无沙盒模式
        self.context_page = ChromiumPage(co)
        self.xhs_client = XHSClient(self.context_page, cookie_str)
        self._db = db
        self._redis = redis

        self._user_service = UserService(db, redis)
        self._note_service = NoteService(db, redis)

    def search_by_browser(self, keyword: str, amount: int = 1):
        """
        通过控制浏览器，按照关键词搜索，抓取笔记和作者数据
        """

        data = self.xhs_client.browser_get_note_by_search(keyword, amount)
        for item in data:
            parsed_url = urllib.parse.urlparse(item['note_link'])
            params = urllib.parse.parse_qs(parsed_url.query)
            self.note_detail_by_browser(item['note_id'], params['xsec_source'][0], params['xsec_token'][0])
            time.sleep(random.uniform(1, 3))

    def note_detail_by_browser(self, note_id: str, xsec_source: str | None = None, xsec_token: str | None = None):
        """
        通过控制浏览器，抓取指定笔记的详情页
        """
        if xsec_source is None:
            xsec_source = "pc_cfeed"
        detail = self.xhs_client.browser_get_note_detail(note_id, xsec_source, xsec_token)
        logger.debug(
            f"{detail['title']}\t喜欢:{detail['liked_count']}\t收藏：{detail['collected_count']}\t{detail['last_update_time']}")

        return detail

    def search_by_api(
            self, keyword: str,
            page_size: int = 1,
            search_type: SearchNoteType = SearchNoteType.ALL,
            sort: SearchSortType = SearchSortType.LATEST
    ) -> dict:
        """
        通过接口搜索笔记
        :keyword: 搜索的关键词
        :page_size: 要抓取数据的页数,默认抓取1页
        """
        page = 1
        has_more = True
        note_ids = []
        user_fields = []
        while page <= page_size and has_more:
            logger.info(f'[xhs.crawler.search_by_api] 开始获取第{page}页数据')
            try:
                data = self.xhs_client.api_get_note_by_keyword(keyword, page, search_type, sort)
                # 获取是否还有更多的数据
                has_more = data.get('has_more', False)

                for item in data['items']:
                    if item['model_type'] in ['rec_query', 'hot_query']:
                        continue

                    # 组装用户数据
                    user_tmp = XHSUser(
                        user_id=item['note_card']['user']['user_id'],
                        nickname=item['note_card']['user']['nick_name']
                    )
                    user_fields.append(user_tmp)
                    note_ids.append({
                        "id": item['id'],
                        "xsec_token": item['xsec_token'],
                        "liked_count": chinese_to_number(item['note_card']['interact_info']['liked_count']),
                    })
                page += 1
                pause_duration = random.uniform(1, 3)
                time.sleep(pause_duration)

            except DataFetchError as e:
                logger.error(f"[xhs.crawler.search_by_api.DataFetchError] 获取数据失败:{e}")
                break
            except Exception as e:
                raise DataFetchError(f"[xhs.crawler.search_by_api.Exception]搜索数据获取失败.{e}")

        return {"user_fields": user_fields, "note_ids": note_ids}

    def note_detail_by_api(self, note_id: str, xsec_token: str, xsec_source: str = 'pc_search',
                           keyword: str = '') -> XHSNote | None:
        """
        获取笔记详情API
        :note_id:笔记ID
        :xsec_token: 搜索关键字之后返回的比较列表中返回的token
        :xsec_source: 渠道来源
        """
        try:
            item = self.xhs_client.api_get_note_detail(note_id, xsec_token, xsec_source)
            return XHSNote(
                note_id=note_id,
                user_id=item['user']['user_id'],
                desc=item['desc'],
                note_url=f"https://www.xiaohongshu.com/explore/{item['note_id']}?xsec_token={xsec_token}&xsec_source={xsec_source}",
                title=item['title'],
                type=item['type'],
                last_update_time=convert_timestamp_to_date(item["last_update_time"]),  # 最后更新时间
                add_time=convert_timestamp_to_date(item["time"]),  # 最后更新时间
                tag_list=item['tag_list'],
                image_list=item['image_list'],
                liked_count=chinese_to_number(item['interact_info']['liked_count']),
                collected_count=chinese_to_number(item['interact_info']['collected_count']),
                comment_count=chinese_to_number(item['interact_info']['comment_count']),
                source_keyword=keyword,
            )
        except DataFetchError as e:
            logger.error(f"[xhs.crawler.note_detail_by_api.DataFetchError] 获取笔记详情失败.{note_id},{e}")
            return None
        except Exception as e:
            logger.error(f"[xhs.crawler.note_detail_by_api.Exception] 获取笔记详情失败.{note_id},{e}")
            return None

    def user_info_by_api(self, user_id):
        """
        获取指定用户的信息
        """
        logger.debug(f"[xhs.crawler.user_info_by_api] 抓取{user_id}用户的数据")
        info = self.xhs_client.browser_user_basic_info(user_id, False)
        return info
