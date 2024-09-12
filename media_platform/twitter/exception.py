# -*- coding: utf-8 -*-

class RateLimitError(Exception):
    """
    访问次数受限
    """
    pass


class TokenWaitError(Exception):
    """
    Token访问受限，等待刷新时间后再访问
    """
    pass


class TokenExpiredError(Exception):
    """
    Token过期，游客cookie会用到
    """
    pass


class AuthError(Exception):
    """
    认证失败
    """
    pass


class DataFetchError(Exception):
    """获取数据时发生错误"""
    pass


class NoData(Exception):
    """
    没有数据
    """
    pass


class DataUpdateError(Exception):
    """更新数据时发生错误"""
    pass


class DataAddError(Exception):
    """添加数据时发生错误"""
    pass


class APINOTFOUNDERROR(Exception):
    """获取api请求cookie错误"""
    pass
