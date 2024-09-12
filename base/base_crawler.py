import re
from abc import ABC, abstractmethod
from typing import Dict

from playwright.async_api import BrowserContext, BrowserType


class AbstractCrawler(ABC):

    @abstractmethod
    async def launch_browser(self, chromium: BrowserType, playwright_proxy: Dict | None = None, user_agent: str | None = None,
                             headless: bool = True) -> BrowserContext:
        pass


class AbstractApiClient(ABC):
    @abstractmethod
    def request(self, method, url, **kwargs):
        pass