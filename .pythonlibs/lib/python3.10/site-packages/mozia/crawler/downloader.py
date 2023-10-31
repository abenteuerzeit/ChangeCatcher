# -*- coding: UTF-8 -*-
import oss2
import time
import re
import requests
from repository import dao
from modules.repository import repositories
from modules.scheduler import task_scheduler
from mozia.crawler.tools.oss_utils import download_file_from_images_media
from mozia.crawler.tools import save_file_to_ftp, TRANSFER_COVER_DIR, PROCESS_COVER_DIR, DOWNLOAD_COVER_DIR
import os

endpoint = "oss-cn-shanghai.aliyuncs.com";
access_key_id = "Ik486j07fnzdJxVC";
access_key_secret = "zv8ESNdIrZ7wv2CZOeEMEgJhiDIoKC";
bucket_name = "images-media";
aliasUrl = "http://cdn.fashionfinger.com";

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)


def download_and_retry(url, times=3):
    try:
        return requests.get(url)
    except Exception as e:
        print("download error, retry...", repr(e))
        if times > 0:
            return download_and_retry(url, times - 1)


def save_image_to_oss(task, image_url, index):
    if is_oss_url(image_url):
        return image_url

    print("image url:", image_url)
    oss_url = "s%02d/%04d/%08d/%02d.jpg" % (task["source_type"], task["designer_id"], task["product_id"], index)
    page = download_and_retry(image_url)
    result = bucket.put_object(oss_url, page.content)
    if 200 != result.status:
        raise Exception("save to oss error", result.status)

    return "https://images-media.oss-cn-shanghai.aliyuncs.com/%s" % oss_url


def is_oss_url(image_url):
    if not image_url:
        print("invalid image url:", image_url)
        return False

    pattern = re.compile("http(s)?://images-media\.oss-cn-shanghai\.aliyuncs\.com/.*")
    match = pattern.match(image_url)
    return match


# 下载图片并设置商品图片
def download_images(task):
    print("download images:", task)
    image_urls = dao.platform.get_product_sku_images(task["product_id"])
    if not image_urls or len(image_urls) == 0:
        print("[%s]no images download" % task["product_id"])
        return

    oss_urls = [
        save_image_to_oss(task, image_url, index)
        for (index, image_url) in enumerate(image_urls)
        if image_url
    ]
    save_product_images(task["product_id"], oss_urls)
    # save_cover_to_dir(task, cover)


def save_product_images(product_id, oss_urls):
    cover_url = "%s/cover.jpg" % os.path.dirname(oss_urls[0])
    dao.platform.save_product_images(product_id, cover_url, oss_urls)
    # 封面图片已从源网站下载到阿里云，等待P图人员处理
    dao.task.set_product_task_status(product_id, 1, oss_urls[0])


def add_ftp_cover_task(cover_task):
    return dao.task.add_ftp_cover_task(cover_task)


def save_cover_to_dir(task, cover_url):
    cover_dir = "%s/%s" % (DOWNLOAD_COVER_DIR, time.strftime('%Y%m%d', time.localtime(time.time())))
    if not os.path.isdir(cover_dir):
        os.makedirs(cover_dir)
    path = cover_url.replace("https://images-media.oss-cn-shanghai.aliyuncs.com/", "")
    cover_path = "%s/%s" % (cover_dir, "-".join(path.split("/")))
    print("save cover:", cover_path)
    page = download_and_retry(cover_url)
    cover_file = open(cover_path, "wb")
    cover_file.write(page.content)
    cover_file.close()


def download_oss_cover(cover_url):
    if not cover_url:
        print("Invalid cover url:", cover_url)
        return
    print("download oss cover:", cover_url)

    local_dir = TRANSFER_COVER_DIR
    if not os.path.isdir(local_dir) and not os.path.islink(local_dir):
        os.makedirs(local_dir)

    pattern = re.compile("https://images-media.oss-cn-shanghai.aliyuncs.com/(.*)")
    match = pattern.match(cover_url)
    if match:
        oss_path = match.group(1)
        file_name = oss_path.replace("/", "-")
        local_path = "%s/%s" % (local_dir, file_name)
        # network.download_image(cover_url, local_path)
        download_file_from_images_media(oss_path, local_path)
        # save_file_to_ftp("cover/%s" % file_name, local_path)
    else:
        print("cover url no match:", cover_url)


def start_images_downloader(sleep_seconds=600):
    dao.task.create_product_tasks()
    task = dao.task.get_product_task()
    while task:
        download_images(task)
        task = dao.task.get_product_task()


def start_download_oss_covers(sleep_seconds=30):
    while True:
        task = dao.task.get_ftp_cover_task()
        while task:
            try:
                download_oss_cover(task["cover_url"])
            except Exception as e:
                print('save ftp cover error', repr(e))
            task = dao.task.get_ftp_cover_task()

        time_string = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print("[%s]no ftp cover task, sleep %ss... " % (time_string, sleep_seconds))
        time.sleep(sleep_seconds)


def get_today_covers():
    today = time.strftime('%Y%m%d', time.localtime(time.time()))
    return get_daily_covers(today)


def get_daily_covers(covers_date):
    cover_dir = "%s/%s" % (PROCESS_COVER_DIR, covers_date)
    pattern = re.compile("s[0-9]{2}-[0-9]{4}-[0-9]{6,8}-[0-9]{2}\.jpg")
    if os.path.isdir(cover_dir):
        return [
            name.replace("-", "/")
            for name in os.listdir(cover_dir)
            if pattern.match(name)
        ]
    else:
        os.makedirs(cover_dir)
        return []


def get_cover_dirs():
    if os.path.isdir(PROCESS_COVER_DIR):
        return [
            name for name in os.listdir(PROCESS_COVER_DIR)
        ]
    else:
        return []


if __name__ == "__main__":
    repositories.connect()
    task_scheduler.connect()
    # start_download_oss_covers()
    start_images_downloader(10)
