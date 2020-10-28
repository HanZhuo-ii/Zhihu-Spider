"""
    @author         满目皆星河
    @creat_date     2020/10/06
    @update_data    2020/10/06
    @desc           知乎回答爬虫，爬某个提问下面全部的回答以及回答的详细信息, 存入MongoDB.知乎.questions
    @main_function  spyder(question_id: str)
"""

from frame import SpiderFrame
import json


class HtmlParser(SpiderFrame.HtmlParser):
    def __init__(self):
        super().__init__()
        self.url_manager = SpiderFrame.UrlManager()


def spider(question_id: str):
    """
        :input str in list 列表内嵌套字符串
    """
    base_url_start = "https://www.zhihu.com/api/v4/questions/"
    base_url_end = "/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed" \
                   "%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by" \
                   "%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count" \
                   "%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info" \
                   "%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting" \
                   "%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%2Cpaid_info%2Cpaid_info_content%3Bdata%5B" \
                   "%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics" \
                   "&limit=5&offset=0"
    html_parser = HtmlParser()
    html_downloader = SpiderFrame.HtmlDownloader()
    data_saver = SpiderFrame.DataSaver(db_name="知乎", set_name="questions")

    # 初始化URL队列
    html_parser.url_manager.add_url(url=base_url_start + question_id + base_url_end)
    if not data_saver.mg_data_db.find_one({"QuestionId": question_id}):
        data_saver.mongo_insert({
            "QuestionId": question_id,
            "result": []
        })

    while html_parser.url_manager.not_complete():
        url = html_parser.url_manager.get()
        res = html_downloader.download(url)
        question_json = json.loads(res)
        # 游标，下个数据包URL
        if not question_json["paging"]["is_end"]:
            next_url = question_json["paging"]["next"]
            html_parser.url_manager.add_url(next_url)

        for data in question_json["data"]:
            data_saver.mg_data_db.update_one({"QuestionId": question_id}, {'$addToSet': {"result": data}})

    # 结束线程
    html_downloader.proxies.__exit__()


if __name__ == '__main__':
    question_list = []
    for question in input("请输入问题ID，多个question_id请用英文逗号分隔：").split(","):
        question_list.append(question.strip())

    for question in question_list:
        spider(question)
