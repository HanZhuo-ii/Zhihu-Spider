"""
    @version: v0.3 dev
    @desc: 通用爬虫框架
    @update_log: v0.1 初始架构Proxies代理模块、UrlManager、HtmlDownloader、HtmlParser、DataSaver
                 v0.2 加入MongoDB存储功能，支持MongoDB自增ID
                 v0.3 加入Redis支持，UrlManager使用Redis运行大型项目可以断点续爬，DataSaver使用Redis解决硬盘I/O低影响爬虫速度
"""
import threading
import pandas as pd
import requests
import redis
import socket
import logging
import time
import config
from os import path

redis = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD)


class exception(Exception):
    class UserNotExist(Exception):
        def __init__(self):
            super().__init__()

        def __str__(self):
            return "用户账户已注销"

    class UrlEmptyException(Exception):
        def __init__(self):
            super().__init__()

        def __str__(self):
            return "Url is Empty"

    class NumInfoLengthException(Exception):
        def __init__(self):
            super().__init__()

        def __str__(self):
            return "Get info error: length of number of info is too short."

    class UnexpectedError(Exception):
        def __init__(self):
            super().__init__()

        def __str__(self):
            return "SOME FATAL ERROR HAS BEEN ACCORDED! "


def custom_logger(__name__):
    # 创建log
    log = logging.getLogger()
    log.setLevel(logging.INFO)  # Log等级总开关

    # 创建handler，用于写入日志文件
    log_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    log_file = path.join(config.LOG_PATH, log_time + '.log')

    logging_file_handler = logging.FileHandler(log_file, mode='a+')
    logging_stream_handler = logging.StreamHandler()
    logging_file_handler.setLevel(logging.WARNING)  # 输出到file的log等级的开关
    logging_stream_handler.setLevel(logging.INFO)  # 输出到控制台log等级开关

    # 定义handler输出格式
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s, line %(lineno)d, in %(funcName)s: %(message)s")
    logging_file_handler.setFormatter(formatter)
    logging_stream_handler.setFormatter(formatter)

    # 将log添加handler里
    log.addHandler(logging_file_handler)
    log.addHandler(logging_stream_handler)
    return log


logger = custom_logger("Base")


# 代理线程
class Proxies(threading.Thread):

    def __init__(self):
        super().__init__()
        # 线程运行标志
        self.__thread__flag = True
        self.get_proxies_api = "http://api.xdaili.cn/xdaili-api/greatRecharge/getGreatIp?spiderId" \
                               "=192b9425f13c47ffbbe4a663c974608b&orderno=YZ2020219595449Wzor&returnType=2&count=1 "
        self.Proxies = {
            "http": "",
            "https": ""
        }

    # 结束线程
    def __exit__(self):
        logger.info("Exit Proxies with code 0")
        self.__thread__flag = False

    # 如果代理失效，通知进程主动更新代理
    def get_proxies(self):
        i = 0
        for i in range(config.REQUEST_RETRY_TIMES):
            res = requests.get(self.get_proxies_api)
            j = eval(res.text)
            if j['ERRORCODE'] == '0':
                self.Proxies['http'] = "http://" + j['RESULT'][0]['ip'] + ":" + j['RESULT'][0]['port']
                self.Proxies['https'] = "http://" + j['RESULT'][0]['ip'] + ":" + j['RESULT'][0]['port']
                logger.info("Successfully get proxies")
                return
            logger.warning("Failed, " + str(i + 1) + " times get proxies...")
            time.sleep(5)
        if i == 4:
            logger.critical("Get proxies failed, exit program...")

    # 监测代理时间。如果超时更新代理
    def run(self) -> None:
        start_time = time.time()
        while self.__thread__flag:
            # 设置代理生存时间为60s
            if start_time - time.time() > config.PROXIES_LIVE_TIME:
                logger.warning("proxies failure, get new one")
                # 重设代理使用时长
                start_time = time.time()
                self.get_proxies()
            time.sleep(3)


class UrlManager(object):
    """url管理, 单个UrlManager对象控制单个队列"""

    # 初始化url池
    def __init__(self, db_set_name='', use_redis=False):
        """支持Redis队列解决断点续爬功能，需指定参数use_redis=True
        :param db_set_name str Redis队列数据库名，默认为空
        """
        self.use_redis = use_redis
        self.db_set_name = db_set_name

        if not use_redis:
            self.url_list = []
            self.url_set = set()
            logger.info("Init UrlManager, use_redis=False")
        else:
            logger.info("Init UrlManager, use_redis=True, db_set_name=" + db_set_name)

    # 定义插入url方法
    def add_url(self, url: str) -> None:
        if not self.use_redis:
            if url not in self.url_set:
                self.url_set.add(url)
                self.url_list.append(url)
        elif redis.sadd("set_" + self.db_set_name, url):  # 如果插入成功，会返回数据量
            redis.rpush("list_" + self.db_set_name, url)  # 列表尾部插入

    @staticmethod
    def add_id(id_set: str, _id: str):
        if type(_id) == int:
            _id = str(_id)
        if redis.sadd("set_" + id_set, _id):
            redis.rpush("list_" + id_set, _id)

    def force_add_url(self, url: str) -> None:
        if not self.use_redis:
            self.url_list.append(url)
        else:
            redis.rpush("list_" + self.db_set_name, url)  # 列表尾部插入

    # 从队列头部提取url
    def get(self) -> str:
        if not self.list_not_null():
            raise exception.UrlEmptyException
        if not self.use_redis:
            return self.url_list.pop(0)
        return redis.lpop("list_" + self.db_set_name).decode("utf-8")  # 列表头部pop

    # 队列还有URL吗
    def list_not_null(self, set_name=None) -> bool:
        if set_name is None:
            set_name = self.db_set_name
        if not self.use_redis and len(self.url_list):
            return True
        elif redis.llen("list_" + set_name) != 0:
            return True
        return False


# 页面资源下载
class HtmlDownloader(threading.Thread):

    def __init__(self):
        """:param None"""
        # 实例化Proxies类
        super().__init__()
        self.proxies = Proxies()
        # 启动代理线程
        self.proxies.start()
        # 默认请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/85.0.4183.102 Safari/537.36 Edg/85.0.564.51 "
        }
        socket.setdefaulttimeout(config.SOCKET_DEFAULT_TIMEOUT)  # 设置超时

    def download(self, url: str, params=None) -> str:
        if url == "":
            raise exception.UrlEmptyException
        res = ''  # 没啥用，消除警告而已
        if params is None:
            params = {}
        for i in range(config.REQUEST_RETRY_TIMES):
            try:
                res = requests.get(url, params=params, headers=self.headers, proxies=self.proxies.Proxies,
                                   timeout=3)
                if res.status_code == 200:
                    return res.text
                # 非200，更换代理，抛出异常
                self.proxies.get_proxies()
                res.raise_for_status()
            # 记录异常
            except requests.exceptions.HTTPError:
                logger.error(u"HTTPError; Code {0}[{1}]".format(str(res.status_code), url))
            except requests.exceptions.Timeout:
                logger.error(url + "; Timeout")
            except Exception:
                logger.error("Undefined Error [{0}]".format(url))
            # 请求失败，更换代理，重试
            self.proxies.get_proxies()
            logger.warning("downloading error , retrying.....{0},3".format(i + 1))
        logger.critical("requests.exceptions.RetryError [{0}]".format(url), exc_info=True)
        raise requests.exceptions.RetryError

    def img_download(self, dir_path: str, url: str) -> None:
        if url == "":
            raise exception.UrlEmptyException
        file_name = path.join(dir_path, path.basename(url).split("?")[0])
        try:
            res = requests.get(url, headers=self.headers, proxies=self.proxies.Proxies)
            with open(file_name, "wb") as f:
                f.write(res.content)
        except:
            logger.error("下载图片失败")


# html解析，需要在主函数中重写
class HtmlParser(object):
    def __init__(self):
        self.get_detail = False
        self.url_manager = None

    def _hot_list_feed(self, data):
        self._find_new_url(data["target"]['url'])

    def _knowledge_ad(self, data):
        self._find_new_url(data['object']['url'])
        # authors = data["object"]["body"]["authors"]
        # for i in range(len(authors)):
        #     authors[i].pop("icon")
        # return {
        #     "type": "knowledge_ad",
        #     "id": data["id"],
        #     "title": data["object"]["body"]["title"],
        #     "authors": authors,
        #     "description": data["object"]["body"]["description"],
        #     # "commodity_type": data["object"]["body"]["commodity_type"],
        #     "footer": data["object"]["footer"],
        #     "url": data['object']['url']
        # }

    def _search_result_answer(self, data):
        self._find_new_url("https://www.zhihu.com/question/" + data['object']['question']['url'].split('/')[-1])
        # return {
        #     "id": data["object"]["id"],
        #     "q_id": data["object"]["question"]["id"],
        #     "type": "search_result_answer",
        #     "author": data["object"]["author"],
        #     "q_name": data["object"]["question"]["name"],
        #     "content": data["object"]["content"],
        #     "excerpt": data["object"]["excerpt"],
        #     "created_time": data["object"]["created_time"],
        #     "updated_time": data["object"]["updated_time"],
        #     "comment_count": data["object"]["comment_count"],
        #     "voteup_count": data["object"]["voteup_count"],
        #     "q_url": "https://www.zhihu.com/question/" + data['object']['question']['url'].split('/')[-1]
        # }

    def _search_result_article(self, data):
        return

    def _search_result_question(self, data):
        return

    def _wiki_box(self, data):
        # data = data['object']
        self._find_new_url("https://www.zhihu.com/topic/" + data['object']['url'].split('/')[-1])
        # return {
        #     "id": data["id"],
        #     "aliases": data['aliases'],
        #     "discussion_count": data["discussion_count"],
        #     "essence_feed_count": data["essence_feed_count"],
        #     "excerpt": data["excerpt"],
        #     "follower_count": data["follower_count"],
        #     "followers_count": data["followers_count"],
        #     "introduction": data["introduction"],
        #     "questions_count": data["questions_count"],
        #     "top_answer_count": data["top_answer_count"],
        #     "type": "wiki_box",
        #     "url": "https://www.zhihu.com/topic/" + data['url'].split('/')[-1]
        # }

    def _find_new_url(self, url):
        if self.get_detail:
            self.url_manager.add_url(url)
        return


class DataSaver(threading.Thread):

    def __init__(self, db_name='', set_name='', use_auto_increase_index=False, use_redis=False):
        """若要使用Redis缓存数据，指定参数use_redis=True \n使用MongoDB自增ID，指定use_auto_increase_index=True
        :param db_name: str 可选 要存储的MongoDB数据库名称
        :param set_name: str 可选 要存储的MongoDB集合名
        :func run: 采用run同步Redis与Mongo数据
        """

        logger.info(
            "Init DataSaver, db_name={0}, set_name={1}, use_auto_increase_index={2}, use_redis={3}".format(db_name,
                                                                                                           set_name,
                                                                                                           use_auto_increase_index,
                                                                                                           use_redis))
        super().__init__()
        import pymongo
        mg_client = pymongo.MongoClient(config.MONGO_CONNECTION)

        self.db_name = db_name
        self.set_name = set_name
        self.use_auto_increase_index = use_auto_increase_index
        self.__tread__flag = True
        self.use_redis = use_redis

        self.mg_client_counter = mg_client["counter"]
        self.mg_client_data = mg_client[db_name]
        self.mg_data_db = self.mg_client_data[set_name]
        self.mg_counter_db = self.mg_client_counter[db_name + "@" + set_name]
        self.nextId = None
        if use_auto_increase_index:  # 使用自增ID
            if db_name + "@" + set_name in self.mg_client_counter.list_collection_names():
                return
            else:
                self.mg_counter_db.insert({
                    "_id": "_id",
                    "index": 0
                })

    def __exit__(self):
        self.__tread__flag = False
        logger.info("Exit DataSaver...")

    # csv存储
    @staticmethod
    def to_csv(data: list, file_name: str, encoding: str = "utf-8") -> None:
        """存储到CSV

        :param data: dict in list 数据集
        :param file_name: str 文件路径
        :param encoding: default "utf-8"

        """
        pd.DataFrame(data).to_csv(file_name, encoding=encoding)

    # MongoDB自增ID
    def getNextId(self) -> None:
        self.nextId = self.mg_counter_db.find_one_and_update({"_id": '_id'}, {"$inc": {"index": 1}})['index']

    def redis_temp(self, data_dict: dict) -> None:
        """数据缓存到Redis 如果使用此函方法请确保实例化DataSaver时指定了use_redis=True
        :param data_dict: dict 数据集合
        """
        # 有序集合
        redis.sadd("data_" + self.db_name + "@" + self.set_name, str(data_dict))

    def mongo_insert(self, data_dict: dict) -> None:
        """向MongoDB直接插入数据，不经过Redis缓存
        :param data_dict: dict 数据集合
        """
        if self.use_auto_increase_index:  # 使用自增ID
            self.getNextId()
            data_dict.update({"_id": self.nextId})
        self.mg_data_db.insert(data_dict)

    def run(self):
        """Redis缓存数据同步到MongoDB, 请在主程序结束后调用本对象的__exit__方法结束该线程"""
        # 只有在redis缓存数据为空，并且主程序退出的时候才会结束
        while redis.scard("data_" + self.db_name + "@" + self.set_name) or self.__tread__flag:
            data = redis.spop("data_" + self.db_name + "@" + self.set_name)
            if data:
                data = eval(data.decode("UTF-8"))
                if self.use_auto_increase_index:  # 使用自增ID
                    self.getNextId()
                    data.update({"_id": self.nextId})
                self.mg_data_db.insert(data)
            # 没有数据，休息一会
            time.sleep(1)
