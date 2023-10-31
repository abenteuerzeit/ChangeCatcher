import requests
import json
import time
from repository import dao


def get_total_page():
    page = requests.get("http://106.14.205.107:8083/shoplus-buyer/Home/get/getProductList?pageNumber=0&pageSize=30")
    product_info = json.loads(page.content)
    product_list = product_info[u'productList']
    total_page = product_list[u'totalPage']
    return int(total_page)


def crawl_catalog():
    url = "http://106.14.205.107:8083/shoplus-buyer/Home/get/getProductList?pageNumber=%s&pageSize=30"
    for i in range(0, get_total_page()):
        print "start url:", url % i
        page = requests.get(url % i)
        product_info = json.loads(page.content.decode(encoding="utf-8"))
        product_list = product_info[u'productList']
        products = product_list[u'list']
        dao.catalog.save_catalogs(products)


if __name__ == "__main__":
    while True:
        try:
            crawl_catalog()
        except Exception as e:
            print e
        dao.catalog.reset()
        time.sleep(600)
