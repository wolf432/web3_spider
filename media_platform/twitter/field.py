from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class Request_Limit(BaseModel):
    limit_remaining: int = Field(..., description='访问剩余次数')
    rate_limit_reset: int = Field(..., description='刷新时间')


class UserInfo(Request_Limit):
    rest_id: int = Field(..., description="用户的id")
    name: str = Field(..., description="用户名，twitter主页显示的")
    followers_count: int = Field(..., description="关注者数量")
    friends_count: int = Field(..., description="关注的人数")
    statuses_count: int = Field(..., description="发帖数量")
    description: str = Field(..., description="描述")
    x_created_at: datetime = Field(..., description="twitter注册日期")
    full_name: str = Field(..., description="主页显示的名字")
    mark: str | None = Field(None, description="账号备注")

class Content(Request_Limit):
    entry_type: int = Field(..., description='1-原文,2-转发贴')
    content: str = Field(..., description="twitter内容")
    id: str = Field(..., description="帖子id")


class CookieIdentity(Enum):
    """
    Cookie池里的身份字段
    """
    GUEST = 1  # 游客
    USER = 2  # 登录用户
