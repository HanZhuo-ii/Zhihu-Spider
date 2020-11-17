# Zhihu-Spider
 
 
**utils和tools中的每个.py文件可作为单独程序运行**

**建议在 MongoDB + Redis 环境下运行**


## 知乎项目结构：

config.py 配置文件

main.py 调度所有模块实现全站爬虫

### frame  框架

&nbsp; &nbsp; SpyderFrame.py 通用爬虫框架

### logs 日志

### tools  工具

&nbsp; &nbsp; KeyWordsSearch.py 关键词搜索

&nbsp; &nbsp; HotList.py 热榜监控爬虫，爬知乎每日热榜，可添加定时任务实现热榜监控功能

### utils
&nbsp; &nbsp; topic.py 知乎话题爬虫，爬某个话题下所有question的信息

&nbsp; &nbsp; question.py 知乎回答爬虫，爬某个提问下面全部的回答以及回答的详细信息

&nbsp; &nbsp; comment.py 知乎评论爬虫，爬某个回答下面所有评论

&nbsp; &nbsp; wiki_box.py（Coding） 知乎百科数据，知乎某些question被收录进知乎百科里，这里仅保留百科词条，question具体信息有专门处理的文件（utils/question.py）

&nbsp; &nbsp; user.py 知乎用户信息爬虫

```shell
pip install -r requirements.txt
```
