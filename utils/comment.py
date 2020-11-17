"""
    @author         满目皆星河
    @creat_date     2020/10/06
    @update_data    2020/10/06
    @desc           评论爬虫，提供answer的id，爬该answer下所有评论 <已实现增量>
    @info           没有其他链接，不需要队列
    @main_function  spyder(question_id: str)
"""

from frame import SpiderFrame
from json import loads as json_lds
from time import sleep
from redis import Redis
import config


logger = SpiderFrame.logger
html_downloader = SpiderFrame.HtmlDownloader()
url_manager = SpiderFrame.UrlManager(use_redis=config.USE_REDIS, db_set_name=config.COMMENT_SET)
data_saver = SpiderFrame.DataSaver(db_name=config.DB_NAME, set_name=config.COMMENT_SET)
redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD)


def spider(answer_id: str) -> None:
    # 增量爬取评论
    offset = config.MONGO_DOC_LIMIT
    logger.info("Get comments for answer id: {0}".format(answer_id))

    url = "https://www.zhihu.com/api/v4/answers/{}/root_comments?limit=10&offset=0&order=normal&status=open" \
        .format(answer_id)
    res = html_downloader.download(url)
    res = json_lds(res)
    redis.set(answer_id, url)

    if not data_saver.mg_data_db.find_one({"AnswerID": answer_id}):
        logger.info("This answer's comments don't exist, creating")
        data_saver.mongo_insert({
            "AnswerID": answer_id,
            "common_counts": res['paging']['totals'],
            "limit": config.MONGO_DOC_LIMIT,
            "offset": offset,
            "end_url": "",
            "data": []
        })

    try:
        while True:
            sleep(.3)
            url = redis.get(answer_id).decode("utf-8")
            try:
                res = html_downloader.download(url)
            except SpiderFrame.exception.RequestRetryError as e:
                logger.error(e, exc_info=True)
                sleep(1)
                continue
            res = json_lds(res)
            for data in res['data']:
                if len(data_saver.mg_data_db.find_one({"AnswerID": answer_id, "offset": offset})["data"]) >= 5000:
                    logger.warning("MongoDB document out of limit, Create new document and update offset")
                    offset += config.MONGO_DOC_LIMIT
                    data_saver.mongo_insert({
                        "AnswerID": answer_id,
                        "common_counts": res['paging']['totals'],
                        "limit": config.MONGO_DOC_LIMIT,
                        "offset": offset,
                        "end_url": "",
                        "data": []
                    })
                if data_saver.mg_data_db.find_one({"data.id": data["id"]}):
                    # 已经存在的，不存储
                    continue
                data_saver.mg_data_db.update_one({"AnswerID": answer_id, "offset": offset}, {'$addToSet': {"data": data}})
                try:
                    if data["author"]["url_token"] is not "":
                        url_manager.add_id(id_set=config.USER_ID_SET, _id=data["author"]["member"]["url_token"])
                except:
                    pass

            if res['paging']['is_end']:
                logger.info("Paging is end, exit")
                data_saver.mg_data_db.update_one({"AnswerID": answer_id, "offset": offset}, {"$set": {"end_url": url}})
                redis.delete(answer_id)
                break
            url = res['paging']['next']
            redis.set(answer_id, url)

    except Exception as e:
        logger.critical("Fatal Error, Message:{0}, With url: <{0}>, Saving data and exit".format(e, url), exc_info=True)
        url_manager.add_id(id_set=config.ANSWER_ID_SET, _id=answer_id)
        # exit
        logger.error("Kill Proxies")
        html_downloader.proxies.__exit__()
        logger.error("Process finished with exit code -1")
        raise SpiderFrame.exception.UnexpectedError


if __name__ == '__main__':
    logger.info("Run as main")
    spider('96208787')
    # exit
    logger.info("Kill Proxies")
    html_downloader.proxies.__exit__()
    logger.info("Process finished with exit code 0")
