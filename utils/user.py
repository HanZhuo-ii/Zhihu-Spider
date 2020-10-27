from frame import SpiderFrame


class JsonParser(SpiderFrame.HtmlParser):
    def __init__(self):
        super.__init__()

    # def user_answered(self):


if __name__ == '__main__':
    USER_BASE_URL = "https://www.zhihu.com/people/"
    JSON_PARSER = JsonParser()
    URL_MANAGER = SpiderFrame.UrlManager("zhihu")
    URL_MANAGER.add_url(USER_BASE_URL + "dear-w-34")
    HTML_DOWNLOADER = SpiderFrame.HtmlDownloader()
    DATA_SAVER = SpiderFrame.DataSaver("知乎", "user")
