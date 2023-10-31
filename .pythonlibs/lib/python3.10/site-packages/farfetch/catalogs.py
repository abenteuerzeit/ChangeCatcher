# -*- coding: UTF-8 -*-
import json
import re
import time
import urllib

from bs4 import BeautifulSoup

from keys import KEY_CATALOG_TASK
from modules.scheduler import task_scheduler
from repository import dao
from task import create_catalog_tasks


class Catalog:
    def __init__(self, language_id=1):
        self.language_id = language_id
        self.store_url = None

    def get_language_id(self):
        return self.language_id

    # 检查商品是否发生了变化
    @staticmethod
    def has_change(product, product_exists):
        context = product["context"]
        context = sorted(context.items(), lambda x, y: cmp(x[1], y[1]))
        context_exists = json.loads(product_exists["context"])
        context_exists = sorted(context_exists.items(), lambda x, y: cmp(x[1], y[1]))
        return str(context) == str(context_exists)

    @staticmethod
    def get_total_page(soup):
        pagination = soup.find("li", class_="pagination-label")
        total_page = pagination.find("span", attrs={
            "data-tstid": "paginationTotal"
        }).string
        return int(total_page)

    def create_catalogs(self, soup):
        soup = soup.find(text=re.compile("window.universal_variable.listing"))
        products = json.loads(soup.string.strip().replace("window.universal_variable.listing =", "").rstrip(";"))
        category_id = products["categoryId"] if products.get("categoryId") else None

        for item in products["items"]:
            product = {
                "catalog_context": json.dumps(item),
                "product_name": item[u"name"],
                "cover": item[u"imageUrl"],
                "url": item[u"url"],
                "store_id": item[u"storeId"],
                "stock": item[u"stock"],
                "designer": item[u"designerName"],
                "currency": item[u"currency"],
                "price": item[u"unit_price"],
                "product_id": item[u"id"],
                "category_id": category_id,
                "sizes": None,
                "tag": None,
                "language_id": self.get_language_id()
            }
            yield dict(item, **product)

    def crawl(self, page_url, task):
        print "begin url:", page_url
        page = urllib.urlopen(page_url)
        html = page.read()
        soup = BeautifulSoup(html, "html.parser")
        for catalog in self.create_catalogs(soup):
            catalog["task_id"] = task["task_id"]
            catalog["gender"] = task["gender"]
            dao.catalog.save_catalog(catalog)
        print "end url:", page_url
        dao.common.update_catalog_task(task)
        return soup

    def crawl_pages(self, task):
        try:
            language = "cn" if 1 == self.get_language_id() else "it"
            url = task[u"url"].strip().replace("/it/", "/%s/" % language)
            self.store_url = url
            soup = self.crawl(url, task)
            quo = url.find("?")
            total_page = self.get_total_page(soup)
            print "total page(%d):" % total_page, url
            for i in range(2, total_page):
                page_url = "%s&page=%d" % (url, i) if quo > 0 else "%s?page=%d" % (url, i)
                self.crawl(page_url, task)
        except Exception as e:
            print 'repr(e):\t', repr(e)

    def start(self):
        catalog_task = task_scheduler.pop(KEY_CATALOG_TASK)
        while catalog_task:
            timestamp = int(time.time())
            catalog_task = json.loads(catalog_task)
            print "[%s]start crawl catalog:" % catalog_task["task_id"], catalog_task["url"]
            self.crawl_pages(catalog_task)
            print "[%s]end crawl catalog, cost(%d)s" % (catalog_task["task_id"], int(time.time()) - timestamp)
            catalog_task = task_scheduler.pop(KEY_CATALOG_TASK)

    @staticmethod
    def get_catalog(product_id):
        return dao.catalog.get_catalog_by_product_id(product_id)


if __name__ == "__main__":
    while True:
        create_catalog_tasks()
        Catalog(language_id=1).start()
        Catalog(language_id=2).start()
        print ">>>>>>>>>>> [S]create catalog tasks and sleep <<<<<<<<<<<"
        time.sleep(100)
