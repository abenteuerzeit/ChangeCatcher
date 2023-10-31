# -*- coding: UTF-8 -*-
import urllib
import os
import oss2
import json
from repository import dao
from task import get_download_images_task, create_download_images_tasks

endpoint = "http://oss-cn-beijing.aliyuncs.com	"
access_key_id = "Ik486j07fnzdJxVC"
access_key_secret = "zv8ESNdIrZ7wv2CZOeEMEgJhiDIoKC"
bucket_name = "intra-mirror"
aliasUrl = "http://cdn.fashionfinger.com"
# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)


# 内容不全重新下载
def download_until_succeed(url, filename):
    try:
        urllib.urlretrieve(url, filename)
    except urllib.ContentTooShortError:
        print 'Network conditions is not good.Reloading.', url
        download_until_succeed(url, filename)


def download_images(image_urls, product_id):
    local_dir = "data/images/%s" % (product_id)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    oss_urls = []
    for index, url in enumerate(image_urls):
        if url:
            print ">>>>>>>>>>>begin download image:", url
            names = url.split("/")
            name = names[len(names) - 1]
            path = "%s\\%s" % (local_dir, name)
            download_until_succeed(url, path)
            print ">>>>>>>>>>>end download image:", url
            oss_url = "intra_mirror/%s/%s" % (product_id, name)
            bucket.put_object_from_file(oss_url, path)
            oss_urls.append("http://intra-mirror.oss-cn-beijing.aliyuncs.com/%s" % oss_url)
    # update_image_status(dir, oss_urls, product_id, cursor)
    dao.catalog.save_catalog_images(local_dir, oss_urls, product_id)


def start_download(task):
    image_urls = task["image_urls"]
    if not image_urls:
        return
    try:
        download_images(json.loads(image_urls), task["product_id"])
    except Exception as e:
        print  e


if __name__ == "__main__":
    while True:
        task = get_download_images_task()
        while task:
            start_download(task)
            task = get_download_images_task()
        create_download_images_tasks()
