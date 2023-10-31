# -*- coding: UTF-8 -*-
from ftplib import FTP

__ftp_client__ = None


def get_ftp_client():
    global __ftp_client__
    if not __ftp_client__:
        __ftp_client__ = FTP()
        __ftp_client__.connect(host="172.16.8.151")
        __ftp_client__.login("ftp", "ftp@123456")
        __ftp_client__.cwd("off-images")

    return __ftp_client__
