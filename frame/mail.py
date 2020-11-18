import smtplib
from time import sleep
from email.mime.text import MIMEText
from frame.SpiderFrame import logger
import config


def send_mail(content):
    while True:
        i = 1
        # 设置服务器所需信息
        mail_host = config.MAIL_HOST
        mail_user = config.MAIL_USER
        mail_pass = config.MAIL_PASSWD
        sender = config.MAIL_SENDER

        receivers = config.MAIL_RECEIVERS

        # 设置email信息
        # 邮件内容设置
        message = MIMEText(content, 'plain', 'utf-8')
        # 邮件主题
        message['Subject'] = '爬虫异常终止'
        # 发送方信息
        message['From'] = sender
        # 接受方信息
        message['To'] = receivers[0]

        # 登录并发送邮件
        try:
            smtpObj = smtplib.SMTP()
            # 连接到服务器
            smtpObj.connect(mail_host, 25)
            # 登录到服务器
            smtpObj.login(mail_user, mail_pass)
            # 发送
            smtpObj.sendmail(
                sender, receivers, message.as_string())
            # 退出
            smtpObj.quit()
            logger.info("Successfully send e-mail to: {0} - [{1}]".format(receivers[0], content))
            return
        except Exception:
            logger.error("Fail to send Email, retry {0}times... Message: {1} - [{2}]".format(i, receivers[0], content),
                         exc_info=True)
            i += 1
            sleep(10)

send_mail("test")