import requests
import json
import re
import time
import random
from DrissionPage import ChromiumPage
from base.base_crawler import AbstractApiClient
from urllib.parse import urlencode, quote

from tools.utils import logger
from tools.time import convert_timestamp_to_date,random_wait
from media_platform.xhs.help import sign, convert_str_cookie_to_dict, convert_cookies, chinese_to_number, get_search_id
from media_platform.xhs.field import SearchSortType, SearchNoteType
from media_platform.xhs.exception import IPBlockError, DataFetchError


class XHSClient(AbstractApiClient):

    def __init__(self, page: ChromiumPage, cookie: dict):
        self._domain = "https://www.xiaohongshu.com"
        self._host = "https://edith.xiaohongshu.com"
        self._header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com",
            "Content-Type": "application/json;charset=UTF-8"
        }
        self.IP_ERROR_STR = "网络连接异常，请检查网络设置或重启试试"
        self.IP_ERROR_CODE = 300012
        self.NOTE_ABNORMAL_STR = "笔记状态异常，请稍后查看"
        self.NOTE_ABNORMAL_CODE = -510001

        logger.debug("[xhs.XHSClient.__init__] 打开小红书主页")
        self._browser = page
        self._tab = self._browser.latest_tab
        self._tab.get(self._domain)
        login_try = 5

        logger.debug("[xhs.XHSClient.__init__] 检查登录状态")
        while not self.login_status() and login_try > 0:
            self.login_cookie(cookie)
            login_try -= 1
            logger.info(f"[xhs.XHSClient.__init__] 尝试登录,剩余次数：{login_try}")
            random_wait(2,5)
        if login_try <= 0:
            logger.error("[xhs.XHSClient.__init__] 尝试登录5次失败，退出")
            exit()

    def request(self, method, url, **kwargs):
        """
        GET、POST统一请求方法，根据http状态码会抛出异常
        :param method: GET或POST方法
        :param url: 请求url
        :param kwargs: 参数
        :return:
        """
        response = requests.request(method, url, **kwargs)

        if response.status_code == 200 or response.status_code == 200:
            return response
        if response.status_code == 461:# 接口请求失败，有可能是请求次数过多，暂停几秒后再继续请求
            logger.info(f"[xhs.XHSClient.request]状态码：461，暂停30-60秒后再请求")
            random_wait(30,60)

        logger.warning(f"[xhs.XHSClient.request]请求错误:{response.content},状态码：{response.status_code}")

    def _pre_headers(self, url: str, data=None):
        """
        设置请求头的参数签名
        url: 请求的url的地址
        data:请求参数
        """
        local_storage = self._tab.local_storage()
        if data:
            encrypt_params = self._tab.run_js('return window._webmsxyw(arguments[0],arguments[1]);', url, data)
        else:
            encrypt_params = self._tab.run_js(f"window._webmsxyw('{url}','{data}')", as_expr=True)

        cookie_str, cookie_dict = convert_cookies(self._tab.cookies())
        _cookie_dict = convert_str_cookie_to_dict(cookie_str)

        signs = sign(
            a1=_cookie_dict['a1'],
            b1=local_storage.get("b1", ""),
            x_s=encrypt_params.get("X-s", ""),
            x_t=str(encrypt_params.get("X-t", ""))
        )

        headers = {
            "X-S": signs["x-s"],
            "X-T": signs["x-t"],
            "x-S-Common": signs["x-s-common"],
            "X-B3-Traceid": signs["x-b3-traceid"],
            'Cookie': cookie_str
        }
        headers.update(self._header)
        return headers

    def get(self, url: str, headers: dict | None = None):
        """
        GET请求
        :param url: 请求地址
        :param headers: http头参数
        :return:
        """
        return self.request(method="GET", url=f"{url}", headers=headers)

    def login_cookie(self, cookie: dict):
        """
        使用cookie登录
        :cookie_str web_session的值
        """
        logger.debug("[xhs.XHSClient.login_cookie]开始设置登录的cookie")
        self._tab.set.cookies(f'a1={cookie["a1"]}; path=/; domain=.xiaohongshu.com;')
        self._tab.set.cookies(f'web_session={cookie["web_session"]}; path=/; domain=.xiaohongshu.com;')
        random_wait(1,3)
        logger.debug("[xhs.XHSClient.login_cookie]设置cookie完成")

    def login_status(self) -> bool:
        """
        检查登录状态
        """
        try:
            uri = '/api/sns/web/v2/user/me'
            result = self.get_with_api(uri)
            return result.json().get('success',False)
        except Exception as e:
            logger.warning('[xhs.XHSClient.login_status]未登录的状态')
            return False

    def get_with_api(self, url: str, domain: str = 'api'):
        """
        GET请求
        :param url: 请求地址
        :param domain: 使用api域名还是网站域名
        :return:
        """
        host = self._host if domain == 'api' else self._domain
        headers = self._pre_headers(url)

        return self.request(method="GET", url=f"{host}{url}", headers=headers)

    def post_with_api(self, url: str, params: dict | None = None):
        """
        GET请求
        :url: 请求地址
        :params: 参数
        :return:
        """
        headers = self._pre_headers(url, params)
        json_str = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
        response = self.request(method="POST", url=f"{self._host}{url}", data=json_str, headers=headers)
        data = response.json()
        if data["success"]:
            return data.get("data", data.get("success", {}))
        elif data["code"] == self.IP_ERROR_CODE:
            raise IPBlockError(self.IP_ERROR_STR)
        else:
            raise DataFetchError(data.get("msg", None))

    def browser_user_basic_info(self, user_id: str, guest: bool = True):
        """
        获取指定用户的首页信息，不需要使用登录用户的cookie
        PC端用户主页的网页存在window.__INITIAL_STATE__这个变量上
        url: https://www.xiaohongshu.com/user/profile/5e66843800000000010007c8
        :guest 是否使用游客模式获取，游客模式获取不到准确的粉丝数
        """
        url = f"/user/profile/{user_id}"

        if guest:
            response = self.get(f'{self._domain}url', headers=self._header)
        else:
            response = self.get_with_api(url, 'domain')

        html_content = response.text
        match = re.search(r'<script>window.__INITIAL_STATE__=(.+)<\/script>', html_content, re.M)

        if match is None:
            logger.warning(f"[xhs.XHSClient.browser_user_basic_info] {user_id} 没有解析出数据")
            return None

        info = json.loads(match.group(1).replace(':undefined', ':null'), strict=False)

        if info is None:
            return {}

        basic_info = info.get('user').get('userPageData')['basicInfo']

        user_basic = {
            'location': basic_info['ipLocation'],
            'desc': basic_info['desc'],
            'nickname': basic_info['nickname'],
            'user_id': user_id,
            'cursor': info['user']['noteQueries'][0]['cursor']  # 分页的id
        }
        interactions = info.get('user').get('userPageData')['interactions']
        for val in interactions:
            if val['type'] == 'fans':
                user_basic['fans'] = val['count']

        tags = [val['name'] for val in info.get('user').get('userPageData')['tags'] if val['tagType'] == 'profession']
        user_basic['tags'] = ','.join(tags)

        return user_basic

    def api_get_notes_by_user(self, user_id: str, cursor: str):
        """
        获取博主的笔记
        creator: 博主ID
        cursor: 上一页最后一条笔记的ID
        page_size: 分页数据长度
        """
        uri = "/api/sns/web/v1/user_posted"
        params = {
            "num": 30,
            "cursor": cursor,
            "user_id": user_id,
            "image_formats": "jpg,webp,avif"
        }

        return self.get_with_api(uri + '?' + urlencode(params))

    def browser_get_note_detail(self, note_id: str, xsec_source: str, xsec_token: str | None = None):
        """
            获取笔记详情API, 笔记内容在window.__INITIAL_STATE__变量里
            note_id:笔记ID
            xsec_source: 渠道来源
            xsec_token: 搜索关键字之后返回的比较列表中返回的token
        """
        if xsec_token is None:
            url = f"{self._domain}/explore/{note_id}"
        else:
            url = f"{self._domain}/explore/{note_id}?xsec_token={xsec_token}&xsec_source={xsec_source}&source=web_explore_feed"
        tab = self._browser.new_tab()
        tab.get(url)
        data_dict = tab.run_js('return window.__INITIAL_STATE__')
        try:
            note = data_dict['note']['noteDetailMap'][note_id]['note']
        except KeyError:
            self._browser.close_tabs(tab.tab_id)
            raise DataFetchError("获取笔记错误")

        self._browser.close_tabs(tab.tab_id)
        return {
            "title": note['title'],
            "desc": note['desc'],
            "liked_count": chinese_to_number(note['interactInfo']['likedCount']),
            "collected_count": chinese_to_number(note['interactInfo']['collectedCount']),
            "comment_count": chinese_to_number(note['interactInfo']['commentCount']),
            "tag_list": note["tagList"],
            "last_update_time": convert_timestamp_to_date(note["lastUpdateTime"]),  # 最后更新时间
            "add_time": convert_timestamp_to_date(note["time"]),
            "ip_location": note.get('ipLocation', ''),
            "type": note["type"],
            "image_list": note["imageList"],
        }

    def api_get_note_comment(self, note_id: str):
        uri = "/api/sns/web/v2/comment/page"
        params = {
            "note_id": note_id,
            "cursor": '',
            "top_comment_id": '',
            "image_formats": "jpg,webp,avif"
        }
        return self.get_with_api(uri + '?' + urlencode(params))

    def browser_get_note_by_search(self, keyword: str, amount: int):
        """
        根据关键词搜索笔记
        :keyword: 关键词参数
        :amount: 下拉次数
        """
        # 填写关键词搜索
        keyword = quote(keyword)
        url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_explore_feed"
        self._tab.get(url)
        notes = []
        for num in range(amount):
            data = self._get_info_by_search()
            notes.extend(data)

            random_secs = random.uniform(2,8)
            logger.debug(f"[xhs.XHSClient.browser_get_note_by_search] 下拉第{num + 1}次,休息{random_secs}秒")
            time.sleep(random_secs)
            self._tab.scroll.to_bottom()
        return notes

    def _get_info_by_search(self):
        data = []
        # 定位包含笔记信息的sections
        container = self._tab.ele('.feeds-page')
        sections = container.eles('.note-item')
        for section in sections:
            # 定位标题、作者、点赞
            try:
                # 定位文章id
                note_link = section.ele('.cover ld mask', timeout=0).link
                link_match = re.search('/search_result/([^?]+)', note_link)
                if link_match:
                    note_id = link_match.group(1)
                else:
                    continue

                # 定位标题、作者、点赞
                footer = section.ele('.footer', timeout=0)
                # 定位标题
                title = footer.ele('.title', timeout=0).text
                # 定位作者
                author_wrapper = footer.ele('.author-wrapper')
                nickname = author_wrapper.ele('.author').text
                author_link = author_wrapper.ele('tag:a', timeout=0).link
                # 提取作者id
                uid_match = re.search(r"/profile/([^?]+)", author_link)
                if uid_match:
                    uid = uid_match.group(1)
                else:
                    continue

                # 定位点赞
                like = footer.ele('.like-wrapper like-active').text
                data.append({
                    "title": title,
                    "nickname": nickname,
                    "note_id": note_id,
                    "note_link": note_link,
                    "uid": uid,
                    "like": like,
                })
            except Exception as e:
                continue
        return data

    def api_get_note_by_keyword(
            self, keyword: str,
            page: int = 1,
            search_type: SearchNoteType = SearchNoteType.ALL,
            sort: SearchSortType = SearchSortType.GENERAL,
            max_try: int = 4
    ):
        """
        根据关键词搜索笔记
        :keyword: 关键词参数
        :page: 分页第几页
        :search_type:笔记类型
        :sort: 搜索结果排序指定
        :max_try: 最大尝试次数，默认4
        """
        uri = "/api/sns/web/v1/search/notes"
        params = {
            "keyword": keyword,
            "page": page,
            "page_size": 20,
            "search_id": get_search_id(),
            "sort": sort.value,
            "note_type": search_type.value
        }
        try_count = 1
        while try_count < max_try:
            try:
                return self.post_with_api(uri, params)
            except IPBlockError as e:
                logger.error(f"[xhs.client.get_note_by_keyword]网络请求异常:{e}.尝试第{try_count}次重新获取")
                try_count += 1
                time.sleep(2)

        raise DataFetchError("获取数据失败")

    def api_get_note_detail(self, note_id: str, xsec_token: str, xsec_source: str):
        """
        通过接口获取笔记详情API
        :note_id:笔记ID
        :xsec_token: 搜索关键字之后返回的比较列表中返回的token
        :xsec_source: 渠道来源
        """
        params = {
            "source_note_id": note_id,
            "image_formats": ["jpg", "webp", "avif"],
            "extra": {"need_body_topic": 1},
            "xsec_source": xsec_source,
            "xsec_token": xsec_token
        }
        uri = "/api/sns/web/v1/feed"
        res = self.post_with_api(uri, params)

        if res.get('items'):
            return res["items"][0]["note_card"]

        # 爬取太频繁会出现没有数据返回的情况
        return {}
