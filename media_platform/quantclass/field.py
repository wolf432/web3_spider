from pydantic import BaseModel, Field
from datetime import datetime


class QuantSummary(BaseModel):
    title: str = Field(..., description='标题')
    category_id: int = Field(..., description='分类id')
    created_at: datetime = Field(..., description="发布日期")
    summary: str = Field(..., description='摘要')
    id: int = Field(..., description='文章id')
    author_id: int = Field(..., description="作者id")
    view_count: int = Field(...,description='查看数量')
    vote_count: int = Field(...,description='葫芦数量')
    is_essence: int = Field(0, description='是否为精华帖')


class QuantArticle(BaseModel):
    id: int = Field(..., description='文章id')
    content: str = Field(..., description="文章内容")


class QuantCategory(BaseModel):
    id: int = Field(..., description='文章id')
    name: str = Field(...,description='分类名')
    pid:int = Field(0, description='父id')
    created_at: datetime = Field(..., description="添加日期")


class QuantUser(BaseModel):
    id: int = Field(..., description='用户id')
    user_name: str = Field(..., description='用户名')
    thread_count: int = Field(0, description='发布文章的数量')
    fans_count: int = Field(0, description='粉丝数量')
    created_at: datetime = Field(..., description="添加日期")