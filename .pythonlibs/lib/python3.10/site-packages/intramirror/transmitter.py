# -*- coding: UTF-8 -*-
import pymysql
import time
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header


class Transfer:
    def __init__(self):
        self.source_connection = pymysql.connect(host='172.16.8.147',
                                                 port=3306,
                                                 user='dba',
                                                 passwd='123456',
                                                 db='intramirror',
                                                 cursorclass=pymysql.cursors.DictCursor,
                                                 charset='utf8mb4')

        # 连接平台数据库
        self.target_connection = pymysql.connect(host='172.16.8.147',
                                                 port=3306,
                                                 user='dba',
                                                 passwd='123456',
                                                 db='fashion_product',
                                                 cursorclass=pymysql.cursors.DictCursor,
                                                 charset='utf8mb4')
        # 设计师映射表
        self.designers_map = {}
        self.categories_mapped = {}
        self.create_designers_map()
        self.create_categories_mapped()
        self.target_product_creates = 0
        self.target_product_updates = 0

    # 加载分类映射
    def create_categories_mapped(self):
        sql = "SELECT * FROM intramirror.t_category_mapped"
        with self.source_connection.cursor() as cursor:
            cursor.execute(sql)
            for category_mapped in cursor.fetchall():
                self.categories_mapped[category_mapped["category_id"]] = category_mapped["target_category_id"]

    # 加载品牌信息
    def create_designers_map(self):
        sql = "SELECT * FROM fashion_product.t_designer"
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql)
            for designer in cursor.fetchall():
                self.designers_map[designer["name"].strip().upper()] = designer
        print "create designers map success"

    def get_source_catalogs(self):
        sql = """
        SELECT `context` FROM intramirror.t_catalog
        """
        with self.source_connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def create_source_season(self, catalog_context):
        catalog_context["cover_img"] = None
        catalog_context["skuList"] = None
        print "catalog context:", catalog_context
        sql = """
        REPLACE INTO t_season (`season_id`, `code`) VALUES (%(season)s, %(season_code)s)
        """
        with self.source_connection.cursor() as cursor:
            cursor.execute(sql, catalog_context)
        self.source_connection.commit()

    def create_source_seasons(self):
        for catalog in self.get_source_catalogs():
            self.create_source_season(json.loads(catalog["context"]))

    def get_source_designers(self):
        sql = """
        SELECT * FROM intramirror.t_designer
        """
        with self.source_connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def check_target_designer(self, designer):
        sql = """
        SELECT * FROM fashion_product.t_designer WHERE name=%s
        """
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql, designer["name"])
            return cursor.fetchone()

    def create_target_designer(self, designer):
        if self.check_target_designer(designer):
            print "designer exists", designer
            return

        sql = """
        INSERT INTO `fashion_product`.`t_designer` (
            `name`,`first_char`,`desc`, `create_time`,`deleted`) VALUES (%s,%s,'intra mirror',UNIX_TIMESTAMP(),'0')
        """
        print "save designer", designer
        designer_name = designer["name"]
        first_char = designer_name[1].upper()
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql, (designer_name, first_char))
            self.target_connection.commit()

    # 检查商品是否存在
    def check_target_product(self, product):
        sql = """
        SELECT * FROM fashion_product.t_shop_product WHERE sn=%s LIMIT 1
        """
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql, product["sn"])
            return cursor.fetchone()

    # 获取爬虫商品sku
    def get_source_product_skus(self, product):
        sql = """
        SELECT * FROM intramirror.t_product_sku WHERE product_id=%s
        """
        with self.source_connection.cursor() as cursor:
            cursor.execute(sql, product["product_id"])
            return cursor.fetchall()

    # 创建商品sku
    def create_target_product_sku(self, sku, product):
        print "create target product sku:", sku
        sql = """
        INSERT INTO `fashion_product`.`t_shop_product_sku` 
        (`shop_product_id`, `size`, `price`, `settlement_price`, `sn`, `status`, `create_time`, `deleted`) 
        VALUES 
        (%(shop_product_id)s, %(size)s, %(price)s, %(sale_price)s, %(im_code)s, 'Created', unix_timestamp(), '0');
        """
        timestamp = str(int(round(time.time() * 1000)))
        sku["shop_product_id"] = product["shop_product_id"]
        sku["im_code"] = "intramirror#%s" % sku["product_sku_id"]
        sku["size"] = sku["size"]
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql, sku)
            sku["shop_product_sku_id"] = cursor.lastrowid
            self.target_connection.commit()

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
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql, sku)
            self.target_connection.commit()

    @staticmethod
    def get_product_season_code(product):
        catalog_context = json.loads(product["catalog_context"])
        return catalog_context["season_code"] if catalog_context.get("season_code") else None

    @staticmethod
    def get_product_image_modified(product):
        catalog_context = json.loads(product["catalog_context"])
        return catalog_context["img_modified"] if catalog_context.get("img_modified") else 0

    # 加载爬虫商品列表
    def get_source_products(self):
        sql = """
        SELECT
            a.*, b.`name` AS designer_name,
            c.`name` AS product_name,
            c.description,
            c.composition,
            c.edd_description,
            c.edd_title,
            c.location,
            d.min_price,
            d.cover,
            d.context AS catalog_context
        FROM
            intramirror.t_product a,
            intramirror.t_designer b,
            intramirror.t_product_description c,
            intramirror.t_catalog d,
            intramirror.t_season e
        WHERE
            a.designer_id = b.designer_id
        AND a.product_id = c.product_id
        AND c.language_id = 1
        AND a.product_id = d.product_id
        AND d.season = e.season_id
        AND (
            (
                d.season = 173
                AND a.designer_id IN (
                    SELECT
                        designer_id
                    FROM
                        intramirror.t_designer_transfer
                )
            )
            OR d.season > 173
        )
        """
        with self.source_connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    # 通过品牌名称获取品牌信息
    def get_target_designer_id(self, name):
        name = name.upper()
        if self.designers_map.get(name):
            return self.designers_map[name]["designer_id"]

        sql = """
        SELECT * FROM fashion_product.t_designer WHERE `name`=%s
        """
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql, name)
            designer = cursor.fetchone()
            return designer["designer_id"] if designer else None

    def get_target_category_id(self, source_target_id):
        return self.categories_mapped[source_target_id] if self.categories_mapped.get(source_target_id) else None

    # 保存商品信息
    def save_target_product(self, product):
        # 检查商品是否存在
        product["context"] = None
        product["catalog_context"] = None
        found_target_product = self.check_target_product(product)
        if found_target_product:
            product["shop_product_id"] = found_target_product["shop_product_id"]
            self.update_target_product(product)
        else:
            self.create_target_product(product)

    def update_target_product(self, product):
        print "[%d]update product(%d)" % (product["product_id"], self.target_product_updates)
        # self.target_product_updates = self.target_product_updates + 1
        sql = """
        UPDATE `fashion_product`.`t_shop_product` SET 
        `name`=%(product_name)s, 
        `description`=%(description)s, 
        `constitute`=%(composition)s, 
        `edd_title`=%(edd_title)s, 
        `edd_description`=%(edd_description)s, 
        `location`=%(location)s, 
        `sn`=%(sn)s, 
        `designer_code`=%(designer_code)s, 
        `price`=%(min_price)s, 
        `currency`=%(currency)s, 
        `designer_id`=%(designer_id)s, 
        `category_id`=%(category_id)s, 
        `shop_id`=%(shop_id)s, 
        `status`=%(product_status)s, 
        `season`=%(season_code)s, 
        `cover`=%(cover)s, 
        `images`=%(image_urls)s, 
        `image_modified`=%(image_modified)s, 
        `modify_time`=unix_timestamp() WHERE shop_product_id=%(shop_product_id)s
        """
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql, product)
            self.target_connection.commit()
            self.target_product_updates = self.target_product_updates + 1

    def create_target_product(self, product):
        print "[%d]create product(%d)" % (product["product_id"], self.target_product_creates)
        sql = """
        INSERT INTO `fashion_product`.`t_shop_product` 
        ( `name`, `description`, `constitute`, 
        `edd_title`, `edd_description`, `location`, 
        `sn`, `designer_code`, `price`, `currency`, 
        `designer_id`, `category_id`, `shop_id`, 
        `status`, `season`, `cover`, `images`, 
        `image_modified`, `create_time`) 
        VALUES 
        (%(product_name)s, %(description)s, %(composition)s,
        %(edd_title)s, %(edd_description)s, %(location)s,
        %(sn)s, %(designer_code)s, %(min_price)s, %(currency)s,
        %(designer_id)s, %(category_id)s, %(shop_id)s,
        %(product_status)s,%(season_code)s,%(cover)s,%(image_urls)s,
        %(image_modified)s,unix_timestamp());
        """
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql, product)
            product["shop_product_id"] = cursor.lastrowid
            self.target_connection.commit()
            self.target_product_creates = self.target_product_creates + 1

        for sku in self.get_source_product_skus(product):
            self.create_target_product_sku(sku, product)
            if sku["quantity"]:
                self.create_product_stock(sku, product)

    def transfer_designers(self):
        for designer in self.get_source_designers():
            self.create_target_designer(designer)

    def transfer_products(self, shop_id):
        for product in self.get_source_products():
            designer_id = self.get_target_designer_id(product["designer_name"])
            category_id = self.get_target_category_id(product["category_id"])
            product["image_modified"] = self.get_product_image_modified(product)
            product["season_code"] = self.get_product_season_code(product)
            product["product_status"] = "Created"
            product["designer_id"] = designer_id
            product["category_id"] = category_id
            product["currency"] = "EUR"
            product["shop_id"] = shop_id
            product["sn"] = "intramirror:" + str(product["product_id"])
            # 创建商品
            self.save_target_product(product)


def send_mail():
    sender = 'yuanjie@fashionfinger.com'
    receiver = 'zhoumin@fashionfinger.com'
    subject = 'intramirror 已同步测试环境'
    smtpserver = 'smtp.fashionfinger.com'
    username = 'yuanjie@fashionfinger.com'
    password = 'qazpl,1234'

    msg = MIMEText('<html><h1>爬虫事件通知</h1></html>', 'html', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    smtp = smtplib.SMTP()
    smtp.connect(smtpserver)
    smtp.login(username, password)
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()


if __name__ == "__main__":
    # Transfer().transfer_designers()
    # Transfer().create_source_seasons()
    # Transfer().transfer_products(8)
    send_mail()
