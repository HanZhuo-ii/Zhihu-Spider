"""
    @author         满目皆星河
    @creat_date     2020/11/09
    @update_data    2020/11/09
    @desc           话题爬虫，许多question归属于某类话题，爬取这些question的信息（以等待回答为基础）
    @main_function  spider(question_id: str)
"""

from frame import SpiderFrame
import config


class HtmlParser(SpiderFrame.HtmlParser):
    def __init__(self):
        super().__init__()


def spider(topic_id: str):
    first_url = "https://www.zhihu.com/api/v4/topics/{}/feeds/top_question?include=data%5B%3F(target.type%3Dtopic_sticky_module)%5D.target.data%5B%3F(target.type%3Danswer)%5D.target.content%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%3Bdata%5B%3F(target.type%3Dtopic_sticky_module)%5D.target.data%5B%3F(target.type%3Danswer)%5D.target.is_normal%2Ccomment_count%2Cvoteup_count%2Ccontent%2Crelevant_info%2Cexcerpt.author.badge%5B%3F(type%3Dbest_answerer)%5D.topics%3Bdata%5B%3F(target.type%3Dtopic_sticky_module)%5D.target.data%5B%3F(target.type%3Darticle)%5D.target.content%2Cvoteup_count%2Ccomment_count%2Cvoting%2Cauthor.badge%5B%3F(type%3Dbest_answerer)%5D.topics%3Bdata%5B%3F(target.type%3Dtopic_sticky_module)%5D.target.data%5B%3F(target.type%3Dpeople)%5D.target.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics%3Bdata%5B%3F(target.type%3Danswer)%5D.target.annotation_detail%2Ccontent%2Chermes_label%2Cis_labeled%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Canswer_type%3Bdata%5B%3F(target.type%3Danswer)%5D.target.author.badge%5B%3F(type%3Dbest_answerer)%5D.topics%3Bdata%5B%3F(target.type%3Danswer)%5D.target.paid_info%3Bdata%5B%3F(target.type%3Darticle)%5D.target.annotation_detail%2Ccontent%2Chermes_label%2Cis_labeled%2Cauthor.badge%5B%3F(type%3Dbest_answerer)%5D.topics%3Bdata%5B%3F(target.type%3Dquestion)%5D.target.annotation_detail%2Ccomment_count%3B&offset=5&limit=20".format(topic_id)
    html_downloader = SpiderFrame.HtmlDownloader()
    html_parser = HtmlParser()
    data_saver = SpiderFrame.DataSaver(db_name=config.DB_NAME, set_name=config.TOPIC_MONGO_SET_NAME)
    topic_url_manager = SpiderFrame.UrlManager(db_set_name="topic", use_redis=config.TOPIC_UrlManager_USE_REDIS)
    # 如果需要将question的id添加到url队列
    if config.TOPIC_ADD_QUESTIONS_ID:
        question_url_manager = SpiderFrame.UrlManager(db_set_name="question_id", use_redis=config.TOPIC_UrlManager_USE_REDIS)
    # 判断断点续爬
    if topic_url_manager.list_not_null():
        first_url = topic_url_manager.get()

    while True:
        html = html_downloader.download(first_url)
