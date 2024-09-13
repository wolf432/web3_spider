from media_platform.twitter import TwitterCrawler
from database import get_db, get_redis

import re





r = get_redis()

x = TwitterCrawler(get_db(),r)

x.sync_user_info()

# c = x.get_content_by_name('Solana_zh',2)
# x.get_detail_content(1833614467487457374)


# x.sync_user_info()
# x.sync_cookie_pool(1)

# x.sync_content_by_name('jason_chen998')


# x.sync_following(1505829104737685505)

# data = x.get_detail_content(1746723714753008102)
# print(data['text'])
# x.sync_cookie_pool(2)
# while True:
#     try:
#         x.sync_user_info()
#     except exception.RateLimitError:
#         continue
#     except exception.NoData:
#         x.sync_cookie_pool(2)
#         continue
#     exit()
