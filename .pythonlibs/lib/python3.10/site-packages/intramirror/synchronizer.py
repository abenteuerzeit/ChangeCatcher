# -*- coding: UTF-8 -*-
import pymysql
import json
import time


class DesignerSynchronizor:
    def __init__(self):
        self.connection = pymysql.connect(host='172.16.8.147',
                                          port=3306,
                                          user='dba',
                                          passwd='123456',
                                          db='fashion_product',
                                          cursorclass=pymysql.cursors.DictCursor,
                                          charset='utf8mb4')

    def start(self):
        sql = """
        SELECT DISTINCT (TRIM(designer)) AS designer_name FROM  test.t_intra_mirror
        WHERE TRIM(designer) NOT IN (  SELECT `name` FROM fashion_product.t_designer b )
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            for designer in cursor.fetchall():
                self.create_designer(designer)

    def create_designer(self, designer):
        sql = """
        INSERT INTO `fashion_product`.`t_designer` (
            `name`,`first_char`,`desc`, `create_time`,`deleted`) VALUES (%s,%s,'intra mirror',UNIX_TIMESTAMP(),'0')
        """
        print "save designer", designer
        designer_name = designer["designer_name"]
        first_char = designer_name[1].upper()
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (designer_name, first_char))
            self.connection.commit()


"""
DELETE FROM t_shop_product_sku WHERE sn LIKE "intramirror%";
DELETE FROM t_shop_product WHERE sn LIKE "intramirror%";
DELETE FROM t_shop_stock WHERE shop_product_sku_id IN (SELECT shop_product_sku_id FROM t_shop_product_sku WHERE sn LIKE "intramirror%");
"""


class ProductSynchronizer:
    def __init__(self):
        # 连接平台数据库
        self.platform_connection = pymysql.connect(host='10.26.235.6',
                                                   port=3066,
                                                   user='dba',
                                                   passwd='123456',
                                                   db='fashion_product',
                                                   cursorclass=pymysql.cursors.DictCursor,
                                                   charset='utf8mb4')

        # 连接intramirror数据库
        self.intramirror_connection = pymysql.connect(host='172.16.8.147',
                                                      port=3306,
                                                      user='dba',
                                                      passwd='123456',
                                                      db='test',
                                                      cursorclass=pymysql.cursors.DictCursor,
                                                      charset='utf8mb4')
        self.designers = {}
        self.load_designers()
        self.created_counter = 0
        self.updated_counter = 0

    # 加载品牌信息
    def load_designers(self):
        sql = "SELECT * FROM fashion_product.t_designer"
        with self.platform_connection.cursor() as cursor:
            cursor.execute(sql)
            for designer in cursor.fetchall():
                self.designers[designer["name"].strip().upper()] = designer
        print json.dumps(self.designers)

    # 加载爬虫商品列表
    def load_products(self):
        sql = """
        SELECT * FROM test.t_intra_mirror a
        """
        with self.intramirror_connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    # 通过品牌名称获取品牌信息
    def get_designer_id(self, name):
        name = name.upper()
        if self.designers.get(name):
            return self.designers[name]["designer_id"]

        sql = """
        SELECT * FROM fashion_product.t_designer WHERE `name`=%s
        """
        with self.platform_connection.cursor() as cursor:
            cursor.execute(sql, name)
            designer = cursor.fetchone()
            return designer["designer_id"] if designer else None

    def start(self, shop_id):
        for product in self.load_products():
            product["_name"] = product["name"]
            product["_status"] = "Created"
            product["shop_id"] = shop_id
            product["currency"] = "EUR"
            product["designer_id"] = self.get_designer_id(product["designer"])
            product["sn"] = "intramirror:" + str(product["product_id"])
            # 创建商品
            self.create_product(product)

    # 检查商品是否存在
    def check_product(self, product):
        sql = """
        SELECT * FROM fashion_product.t_shop_product WHERE sn=%s LIMIT 1
        """
        with self.platform_connection.cursor() as cursor:
            cursor.execute(sql, product["sn"])
            return cursor.fetchone()

    # 获取爬虫商品sku
    def get_product_skus(self, product):
        sql = """
        SELECT * FROM test.t_intra_mirror_skus WHERE product_id=%s
        """
        with self.intramirror_connection.cursor() as cursor:
            cursor.execute(sql, product["product_id"])
            return cursor.fetchall()

    # 创建商品sku
    def create_product_sku(self, sku, product):
        print "create product sku:", sku
        sql = """
        INSERT INTO `fashion_product`.`t_shop_product_sku` 
        (`shop_product_id`, `size`, `price`, `settlement_price`, `sn`, `status`, `create_time`, `deleted`) 
        VALUES 
        (%(shop_product_id)s, %(size)s, %(price)s, %(sale_price)s, %(im_code)s, 'Created', unix_timestamp(), '0');
        """
        timestamp = str(int(round(time.time() * 1000)))
        sku["shop_product_id"] = product["shop_product_id"]
        sku["im_code"] = "intramirror#" + (sku["code"] if sku["code"] != "#" else timestamp)
        sku["size"] = sku["size"]
        with self.platform_connection.cursor() as cursor:
            cursor.execute(sql, sku)
            sku["shop_product_sku_id"] = cursor.lastrowid
            self.platform_connection.commit()

    # 设置库存数量
    def create_product_stock(self, sku, product):
        print "create product sku stock:", sku["quantity"], ">>>>>>>>>>>>>>>"
        sql = """
        REPLACE INTO `fashion_product`.`t_shop_stock` 
        (`shop_product_id`, `shop_product_sku_id`, `shop_id`, `quantity`, `create_time`) 
        VALUES 
        (%(shop_product_id)s,%(shop_product_sku_id)s,%(shop_id)s,%(quantity)s,unix_timestamp());
        """
        sku["shop_id"] = product["shop_id"]
        with self.platform_connection.cursor() as cursor:
            cursor.execute(sql, sku)
            self.platform_connection.commit()

    def update_product(self, product):
        print "[%d]product exists, skip >>>>>>>>>>" % self.updated_counter, product["product_id"]
        return

    def get_season_code(self, product):
        referer = json.loads(product["referer"])
        return referer["season_code"] if referer.get("season_code") else None

    # 从 intramirror 爬虫库创建商品到平台库
    def create_product(self, product):
        # 检查商品是否存在
        product_exists = self.check_product(product)
        if product_exists:
            self.updated_counter = self.updated_counter + 1
            return self.update_product(product)

        product["season_code"] = self.get_season_code(product)
        print "[%d]create product:" % self.created_counter, product
        sql = """
        INSERT INTO `fashion_product`.`t_shop_product` 
        (`name`, `sn`, `price`, `settlement_price`, `currency`, `designer_id`,`shop_id`, `status`, `cover`, `images`,`season`,`create_time`) 
        VALUES 
        (%(_name)s,%(sn)s,%(min_price)s,NULL,%(currency)s,%(designer_id)s,%(shop_id)s,%(_status)s,%(cover)s,%(image_urls)s,%(season_code)s,unix_timestamp());
        """
        with self.platform_connection.cursor() as cursor:
            cursor.execute(sql, product)
            product["shop_product_id"] = cursor.lastrowid
            self.platform_connection.commit()
            self.created_counter = self.created_counter + 1

        for sku in self.get_product_skus(product):
            self.create_product_sku(sku, product)
            if sku["quantity"]:
                self.create_product_stock(sku, product)


if __name__ == "__main__":
    # DesignerSynchronizer().start()
    ProductSynchronizer().start(8)
