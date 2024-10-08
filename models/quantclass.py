from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, TIMESTAMP, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped
from tools.time import current_time


class Base(DeclarativeBase):
    pass


class QtcArticleContent(Base):
    __tablename__ = "qtc_article_content"

    aid: Mapped[int] = Column(Integer, nullable=False, primary_key=True, comment="文章ID")
    content: Mapped[str] = Column(Text, nullable=False, comment="文章内容")


class QtcArticleSummary(Base):
    __tablename__ = "qtc_article_summary"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    title: Mapped[str] = Column(String(300), nullable=False, comment="标题")
    tags: Mapped[str] = Column(String(500), nullable=True, default='', comment="标签")
    category_id: Mapped[int] = Column(Integer, nullable=False, comment="分类ID")
    summary: Mapped[str] = Column(String(1000), nullable=False, comment="简介")
    aid: Mapped[int] = Column(Integer, nullable=False, comment="文章ID")
    author_id: Mapped[int] = Column(Integer, nullable=False, comment="作者ID")
    fetch: Mapped[int] = Column(Integer, nullable=True, default=1, comment="1-没抓取内容,2-抓取内容")
    view_count: Mapped[Optional[int]] = Column(Integer, nullable=True, default=0, comment="查看数")
    vote_count: Mapped[Optional[int]] = Column(Integer, nullable=True, default=0, comment="投票数")
    is_essence: Mapped[Optional[int]] = Column(Integer, nullable=True, default=1, comment="是否为加精文章, 1-否，2-是")
    created_at: Mapped[Optional[datetime]] = Column(TIMESTAMP, nullable=True, default=current_time, comment="创建时间")
    updated_at: Mapped[Optional[datetime]] = Column(TIMESTAMP, nullable=True, onupdate=current_time, comment="更新时间")
    add_time: Mapped[Optional[datetime]] = Column(TIMESTAMP, nullable=True, comment="文章发布时间")


class QtcCategories(Base):
    __tablename__ = "qtc_categories"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name: Mapped[str] = Column(String(30), nullable=False, comment="分类名称")
    pid: Mapped[Optional[int]] = Column(Integer, nullable=True, default=0, comment="父分类ID")
    created_at: Mapped[Optional[datetime]] = Column(TIMESTAMP, nullable=True, default=current_time, comment="创建时间")
