# -*- coding: UTF-8 -*-
import json
import re
import time
from modules import network
from bs4 import BeautifulSoup
from repository import dao
from modules.repository import repositories


class IntramirrorCatalogCrawler:
    def __init__(self, task):
        self.task = task

    def start(self):
        url = self.task["url"]
        products = json.loads(network.download(url))
        self.create_catalogs(products["productList"])

    @staticmethod
    def get_product_url(catalog):
        return "http://106.14.205.107:8083/shoplus-buyer/api/product?id=%s" % catalog["shop_product_id"]

    @staticmethod
    def get_product_name(catalog):
        if catalog.get("skuList"):
            return catalog["skuList"][0]["name"]
            # skus = catalog["skuList"]

    @staticmethod
    def get_product_cover(catalog):
        if catalog.get("cover_img"):
            return json.loads(catalog["cover_img"])[0]

    @staticmethod
    def get_product_quantity(product):
        skus = product.get('skuList')
        if not skus:
            return 0
        quantity = 0
        for sku in skus:
            quantity += sku['store'] if sku.get('store') else 0
        return quantity

    def create_catalog(self, product):
        catalog = {
            "source_type": 3,
            "url": self.get_product_url(product),
            "source_id": product["shop_product_id"],
            "catalog_context": json.dumps(product),
            "catalog_status": 0,
            "product_name": self.get_product_name(product),
            "thumbnail": self.get_product_cover(product),
            "language_id": self.task["language_id"],
            "designer_name": product['brand_englishName'],
            "season": product['season_code'],
            "quantity": self.get_product_quantity(product)
        }
        # product["extend"] = extend
        dao.catalog.save_catalog(catalog)

    def create_catalogs(self, products):
        # print(json.dumps(products))
        for product in products["list"]:
            try:
                self.create_catalog(product)
            except Exception as e:
                print(repr(e))


class FarfetchCatalogCrawler:
    def __init__(self, task):
        self.task = task

    @staticmethod
    def get_total_page(soup):
        pagination = soup.find("li", class_="pagination-label")
        total_page = pagination.find("span", attrs={
            "data-tstid": "paginationTotal"
        }).string
        return int(total_page)

    def create_catalogs(self, soup):
        pattern = re.compile("window.universal_variable.listing\s*=\s*({.*});")
        # soup = soup.find(pattern)
        script_soup = soup.find("script", text=pattern)
        match = re.search(pattern, script_soup.string.strip())
        products = json.loads(match.group(1).strip())

        # products = json.loads(soup.string.strip().replace("window.universal_variable.listing =", "").rstrip(";"))
        # extend = json.loads(self.task.get("extend") or "{}")
        # extend["catalog_id"] = products.get("categoryId")

        for product in products["items"]:
            catalog = {
                "source_type": 1,
                "url": product["url"],
                "source_id": product["id"],
                "store_id": product["storeId"],
                "catalog_context": json.dumps(product),
                "catalog_status": 0,
                "product_name": product["name"],
                "thumbnail": product["imageUrl"],
                "language_id": self.task["language_id"],
                "designer_name": product["designerName"],
                "quantity": product["stock"],
                "season": None
            }
            # product["extend"] = extend
            dao.catalog.save_catalog(catalog)

    def crawl(self, page_url, task):
        print("begin url:", page_url)
        html = network.download(page_url)
        soup = BeautifulSoup(html, "html.parser")
        self.create_catalogs(soup)
        print("end url:", page_url)
        return soup

    def start(self):
        task = self.task
        url = task["url"]
        soup = self.crawl(url, task)
        quo = url.find("?")
        total_page = self.get_total_page(soup)

        print("total page(%d):" % total_page, url)
        for i in range(2, total_page):
            page_url = "%s&page=%d" % (url, i) if quo > 0 else "%s?page=%d" % (url, i)
            self.crawl(page_url, task)

            # dao.task.update_task_status(task)
            # try:
            #
            # except Exception as e:
            #     print('repr(e):', repr(e))


def crawl_intramirror_catalogs():
    task = {
        "url": "http://106.14.205.107:8083/shoplus-buyer/Home/get/getProductList?pageNumber=0&pageSize=6000",
        "language_id": 1
    }
    IntramirrorCatalogCrawler(task).start()


def crawl_farfetch_catalogs():
    url_string = """
https://www.farfetch.cn/cn/shopping/women/julian-fashion/items.aspx
https://www.farfetch.cn/cn/shopping/men/julian-fashion/items.aspx
https://www.farfetch.cn/cn/shopping/women/ratti/items.aspx
https://www.farfetch.cn/cn/shopping/men/ratti/items.aspx
https://www.farfetch.cn/cn/shopping/women/Luisa-Boutique/items.aspx
https://www.farfetch.cn/cn/shopping/men/Luisa-Boutique/items.aspx
https://www.farfetch.cn/cn/shopping/women/pozzilei/items.aspx
https://www.farfetch.cn/cn/shopping/men/pozzilei/items.aspx
https://www.farfetch.cn/cn/shopping/women/tessabit/items.aspx
https://www.farfetch.cn/cn/shopping/men/tessabit/items.aspx
https://www.farfetch.cn/cn/shopping/women/tiziana-fausti/items.aspx
https://www.farfetch.cn/cn/shopping/men/tiziana-fausti/items.aspx
https://www.farfetch.cn/cn/shopping/women/Base-blu/items.aspx
https://www.farfetch.cn/cn/shopping/men/Base-blu/items.aspx
https://www.farfetch.cn/cn/shopping/women/Boutique-Sugar/items.aspx
https://www.farfetch.cn/cn/shopping/men/Boutique-Sugar/items.aspx
https://www.farfetch.cn/cn/shopping/women/voga/items.aspx
https://www.farfetch.cn/cn/shopping/men/voga/items.aspx
https://www.farfetch.cn/cn/shopping/women/vinicio/items.aspx
https://www.farfetch.cn/cn/shopping/men/vinicio/items.aspx
https://www.farfetch.cn/cn/shopping/women/Wise-Boutique/items.aspx
https://www.farfetch.cn/cn/shopping/men/Wise-Boutique/items.aspx
https://www.farfetch.cn/cn/shopping/women/fiacchini/items.aspx
https://www.farfetch.cn/cn/shopping/men/fiacchini/items.aspx
https://www.farfetch.cn/cn/shopping/women/mantovani/items.aspx
https://www.farfetch.cn/cn/shopping/men/mantovani/items.aspx
https://www.farfetch.cn/cn/shopping/women/stefania-mode/items.aspx
https://www.farfetch.cn/cn/shopping/men/stefania-mode/items.aspx
https://www.farfetch.cn/cn/shopping/women/coltorti/items.aspx
https://www.farfetch.cn/cn/shopping/men/coltorti/items.aspx
https://www.farfetch.cn/cn/shopping/women/boutique-parisi/items.aspx
https://www.farfetch.cn/cn/shopping/men/boutique-parisi/items.aspx
https://www.farfetch.cn/cn/shopping/women/papini/items.aspx
https://www.farfetch.cn/cn/shopping/men/papini/items.aspx"""

    tasks = [{"url": url.strip(), "language_id": 1} for url in url_string.split("\n") if url.strip()]
    for task in tasks:
        print(task)
        FarfetchCatalogCrawler(task).start()


if __name__ == "__main__":
    repositories.connect()
    crawl_intramirror_catalogs()
    # crawl_farfetch_catalogs()
