from __future__ import annotations
from typing import Optional
from sqlalchemy import JSON, String, Integer, TIMESTAMP, BigInteger, SmallInteger
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from datetime import datetime


class Base(DeclarativeBase):
    pass


class CookiePool(Base):
    __tablename__ = "cookie_pool"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    value: Mapped[dict] = mapped_column(JSON, nullable=False, comment="存储所需的cookie字段")
    identity_type: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1,
                                               comment="身份类型:1-游客,2-登录用户")
    expired: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=1924790400,
                                                   comment="过期时间,默认算一个很大的值")
    use_status: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True, default=1,
                                                      comment="使用状态:1-可用,2-不可用")
    platform: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default='', comment="平台名")
    amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=2000,
                                                  comment="剩余次数，guest是每30分钟2000次")
