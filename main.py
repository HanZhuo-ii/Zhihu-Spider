# -*- coding: utf-8 -*-
"""
@Author      : 满目皆星河
@Project     : 知乎
@File        : main.py
@Time        : 2020/11/13 0:53
@Description : 
"""

import os
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
        # self.id_manager.add_id(config.TOPIC_ID_SET, "19610306")
        try:
            while self.id_manager.list_not_null():
                _id = self.id_manager.get()
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
            while self.id_manager.list_not_null():
                _id = self.id_manager.get()
                question.spider(_id)
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
            while self.id_manager.list_not_null():
                _id = self.id_manager.get()
                comment.spider(_id)
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
            while self.id_manager.list_not_null():
                _id = self.id_manager.get()
                user.spider(_id)
        except Exception as e:
            # 之前的报错信息已被记录
            logger.critical("Unexpected Exit UserSpider: {0}, Message: {1}".format(_id, e), exc_info=True)
            send_mail("UserSpider发生意料之外的错误，已退出线程")
        finally:
            logger.warning("UserSpider finished with exit code 0")
            user.html_downloader.proxies.__exit__()


class Order(Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            logger.warning("Clear the console...")
            for i in range(0, 300):     # 间接sleep了clc
                logger.info("Redis: Saving data")
                redis.save()
                sleep(2)
                if not (TS.is_alive() or QS.is_alive() or CS.is_alive() or US.is_alive()):
                    logger.warning("All Threads already exit, Order is exiting with code 0")
                    exit(0)
            os.system('cls')  # 执行cls命令清空Python控制台



if __name__ == '__main__':
    order = Order()
    TS = TopicSpider()
    QS = QuestionSpider()
    CS = CommentSpider()
    US = UserSpider()

    order.start()
    TS.start()
    logger.info("Waiting to start next thread...")
    sleep(5)
    QS.start()
    logger.info("Waiting to start next thread...")
    sleep(5)
    CS.start()
    logger.info("Waiting to start next thread...")
    sleep(5)
    US.start()
