import json

from sqlalchemy.orm import Session
from redis import Redis
from datetime import datetime

from models.xhs import XHSNote, XHSUser, XhsUserSnapshot
from tools.utils import to_dict, logger


class UserService:
    def __init__(self, db: Session, redis: Redis):
        self._db = db
        self._redis = redis
        self.cache_ex = 86400 * 14

    def get_by_page(self,page_number: int, page_size: int):
        try:
            # 获取记录的总数
            total_count = self.get_amount()

            # 根据总记录数和每页大小计算总页数
            total_pages = (total_count + page_size - 1) // page_size

            # 计算从哪一条数据开始获取
            offset_value = (page_number - 1) * page_size

            # 查询数据库，并使用limit和offset进行分页
            query = self._db.query(XHSUser).offset(offset_value).limit(page_size)
            data_list = query.all()

            return total_pages,data_list
        except Exception as e:
            logger.error(f'[xhs.user_service.get_by_page] 获取数据失败{e}')
            return 0, None

    def get_amount(self):
        """
        获取用户数量总数
        """
        return self._db.query(XHSUser).count()

    def add_user(self, fields: XHSUser):
        # 过虑小红薯开头的账号，名字都没改账号不可能有意义
        if fields.nickname.startswith('小红薯'):
            return True

        user_info = self.get_info_by_user_id(fields.user_id)
        if user_info:  # 如果存在则进行更新
            cache_key = self.get_cache_keys('get_info_by_user_id', fields.user_id)
            self._redis.delete(cache_key)

            # 更新 user_info 的字段
            for key, value in vars(fields).items():
                if key != "_sa_instance_state" and value is not None:  # 过滤掉 SQLAlchemy 内部属性
                    setattr(user_info, key, value)

        else:
            self._db.add(fields)
        self._db.commit()

    def add_snapshot(self,field: XhsUserSnapshot):
        self._db.add(field)
        self._db.commit()

    def get_info_by_user_id(self, user_id: str) -> XHSUser:
        cache_key = self.get_cache_keys('get_info_by_user_id', user_id)
        info: str = self._redis.get(cache_key)
        if info:
            info_json = json.loads(info)
            # 将字典中的 created_at 和 updated_at 字符串转换为 datetime 对象
            if 'created_at' in info_json:
                info_json['created_at'] = datetime.fromisoformat(info_json['created_at'])
            if 'updated_at':
                info_json['updated_at'] = datetime.fromisoformat(info_json['updated_at']) if info_json[
                                                                                                 'updated_at'] is not None else ""
            return XHSUser(**info_json)

        info: XHSUser = self._db.query(XHSUser).where(XHSUser.user_id == user_id).first()
        if info:
            json_str = json.dumps(to_dict(info))
            self._redis.set(cache_key, json_str, ex=self.cache_ex)
        return info

    @staticmethod
    def get_cache_keys(fun: str, key: str):
        return f'xhs_user_{fun}_{key}'


class NoteService:
    def __init__(self, db: Session, redis: Redis):
        self._db = db
        self._redis = redis
        self.cache_ex = 86400 * 14

    def add_note(self, field: XHSNote):
        note_info = self.get_info_by_note_id(field.note_id)
        if note_info:  # 如果存在则进行更新
            logger.debug(f'[xhs.service.add_note]更新笔记{field.note_id}')
            cache_key = self.get_cache_keys('get_info_by_note_id', field.note_id)
            self._redis.delete(cache_key)

            # 更新 user_info 的字段
            for key, value in vars(field).items():
                if key != "_sa_instance_state" and value is not None:  # 过滤掉 SQLAlchemy 内部属性
                    setattr(note_info, key, value)
        else:
            logger.debug(f'[xhs.service.add_note]新增笔记{field.note_id}')
            self._db.add(field)
        self._db.commit()

    def get_info_by_note_id(self, note_id: str) -> XHSNote:
        cache_key = self.get_cache_keys('get_info_by_note_id', note_id)
        info: str = self._redis.get(cache_key)
        if info:
            info_json = json.loads(info)
            # 将字典中的 created_at 和 updated_at 字符串转换为 datetime 对象
            if 'created_at' in info_json:
                info_json['created_at'] = datetime.fromisoformat(info_json['created_at'])
            if 'updated_at':
                info_json['updated_at'] = datetime.fromisoformat(info_json['updated_at']) if info_json[
                                                                                                 'updated_at'] is not None else ""
            return XHSNote(**info_json)

        info: XHSNote = self._db.query(XHSNote).where(XHSNote.note_id == note_id).first()
        if info:
            json_str = json.dumps(to_dict(info))
            self._redis.set(cache_key, json_str, ex=self.cache_ex)
        return info

    @staticmethod
    def get_cache_keys(fun: str, key: str):
        return f'xhs_note_{fun}_{key}'
