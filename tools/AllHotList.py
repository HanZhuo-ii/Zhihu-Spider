"""
知乎热榜（全站）
"""

from frame import SpiderFrame
import json


class HTMLParser(SpiderFrame.HtmlParser):

    def parse(self, data_list: list) -> dict:
        for data in data_list:
            _type = data['type']
            if _type == 'hot_list_feed':
                yield self._hot_list_feed(data)


def get_hot_list():
    html_downloader = SpiderFrame.HtmlDownloader()
    html_parser = HTMLParser()
    data_saver = SpiderFrame.DataSaver(db_name="知乎", set_name="热榜")
    url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true"
    while True:
        res = html_downloader.download(url)
        res = json.loads(res)
        for data in html_parser.parse(res['data']):
            data_saver.mongo_insert(data)
        if res['paging']['is_end']:
            break

    html_downloader.proxies.__exit__()
    print('Complete!')


if __name__ == '__main__':
    get_hot_list()
