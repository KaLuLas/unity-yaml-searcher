import time

def local_time_str(format:str=None):
    """
    日志用
    :param format: 格式字符串，为空默认"%Y-%m-%d %H:%M:%S"
    :return: 本地时间字符串
    """
    formatStr = format or '%Y-%m-%d %H:%M:%S'
    return time.strftime(formatStr, time.localtime())