# -*- coding: UTF-8 -*-
import oss2

endpoint = "http://oss-cn-shenzhen.aliyuncs.com";
access_key_id = "Ik486j07fnzdJxVC";
access_key_secret = "zv8ESNdIrZ7wv2CZOeEMEgJhiDIoKC";
bucket_name = "ssfk-media01";
aliasUrl = "http://cdn.fashionfinger.com";

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

endpoint2 = "oss-cn-shanghai.aliyuncs.com";
access_key_id2 = "Ik486j07fnzdJxVC";
access_key_secret2 = "zv8ESNdIrZ7wv2CZOeEMEgJhiDIoKC";
bucket_name2 = "images-media";
aliasUrl2 = "http://cdn.fashionfinger.com";

bucketImages = oss2.Bucket(oss2.Auth(access_key_id2, access_key_secret2), endpoint2, bucket_name2)


class PutObjectResult:
    def __init__(self):
        self.status = 200
        self.etag = "EXISTS"


def download_file_from_images_media(oss_url, local_path):
    bucketImages.get_object_to_file(oss_url, local_path)


def put_file(oss_path, file_path, is_rewrite=True):
    if not is_rewrite:
        exists = bucket.object_exists(oss_path)
        if exists:
            print "object exists:", exists
            return PutObjectResult()

    print "put file:", oss_path
    return bucket.put_object_from_file(oss_path, file_path)


def put_file_to_images_media(oss_path, file_path, is_rewrite=True):
    if not is_rewrite:
        exists = bucketImages.object_exists(oss_path)
        if exists:
            print "object exists:", exists
            return PutObjectResult()

    print "put file:", oss_path
    return bucketImages.put_object_from_file(oss_path, file_path)
