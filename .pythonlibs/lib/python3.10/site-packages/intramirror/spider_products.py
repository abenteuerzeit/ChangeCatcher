# -*- coding: UTF-8 -*-
import urllib
import json
import pymysql
import sys


def saveError(key, error, refer, cursor):
    print "saveLog:", key, error
    sql = """
    INSERT INTO `test`.`t_intra_mirror_error` (`key`, `error`, `referer`, `date_added`, `date_modified`) VALUES 
    (%s, %s, %s, now(), now());
    """
    try:
        cursor.execute(sql, (key, str(error), str(refer)))
    except Exception as e:
        print e


def downloadImages(image_urls, product_id):
    for index, image_url in image_urls:
        print image_url, product_id


def checkProductExists(product_id, cursor):
    sql = """
    select product_id from test.t_intra_mirror where product_id=%s
    """
    try:
        cursor.execute(sql, (product_id))
        return cursor.fetchone()
    except Exception as e:
        print e
    return True


def checkSkuExists(product_sku_id, cursor):
    sql = """
    select product_sku_id from test.t_intra_mirror_skus where product_sku_id=%s
    """
    try:
        cursor.execute(sql, (product_sku_id))
        return cursor.fetchone()
    except Exception as e:
        print e
    return True


def saveSkus(skus, cursor):
    for index, sku in enumerate(skus):
        product_sku_id = sku[u'sku_id']
        shop_product_sku_id = sku[u'shop_product_sku_id']
        price = sku[u'price']
        code = sku[u'sku_code']
        name = sku[u'name']
        quantity = sku[u'store'] or None
        product_id = sku[u'product_id']
        sale_price = sku[u'sale_price']
        size = sku[u'productValue']
        try:
            if checkSkuExists(product_sku_id, cursor):
                sql = """
                    UPDATE `test`.`t_intra_mirror_skus` SET  
                    `product_id`=%s, 
                    `name`=%s, 
                    `size`=%s, 
                    `price`=%s, 
                    `sale_price`=%s, 
                    `quantity`=%s,
                    `code`=%s, 
                    `shop_product_sku_id`=%s, 
                    `referer`=%s,
                    `date_modified`=now() WHERE (`product_sku_id`=%s)
                """
                cursor.execute(sql, (
                    product_id, name, size, price, sale_price, quantity, code, shop_product_sku_id,
                    json.dumps(sku), product_sku_id))
            else:
                sql = """
                    INSERT INTO `test`.`t_intra_mirror_skus` 
                    (`product_sku_id`, `product_id`, `name`, `size`, `price`, `sale_price`, `quantity`,`code`, `shop_product_sku_id`, `referer`, `date_added`) VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                """
                cursor.execute(sql, (
                    product_sku_id, product_id, name, size, price, sale_price, quantity, code, shop_product_sku_id,
                    json.dumps(sku)))
        except Exception as e:
            saveError("sku:%s" % (product_sku_id), e, sku, cursor)


def saveProducts(products, cursor):
    for index, product in enumerate(products):
        product_id = product[u'product_id']
        image_urls = json.loads(product[u'cover_img'])
        cover = image_urls[0]
        season = product[u'season']
        season_code = product[u'season_code']
        sale_at = product[u'sale_at']
        img_modified = product[u'img_modified']
        min_price = product[u'minprice']
        shop_product_id = product[u'shop_product_id']
        designer = product[u'brand_englishName']
        skus = product[u'skuList']
        name = None
        if skus:
            name = skus[0][u'name']

        # 检查商品是否已存在
        if checkProductExists(product_id, cursor):
            sql = """
              UPDATE `test`.`t_intra_mirror` SET  
              `cover`=%s, 
              `name`=%s,
              `designer`=%s, 
              `season`=%s, 
              `min_price`=%s, 
              `image_urls`=%s, 
              `shop_product_id`=%s, 
              `referer`=%s, 
              `date_modified`=now() WHERE product_id=%s
            """
            try:
                # 保存商品信息
                cursor.execute(sql, (
                    cover, name, designer, season, min_price, json.dumps(image_urls), shop_product_id,
                    json.dumps(product), product_id))
                # 保存sku 信息
                saveSkus(skus, cursor)
            except Exception as e:
                saveError('product:%s' % (product_id), e, product, cursor)
        else:
            sql = """
              INSERT INTO `test`.`t_intra_mirror` 
              (`product_id`, `cover`, `name`, `designer`, `season`, `min_price`, `image_urls`, `shop_product_id`, `referer`, `date_added`) 
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,now());
            """
            try:
                # 保存商品信息
                cursor.execute(sql, (
                    product_id, cover, name, designer, season, min_price, json.dumps(image_urls), shop_product_id,
                    json.dumps(product)))
                # 保存sku 信息
                saveSkus(skus, cursor)
            except Exception as e:
                saveError('product:%s' % (product_id), e, product, cursor)

                # 下载图片
                # downloadImages(image_urls, product_id)


if __name__ == "__main__":
    spider_pages = None
    if len(sys.argv) == 2:
        spider_pages = int(sys.argv[1])

    db = pymysql.connect(host='172.16.8.147', port=3306, user='dba', passwd='123456', db='asos', charset='utf8mb4')
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    page = urllib.urlopen("http://106.14.205.107:8083/shoplus-buyer/Home/get/getProductList?pageNumber=0&pageSize=30")
    html = page.read().decode("utf8")
    product_info = json.loads(html)
    product_list = product_info[u'productList']
    total_page = product_list[u'totalPage']
    products = product_list[u'list']
    saveProducts(products, cursor)
    db.commit()

    # 参数决定爬多少页
    total_page = spider_pages or total_page

    for i in range(1, total_page):
        url = "http://106.14.205.107:8083/shoplus-buyer/Home/get/getProductList?pageNumber=%s&pageSize=30" % (i)
        print "begin fetch url:", url
        page = urllib.urlopen(url)
        html = page.read().decode("utf8")
        product_info = json.loads(html)
        product_list = product_info[u'productList']
        products = product_list[u'list']
        saveProducts(products, cursor)
        db.commit()
        print "end fetch url:", url
