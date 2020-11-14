# -*- coding: utf-8 -*-
"""
@Author      : 满目皆星河
@Project     : 知乎
@File        : user.py
@Time        : 2020/11/12 18:21
@Description : 知乎用户信息爬虫
@Warning     : 请务必在外部函数控制user.html_downloader.proxies.__exit__()来关闭代理，否则代理耗尽
"""

from bs4.element import NavigableString
from bs4 import BeautifulSoup
from frame import SpiderFrame
import config
import re

logger = SpiderFrame.logger
html_downloader = SpiderFrame.HtmlDownloader()
data_saver = SpiderFrame.DataSaver(db_name=config.DB_NAME, set_name=config.USER_SET)
logger.warning("如果是外部函数调用user，请务必在外部函数控制user.html_downloader.proxies.__exit__()来关闭代理，否则会耗尽代理")


def _parse_(html: str, u_id: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    detail_info_list = []
    auth = out_resp = zhihu_include = agreed = liked = pro_confirm = public_edit = follow = \
        followed = pub_judge = follow_topic = follow_column = follow_question = follow_favorite = 0
    try:
        name = soup.find("span", {"class": "ProfileHeader-name"}).text
    except:
        # logger.warning("User id:{0}, name not find".format(u_id))
        raise SpiderFrame.exception.UserNotExist
    try:
        headline = soup.find("span", {"class": "ProfileHeader-headline"}).text
    except:
        logger.warning("User id:{0}, headline not find".format(u_id))
        headline = ''
    try:
        detail_infos = soup.find_all("div", {"class": "ProfileHeader-infoItem"})
        for info in detail_infos:
            for i in info:
                if type(i) == NavigableString:
                    detail_info_list.append(str(i))
    except:
        logger.warning("User id:{0}, detail_info not find".format(u_id))
    try:
        num_info_list = []
        num_info = soup.find_all("span", {"class": "Tabs-meta"})
        if len(num_info) != 7:
            raise SpiderFrame.exception.NumInfoLengthException
        for num in num_info:
            num_info_list.append(int(num.text.replace(",", "")))
    except:
        logger.warning("User id:{0}, num_info not find".format(u_id))
        num_info_list = [0, 0, 0, 0, 0, 0, 0]
    try:
        side_info = soup.find("div", {"class": "Profile-sideColumn"})
        text = side_info.text
        auth = True if "认证信息" in text else False  # 伪三目运算
        out_resp = True if "优秀回答者" in text else False
        try:
            zhihu_include = int(re.findall("知乎收录([0-9, ]*)个回答", text)[0].strip().replace(",", ""))
        except:
            zhihu_include = 0
        try:
            agreed = int(re.findall("([0-9, ]*)次赞同", text)[0].strip().replace(",", ""))
        except:
            agreed = 0
        try:
            liked = int(re.findall("([0-9, ]*)次喜欢", text)[0].strip().replace(",", ""))
        except:
            liked = 0
        try:
            pro_confirm = int(re.findall("([0-9, ]*)次专业认可", text)[0].strip().replace(",", ""))
        except:
            pro_confirm = 0
        try:
            public_edit = int(re.findall("([0-9, ]*)次公共编辑", text)[0].strip().replace(",", ""))
        except:
            public_edit = 0
        try:
            follow = int(re.findall("关注了([0-9, ]*)", text)[0].strip().replace(",", ""))
        except:
            follow = 0
        try:
            followed = int(re.findall("关注者([0-9, ]*)", text)[0].strip().replace(",", ""))
        except:
            followed = 0
        try:
            pub_judge = int(re.findall("([0-9, ]*)次众裁", text)[0].strip().replace(",", ""))
        except:
            pub_judge = 0
        try:
            follow_topic = int(re.findall("关注的话题([0-9, ]*)", text)[0].strip().replace(",", ""))
        except:
            follow_topic = 0
        try:
            follow_column = int(re.findall("关注的专栏([0-9, ]*)", text)[0].strip().replace(",", ""))
        except:
            follow_column = 0
        try:
            follow_question = int(re.findall("关注的问题([0-9, ]*)", text)[0].strip().replace(",", ""))
        except:
            follow_question = 0
        try:
            follow_favorite = int(re.findall("关注的收藏夹([0-9, ]*)", text)[0].strip().replace(",", ""))
        except:
            follow_favorite = 0

    except:
        logger.warning("User id:{0}, side_info not find".format(u_id))
    return {
        "user_token": u_id,
        "name": name,
        "headline": headline,
        "detail_info": ", ".join(detail_info_list),
        "answers": num_info_list[0],
        "videos": num_info_list[1],
        "questions": num_info_list[2],
        "posts": num_info_list[3],
        "columns": num_info_list[4],
        "ideas": num_info_list[5],
        "collections": num_info_list[6],
        "auth": auth,
        "out_response": out_resp,
        "zhihu_include": zhihu_include,
        "agreed": agreed,
        "liked": liked,
        "pro_confirm": pro_confirm,
        "public_edit": public_edit,
        "follow": follow,
        "followed": followed,
        "pub_judge": pub_judge,
        "follow_topic": follow_topic,
        "follow_column": follow_column,
        "follow_question": follow_question,
        "follow_favorite": follow_favorite
    }


def spider(u_id: str) -> None:
    try:
        url = "https://www.zhihu.com/people/{0}".format(u_id)
        res = html_downloader.download(url)
        data = _parse_(res, u_id)
        if data_saver.mg_data_db.find_one({"user_token": u_id}):
            data_saver.mg_data_db.find_one_and_update({"user_token": u_id}, {"$set": data})
        else:
            data_saver.mongo_insert(data)
    except SpiderFrame.exception.UserNotExist as e:
        logger.error(e)
    except Exception as e:
        logger.error(e, exc_info=True)


if __name__ == '__main__':
    logger.info("Run as main")
    input("Warning: 如果是外部函数调用user，请务必在外部函数控制user.html_downloader.proxies.__exit__()来关闭代理，否则会耗尽代理")
    spider("laoqinppt")
    # 结束线程
    logger.info("Kill Proxies")
    html_downloader.proxies.__exit__()
    logger.info("Process finished with exit code 0")
