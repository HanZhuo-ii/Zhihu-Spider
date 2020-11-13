import smtplib
from time import sleep
from email.mime.text import MIMEText
from frame.SpiderFrame import logger


def send_mail(content):
    while True:
        i = 1
        # 设置服务器所需信息
        # 163邮箱服务器地址
        mail_host = 'smtp.163.com'
        # 163用户名
        mail_user = 'hanzhuoii@163.com'
        # 密码(部分邮箱为授权码)
        mail_pass = 'RICFGHQXKBUPWBQN'
        # 邮件发送方邮箱地址
        sender = 'hanzhuoii@163.com'
        # 邮件接受方邮箱地址，注意需要[]包裹，这意味着你可以写多个邮件地址群发
        receivers = ['e.hanzhuo@gmail.com']

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
            logger.error("Fail to send Email, retry {0}times... Message: {1} - [{2}]".format(i, receivers[0], content), exc_info=True)
            i += 1
            sleep(10)
