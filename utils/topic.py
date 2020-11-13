"""
    @author         满目皆星河
    @creat_date     2020/11/09
    @update_data    2020/11/09
    @desc           话题爬虫，许多question归属于某类话题，爬取这些question的信息（以等待回答为基础）
    @main_function  spider(question_id: str)
"""
from frame import SpiderFrame
from bs4 import BeautifulSoup

import config
import json

logger = SpiderFrame.logger
html_downloader = SpiderFrame.HtmlDownloader()
data_saver = SpiderFrame.DataSaver(db_name=config.DB_NAME, set_name=config.TOPIC_SET)
url_manager = SpiderFrame.UrlManager(db_set_name=config.TOPIC_SET, use_redis=config.USE_REDIS)


def parse_base_topic_info(html: str):
    soup = BeautifulSoup(html, "lxml")
    try:
        title = soup.find("h2", {"class": "ContentItem-title"}).text
    except Exception as e:
        logger.error("Get Topic title failed, Exception: {0}".format(e))
        title = ''
    # 暂时失效
    # father_tag_list = []
    # tags = soup.find_all("div", {"class": "TopicTagsContainer"})[0].find_all("span", {"class": "Tag-content"})
    # for tag in tags:
    #     father_tag_list.append(tag.text)
    #
    # child_tag_list = []
    # tags = soup.find_all("div", {"class": "TopicTagsContainer"})[1].find_all("span", {"class": "Tag-content"})
    # for tag in tags:
    #     child_tag_list.append(tag.text)
    try:
        follower = soup.find_all("strong", {"class": "NumberBoard-itemValue"})[0].text
        question_num = soup.find_all("strong", {"class": "NumberBoard-itemValue"})[1].text
    except Exception as e:
        logger.error("Get topic follower and question_num failed, Exception: {0}".format(e))
        follower, question_num = '', ''
    return title, follower, question_num


def spider(topic_id: str):
    url = "https://www.zhihu.com/api/v4/topics/{0}/feeds/top_question?include=data%5B%3F(target.type%3Dtopic_sticky_module)%5D.target.data%5B%3F(target.type%3Danswer)%5D.target.content%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%3Bdata%5B%3F(target.type%3Dtopic_sticky_module)%5D.target.data%5B%3F(target.type%3Danswer)%5D.target.is_normal%2Ccomment_count%2Cvoteup_count%2Ccontent%2Crelevant_info%2Cexcerpt.author.badge%5B%3F(type%3Dbest_answerer)%5D.topics%3Bdata%5B%3F(target.type%3Dtopic_sticky_module)%5D.target.data%5B%3F(target.type%3Darticle)%5D.target.content%2Cvoteup_count%2Ccomment_count%2Cvoting%2Cauthor.badge%5B%3F(type%3Dbest_answerer)%5D.topics%3Bdata%5B%3F(target.type%3Dtopic_sticky_module)%5D.target.data%5B%3F(target.type%3Dpeople)%5D.target.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics%3Bdata%5B%3F(target.type%3Danswer)%5D.target.annotation_detail%2Ccontent%2Chermes_label%2Cis_labeled%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Canswer_type%3Bdata%5B%3F(target.type%3Danswer)%5D.target.author.badge%5B%3F(type%3Dbest_answerer)%5D.topics%3Bdata%5B%3F(target.type%3Danswer)%5D.target.paid_info%3Bdata%5B%3F(target.type%3Darticle)%5D.target.annotation_detail%2Ccontent%2Chermes_label%2Cis_labeled%2Cauthor.badge%5B%3F(type%3Dbest_answerer)%5D.topics%3Bdata%5B%3F(target.type%3Dquestion)%5D.target.annotation_detail%2Ccomment_count%3B&offset=5&limit=20".format(
        topic_id)
    url_manager.add_url(url)

    try:
        base_url = "https://www.zhihu.com/topic/{0}/hot".format(topic_id)
        res = html_downloader.download(base_url)
        title, follower, question_num = parse_base_topic_info(res)

        if not data_saver.mg_data_db.find_one({"TopicId": topic_id}):
            data_saver.mongo_insert({
                "TopicId": topic_id,
                "title": title,
                # "father_tag_list": father_tag_list,
                # "child_tag_list": child_tag_list,
                "follower": follower,
                "question_num": question_num,
                "end_url": "",
                "result": [],
            })

        while url_manager.list_not_null():
            url = url_manager.get()
            res = html_downloader.download(url)
            topic_json = json.loads(res)

            for data in topic_json["data"]:
                if config.TOPIC_ADD_QUESTIONS_ID:
                    url_manager.add_id(config.QUESTION_ID_SET, data["target"]["id"])
                if data_saver.mg_data_db.find_one({"result.id": data["target"]["id"]}):
                    continue
                data_saver.mg_data_db.update_one({"TopicId": topic_id}, {'$addToSet': {"result": data["target"]}})
                try:
                    if data["author"]["url_token"] is not "":
                        url_manager.add_id(id_set=config.USER_ID_SET, _id=data["author"]["url_token"])
                except:
                    pass

            # 游标，下个数据包URL
            if topic_json["paging"]["is_end"]:
                logger.warning("Topic id {0} is complete! ".format(topic_id))
                data_saver.mg_data_db.update_one({"TopicId": topic_id}, {"$set": {"end_url": url}})
                break

            next_url = topic_json["paging"]["next"]
            logger.info("New url has been find: <{0} ... {1}>".format(url[:21], url[-11:]))
            url_manager.add_url(next_url)

    except Exception as e:
        logger.critical("Fatal Error, Message:{0}, With url: <{0}>, Saving data and exit".format(e, url), exc_info=True)
        url_manager.force_add_url(url)
        url_manager.add_id(id_set=config.TOPIC_ID_SET, _id=topic_id)
        # send_mail("Fatal Error With url: <{0}>, Message:{1}".format(url, e))
        # 结束线程
        logger.error("Kill Proxies")
        html_downloader.proxies.__exit__()
        logger.error("Process finished with exit code -1")
        raise SpiderFrame.exception.UnexpectedError



if __name__ == '__main__':
    logger.info("Run as main")
    spider("19610306")
    # 结束线程
    logger.info("Kill Proxies")
    html_downloader.proxies.__exit__()
    logger.info("Process finished with exit code 0")

