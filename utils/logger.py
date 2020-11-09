import logging
import time


def custom_logger(__name__):
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Log等级总开关

    # 创建handler，用于写入日志文件
    log_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    log_file = "logs/" + __name__ + "_" + log_time + '.log'

    logging_file_handler = logging.FileHandler(log_file, mode='a+')
    logging_file_handler.setLevel(logging.INFO)  # 输出到file的log等级的开关

    # 定义handler输出格式
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s, line %(lineno)d, in <%(funcName)s>: %(message)s")
    logging_file_handler.setFormatter(formatter)

    # 将logger添加handler里
    logger.addHandler(logging_file_handler)
    return logger
