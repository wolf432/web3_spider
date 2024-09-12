from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis

from config import settings

# 创建数据库引擎
database_echo = True if settings.DATABASE_ECHO == "True" else False
engine = create_engine(settings.DATABASE_URL, echo=database_echo, pool_size=10, max_overflow=20)

# 创建一个基础类
Base = declarative_base()

# 创建数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 获取数据库会话
def get_db():
    return SessionLocal()


def get_redis():
    return redis.Redis(host=settings.REDIS_URI, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)
