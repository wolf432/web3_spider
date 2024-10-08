# 说明

## 帖子接口

### 主页列表接口

没有做认证校验

https://bbs.quantclass.cn/api/threads.v2?page=1&perPage=10&filter[sticky]=0&filter[essence]=0&filter[attention]=0&filter[createdAtBegin]=&filter[createdAtEnd]=&filter[unread]=0&filter[sort]=2

### 帖子详情接口

有认证校验，没登录能获取部分数据

https://bbs.quantclass.cn/api/threads.detail.v2?pid=46354

## 分类接口

没有做认证校验

https://bbs.quantclass.cn/api/categories

## 用户接口

### 获取葫芦数量

#### 验证：不验证

#### 请求方法：GET

#### URL：https://bbs.quantclass.cn/api/68c14ce2jIVBexDq3r1BpvS720211215181559?id=43149

### 获取用户详情

#### 验证：不验证

#### 请求方法：GET

#### URL:https://bbs.quantclass.cn/api/users/43149

### 获取指定用户的所有帖子
https://bbs.quantclass.cn/api/threads?filter[isDeleted]=no&filter[isDisplay]=yes&filter[type]=0,1,2,3,4,6&sort=-createdAt&include=user,user.groups,firstPost,firstPost.images,firstPost.postGoods,category,threadVideo,threadAudio,question,question.beUser,question.beUser.groups&page[number]=11&page[limit]=10&filter[isApproved]=1&filter[userId]=43149&filter[isEssence]=0