from models.cookie_pool import CookiePool
from database import get_db
from tools.time import current_unixtime
from sqlalchemy import update

db = get_db()


def get_cookie_by_platform(platform: str, identity_type: int = 2):
    """
    获取指定平台可用的cookie
    :platform: 平台名
    :identity_type: 身份类型:1-游客,2-登录用户
    """
    now = current_unixtime()
    return db.query(CookiePool).where(CookiePool.platform == platform, CookiePool.identity_type == identity_type,
                                      CookiePool.expired >= now, CookiePool.use_status == 1).all()


def set_cookie_invalid(platform:str, ids: [int]):
    """
    修改数据位无效
    :param ids:
    :return:
    """
    stmt = update(CookiePool).values(use_status=2).where(CookiePool.id.in_(ids), CookiePool.platform == platform)
    db.execute(stmt)
    db.commit()
