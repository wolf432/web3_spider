import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_URL_TEST: str = os.getenv("DATABASE_URL_TEST")
    DATABASE_ECHO: str = os.getenv("DATABASE_ECHO")
    WEB3_ENV: str = os.getenv("WEB3_ENV")
    REDIS_URI: str = os.getenv("REDIS_URI")
    REDIS_PORT: int = os.getenv("REDIS_PORT")
    REDIS_DB: int = os.getenv("REDIS_DB")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL")


settings = Settings()
