"""
    @author         满目皆星河
    @creat_date     2020/10/06
    @update_data    2020/10/06
    @desc           评论爬虫，提供answer的id，爬该answer下所有评论
    @main_function  spyder(question_id: str)
"""

from frame import SpiderFrame
from json import loads as json_lds


def spider(answer_id: str) -> None:
    html_downloader = SpiderFrame.HtmlDownloader()
    data_saver = SpiderFrame.DataSaver(db_name='知乎', set_name='评论')
    url = "https://www.zhihu.com/api/v4/answers/{}/root_comments?limit=10&offset=0&order=normal&status=open" \
        .format(answer_id)
    res = html_downloader.download(url)
    res = json_lds(res)
    if not data_saver.mg_data_db.find_one({"AnswerID": answer_id}):
        data_saver.mongo_insert({
            "AnswerID": answer_id,
            "common_counts": res['paging']['totals'],
            "result": []
        })
    while True:
        for data in res['data']:
            data_saver.mg_data_db.update_one({"AnswerID": answer_id}, {'$addToSet': {"result": data}})
        if res['paging']['is_end']:
            break
        url = res['paging']['next']
        res = html_downloader.download(url)
        res = json_lds(res)
    # exit
    html_downloader.proxies.__exit__()


if __name__ == '__main__':
    spider('1546030375')
