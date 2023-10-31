# -*- coding: UTF-8 -*-
import json
import re
import time

from bs4 import BeautifulSoup

import network
from converter import ProductConverter
from keys import KEY_PRODUCT_TASK, KEY_DOWNLOAD_IMAGES, KEY_PRODUCT_OVERSOLD
from modules.scheduler import task_scheduler
from repository import dao
from task import create_product_tasks


class Product:
    def __init__(self):
        self.host = "https://www.farfetch.cn/"

    @staticmethod
    def get_language(language_id):
        if 1 == language_id:
            return "cn"
        elif 3 == language_id:
            return "it"
        elif 2 == language_id:
            return "it"

    def get_sizes_url(self, product, language_id):
        url = "/product/GetDetailState?productId=%s&storeId=%s&sizeId=&categoryId=%s&designerId=%s"
        return self.host + self.get_language(language_id) + url % (product["product_id"],
                                                                   product["store_id"],
                                                                   product["category_id"],
                                                                   product["manufacturer_id"])

    @staticmethod
    def get_store_id(product, url):
        if product.get("storeId"):
            return product["storeId"]

        pattern = re.compile("storeid=(\d+)")
        match = pattern.findall(url)
        if match:
            return match[0]
        return None

    def crawl(self, url, index, link):
        timestamp = int(time.time())
        print("begin url:%s - %s, %s" % (url, index, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
        html = network.download(url)
        if not html:
            return

        soup = BeautifulSoup(html, "html.parser")
        script_soup = soup.find("script", text=re.compile("window.universal_variable.product\s*=\s*"))

        # 找不到商品信息
        if not script_soup:
            # 商品已售罄
            print "product sold out:", link
            dao.catalog.set_catalog_status(link, 2)
            task_scheduler.push(KEY_PRODUCT_OVERSOLD, json.dumps(link))
            return

        product = json.loads(
            script_soup.string.strip().replace("window.universal_variable.product =", "").strip().rstrip(";"))
        product["product_id"] = product["id"]
        product["manufacturer_id"] = product["manufacturerId"]
        product["category_id"] = product["categoryId"]
        product["language_id"] = link["language_id"]
        product["store_id"] = self.get_store_id(product, url)
        product["source_url"] = url

        # 获取尺码的请求地址
        sizes_url = self.get_sizes_url(product, link["language_id"])

        # 获取尺码信息
        sizes_string = network.download(sizes_url)
        # 将内容提交给解析器
        converter = ProductConverter(soup, product, sizes_string, link["language_id"])
        # 开始解析商品
        product = converter.create()

        print "product:", json.dumps(product)
        # 没有尺码 / 售罄
        if converter.is_sold_out() or not converter.get_product_sizes():
            print "product sold out", product["product_id"]
            product["product_status"] = "OVERSOLD"

        # 保存到数据库
        dao.product.save(product, link["language_id"])

        # # 添加图片下载任务
        task_scheduler.push(KEY_DOWNLOAD_IMAGES, json.dumps({
            "product_id": product["product_id"],
            "image_urls": product["image_urls"]
        }))

        # 更新目录状态
        dao.catalog.set_catalog_status(link, 1)
        print("end url:%s - %s, cost:%d" % (url, index, int(time.time()) - timestamp))

    def start(self):
        index = 0
        product_task = task_scheduler.pop(KEY_PRODUCT_TASK)
        while product_task:
            timestamp = int(time.time())
            product_task = json.loads(product_task)
            if not product_task.get("language_id"):
                print "product no language special:", product_task["product_id"]
                continue

            print "start crawl product(%d)" % product_task["product_id"]
            print "start task:", product_task
            url = "https://www.farfetch.cn%s" % product_task["url"]
            self.crawl(url, index, product_task)
            index = index + 1
            print "end crawl product(%d), cost(%d)s" % (product_task["product_id"], int(time.time()) - timestamp)
            product_task = task_scheduler.pop(KEY_PRODUCT_TASK)


if __name__ == "__main__":
    while True:
        create_product_tasks()
        Product().start()
        print ">>>>>>>>>>> [S]create product tasks and sleep <<<<<<<<<<<"
        time.sleep(30)
