# -*- coding: UTF-8 -*-
import requests
import json
from repository import dao


def crawl_third_category():
    category_ids = [1504, 1505, 1506, 1507, 1569, 1584, 1598, 1608]
    url = "http://106.14.205.107:8083/shoplus-buyer/product/get/threeCategories?parent_category_id=%d"
    for category_id in category_ids:
        page = requests.get(url % category_id)
        category = json.loads(page.content.decode(encoding="utf-8"))
        print json.dumps(category)
        dao.category.save_categories(category["categories"])


def crawl_category():
    url = "http://106.14.205.107:8083/shoplus-buyer/product/get/categories?parent_category_id=1568"
    page = requests.get(url)
    category = json.loads(page.content.decode(encoding="utf-8"))
    print json.dumps(category)
    dao.category.save_categories(category["categories"])


if __name__ == "__main__":
    crawl_third_category()
