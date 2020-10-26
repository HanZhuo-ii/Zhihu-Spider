from frame import SpyderFrame


class JsonParser(SpyderFrame.HtmlParser):
    def __init__(self):
        super.__init__()

    # def user_answered(self):


if __name__ == '__main__':
    USER_BASE_URL = "https://www.zhihu.com/people/"
    JSON_PARSER = JsonParser()
    URL_MANAGER = SpyderFrame.UrlManager("zhihu")
    URL_MANAGER.add_url(USER_BASE_URL + "dear-w-34")
    HTML_DOWNLOADER = SpyderFrame.HtmlDownloader()
    DATA_SAVER = SpyderFrame.DataSaver("知乎", "user")
