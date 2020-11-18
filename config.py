# - global -
DB_NAME = "知乎"  # MongoDB 数据库名称
THREAD_ID = 1   # 每个线程单独使用一个代理，防止并发量过大造成代理无法连接

# Mail
MAIL_HOST = 'smtp.163.com'              # 邮箱服务器地址
MAIL_USER = '163用户名'                  # 163用户名
MAIL_PASSWD = '密码(部分邮箱为授权码)'      # 密码(部分邮箱为授权码)
MAIL_SENDER = '邮件发送方邮箱地址'          # 邮件发送方邮箱地址
MAIL_RECEIVERS = ['收件地址']

# Redis
USE_REDIS = True    # 如果设置为False，后面的*_ADD_*_ID将不会添加，
REDIS_HOST = "192.168.100.101"  # Redis Host
REDIS_PORT = 6379               # Redis Port
REDIS_PASSWORD = None           # Redis Password
"""
    这两个SET主要用于存储从其他数据包中提取出的question_id和answer_id
"""
TOPIC_ID_SET = "topic_ids"
QUESTION_ID_SET = "question_ids"

"""
    后面的SET主要用于MongoDB的数据存储，以及Redis的Url队列
"""
ANSWER_ID_SET = "answer_ids"
USER_ID_SET = "user_ids"

# MongoDB Config
MONGO_CONNECTION = "mongodb://localhost:27017/"
MONGO_DOC_LIMIT = 5000  # 每个文档最多存储5000条data, 否则会造成索引过慢

# 代理与网络请求部分
USE_PROXIES = True
PROXIES_API = "代理API"
PROXIES_LIVE_TIME = 60
REQUEST_RETRY_TIMES = 5
SOCKET_DEFAULT_TIMEOUT = 20     # 整个request生命周期

# 日志路径，请使用绝对路径
LOG_PATH = "E:/PycharmProjects/知乎/logs"

# -- utils --
"""
    utils模块中的文件在此配置
"""

# --- topic ---
# 结果为每个话题下的question，该参数控制是否将搜索出来的question_id添加到question_id集合中
# 如果想要获取这些question的具体回答信息，设置为True
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
# Redis，MongoDB的集合名称
KEY_WORDS_SEARCH_SET = "关键词搜索"
