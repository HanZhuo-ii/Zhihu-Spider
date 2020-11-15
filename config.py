# - global -
DB_NAME = "知乎"

USE_REDIS = True    # 如果设置为False，后面的*_ADD_*_ID都将失效
REDIS_HOST = "192.168.100.101"
REDIS_PORT = 6379
REDIS_PASSWORD = None

MONGO_CONNECTION = "mongodb://localhost:27017/"
MONGO_DOC_LIMIT = 5000  # 每个文档最多存储5000条data

PROXIES_LIVE_TIME = 60
REQUEST_RETRY_TIMES = 5
SOCKET_DEFAULT_TIMEOUT = 20     # 整个request生命周期

"""
    这两个SET主要用于存储从其他数据包中提取出的question_id和answer_id
    后面的SET主要用于MongoDB的数据存储，以及Redis的Url队列
"""
TOPIC_ID_SET = "topic_ids"
QUESTION_ID_SET = "question_ids"
ANSWER_ID_SET = "answer_ids"
USER_ID_SET = "user_ids"

LOG_PATH = "E:/PycharmProjects/知乎/logs"     # 请使用绝对路径

# -- utils --
"""
    utils模块中的文件在此配置
"""
# --- topic ---
# 结果为question的列表，该参数控制是否将搜索出来的question_id添加到question_id集合中
# 如果想要获取这些question的具体信息，设置为True
TOPIC_ADD_QUESTIONS_ID = True
#  MongoDB, Redis集合名
TOPIC_SET = "话题"

# --- question ---
#  MongoDB, Redis集合名
QUESTION_SET = "提问"
# question获取某个提问下所有回答，QUESTION_GET_DETAIL控制是否将回答ID添加到Answer_id集合
QUESTION_ADD_ANSWER_ID = True
ANSWER_IMG_DIR = "E:/Data/知乎/img/answer"
DOWNLOAD_IMG = False

# --- comment ---
#  MongoDB, Redis集合名
COMMENT_SET = "评论"

# --- user ---
USER_SET = "用户"

# -- tools --
"""
    tools模块中的文件在此配置
"""
# --- key_words_search ---
# 搜索结果为question的列表，该参数控制是否将搜索出来的question_id添加到question_id集合中
# 如果想要获取这些question的具体信息，设置为True
KEY_WORDS_SEARCH_ADD_QUESTION_ID = True
KEY_WORDS_SEARCH_SET = "关键词搜索"
