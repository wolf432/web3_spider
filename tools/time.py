import time
from datetime import datetime
from zoneinfo import ZoneInfo


def current_time():
    """
    返回东八区的当前时间
    :return: 当前时间，时区为 Asia/Shanghai
    """
    CST = ZoneInfo('Asia/Shanghai')
    return datetime.now(CST)


def format_datetime(dt: datetime | None) -> str:
    """
    把datetime类型转换为字符串类型
    :param dt:
    :return:
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ''


def current_unixtime():
    """
    获取当前unixtime时间戳的时间
    :return:
    """
    return int(time.time())


def convert_to_ymd(date_str: str) -> str:
    """
    将Twitter日期字符串转换为'年-月-日'格式的日期字符串。

    :param date_str: 输入的日期字符串，如 "Tue Apr 17 00:56:17 +0000 2012"
    :return: 转换后的日期字符串，格式为'年-月-日'
    """
    # 转换为datetime对象
    date_obj = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")

    # 转换为目标时区
    local_date_obj = date_obj.astimezone(ZoneInfo('Asia/Shanghai'))

    # 格式化为 年-月-日 小时:分钟:秒
    formatted_date = local_date_obj.strftime("%Y-%m-%d %H:%M:%S")

    return formatted_date
