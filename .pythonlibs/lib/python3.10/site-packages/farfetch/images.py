# -*- coding: UTF-8 -*-
import json
import os
import time
import urllib

import oss2

from keys import KEY_DOWNLOAD_IMAGES
from modules.scheduler.scheudler import RedisTaskScheduler
from repository import create_connection

endpoint = "http://oss-cn-shanghai.aliyuncs.com";
access_key_id = "Ik486j07fnzdJxVC";
access_key_secret = "zv8ESNdIrZ7wv2CZOeEMEgJhiDIoKC";
bucket_name = "farfetch-media";
aliasUrl = "http://cdn.fashionfinger.com";

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

connection = create_connection()


# 内容不全重新下载
def download_with_retry(url, filename):
    try:
        urllib.urlretrieve(url, filename)
    except urllib.ContentTooShortError:
        print 'Network conditions is not good.Reloading.', url
        download_with_retry(url, filename)


def download_images(image_urls, product_id):
    image_dir = "data/images/%s" % product_id
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    oss_urls = []
    for index, image_url in enumerate(image_urls):
        print ">>>>>>>>>>>begin download image:", image_url
        if image_url:
            names = image_url.split("/")
            name = names[len(names) - 1]
            path = "%s\\%s" % (image_dir, name)
            download_with_retry(image_url, path)
            print ">>>>>>>>>>>end download image:", image_url
            oss_path = "farfetch/%s/%s" % (product_id, name)
            bucket.put_object_from_file(oss_path, path)
            oss_url = "http://farfetch-media.oss-cn-shanghai.aliyuncs.com/%s" % oss_path
            oss_urls.append(oss_url)
            save_image_url(image_url, oss_url)
            # update_image_status(dir, oss_urls, product_id, cursor)
    save_image_urls(image_urls, oss_urls, product_id)


def save_image_urls(image_urls, oss_urls, product_id):
    sql = """
    REPLACE INTO `farfetch`.`t_product_image` 
    (`product_id`, `image_urls`, `oss_urls`, `date_added`) 
    VALUES 
    (%s,%s,%s,now());
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, (product_id, json.dumps(image_urls), json.dumps(oss_urls)))
        connection.commit()


def save_image_url(image_url, oss_url):
    sql = """
    REPLACE INTO `farfetch`.`t_download_image` (`image_url`, `oss_url`, `date_added`) VALUES (%s,%s,now());
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, (image_url, oss_url))
        connection.commit()


def get_oss_urls(image_urls):
    length = len(image_urls)
    sql = """
    SELECT * FROM t_download_image WHERE image_url IN (%s)
    """

    with connection.cursor() as cursor:
        cursor.execute(sql % (",".join(["'" + url + "'" for url in image_urls])))
        connection.commit()
        oss_urls = cursor.fetchall()
        if length != len(oss_urls):
            return None

        return [o["oss_url"] for o in oss_urls]


if __name__ == "__main__":
    while True:
        task = RedisTaskScheduler().pop(KEY_DOWNLOAD_IMAGES)
        if not task:
            time.sleep(3)
            continue
        timestamp = int(time.time())
        task = json.loads(task)
        print "begin task:", task
        oss_urls = get_oss_urls(task["image_urls"])
        if oss_urls:
            save_image_urls(task["image_urls"], oss_urls, task["product_id"])
        else:
            download_images(task["image_urls"], task["product_id"])
        print "end task:", task, "cost:", int(time.time()) - timestamp
