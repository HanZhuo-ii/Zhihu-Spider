"""
    @author         满目皆星河
    @creat_date     2020/10/06
    @update_data    2020/10/06
    @desc           知乎回答爬虫，爬某个提问下面全部的回答以及回答的详细信息, 存入MongoDB.知乎.questions
    @main_function  spider(question_id: str)
"""

from frame import SpiderFrame
from bs4 import BeautifulSoup
from re import findall
from os import path, makedirs
import json
import config
from time import sleep

logger = SpiderFrame.logger


class HtmlParser(SpiderFrame.HtmlParser):
    def __init__(self):
        super().__init__()
        self.url_manager = SpiderFrame.UrlManager(use_redis=config.USE_REDIS, db_set_name=config.QUESTION_SET)

    @staticmethod
    def parse_base_question_info(html: str):
        soup = BeautifulSoup(html, "lxml")
        try:
            title = soup.find("h1", {"class": "QuestionHeader-title"}).text
        except:
            title = ""
        try:
            question = soup.find("div", {"class": "QuestionRichText--collapsed"}).text
        except:
            question = ''
        tag_list = []
        try:
            tags = soup.find_all("div", {"class": "QuestionTopic"})
            for tag in tags:
                tag_list.append(tag.text)
        except:
            pass
        try:
            follower = int(soup.find_all("strong", {"class": "NumberBoard-itemValue"})[0].text.strip().replace(",", ""))
        except:
            follower = 0
        try:
            watched = int(soup.find_all("strong", {"class": "NumberBoard-itemValue"})[1].text.strip().replace(",", ""))
        except:
            watched = 0
        return title, question, tag_list, follower, watched


html_parser = HtmlParser()
html_downloader = SpiderFrame.HtmlDownloader()
data_saver = SpiderFrame.DataSaver(db_name=config.DB_NAME, set_name=config.QUESTION_SET)


def _init_url_(_question_id: str):
    base_url_start = "https://www.zhihu.com/api/v4/questions/"
    base_url_end = "/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed" \
                   "%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by" \
                   "%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count" \
                   "%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info" \
                   "%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting" \
                   "%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%2Cpaid_info%2Cpaid_info_content%3Bdata%5B" \
                   "%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics" \
                   "&limit=5&offset=0"
    return base_url_start + _question_id + base_url_end


def spider(question_id: str):
    """
        :param question_id: 问题ID
    """
    url = ""
    offset = config.MONGO_DOC_LIMIT
    try:
        # 初始化URL队列，如果之前已经爬过，添加不进去，继续上次断点
        html_parser.url_manager.add_url(url=_init_url_(question_id))

        # question base info
        url = "https://www.zhihu.com/question/" + question_id
        res = html_downloader.download(url)
        title, question, tag_list, follower, watched = html_parser.parse_base_question_info(res)

        if not data_saver.mg_data_db.find_one({"QuestionId": question_id, "offset": offset}):
            data_saver.mongo_insert({
                "QuestionId": question_id,
                "title": title,
                "question": question,
                "tag_list": tag_list,
                "follower": follower,
                "watched": watched,
                "limit": config.MONGO_DOC_LIMIT,
                "offset": offset,
                "end_url": "",
                "data": []
            })

        # question detail
        while html_parser.url_manager.list_not_null():
            sleep(.3)
            url = html_parser.url_manager.get()
            try:
                res = html_downloader.download(url)
            except SpiderFrame.exception.RequestRetryError as e:
                logger.error(e, exc_info=True)
                html_parser.url_manager.add_url(url)
                sleep(1)
                continue
            try:
                question_json = json.loads(res)
            except:
                logger.error("Json格式校验错误")
                continue
            for data in question_json["data"]:
                if len(data_saver.mg_data_db.find_one({"QuestionId": question_id, "offset": offset})["data"]) >= 5000:
                    logger.warning("MongoDB document out of limit, Create new document and update offset")
                    offset += config.MONGO_DOC_LIMIT
                    data_saver.mongo_insert({
                        "QuestionId": question_id,
                        "title": title,
                        "question": question,
                        "tag_list": tag_list,
                        "follower": follower,
                        "watched": watched,
                        "limit": config.MONGO_DOC_LIMIT,
                        "offset": offset,
                        "end_url": "",
                        "data": []
                    })
                if config.QUESTION_ADD_ANSWER_ID:
                    html_parser.url_manager.add_id(config.ANSWER_ID_SET, data["id"])
                if data_saver.mg_data_db.find_one({"data.id": data["id"]}) and data_saver.mg_data_db.find_one({"data.updated_time": data['updated_time']}):
                    continue
                try:
                    data.pop("excerpt")
                    if config.DOWNLOAD_IMG:
                        url_list = findall("<img src=\"(http.*?)\"", data["content"])
                        img_path = path.join(config.ANSWER_IMG_DIR, question_id)
                        if not path.exists(img_path):
                            logger.info("Img file not exist, creating...")
                            makedirs(img_path)
                        for img_url in url_list:
                            html_downloader.img_download(img_path, img_url)
                except:
                    logger.error("Answer:{0}, Message: 图片下载失败".format(data["id"]))
                data_saver.mg_data_db.update_one({"QuestionId": question_id, "offset": offset}, {'$addToSet': {"data": data}})
                try:
                    if data["author"]["url_token"] is not "":
                        html_parser.url_manager.add_id(id_set=config.USER_ID_SET, _id=data["author"]["url_token"])
                except:
                    pass

            # 游标，下个数据包URL
            if question_json["paging"]["is_end"]:
                logger.info("Question id {0} is complete! ".format(question_id))
                data_saver.mg_data_db.update_one({"QuestionId": question_id, "offset": offset}, {"$set": {"end_url": url}})
                break

            next_url = question_json["paging"]["next"]
            logger.info("New url has been find: <{0} ... {1}>".format(url[:21], url[-11:]))
            html_parser.url_manager.add_url(next_url)

    except Exception as e:
        logger.critical("Fatal Error, Message:{0}, With url: <{0}>, Saving data and exit".format(e, url), exc_info=True)
        html_parser.url_manager.force_add_url(url)
        html_parser.url_manager.add_id(id_set=config.QUESTION_ID_SET, _id=question_id)
        # send_mail("Fatal Error With url: <{0}>, Message:{1}".format(url, e))
        # 结束线程
        logger.error("Kill Proxies")
        html_downloader.proxies.__exit__()
        logger.error("Process finished with exit code -1")
        raise SpiderFrame.exception.UnexpectedError




if __name__ == '__main__':
    logger.info("Running as main")
    q_list = []
    for q_id in input("请输入问题ID，多个question_id请用英文逗号分隔：").split(","):
        q_list.append(q_id.strip())
    for q_id in q_list:
        spider(q_id)
    # 结束线程
    logger.info("Kill Proxies")
    html_downloader.proxies.__exit__()
    logger.info("Process finished with exit code 0")
