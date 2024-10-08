import requests

from sqlalchemy.orm import Session
from redis import Redis

from base.base_crawler import AbstractApiClient
from tools.time import get_time_within_duration
from media_platform.quantclass.exception import DataFetchError,AUTHENError
from tools import utils


class QuantClassClient(AbstractApiClient):
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
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            "Referer": "https://bbs.quantclass.cn",
            "Content-Type": "application/json;charset=UTF-8"
        }

    def request(self, method, url, **kwargs):
        """
        GET、POST统一请求方法，根据http状态码会抛出异常
        :param method: GET或POST方法
        :param url: 请求url
        :param kwargs: 参数
        :return:
        """
        response = None
        headers = self._headers
        if kwargs.get('headers'):
            headers.update(kwargs['headers'])

        kwargs['headers'] = headers

        if method == "GET":
            response = requests.request(method, url, **kwargs)
        elif method == "POST":
            response = requests.request(method, url, **kwargs)

        if response.status_code == 200:
            return response

        utils.logger.warning(f'[quantclass.client.request]请求异常,状态码={response.status_code},body={response.text}')

        if response.status_code == 401:
            raise AUTHENError("没登录")

    def api_get_article_list(self, page: int = 1, pre_page: int = 20, category_id: int = 0, essence: int = 0,
                             days: int = 0):
        """
        获取文章列表数据
        :page: 页数
        :pre_page: 每页数量,最大50条
        :category_id: 分类id
        :essence: 是否搜索加精文章
        :days: 查询几天内的数据
        """
        url = f"https://bbs.quantclass.cn/api/threads.v2?page={page}&perPage={pre_page}&filter[sticky]=0&filter[essence]={essence}&filter[attention]=0&filter[createdAtBegin]=&filter[createdAtEnd]=&filter[unread]=0&filter[sort]=2"
        if category_id > 0:
            url += f'&filter[categoryids][0]={category_id}'
        if days > 0:
            start_time, end_time = get_time_within_duration(days)
            url += f'&filter[createdAtBegin]={start_time}&filter[createdAtEnd]={end_time}'
        response = self.request('GET', url)
        try:
            result = response.json()
            if result['Code'] != 0:
                raise DataFetchError(f"[quantclass.client.api_get_article_list]获取数据失败。{result['Message']}")
            return result['Data']
        except Exception as e:
            raise DataFetchError(f"[quantclass.client.api_get_article_list]获取数据失败。{e}")

    def api_get_article_detail(self, article_id: int = 0, headers=None):
        """
        获取文章详情
        :article_id: 文章id
        :headers: 头的认证信息
        """
        url = f"https://bbs.quantclass.cn/api/threads.detail.v2?pid={article_id}"
        response = self.request('GET', url, headers=headers)
        try:
            result = response.json()
            if result['Code'] != 0:
                raise DataFetchError(f"[quantclass.client.api_get_article_detail]获取数据失败。{result['Message']}")
            return result['Data']
        except Exception as e:
            raise DataFetchError(f"[quantclass.client.api_get_article_detail]获取数据失败。{e}")

    def api_get_categories(self):
        """
        获取所有分类数据
        """
        url = f"https://bbs.quantclass.cn/api/categories"
        response = self.request('GET', url)
        try:
            result = response.json()
            return result['data']
        except Exception as e:
            raise DataFetchError(f"[quantclass.client.api_get_categories]获取数据失败。{e}")

    def api_is_login(self,headers:dict):
        url = 'https://bbs.quantclass.cn/api/wallet/cash?filter%5Buser%5D=96&filter%5Bstart_time%5D=2024-10-01-00-00-00&filter%5Bend_time%5D=2024-10-31-23-59-59'
        response = self.request('GET', url, headers=headers)
