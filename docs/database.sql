create table cookie_pool
(
    id            int auto_increment
        primary key,
    value         json                       not null comment '存储所需的cookie字段',
    identity_type tinyint default 1          not null comment '身份类型:1-游客,2-登录用户',
    expired       int     default 1924790400 null comment '过期时间,默认算一个很大的值',
    use_status    tinyint default 1          null comment '使用状态:1-可用,2-不可用',
    amount        int     default 2000       null comment '剩余次数，guest是每30分钟2000次'
)
    comment 'pool池' charset = utf8mb4 collate = utf8mb4_general_ci;

create table tweet_raw
(
    id          bigint auto_increment comment '唯一标识符'
        primary key,
    content_id  bigint           not null comment '引用tweet_summaries表中的内容ID',
    pid         bigint default 0 null comment '父内容ID，用于记录回复关系',
    raw_content text             not null comment '原文'
)
    comment '存储发布的原文' charset = utf8mb4 collate = utf8mb4_general_ci;

create table tweet_summaries
(
    id            bigint auto_increment comment '唯一标识符'
        primary key,
    content       varchar(280)                        not null comment '固定长度的内容',
    reply_count   int       default 0                 null comment '回复数',
    retweet_count int       default 0                 null comment '转发数',
    like_count    int       default 0                 null comment '喜欢数',
    views_count   int       default 0                 null comment '查看数',
    x_created_at  timestamp default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP comment '推特文章发表时间',
    created_at    timestamp default CURRENT_TIMESTAMP null comment '发表时间',
    updated_at    timestamp default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP comment '最后更新时间',
    rest_id       bigint                              not null comment '用户ID',
    user_id       bigint                              not null
)
    comment '存储Twitter用户发表的内容概要信息' charset = utf8mb4 collate = utf8mb4_general_ci;

create index rest_id
    on tweet_summaries (rest_id)
    comment '用户ID索引，创建索引以加速查询';

create index user_id
    on tweet_summaries (user_id);

create table x_users
(
    id              int auto_increment
        primary key,
    rest_id         varchar(50)   default ''                null comment '用户id',
    name            varchar(50)                             not null comment '用户名@后面的',
    full_name       varchar(50)   default ''                null comment '全名,主页上显示的名字',
    description     varchar(1000) default ''                null comment '简介',
    x_created_at    datetime                                null comment '账号创建日期',
    created_at      datetime      default CURRENT_TIMESTAMP null,
    updated_at      datetime      default (now())           null on update CURRENT_TIMESTAMP,
    followers_count int           default 0                 null comment '粉丝数',
    friends_count   int           default 0                 null comment '关注数量',
    statuses_count  int           default 0                 null comment '帖子数'
)
    comment '推特的用户表' charset = utf8mb4 collate = utf8mb4_general_ci;

