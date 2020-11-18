# -*- coding: utf-8 -*-
"""
@Author      : 满目皆星河
@Project     : 知乎
@File        : main.py
@Time        : 2020/11/13 0:53
@Description :
"""

import redis
import config
from time import sleep
from threading import Thread
from frame import SpiderFrame
from frame.mail import send_mail

logger = SpiderFrame.logger
redis = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD)


class TopicSpider(Thread):
    def __init__(self):
        logger.info("TopicSpider init...")
        super().__init__()
        # url_manager方法已经内置，只需要使用id_manager传入ID参数即可
        self.id_manager = SpiderFrame.UrlManager(db_set_name=config.TOPIC_ID_SET, use_redis=config.USE_REDIS)
        self.exit_code = 1

    def run(self):
        from utils import topic
        logger.info("TopicSpider thread start...")
        _id = ""
        try:
            while self.id_manager.list_not_null():
                _id = self.id_manager.get()
                try:
                    topic.spider(_id)
                except:
                    continue
            self.exit_code = 0
        except Exception as e:
            # 之前的报错信息已被记录
            logger.critical("Unexpected Exit TopicSpider: {0}, Message: {1}".format(_id, e), exc_info=True)
            # send_mail("TopicSpider发生意料之外的错误，已退出线程")
        finally:
            logger.warning("TopicSpider finished with exit code 0")
            topic.html_downloader.proxies.__exit__()


class QuestionSpider(Thread):
    def __init__(self):
        logger.info("QuestionSpider init...")
        super().__init__()
        self.exit_code = 1

        self.flag = True
        # url_manager方法已经内置，只需要使用id_manager传入ID参数即可
        self.id_manager = SpiderFrame.UrlManager(db_set_name=config.QUESTION_ID_SET, use_redis=config.USE_REDIS)

    def __exit__(self):
        logger.warning("强制终止线程: QuestionSpider")
        self.flag = False

    def run(self):
        from utils import question
        logger.info("QuestionSpider thread start...")
        _id = ''
        try:
            while self.flag:
                if self.id_manager.list_not_null():
                    _id = self.id_manager.get()
                    try:
                        question.spider(_id)
                    except:
                        continue
                elif not self.id_manager.list_not_null("list_"+config.TOPIC_SET):
                    break
                else:
                    sleep(5)
            self.exit_code = 0
        except Exception as e:
            # 之前的报错信息已被记录
            logger.critical("Unexpected Exit QuestionSpider: {0}, Message: {1}".format(_id, e), exc_info=True)
            # send_mail("QuestionSpider发生意料之外的错误，已退出线程")
        finally:
            logger.warning("QuestionSpider finished with exit code 0")
            question.html_downloader.proxies.__exit__()


class CommentSpider(Thread):
    def __init__(self):
        logger.info("CommentSpider init...")
        super().__init__()
        self.exit_code = 1

        self.flag = True
        # url_manager方法已经内置，只需要使用id_manager传入ID参数即可
        self.id_manager = SpiderFrame.UrlManager(db_set_name=config.ANSWER_ID_SET, use_redis=config.USE_REDIS)

    def __exit__(self):
        logger.warning("强制终止线程: CommentSpider")
        self.flag = False

    def run(self):
        from utils import comment
        _id = ''
        try:
            logger.info("CommentSpider thread start...")
            while True:
                if self.id_manager.list_not_null():
                    _id = self.id_manager.get()
                    try:
                        comment.spider(_id)
                    except:
                        continue
                elif not (self.id_manager.list_not_null("list_"+config.TOPIC_SET) or self.id_manager.list_not_null("list_"+config.QUESTION_SET)):
                    break
                else:
                    sleep(5)
            self.exit_code = 0
        except Exception as e:
            # 之前的报错信息已被记录
            logger.critical("Unexpected Exit CommentSpider: {0}, Message: {1}".format(_id, e), exc_info=True)
            # send_mail("CommentSpider发生意料之外的错误，已退出线程")
        finally:
            logger.warning("CommentSpider finished with exit code 0")
            comment.html_downloader.proxies.__exit__()


class UserSpider(Thread):
    def __init__(self):
        logger.info("UserSpider init...")
        super().__init__()
        self.exit_code = 1

        self.flag = True
        # url_manager方法已经内置，只需要使用id_manager传入ID参数即可
        self.id_manager = SpiderFrame.UrlManager(db_set_name=config.USER_ID_SET, use_redis=config.USE_REDIS)

    def __exit__(self):
        logger.warning("强制终止线程: UserSpider")
        self.flag = False

    def run(self):
        from utils import user
        logger.info("UserSpider thread start...")
        _id = ''
        try:
            while True:
                if self.id_manager.list_not_null():
                    _id = self.id_manager.get()
                    try:
                        user.spider(_id)
                    except:
                        continue
                elif not (self.id_manager.list_not_null("list_"+config.TOPIC_SET) or self.id_manager.list_not_null("list_"+config.QUESTION_SET) or self.id_manager.list_not_null("list_"+config.COMMENT_SET)):
                    break
                else:
                    sleep(5)
            self.exit_code = 0
        except Exception as e:
            # 之前的报错信息已被记录
            logger.critical("Unexpected Exit UserSpider: {0}, Message: {1}".format(_id, e), exc_info=True)
            # send_mail("UserSpider发生意料之外的错误，已退出线程")
        finally:
            logger.warning("UserSpider finished with exit code 0")
            user.html_downloader.proxies.__exit__()


def ProcessError():
    keys = redis.keys("*")
    for key in keys:
        try:
            int(key)
            url = redis.get(key).decode("utf-8").split("/")
            if url[5] == "answers":
                redis.rpush("list_"+config.ANSWER_ID_SET, url[5])
                redis.delete(key)
            elif url[5] == "questions":
                redis.rpush("list_"+config.ANSWER_ID_SET, url[5])
                redis.delete(key)
            elif url[5] == "topics":
                redis.rpush("list_"+config.ANSWER_ID_SET, url[5])
                redis.delete(key)
        except:
            pass


class running(Thread):
    def __init__(self):
        super(running, self).__init__()

    def run(self):
        
        TS = TopicSpider()
        QS = QuestionSpider()
        CS = CommentSpider()
        US = UserSpider()

        # logger.info("Processing Error Data")
        # ProcessError()
        TS.start()
        logger.info("Next thread will be start after 7.5s")
        sleep(7.5)
        QS.start()
        logger.info("Next thread will be start after 7.5s")
        sleep(7.5)
        CS.start()
        logger.info("Next thread will be start after 7.5s")
        sleep(7.5)
        US.start()

        logger.warning("爬虫进程启动完成，启动监控进程")
        # watching
        TS_i = QS_i = CS_i = US_i = 1
        while True:
            if TS.exit_code != 0 and not TS.is_alive():
                for i in range(1, 4):
                    if TS.is_alive():
                        continue
                    logger.warning("TS is exit, try active it. ({0}/3)".format(TS_i))
                    TS = TopicSpider()
                    TS.start()
                    sleep(5)
                    if i == 3 and not TS.is_alive():
                        logger.error("Active thread TS failed")
                        send_mail("TS is exit and try to activate it failed")
            if QS.exit_code != 0 and not QS.is_alive():
                for i in range(1, 4):
                    if QS.is_alive():
                        QS_i = 1
                        continue
                    logger.warning("QS is exit, try active it. ({0}/3)".format(QS_i))
                    QS = QuestionSpider()
                    QS.start()
                    sleep(5)
                    if i == 3 and not QS.is_alive():
                        logger.error("----- Active thread QS failed -----")
                        send_mail("QS is exit and try to activate it failed")
            if CS.exit_code != 0 and not CS.is_alive():
                for i in range(1, 4):
                    if CS.is_alive():
                        CS_i = 1
                        continue
                    logger.warning("QS is exit, try active it. ({0}/3)".format(CS_i))
                    CS = CommentSpider()
                    CS.start()
                    sleep(5)
                    if i == 3 and not CS.is_alive():
                        logger.error("----- Active thread CS failed -----")
                        send_mail("CS is exit and try to activate it failed")
            if US.exit_code != 0 and not US.is_alive():
                for i in range(1, 4):
                    if US.is_alive():
                        US_i = 1
                        continue
                    logger.warning("US is exit, try active it. ({0}/3)".format(US_i))
                    US = UserSpider()
                    US.start()
                    sleep(5)
                    if i == 3 and not US.is_alive():
                        logger.error("----- Active thread US failed -----")
                        send_mail("US is exit and try to activate it failed")
            if TS.exit_code == 0 and QS.exit_code == 0 and CS.exit_code == 0 and US.exit_code == 0:
                logger.critical("----- All thread exited and can't be actived, main thread is exiting -----")
                return
            if (TS.is_alive() or TS.exit_code == 0) and (QS.is_alive() or QS.exit_code == 0) and (CS.is_alive() or CS.exit_code == 0) and (US.is_alive() or US.exit_code == 0):
                logger.info("----- ALL THREAD IS ALIVE -----")
            sleep(10)


if __name__ == '__main__':
    redis.delete("ProxiesThreadCode_{0}".format(config.THREAD_ID))
    r1 = running()
    r1.start()
