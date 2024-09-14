from media_platform.twitter import TwitterCrawler
from database import get_db, get_redis
from ai_toolkit.help import model_client_factory, system_message, user_message
from ai_toolkit.prompt_manager import PromptManager

import re

con = """
镜月指针的内容
看到这套装备，有个不成熟的想法😂

𝘁𝗮𝗿𝗲𝘀𝗸𝘆的内容
看到很多自由职业的朋友，还在主动自费缴纳社保，感到悲痛惋惜。来分享一下我的观点：

🏥医保

1. 大部分缴纳医保的年轻人，从未真正使用过医保。

这是一个恶意的文字游戏，自费是自己掏钱，医保支付大部分情况下依然是自
"""

ai_client = model_client_factory('zhipu')

p = PromptManager()
prompts = p.get_prompt('filter_market_noise.md')
message_list = [
    system_message(prompts),
    user_message(con)
]
response = ai_client.chat(message_list,'GLM-4-Plus')
print(response.choices[0].message.content)
# r = get_redis()

# x = TwitterCrawler(get_db(),r)

# x.sync_user_info()

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
