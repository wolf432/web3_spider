from enum import Enum


class SearchNoteType(Enum):
    """search note type
    """
    # default
    ALL = 0
    # only video
    VIDEO = 1
    # only image
    IMAGE = 2


class SearchSortType(Enum):
    """
    搜索接口，排序类型
    """
    # default
    GENERAL = "general"
    # most popular
    MOST_POPULAR = "popularity_descending"
    # Latest
    LATEST = "time_descending"
