# -*- coding: UTF-8 -*-
from ftplib import FTP
import os
import re
from oss_utils import put_file, put_file_to_images_media
import time
from ftp_client import get_ftp_client

oss_root = "ptncp"

DATA_DIR = "/home/develop/data"
TRANSFER_COVER_DIR = "%s/transfer_covers" % DATA_DIR
DOWNLOAD_COVER_DIR = "%s/download_covers" % DATA_DIR
PROCESS_COVER_DIR = "%s/process_covers" % DATA_DIR


def save_file_to_oss(local_path):
    base_name = os.path.basename(local_path)
    (name, ext) = os.path.splitext(base_name)
    oss_url = oss_root + "/" + name + "/cover" + ext
    return put_file(oss_url, local_path)


def save_file_to_local(ftp_file):
    ftp = get_ftp_client()
    print("save ftp file:", ftp_file)
    today = time.strftime('%Y%m%d', time.localtime(time.time()))
    local_dir = "%s/%s" % (PROCESS_COVER_DIR, today)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    path = "%s/%s" % (local_dir, os.path.basename(ftp_file))
    local_file = open(path, 'wb')  # 打开要保存文件
    ftp.retrbinary("RETR " + ftp_file, local_file.write)  # 保存FTP上的文件
    local_file.close()
    return path


def save_file_to_images_media(path):
    cover_name = os.path.basename(path)
    oss_url = cover_name.replace("-", "/")
    # print(os.path.dirname(oss_url))
    oss_url = "%s/cover.jpg" % os.path.dirname(oss_url)
    put_file_to_images_media(oss_url, path, True)


def is_images_media_cover(cover_path):
    cover_name = os.path.basename(cover_path)
    pattern = re.compile("s[0-9]{2}-[0-9]{4}-[0-9]{6,8}-[0-9]{2}\.jpg")
    return pattern.match(cover_name)


def upload_modified_covers():
    ftp = get_ftp_client()

    for ftp_file in ftp.nlst("cover_modified"):
        path = save_file_to_local(ftp_file)
        if is_images_media_cover(path):
            save_file_to_images_media(path)
        else:
            save_file_to_oss(path)

        ftp.rename(ftp_file, "cover_updated/" + os.path.basename(ftp_file))


def start_cover_uploader():
    while True:
        try:
            timestamp = int(time.time())
            print "[%s]start upload cover" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            upload_modified_covers()
            end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print "[%s]end upload cover, cost %d," % (end_time, (int(time.time()) - timestamp))
            time.sleep(10)
        except Exception as e:
            print repr(e)


if __name__ == "__main__":
    start_cover_uploader()
