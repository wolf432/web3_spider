import random
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


from datetime import datetime


def convert_timestamp_to_date(timestamp_ms: int) -> str:
    """
    将毫秒级时间戳转换为格式为 “年 - 月 - 日” 的日期字符串

    :param timestamp_ms: 毫秒级时间戳
    :return: A string representing the date in  YYYY-MM-DD HH:MM:SS format
    """
    # Convert milliseconds to seconds
    timestamp_s = timestamp_ms / 1000

    # Convert to a datetime object
    dt = datetime.fromtimestamp(timestamp_s)

    # Format the datetime object to "YYYY-MM-DD H:i:s"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def random_wait(start: int, end: int):
    """
    在一个区间内随机等待
    """
    sec = random.uniform(start, end)
    time.sleep(sec)
