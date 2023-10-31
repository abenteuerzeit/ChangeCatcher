# -*- coding: UTF-8 -*-
from modules import network
import json


def get_product_gender(product):
    if 1568 == product["category1Id"]:
        return 1
    elif 1499 == product["category1Id"]:
        return 2
    else:
        return 3


def get_product_categories(product):
    categories_string = "%s/%s" % (product["category1"], product["category2"])
    return categories_string.split("/")


def get_product_sizes(product):
    skus = product["skus"] if product.get("skus") else []
    supply_price = product.get("salePrice")
    original_price = product.get("price")
    return [
        {
            "size": sku["size"],
            "quantity": sku["count"],
            "supply_price": supply_price,
            "original_price": original_price,
            "currency": "EURO",
            "label": sku["count"]
        }
        for sku in skus
    ]


def get_product_season(catalog):
    context = catalog.get('context')
    if context and context.get("context"):
        context = json.loads(context.get("context"))
        return context.get("season")


def crawl_intramirror_product(catalog):
    page_content = network.download(catalog["url"])
    product = json.loads(page_content.decode(encoding="utf-8"))
    if not product.get("productStatus"):
        print("product no found:", product, catalog["url"])
        return None

    # return this.sourceProduct.category1 + "/" + this.sourceProduct.category2
    # print (json.dumps(product).decode("unicode_escape"))
    return {
        "name": product["name"],
        "source_id": catalog["source_id"],
        "source_type": catalog["source_type"],
        "image_urls": product["pics"],
        "description": product["description"],
        "designer_name": product["brand"],
        "designer_code": product["brandCode"],
        "season": get_product_season(catalog),
        "gender": get_product_gender(product),
        "categories": get_product_categories(product),
        "sizes": get_product_sizes(product),
        "context": product
    }
