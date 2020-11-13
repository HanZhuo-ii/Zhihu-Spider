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
import config


logger = SpiderFrame.logger
html_downloader = SpiderFrame.HtmlDownloader()
url_manager = SpiderFrame.UrlManager(use_redis=config.USE_REDIS, db_set_name=config.COMMENT_SET)
data_saver = SpiderFrame.DataSaver(db_name=config.DB_NAME, set_name=config.COMMENT_SET)


def spider(answer_id: str) -> None:
    # 增量爬取评论
    logger.info("Get comments for answer id: {0}".format(answer_id))
    url = "https://www.zhihu.com/api/v4/answers/{}/root_comments?limit=10&offset=0&order=normal&status=open" \
        .format(answer_id)
    res = html_downloader.download(url)
    res = json_lds(res)
    url_manager.add_url(url)

    if not data_saver.mg_data_db.find_one({"AnswerID": answer_id}):
        logger.info("This answer's comments don't exist, creating")
        data_saver.mongo_insert({
            "AnswerID": answer_id,
            "common_counts": res['paging']['totals'],
            "result": []
        })

    try:
        while url_manager.list_not_null():
            res = html_downloader.download(url_manager.get())
            res = json_lds(res)
            for data in res['data']:
                if data_saver.mg_data_db.find_one({"result.id": data["id"]}):
                    # 已经存在的，不存储
                    continue
                data_saver.mg_data_db.update_one({"AnswerID": answer_id}, {'$addToSet': {"result": data}})
                try:
                    if data["author"]["url_token"] is not "":
                        url_manager.add_id(id_set=config.USER_ID_SET, _id=data["author"]["member"]["url_token"])
                except:
                    pass
            if res['paging']['is_end']:
                logger.info("Paging is end, exit")
                break
            url = res['paging']['next']
            url_manager.add_url(url)

    except Exception as e:
        logger.critical("Fatal Error, Message:{0}, With url: <{0}>, Saving data and exit".format(e, url), exc_info=True)
        url_manager.force_add_url(url)
        url_manager.add_id(id_set=config.ANSWER_ID_SET, _id=answer_id)
        # exit
        logger.error("Kill Proxies")
        html_downloader.proxies.__exit__()
        logger.error("Process finished with exit code -1")
        # send_mail("Fatal Error With url: <{0}>, Message:{1}".format(url, e))
        raise SpiderFrame.exception.UnexpectedError


if __name__ == '__main__':
    logger.info("Run as main")
    spider('96208787')
    # exit
    logger.info("Kill Proxies")
    html_downloader.proxies.__exit__()
    logger.info("Process finished with exit code 0")
