from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, TIMESTAMP, JSON, SmallInteger, BigInteger, Text
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from tools.time import current_time


class Base(DeclarativeBase):
    pass


class XUser(Base):
    __tablename__ = "x_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    rest_id: Mapped[int] = mapped_column(BigInteger, default=0, nullable=True, comment="用户id")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户名@后面的")
    full_name: Mapped[str] = mapped_column(String(50), default='', nullable=True, comment="全名,主页上显示的名字")
    description: Mapped[str] = mapped_column(String(200), default='', nullable=True, comment="简介")
    x_created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, comment="账号创建日期")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=current_time, comment="创建时间")
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, onupdate=current_time,
                                                           comment="更新时间")
    followers_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True, comment="粉丝数")
    friends_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True, comment="关注数量")
    statuses_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True, comment="帖子数")
    is_monitored: Mapped[int] = mapped_column(Integer, default=1, nullable=True, comment="是否监控内容")


class CookiePool(Base):
    __tablename__ = "cookie_pool"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    value: Mapped[str] = mapped_column(JSON, nullable=False, comment="存储所需的cookie字段")
    identity_type: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1,
                                               comment="身份类型:1-游客,2-登录用户")
    amount: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=2000, comment="剩余次数，默认2000")
    expired: Mapped[Optional[int]] = mapped_column(Integer, default=1924790400, nullable=True,
                                                   comment="过期时间,默认算一个很大的值")
    use_status: Mapped[Optional[int]] = mapped_column(SmallInteger, default=1, nullable=True,
                                                      comment="使用状态:1-可用,2-不可用")


class TweetSummaries(Base):
    __tablename__ = "tweet_summaries"
    __table_args__ = (
        {"comment": "存储Twitter用户发表的内容概要信息"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="唯一标识符")
    content: Mapped[str] = mapped_column(String(280), nullable=False, comment="固定长度的内容")
    reply_count: Mapped[int] = mapped_column(Integer, default=0, comment="回复数")
    retweet_count: Mapped[int] = mapped_column(Integer, default=0, comment="转发数")
    like_count: Mapped[int] = mapped_column(Integer, default=0, comment="喜欢数")
    views_count: Mapped[int] = mapped_column(Integer, default=0, comment="查看数")
    x_created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=current_time,
                                                   comment="推特发表时间")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=current_time, comment="创建时间")
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, onupdate=current_time,
                                                           comment="更新时间")
    rest_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="帖子ID")
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="用户ID")


class TweetRaw(Base):
    __tablename__ = "tweet_raw"
    __table_args__ = (
        {"comment": "存储发布的原文"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="唯一标识符")
    content_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="引用tweet_summaries表中的内容ID")
    pid: Mapped[int] = mapped_column(BigInteger, default=0, comment="父内容ID，用于记录回复关系")
    raw_content: Mapped[str] = mapped_column(Text, nullable=False, comment="原文")


class WatchXUser(Base):
    __tablename__ = "watch_x_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    group_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="分组监控的名")
    user_ids: Mapped[str] = mapped_column(JSON, nullable=False, comment="分组里包含的用户id")
    ai_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="要使用的第三方AI大模型")
    ai_model: Mapped[str] = mapped_column(String(30), nullable=False, comment="要使用的AI模型名")
    ai_prompt: Mapped[str] = mapped_column(String(50), nullable=False, comment="要使用的提示词模版名")
    interval: Mapped[int] = mapped_column(Integer, nullable=False, comment="监控的间隔时间(分钟)")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=current_time, comment="创建时间")
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, onupdate=current_time,comment="更新时间")
    last_execution_time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True,comment="下次执行时间")
