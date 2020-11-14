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
from utils import topic, question, comment, user

logger = SpiderFrame.logger
redis = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD)


class TopicSpider(Thread):
    def __init__(self):
        logger.info("TopicSpider init...")
        super().__init__()
        # url_manager方法已经内置，只需要使用id_manager传入ID参数即可
        self.id_manager = SpiderFrame.UrlManager(db_set_name=config.TOPIC_ID_SET, use_redis=config.USE_REDIS)

    def run(self):
        logger.info("TopicSpider thread start...")
        _id = ''
        # self.id_manager.add_id(config.TOPIC_ID_SET, "19563451")
        try:
            while self.id_manager.list_not_null() or self.id_manager.list_not_null(config.TOPIC_SET):
                try:
                    _id = self.id_manager.get()
                except:
                    _id = ''
                topic.spider(_id)
        except Exception as e:
            # 之前的报错信息已被记录
            logger.critical("Unexpected Exit TopicSpider: {0}, Message: {1}".format(_id, e), exc_info=True)
            send_mail("TopicSpider发生意料之外的错误，已退出线程")
        finally:
            logger.warning("TopicSpider finished with exit code 0")
            topic.html_downloader.proxies.__exit__()


class QuestionSpider(Thread):
    def __init__(self):
        logger.info("QuestionSpider init...")
        super().__init__()
        # url_manager方法已经内置，只需要使用id_manager传入ID参数即可
        self.id_manager = SpiderFrame.UrlManager(db_set_name=config.QUESTION_ID_SET, use_redis=config.USE_REDIS)

    def run(self):
        logger.info("QuestionSpider thread start...")
        _id = ''
        try:
            while True:
                if self.id_manager.list_not_null():
                    _id = self.id_manager.get()
                    question.spider(_id)
                else:
                    sleep(5)
        except Exception as e:
            # 之前的报错信息已被记录
            logger.critical("Unexpected Exit QuestionSpider: {0}, Message: {1}".format(_id, e), exc_info=True)
            send_mail("QuestionSpider发生意料之外的错误，已退出线程")
        finally:
            logger.warning("QuestionSpider finished with exit code 0")
            question.html_downloader.proxies.__exit__()


class CommentSpider(Thread):
    def __init__(self):
        logger.info("CommentSpider init...")
        super().__init__()
        # url_manager方法已经内置，只需要使用id_manager传入ID参数即可
        self.id_manager = SpiderFrame.UrlManager(db_set_name=config.ANSWER_ID_SET, use_redis=config.USE_REDIS)

    def run(self):
        _id = ''
        try:
            logger.info("CommentSpider thread start...")
            while True:
                if self.id_manager.list_not_null():
                    _id = self.id_manager.get()
                    comment.spider(_id)
                else:
                    sleep(5)
        except Exception as e:
            # 之前的报错信息已被记录
            logger.critical("Unexpected Exit CommentSpider: {0}, Message: {1}".format(_id, e), exc_info=True)
            send_mail("CommentSpider发生意料之外的错误，已退出线程")
        finally:
            logger.warning("CommentSpider finished with exit code 0")
            comment.html_downloader.proxies.__exit__()


class UserSpider(Thread):
    def __init__(self):
        logger.info("UserSpider init...")
        super().__init__()
        # url_manager方法已经内置，只需要使用id_manager传入ID参数即可
        self.id_manager = SpiderFrame.UrlManager(db_set_name=config.USER_ID_SET, use_redis=config.USE_REDIS)

    def run(self):
        logger.info("UserSpider thread start...")
        _id = ''
        try:
            while True:
                if self.id_manager.list_not_null():
                    _id = self.id_manager.get()
                    user.spider(_id)
                else:
                    sleep(5)
        except Exception as e:
            # 之前的报错信息已被记录
            logger.critical("Unexpected Exit UserSpider: {0}, Message: {1}".format(_id, e), exc_info=True)
            send_mail("UserSpider发生意料之外的错误，已退出线程")
        finally:
            logger.warning("UserSpider finished with exit code 0")
            user.html_downloader.proxies.__exit__()


if __name__ == '__main__':
    TS = TopicSpider()
    QS = QuestionSpider()
    CS = CommentSpider()
    US = UserSpider()

    TS.start()
    logger.info("Next thread will be start after 10s")
    sleep(10)
    QS.start()
    logger.info("Next thread will be start after 10s")
    sleep(10)
    CS.start()
    logger.info("Next thread will be start after 10s")
    sleep(10)
    US.start()

    logger.warning("爬虫进程启动完成，启动监控进程")
    # watching
    while True:
        TS_i = QS_i = CS_i = US_i = 1
        if not TS.is_alive() and (redis.llen(config.TOPIC_ID_SET) or redis.llen(config.TOPIC_SET)):
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
        if not QS.is_alive() and (redis.llen(config.QUESTION_ID_SET) or redis.llen(config.QUESTION_SET)):
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
        if not CS.is_alive() and (redis.llen(config.ANSWER_ID_SET) or redis.llen(config.COMMENT_SET)):
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
        if not US.is_alive() and redis.llen(config.USER_ID_SET):
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
        if not(TS.is_alive() or QS.is_alive() or CS.is_alive() or US.is_alive()):
            logger.critical("----- All thread exited and can't be actived, main thread is exiting -----")
        if TS.is_alive() and QS.is_alive() and CS.is_alive() and US.is_alive():
            logger.info("----- ALL THREAD IS ALIVE -----")
        sleep(10)