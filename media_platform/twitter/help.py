from playwright.sync_api import sync_playwright
import re

def get_headers():
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.3",
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
    }


def get_guest_cookie(user_agent: str):
    """
    获取游客cookie
    :param user_agent: header的浏览器代理设置，不设置会获取不到
    :return:
    """
    cookies = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(timeout=15000)
        context = browser.new_context(
            user_agent=user_agent
        )

        # 创建新的页面
        page = context.new_page()
        # 访问 Twitter 页面
        page.goto("https://x.com")
        # 获取指定的cookie值
        fields = ["guest_id", "gt", "guest_id_marketing"]
        for val in page.context.cookies():
            if val["name"] in fields:
                # 转换过期时间
                expired = int(val["expires"])
                # 只保留domain为x.com
                if val["domain"] != ".x.com":
                    continue
                cookies.update({
                    val["name"]: val["value"]
                })
        browser.close()
    return {"cookies": cookies, "expired": expired}


def get_header_by_guest(cookie):
    _headers = get_headers()
    _headers['x-guest-token'] = cookie.get('gt', '')
    _headers['cookie'] = (
        f"guest_id={cookie.get('guest_id', '')};"
        f"gt={cookie.get('gt', '')};"
    )
    return _headers


def get_user_cookie(cookie):
    auth_token = cookie.get('auth_token', '')
    cto = cookie.get('cto', '')
    _headers = get_headers()
    _headers["cookie"] = f'auth_token={auth_token};ct0={cto}'
    _headers["x-csrf-token"] = cto
    return _headers


def extract_value_from_url(url):
    """
    从url提取api接口名
    :return:
    """
    pattern = r'graphql/.*?/(.*?)\?'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        return None
