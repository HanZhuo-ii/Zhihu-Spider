# 知乎全站爬虫
# Zhihu-Spider
 
> 最初版本功能可能不够完善，欢迎提Issues

**utils和tools中的每个.py文件可作为单独程序运行**

**建议在 MongoDB + Redis 环境下运行**


## 知乎项目结构：

config.py 配置文件

main.py 调度所有模块实现全站爬虫

### frame  框架

&nbsp; &nbsp; SpyderFrame.py 通用爬虫框架

### logs 日志

### tools  工具

&nbsp; &nbsp; KeyWordsSearch.py 关键词搜索

&nbsp; &nbsp; HotList.py 热榜监控爬虫，爬知乎每日热榜，可添加定时任务实现热榜监控功能

### utils
&nbsp; &nbsp; topic.py 知乎话题爬虫，爬某个话题下所有question的信息

&nbsp; &nbsp; question.py 知乎回答爬虫，爬某个提问下面全部的回答以及回答的详细信息

&nbsp; &nbsp; comment.py 知乎评论爬虫，爬某个回答下面所有评论

&nbsp; &nbsp; wiki_box.py（Coding） 知乎百科数据，知乎某些question被收录进知乎百科里，这里仅保留百科词条，question具体信息有专门处理的文件（utils/question.py）

&nbsp; &nbsp; user.py 知乎用户信息爬虫

```shell
pip install -r requirements.txt
```

## 详解
### config.py 自定义配置文件

``` python

# - global -
DB_NAME = "知乎"  # MongoDB 数据库名称
THREAD_ID = 1   # 每个线程单独使用一个代理，防止并发量过大造成代理无法连接

# Mail
MAIL_HOST = 'smtp.163.com'              # 邮箱服务器地址
MAIL_USER = '*@163.com'         # 163用户名
MAIL_PASSWD = 'password'        # 密码(部分邮箱为授权码)
MAIL_SENDER = '*@163.com'       # 邮件发送方邮箱地址
MAIL_RECEIVERS = ['*@outlook.com']     # 邮件接受方邮箱地址，注意需要[]包裹，这意味着你

# Redis
USE_REDIS = True    # 如果设置为False，后面的*_ADD_*_ID将不会添加，
REDIS_HOST = "127.0.0.1"  # Redis Host
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
MONGO_DOC_LIMIT = 1000  # 每个文档最多存储5000条data, 否则会造成索引过慢

# 代理与网络请求部分
USE_PROXIES = True		# 是否使用代理
PROXIES_API = "代理API"	# 代理API，请在SpiderFrame中修改代理获取规则
PROXIES_LIVE_TIME = 60	# 代理默认存活时间，单位（秒）
REQUEST_RETRY_TIMES = 5	# requests请求允许失败的次数，超过限制后抛出RetryError
SOCKET_DEFAULT_TIMEOUT = 20     # 整个request生命周期

# 日志路径，请使用绝对路径
LOG_PATH = "/home/zhihu/logs"

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
ANSWER_IMG_DIR = "/home/zhihu/img/answer"	# 回答的图片下载路径
DOWNLOAD_IMG = False			# 是否下载图片

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
```

### main.py 主文件
全站爬虫的主调度函数，此函数主要分为五个功能模块和一个调度模块

#### 功能模块
TopicSpider：话题爬虫，负责调度爬虫根据topicID爬取不同话题下的提问信息

QuestionSpider：提问爬虫，负责调度爬虫根据questionID爬取不同提问下的回答信息

CommentSpider：评论爬虫，负责调度爬虫根据answerID爬取不同回答下的评论信息

UserSpider：用户信息爬虫

RecoverErrorID：爬虫运行过程中会产生一些错误，这些错误引发爬虫中断，导致部分信息没有爬完就提前终止，此模块可以将异常的ID进行回收

#### 调度模块
running：多线程爬虫与监控
	多个模块同时进行爬取，首先按照顺序启动线程（不按照顺序可能导致其他模块无可用ID）
	然后启动监控，如果 爬虫死掉 and （爬虫异常退出 or ID还未爬完）
	如果四个模块都正常退出，则爬虫结束，running也退

### frame.SpiderFrame.py 爬虫框架
>     @version: v0.3 dev
>     @desc: 通用爬虫框架
>     @update_log: v0.1 初始架构Proxies代理模块、UrlManager、HtmlDownloader、HtmlParser、DataSaver
>                  v0.2 加入MongoDB存储功能，支持MongoDB自增ID
>                  v0.3 加入Redis支持，UrlManager使用Redis运行大型项目可以断点续爬，DataSaver使用Redis解决硬盘I/O低影响爬虫速度

#### class exception
> 自定义异常

RequestRetryError：同一URL连续多次请求失败

UserNotExist：知乎用户已注销

UrlEmptyException：requests的URL为空

NumInfoLengthException

UnexpectedError：意料之外的异常

ProxiesPoolNull：代理用尽

TooManyErrorsInJsonLoad：尝试了过多次错误的Json解析

#### def custom_logger() 
> logging日志

#### class Proxies(Thread) 
> 多线程代理

支持代理随时切换，同一个THREAD_ID（在config.py中配置）仅会开启一个代理
运行时会自动监测代理是否过期
#### class UrlManager(object) 
> Url管理, 单个UrlManager对象控制单个队列

        """支持Redis队列解决断点续爬功能，需指定参数use_redis=True
        :param db_set_name str Redis队列数据库名，默认为空
        """
```python
def add_url(self, url: str) -> None
# 定义插入url方法
```

```python
def get(self, db_set_name="") -> str
# 从队列头部提取url
```

#### class HtmlDownloader(Thread)
> 页面资源下载

```python
def download(self, url: str, params=None) -> str
# 通用下载函数，包含各种异常处理
```

```python
def img_download(self, dir_path: str, url: str) -> None
# 图片下载器
```

#### class HtmlParser(object)
> html解析，需要重写

#### class DataSaver(Thread)
> 数据存储器

        """若要使用Redis缓存数据，指定参数use_redis=True 使用MongoDB自增ID，指定use_auto_increase_index=True
        :param db_name: str 可选 要存储的MongoDB数据库名称
        :param set_name: str 可选 要存储的MongoDB集合名
        :func run: 采用run同步Redis与Mongo数据
        """
```python
def to_csv(data: list, file_name: str, encoding: str = "utf-8") -> None
        """存储到CSV
        :param data: dict in list 数据集
        :param file_name: str 文件路径
        :param encoding: default "utf-8"
        """
```

```python
def mongo_insert(self, data_dict: dict) -> None
        """向MongoDB直接插入数据，不经过Redis缓存
        :param data_dict: dict 数据集合
        """
```

```python
def run(self)
		"""Redis缓存数据同步到MongoDB, 请在主程序结束后调用本对象的__exit__方法结束该线程"""
```

### frame.mail.py 邮件提醒
> 爬虫出现异常后，自动发送邮件提醒

```python
def send_mail(content)
```

### tools.HotList.py 知乎热榜
> 知乎热榜监控（全站）

```python
class HTMLParser(SpiderFrame.HtmlParser)
```

```python
def get_hot_list(get_detail=False) -> None
		"""获取热榜数据"""
```

### tools.KeyWordsSearch.py 关键词搜索
> 关键词搜索，可以将关键词搜索的简略信息存储，也支持将搜索到的结果添加到ID队列，以便于获取详细信息

```python
class HTMLParser(SpiderFrame.HtmlParser)
		# 页面解析
```

```python
def search(keyword)
		# 搜索
```


### utils.topic.py 话题爬虫
> 爬某个话题ID下面的所有提问及相关信息

"""
    @author         满目皆星河
    @creat_date     2020/11/09
    @update_data    2020/11/09
    @desc           话题爬虫，许多question归属于某类话题，爬取这些question的信息（以等待回答为基础）
    @main_function  spider(question_id: str)
"""

#### def parse_base_topic_info(html: str)
> 解析话题基本信息，例如话题的关注者、提问数、浏览量等数据

#### def spider(topic_id: str)
> 话题爬虫
> 
	在爬虫运行过程中，会利用UrlManager记录url的值，可以在爬虫异常终端时接着上一次爬

	首先获取话题基本信息，然后在redis中查询该话题是否已经爬过，如果已经爬过，将redis中的纪录值复制给url参数，继续爬取，否则重新开始。为了保证MongoDB性能，在config.py中设计了MONGO_DOC_LIMIT参数，限制每一个集合中数据条数，默认为5000条。
```python
def spider(topic_id: str) -> None
```

### utils.question.py 提问爬虫
> 爬某个提问ID下面的所有回答及相关信息

"""
    @author         满目皆星河
    @creat_date     2020/10/06
    @update_data    2020/10/06
    @desc           知乎回答爬虫，爬某个提问下面全部的回答以及回答的详细信息, 存入MongoDB.知乎.questions
    @main_function  spider(question_id: str)
"""

底层逻辑与前者相同
```python
def spider(question_id: str) -> None
```

### utils.comment.py 评论爬虫
> 爬某个回答ID下面的所有评论及相关信息

底层逻辑与前者相同
```python
def spider(answer_id: str) -> None
```

### utils.user.py 用户爬虫
> 根据用户ID爬用户信息

"""
    @Author      : 满目皆星河
    @Project     : 知乎
    @File        : user.py
    @Time        : 2020/11/12 18:21
    @Description : 知乎用户信息爬虫
    @Warning     : 请务必在外部函数控制user.html_downloader.proxies.__exit__()来关闭代理，否则代理耗尽
"""

## 运行情况
