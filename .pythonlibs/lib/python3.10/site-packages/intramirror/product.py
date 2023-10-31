# -*- coding: UTF-8 -*-
import json
import requests
import random
import time
from repository import dao


def crawl_product_from_monitor(product_id, url):
    page = requests.get(url)
    return json.loads(page.content.decode(encoding="utf-8"))


def crawl_product(catalog):
    url = "http://106.14.205.107:8083/shoplus-buyer/api/product?id=%s" % catalog["shop_product_id"]
    page = requests.get(url)
    product_string = page.content.decode(encoding="utf-8")
    product = json.loads(product_string)
    if not product.get("productStatus"):
        print "invalid product:", product, url
        dao.catalog.set_catalog_status(catalog["product_id"], 0)
        return None

    product["context_string"] = json.dumps(product)
    product["product_id"] = catalog["product_id"]
    product["category_id"] = product["categoryId"]
    product["designer_id"] = product["brandId"]
    product["color_code"] = product["colorCode"]
    product["product_status"] = product["productStatus"]
    product["designer_code"] = product["brandCode"]
    product["sale_price"] = product.get("salePrice")
    product["price"] = product.get("price")
    image_urls = product.get("pics")
    product["image_urls"] = json.dumps(image_urls) if image_urls else None
    thumbnails = product.get("thumbnails")
    product["thumbnails"] = json.dumps(thumbnails) if thumbnails else None
    product["skus"] = None
    dao.product.save_product(product)

    product["composition"] = product.get("composition")
    product["product_name"] = product["name"]
    product["location"] = product.get("madeIn")
    product["edd_description"] = product.get("edd_desc")
    product["edd_title"] = product.get("edd_title")
    dao.product.save_description(product)

    product["designer_name"] = product["brand"]
    dao.product.save_designer(product)
    return product


if __name__ == "__main__":
    while True:
        timestamp = int(time.time())
        print "begin crawl products", time.time()
        try:
            for catalog in dao.catalog.find_catalogs_for_task():
                crawl_product(catalog)
                # time.sleep(random.randint(1, 5))
        except Exception as e:
            print "crawl error", e
        print "end crawl products, cost:", int(time.time()) - timestamp
        # 重置连接
        dao.catalog.reset()
        time.sleep(random.randint(10, 15))
