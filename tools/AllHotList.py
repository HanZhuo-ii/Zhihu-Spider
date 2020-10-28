"""
知乎热榜（全站）
"""

from frame import SpiderFrame
from json import loads as json_lds
from time import localtime, strftime


class HTMLParser(SpiderFrame.HtmlParser):
    def __init__(self, get_detail=False):
        super().__init__()
        self.get_detail = get_detail
        if get_detail:
            self.url_manager = SpiderFrame.UrlManager(db_set_name='知乎@HotList')

    def parse(self, data: dict) -> None:
        _type = data['type']
        if _type == 'hot_list_feed':
            self._hot_list_feed(data)


def get_hot_list(get_detail=False):
    html_downloader = SpiderFrame.HtmlDownloader()
    html_parser = HTMLParser(get_detail)
    data_saver = SpiderFrame.DataSaver(db_name="知乎", set_name="热榜")
    url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true"
    result = {
        "HotListUpdated": strftime("%Y-%m-%d", localtime()),
        "data": []
    }
    while True:
        res = html_downloader.download(url)
        res = json_lds(res)
        for data in res['data']:
            html_parser.parse(data)
            result['data'].append(data)
        if res['paging']['is_end']:
            break
        url = res['paging']['next']

    html_downloader.proxies.__exit__()
    data_saver.mongo_insert(result)
    print('Complete!')




if __name__ == '__main__':
    get_hot_list()
