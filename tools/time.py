import random
import time
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

from tools.utils import logger


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


def convert_timestamp_to_date(timestamp_ms: int, format = '%Y-%m-%d %H:%M:%S') -> str:
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
    return dt.strftime(format)


def timestamp_to_date(timestamp: int, format = '%Y-%m-%d %H:%M:%S') -> str:
    """
    将unix时间戳转换为格式为 “年 - 月 - 日” 的日期字符串

    :param timestamp: unix时间戳
    :return: 返回指定的时间格式
    """

    # Convert to a datetime object
    dt = datetime.fromtimestamp(timestamp)

    # Format the datetime object to "YYYY-MM-DD H:i:s"
    return dt.strftime(format)


def random_wait(start: int, end: int):
    """
    在一个区间内随机等待
    """
    sec = random.uniform(start, end)
    logger.debug(f'暂停{sec}秒执行')
    time.sleep(sec)


def get_time_within_duration(days_duration):
    """
    获取以指定时间为基础，指定天数范围内的时间区间。

    参数：
    days_duration：天数范围。

    返回：
    开始时间和结束时间
    """
    current_time = datetime.now()
    end_time = current_time - timedelta(days=days_duration)
    end_time_without_microseconds = end_time.replace(microsecond=0)
    return end_time_without_microseconds.strftime('%Y-%m-%d 00:00:00'), current_time.strftime('%Y-%m-%d 23:59:59')


def today_unix_time():
    # 获取当前时间
    now = datetime.now()
    # 获取当天 0 点时间
    today_zero = datetime(now.year, now.month, now.day)
    # 将 0 点时间转换为时间戳
    return int(time.mktime(today_zero.timetuple()))
