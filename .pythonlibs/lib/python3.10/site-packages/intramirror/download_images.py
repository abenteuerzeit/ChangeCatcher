# -*- coding: UTF-8 -*-
import urllib
import os
import pymysql
import json
import sys
import oss2

endpoint = "http://oss-cn-beijing.aliyuncs.com	";
access_key_id = "Ik486j07fnzdJxVC";
access_key_secret = "zv8ESNdIrZ7wv2CZOeEMEgJhiDIoKC";
bucket_name = "intra-mirror";
aliasUrl = "http://cdn.fashionfinger.com";

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)


# 内容不全重新下载
def download_with_retry(url, filename):
    try:
        urllib.urlretrieve(url, filename)
    except urllib.ContentTooShortError:
        print 'Network conditions is not good.Reloading.', url
        download_with_retry(url, filename)


def download_images(image_urls, product_id, cursor):
    dir = "spider/intra_mirror/%s" % (product_id)
    if not os.path.exists(dir):
        os.makedirs(dir)

    oss_urls = []
    for index, url in enumerate(image_urls):
        print ">>>>>>>>>>>begin download image:", url
        if url:
            names = url.split("/")
            name = names[len(names) - 1]
            path = "%s\\%s" % (dir, name)
            download_with_retry(url, path)
            print ">>>>>>>>>>>end download image:", url
            oss_url = "intra_mirror/%s/%s" % (product_id, name)
            bucket.put_object_from_file(oss_url, path)
            oss_urls.append("http://intra-mirror.oss-cn-beijing.aliyuncs.com/%s" % (oss_url))
    update_image_status(dir, oss_urls, product_id, cursor)


def update_image_status(dir, oss_urls, product_id, cursor):
    sql = """
        REPLACE INTO `test`.`t_intra_mirror_images` 
        (`product_id`,`local_dir`, oss_urls, `date_added`) 
        VALUES 
        (%s, %s, %s, now())
    """
    try:
        # 保存商品信息
        cursor.execute(sql, (product_id, dir, json.dumps(oss_urls)))
    except Exception as e:
        print e


if __name__ == "__main__":
    print sys.argv[0]
    limit_str = "limit 10"
    if len(sys.argv) == 2:
        limit_str = "limit %s" % (sys.argv[1])
    elif len(sys.argv) == 3:
        limit_str = "limit %s, %s" % (sys.argv[1], sys.argv[2])

    dbQuery = pymysql.connect(host='172.16.8.147', port=3306, user='dba', passwd='123456', db='test', charset='utf8mb4')
    cursor = dbQuery.cursor()

    dbUpdate = pymysql.connect(host='172.16.8.147', port=3306, user='dba', passwd='123456', db='test',
                               charset='utf8mb4')
    cursorUpdate = dbUpdate.cursor()
    sql = """
    select a.product_id, a.image_urls from t_intra_mirror a LEFT JOIN t_intra_mirror_images b ON a.product_id = b.product_id where b.local_dir is null %s
    """
    print "sql:", sql % (limit_str)
    try:
        cursor.execute(sql % (limit_str))
        data = cursor.fetchone()
        while data:
            image_urls = json.loads(data[1])
            download_images(image_urls, data[0], cursorUpdate)
            dbUpdate.commit()
            data = cursor.fetchone()
    except Exception as e:
        print e
    dbQuery.commit()
    dbQuery.close()
    dbUpdate.close()
