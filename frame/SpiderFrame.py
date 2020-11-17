"""
    @version: v0.3 dev
    @desc: 通用爬虫框架
    @update_log: v0.1 初始架构Proxies代理模块、UrlManager、HtmlDownloader、HtmlParser、DataSaver
                 v0.2 加入MongoDB存储功能，支持MongoDB自增ID
                 v0.3 加入Redis支持，UrlManager使用Redis运行大型项目可以断点续爬，DataSaver使用Redis解决硬盘I/O低影响爬虫速度
"""
from os import path
from redis import Redis
from threading import Thread
from pandas import DataFrame
from random import randrange
from socket import setdefaulttimeout

import requests
import logging
import time
import config

redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD)


class exception:
    class RequestRetryError(Exception):
        def __init__(self):
            super().__init__()

        def __str__(self):
            return "发起过多次失败的Requests请求"

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

    class ProxiesPoolNull(Exception):
        def __init__(self):
            super().__init__()

        def __str__(self):
            return "代理已用完"


def custom_logger(__name__):
    # 创建log
    log = logging.getLogger()
    log.setLevel(logging.INFO)  # Log等级总开关
    logging.getLogger("requests").setLevel(logging.WARNING)
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
class Proxies(Thread):

    def __init__(self):
        super().__init__()
        self.__main_thread__ = False  # 主代理线程运行
        self.__thread__flag = True  # 线程运行标志
        self.__proxies__ = ''
        self.live_time = config.PROXIES_LIVE_TIME
        self.get_proxies_api = "http://http.tiqu.alicdns.com/getip3?num=1&type=2&pro=0&city=0&yys=0&port=11&pack=125417&ts=1&ys=0&cs=0&lb=1&sb=0&pb=45&mr=1&regions=110000,130000,140000,310000,320000,330000,340000,350000,360000,370000,410000,420000,430000,440000,500000,510000,610000&gm=4"
        self.Proxies = {
            "http": "",
            "https": ""
        }

    # 结束线程
    def __exit__(self):
        logger.info("Exit Proxies with code 0")
        self.__thread__flag = False
        if self.__main_thread__:
            redis.delete("ProxiesThreadCode")

    # 如果代理失效，通知进程主动更新代理
    @staticmethod
    def need_update():
        redis.set("ProxiesThreadCode", "2")

    def get_proxies(self):
        i = 0
        for i in range(config.REQUEST_RETRY_TIMES):
            res = requests.get(self.get_proxies_api)
            j = eval(res.text.replace("true", "True").replace("false", "False").replace("null", "'null'"))
            if j['code'] == 0:
                redis.set("Proxies", j['data'][0]['ip'] + ":" + str(j['data'][0]['port']))
                self.live_time = int(
                    time.mktime(time.strptime(j["data"][0]["expire_time"], "%Y-%m-%d %H:%M:%S"))) - time.time()
                logger.info("Successfully get proxies")
                return
            if j['code'] == 121:
                raise exception.ProxiesPoolNull
            logger.warning("Failed, " + str(i + 1) + " times get proxies...")
            time.sleep(randrange(0, 2))
        if i == 4:
            logger.critical("Get proxies failed, exit program...")

    def update_self_proxies(self):
        temp = redis.get("Proxies").decode("utf-8")
        if self.__proxies__ != temp:
            self.Proxies['http'] = "http://" + temp
            self.Proxies['https'] = "https://" + temp

    # 监测代理时间。如果超时更新代理，同一时间只允许存在一个代理监控进程，其余只负责更新，读取已经存在的代理
    def run(self) -> None:
        start_time = time.time()
        logger.info("------------ Run as following proxies thread ------------")
        while self.__thread__flag:

            if redis.get("ProxiesThreadCode") is None:
                redis.set("ProxiesThreadCode", "2")  # 抢占代理主线
                self.__main_thread__ = True  # 以主线运行标志
                logger.info("------------ Switch to main proxies thread ------------")

            if self.__main_thread__ and (
                    time.time() - start_time > self.live_time or redis.get("ProxiesThreadCode").decode("utf-8") == "2"):
                logger.warning("Proxies failure, get new one")
                # 重设代理使用时长
                start_time = time.time()
                self.get_proxies()
                self.update_self_proxies()
                redis.set("ProxiesThreadCode", "1")
            elif not self.__main_thread__:
                self.update_self_proxies()

            time.sleep(1)


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
    def get(self, db_set_name="") -> str:
        if db_set_name is "":
            db_set_name = self.db_set_name
        if not self.list_not_null(db_set_name):
            raise exception.UrlEmptyException
        if not self.use_redis:
            return self.url_list.pop(0)
        return redis.lpop("list_" + db_set_name).decode("utf-8")  # 列表头部pop

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
class HtmlDownloader(Thread):

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
        setdefaulttimeout(config.SOCKET_DEFAULT_TIMEOUT)  # 设置超时

    def download(self, url: str, params=None) -> str:
        if url == "":
            raise exception.UrlEmptyException
        if params is None:
            params = {}

        error = 0

        for i in range(1, config.REQUEST_RETRY_TIMES + 1):
            try:
                res = requests.get(url, params=params, headers=self.headers, proxies=self.proxies.Proxies,
                                   timeout=15)
                if res.status_code == 200:
                    return res.text
                res.raise_for_status()
            # 记录异常
            except requests.exceptions.HTTPError:
                logger.warning(
                    "HTTPError with url:<{0}> retrying.....{1},{2}".format(url[:25] + " ... " + url[-15:], i,
                                                                           config.REQUEST_RETRY_TIMES))
            except requests.exceptions.Timeout:
                logger.warning(
                    "Timeout with url:<{0}> retrying.....{1},{2}".format(url[:25] + " ... " + url[-15:], i,
                                                                         config.REQUEST_RETRY_TIMES))
            except requests.exceptions.ProxyError:
                logger.error("Cannot connect to proxy.', timeout('timed out')")
            except Exception:
                logger.error("Undefined Error [{0}]".format(url), exc_info=True)
            if error == 3:
                self.proxies.need_update()
            time.sleep(5)
        self.proxies.need_update()
        logger.critical("requests.exceptions.RetryError [{0}]".format(url))
        time.sleep(10)
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


class DataSaver(Thread):

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
        DataFrame(data).to_csv(file_name, encoding=encoding)

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
