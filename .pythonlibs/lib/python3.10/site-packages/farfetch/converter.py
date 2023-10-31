# -*- coding: UTF-8 -*-
import json
import re
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


class ProductConverter:
    def __init__(self, soup, product, sizes_string, language_id):
        self.soup = soup
        self.product = product
        self.language_id = language_id
        if sizes_string:
            sizes_wrapper = json.loads(sizes_string)["SizesInformationViewModel"]
            self.sizes = [self.get_product_size(size, sizes_wrapper["IsLowStock"]) for size in
                          sizes_wrapper["AvailableSizes"]]
        else:
            self.sizes = []

    @staticmethod
    def get_text_strings(soup):
        if not soup:
            return None

        lines = []
        dt = soup.find("dt")
        while dt:
            dd = dt.find_next_sibling("dd")
            lines.append(dt.string.strip() + dd.string.strip() if dd else "")
            dt = dd.find_next_sibling("dt")
        return lines

    def get_product_size(self, size_context, low_stock):
        price_info = size_context["PriceInfo"]
        size = {
            "size": size_context["Description"],
            "size_id": size_context["SizeId"],
            "store_id": size_context["StoreId"],
            "scale_id": size_context["ScaleId"],
            "market_price": price_info.get("Price"),
            "scale": size_context["ScaleDescription"]
        }

        if size_context["LastInStock"]:
            size["quantity"] = 1
        else:
            size["quantity"] = 0 if low_stock else None

        formated_price_without_promotion = price_info["FormatedPriceWithoutPromotion"]
        formated_price = price_info["FormatedPrice"]
        if formated_price_without_promotion:
            size["price"] = formated_price_without_promotion
            size["sale_price"] = formated_price
        else:
            size["price"] = formated_price
            size["sale_price"] = formated_price
        if 1 == self.language_id:
            size["currency"] = size["price"][:1]
            size["price"] = (size["price"][1:]).replace(",", "")
            size["sale_price"] = (size["sale_price"][1:]).replace(",", "")
        elif 3 == self.language_id or 2 == self.language_id:
            size["currency"] = size["price"][-1:]
            size["price"] = (size["price"][:-1]).replace(".", "").strip()
            size["sale_price"] = (size["sale_price"][:-1]).replace(".", "").strip()

        return size

    def get_product_sizes(self):
        return self.sizes

    # 如果全是英文需要翻译
    def description(self):
        description = self.soup.find("p", itemprop="description").string.strip()
        return description

    def color(self):
        soup = self.soup.find("span", itemprop="color")
        return soup.string.strip() if soup else None

    # 尺码信息
    def size_description(self):
        content_size_soup = self.soup.find("div", attrs={"data-tstid": "Content_Size&Fit"})
        if not content_size_soup:
            return None

        size_soup = content_size_soup.find("div", class_="mb30")
        strings = []
        if size_soup:
            strings += [string for string in size_soup.stripped_strings]

        measure_info_soup = content_size_soup.find("div", class_="measure-info")
        if measure_info_soup:
            for string in measure_info_soup.stripped_strings:
                strings.append(string)

        centimeters_soup = content_size_soup.find(id="centimeters_wrapper")
        if centimeters_soup:
            if centimeters_soup.dl.p:
                strings.append(centimeters_soup.dl.p.string.strip())
            if centimeters_soup.dl:
                measure_strings = self.get_text_strings(centimeters_soup.dl)
                strings += measure_strings

        model_is_wearing_soup = content_size_soup.find("p", class_="model_is_wearing")
        if model_is_wearing_soup:
            strings.append("".join([x for x in model_is_wearing_soup.stripped_strings]))

        return "\n".join(strings)

    def location(self):
        soup = self.soup.find("span", attrs={"data-tstid": "shippingCountryName"})
        if soup:
            return soup.string.strip()

    def designer_code(self):
        soup = self.soup.find("p", attrs={"data-tstid": "designerStyleId"})
        return soup.span.string.strip() if soup else None

    def category_id(self):
        return self.product["categoryId"]

    def manufacturer_id(self):
        return self.product["manufacturerId"]

    def designer_name(self):
        return self.product["designerName"]

    def price(self):
        return self.product["unitPrice"]

    def sale_price(self):
        return self.product["unitSalePrice"]

    def name(self):
        return self.product["name"]

    def product_id(self):
        return self.product["id"]

    def store_id(self):
        return self.product["storeId"]

    def currency(self):
        currency_code = self.product["currency"]
        if "EUR" == currency_code:
            return "EURO"
        else:
            return "RMB"

    def constitute(self):
        # data - tstid = "Content_Composition&amp;Care" >
        ingredients = self.soup.find("div", attrs={
            "data-tstid": re.compile("Content_Composition")
        })
        lines = self.get_text_strings(ingredients)
        return "\n".join(lines)

    def image_urls(self):
        images = []
        soup = self.soup.find("ul", class_="sliderProduct js-sliderProduct js-sliderProductPage")
        for image in soup.find_all("img", itemprop="image"):
            image_url = image["src"]
            # 图片只是 70 换成 1000
            images.append(image_url[:-6] + "1000.jpg")
        return images

    def gender(self):
        gender = self.product["gender"]
        if "MEN" == gender.upper():
            return 2
        elif "WOMEN" == gender.upper():
            return 1
        else:
            return 4

    def is_sold_out(self):
        sold_out_soup = self.soup.find("div", class_="soldOut color-red bold h4")
        if sold_out_soup:
            return sold_out_soup.prettify()

    def create(self):
        product = {
            "description": self.description(),
            "size_description": self.size_description(),
            "color": self.color(),
            "constitute": self.constitute(),
            "designer_code": self.designer_code(),
            "image_urls": self.image_urls(),
            "sizes": self.get_product_sizes(),
            "gender": self.gender(),
            "location": self.location(),
            "resource_code": self.product["product_id"],
            "designer": self.product["designerName"],
            "is_sold_out": self.is_sold_out(),
            "currency": self.currency(),
            "cover": self.product["imageUrl"]
        }
        return dict(self.product, **product)
