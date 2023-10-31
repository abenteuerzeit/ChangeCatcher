# -*- coding: UTF-8 -*-
# from bs4 import BeautifulSoup
import re
import json
from mozia.crawler.repository import dao

COLOR_MAPPED = {
    "BLACK": "黑色"
}


# return {
#     "name": product["name"],
#     "label": get_product_label(soup),
#     "gender": get_product_gender(catalog["url"]),
#     "image_urls": get_product_image_urls(soup),
#     "designer_name": product["designerName"],
#     "designer_code": product["designerStyleId"],
#     "source_id": catalog["source_id"],
#     "source_type": catalog["source_type"],
#     "categories": [product["category"], product["subcategory"]],
#     "description": get_product_description(product, soup),
#     "sizes": get_product_sizes(product, catalog),
#     "context": product
# }

# "designerDetails": {
#     "name": "Mm6 Maison Margiela",
#     "designerStyleId": "S52CT0312S25322",
#     "designerColour": "964 RUBBER/FUXIA",
#     "link": {
#         "url": "/cn/shopping/women/mm6-maison-margiela/items.aspx",
#         "text": "Mm6 Maison Margiela",
#         "trackingId": "pp_infobrd"
#     },
#     "id": 114084,
#     "description": "绝不在设计上妥协的MM6是Maison Martin Margiela的主要副线品牌。先将旧衣拆损，然后再将它们拼组成崭新的衣服，其创新精神在此独特的制衣手法得到完美的体现。"
# }

#  "composition": [
# {
#    "material": "成分:",
#    "value": "棉 100%"
# },
# {
#    "material": "成分:",
#    "value": "涤纶 100%"
# }
# ],
# "categories": {
# "135967": "服装",
# "135979": "连衣裙",
# "136189": "OL连衣裙"
# },


# "sizes": {
#     "available": {
#         "19": {
#             "lastInStock": false,
#             "storeId": 9306,
#             "sizeId": 19,
#             "description": "XS",
#             "quantity": 2
#         },
#         "20": {
#             "lastInStock": true,
#             "storeId": 9306,
#             "sizeId": 20,
#             "description": "S",
#             "quantity": 1
#         }
#     },
#     "selectedSize": null,
#     "friendlyScaleName": "",
#     "scaleId": 115,
#     "scaleDescription": "成衣均码",
#     "isOneSize": false
# }

class FarfetchResolver():
    def __init__(self, soup):
        self.soup = soup
        self.product = None

    # /cn/shopping/women/dolce-gabbana-bellucci--item-11845899.aspx?storeid=9306&from=listing
    def get_product_gender(self, url):
        pos = url.find("women")
        return 2 if -1 == pos else 1

    def get_product_color(self):
        colors_string = self.product['details']['colors']
        if not colors_string or ',' not in colors_string:
            return None

        color_values = colors_string.split(",")
        if len(color_values) != 2:
            print("invalid color string:%s" % colors_string)
            return None

        [color_word, color_code] = colors_string.split(",")
        color = dao.catalog.get_product_color(color_code, 1)
        if not color:
            dao.catalog.save_product_color({
                "color_code": color_code,
                "description": color_word,
                "source_type": 1,
                "color_name": COLOR_MAPPED.get(color_word)
            })
            return color_word
        return color["name"]

    def get_product_size(self, sku, color):
        price_info = self.product["priceInfo"]["default"]
        return {
            "original_price": int(price_info["initialPrice"]),
            "size": sku["description"],
            "currency": "EURO",
            "color": color,
            "label": sku["quantity"]
        }

    def get_product_sizes(self, color):
        sizes = self.product['sizes']['available']
        return [
            self.get_product_size(size, color)
            for size in sizes.values()
        ]

    def get_designer_name(self):
        designer_details = self.product['designerDetails']
        return designer_details['name']

    def get_designer_code(self):
        designer_details = self.product['designerDetails']
        return designer_details['designerStyleId']

    def get_compositions(self):
        compositions = self.product['composition']
        items = []
        for item in compositions:
            items.append("%s%s" % (item['material'], item['value']))
        return items

    def get_measurements(self):
        measurements = self.product['measurements']
        if not measurements:
            return []

        if not measurements.get('modelMeasurements'):
            return []

        items = ["模特"]
        for (key, value) in measurements['modelMeasurements'].items():
            items.append("%s:%s" % (key, value[0]))
        return items

    def get_product_description(self):
        product_details = self.product['details']
        items = [product_details['description'] or "" ] + self.get_measurements() + self.get_compositions()
        if items:
            return "\n".join(items)

    def get_product_details(self):
        product_details = self.product['details']
        season = None
        if product_details.get('merchandiseTag'):
            tag = product_details['merchandiseTag']
            season = '18SS' if '新季' == tag else None

        return {
            'name': product_details['shortDescription'],
            'description': self.get_product_description(),
            'source_id': product_details['productId'],
            'source_type': 1,
            'season': season
        }

    # "categories": {
    #     "135967": "服装",
    #     "135979": "连衣裙",
    #     "136189": "OL连衣裙"
    # }
    def get_categories(self):
        categories = self.product['categories']
        items = []
        for category_id in sorted(categories.keys()):
            items.append(categories[category_id])
        # return categories.values()
        return items

    def get_image_urls(self):
        images_main = self.product['images']['main']
        image_urls = []
        for item in images_main:
            image_urls.append(item['zoom'])
        return image_urls

    def process(self):
        pattern = re.compile("window\['__initialState_slice-pdp__'\]\s*=\s*(.*);")
        product_script_soup = self.soup.find("script", text=pattern)

        # 找不到商品代码
        if not product_script_soup:
            return

        match = pattern.match(product_script_soup.string)
        if not match:
            return

        json_object = json.loads(match.group(1))
        self.product = json_object['productViewModel']
        # print(json.dumps(self.product).decode("unicode_escape"))

        color = self.get_product_color()
        product_object = {
            'measurements': self.get_measurements(),
            'designer_name': self.get_designer_name(),
            'designer_code': self.get_designer_code(),
            'compositions': self.get_compositions(),
            'categories': self.get_categories(),
            'image_urls': self.get_image_urls(),
            'sizes': self.get_product_sizes(color)
        }
        product_object.update(self.get_product_details())
        return product_object
