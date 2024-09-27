import os
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from config import settings

# 获取当前脚本所在目录的绝对路径，然后找到项目根目录（假设当前脚本位于项目的子目录中）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def init_loging_config(level):
    _logger = logging.getLogger("web3_spider")
    _logger.setLevel(level)

    # 判断日志路径不存在则创建
    log_dir = os.path.join(project_root, 'logs')
    log_file = os.path.join(log_dir, 'spider.log')

    # 判断日志文件目录是否存在，如果不存在则创建
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 检查日志文件是否存在，不存在的话创建（直接写入日志会自动创建文件，这里是手动检查）
    if not os.path.exists(log_file):
        open(log_file, 'w').close()  # 创建一个空的日志文件

    # 创建一个处理器，按照星期分割日志
    # when='W0': 表示每周一分割日志文件。
    # interval=1: 表示每 1 周分割一次日志。
    # backupCount=4: 表示最多保留 4 个备份的日志文件，超过后旧日志将被删除。
    handler = TimedRotatingFileHandler(log_file, when='W0', interval=1, backupCount=4)
    handler.setLevel(level)

    # 设置格式化器
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s (%(filename)s:%(lineno)d) - %(message)s')
    handler.setFormatter(formatter)

    # 添加一个控制台处理器以便在控制台中也能看到日志输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    _logger.addHandler(handler)

    return _logger


leve_map = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'error': logging.ERROR,
    'warning': logging.WARNING
}

logger = init_loging_config(leve_map.get(settings.LOG_LEVEL, logging.INFO))


def to_dict(obj):
    """
    将SQLAlchemy对象转换为字典
    """
    data = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()  # 将 datetime 对象转换为 ISO 8601 字符串
        data[column.name] = value
    return data