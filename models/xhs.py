"""
抓取小红书所用的数据表
"""
from sqlalchemy import Column, Integer, String, BigInteger, JSON, Text, TIMESTAMP
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class XHSUser(Base):
    __tablename__ = 'xhs_users'
    __table_args__ = {'comment': '小红书博主'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增ID')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    nickname = Column(String(64), nullable=False, comment='用户昵称')
    location = Column(String(64), nullable=True, comment='所在地')
    desc = Column(Text, nullable=True, comment='用户描述')  # 注意: `desc` 是关键字，所以加了反引号
    fans = Column(BigInteger, default=0, nullable=True, comment='粉丝数')
    tag_list = Column(JSON, nullable=True, comment='标签列表')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=True, comment='创建时间')
    updated_at = Column(TIMESTAMP, onupdate=datetime.utcnow, nullable=True, comment='最后更新时间')


class XHSNote(Base):
    __tablename__ = 'xhs_note'
    __table_args__ = {'comment': '小红书笔记'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增ID')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    note_id = Column(String(64), nullable=False, comment='笔记ID')
    type = Column(String(16), nullable=True, comment='笔记类型(normal | video)')
    title = Column(String(255), nullable=True, comment='笔记标题')
    desc = Column(Text, nullable=True, comment='笔记描述')
    video_url = Column(Text, nullable=True, comment='视频地址')
    liked_count = Column(BigInteger, default=0, nullable=True, comment='笔记点赞数')
    collected_count = Column(BigInteger, default=0, nullable=True, comment='笔记收藏数')
    comment_count = Column(BigInteger, default=0, nullable=True, comment='笔记评论数')
    image_list = Column(JSON, nullable=True, comment='笔记封面图片列表')
    tag_list = Column(JSON, nullable=True, comment='标签列表')
    note_url = Column(String(255), nullable=True, comment='笔记详情页的URL')
    source_keyword = Column(String(255), default='', nullable=True, comment='搜索来源关键字')
    last_update_time = Column(TIMESTAMP, nullable=True, comment='最后更新时间')
    add_time = Column(TIMESTAMP, nullable=True, comment='发布时间')
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=True, comment='创建时间')
    updated_at = Column(TIMESTAMP, onupdate=datetime.utcnow, nullable=True, comment='最后更新时间')


class XhsUserSnapshot(Base):
    __tablename__ = "xhs_user_snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=True, comment='创建时间')
    user_id = Column(String(64), nullable=False, comment="用户ID")
    fans = Column(Integer, nullable=False, comment="粉丝数")
