# -*- coding: UTF-8 -*-
import requests
import urllib

session = requests.Session()


def download(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
    }
    if url.startswith("//"):
        url = "http:%s" % url

    try:
        page = session.get(url, headers=headers)
        return page.content
    except Exception as e:
        print("download error:%s, retrying" % url, repr(e))
        return download(url)


# 内容不全重新下载
def download_image(url, filename):
    try:
        urllib.urlretrieve(url, filename)
    except urllib.ContentTooShortError:
        print 'Network conditions is not good.Reloading.', url
        download_image(url, filename)
