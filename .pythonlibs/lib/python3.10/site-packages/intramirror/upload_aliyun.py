# -*- coding: UTF-8 -*-
import oss2

if __name__ == "__main__":
    print  oss2.__version__
    # 以下代码展示了基本的文件上传、下载、罗列、删除用法。
    # 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
    # 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
    #
    # 以杭州区域为例，Endpoint可以是：
    #   http://oss-cn-hangzhou.aliyuncs.com
    #   https://oss-cn-hangzhou.aliyuncs.com
    # 分别以HTTP、HTTPS协议访问。
    # access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
    # access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
    # bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
    # endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')

    endpoint = "http://oss-cn-beijing.aliyuncs.com	";
    access_key_id = "Ik486j07fnzdJxVC";
    access_key_secret = "zv8ESNdIrZ7wv2CZOeEMEgJhiDIoKC";
    bucket_name = "intra-mirror";
    aliasUrl = "http://cdn.fashionfinger.com";

    # 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
    bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

    # 上传一段字符串。Object名是motto.txt，内容是一段名言。
    bucket.put_object('motto.txt', 'Never give up. - Jack Ma')

    # 下载到本地文件
    bucket.get_object_to_file('motto.txt', '本地文件名.txt')
    # 上面两行代码，也可以用下面的一行代码来实现
    bucket.put_object_from_file('yunshang/云上座右铭.txt', '本地文件名.txt')