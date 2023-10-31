# -*- coding: UTF-8 -*-
import json

import pymysql

from keys import KEY_PRODUCT_TASK
from modules.scheduler.scheudler import RedisTaskScheduler
from modules.tools import DatetimeEncoder
from modules.repository import Repository
from modules.tools import contain_zh


#
# def create_connection():
#     return pymysql.connect(host='172.16.8.147',
#                            port=3306,
#                            user='dba',
#                            passwd='123456',
#                            db='farfetch',
#                            cursorclass=pymysql.cursors.DictCursor,
#                            charset='utf8mb4')
#
#
# class TestConnection(Repository):
#     def __init__(self, db):
#         Repository.__init__(self, host='172.16.8.147', db=db)
#         # self.connection = pymysql.connect(host='172.16.8.147',
#         #                                   port=3306,
#         #                                   user='dba',
#         #                                   passwd='123456',
#         #                                   db=db,
#         #                                   cursorclass=pymysql.cursors.DictCursor,
#         #                                   charset='utf8mb4')
#
#
# class ProductionConnection(Repository):
#     def __init__(self, db):
#         Repository.__init__(self, host='10.26.235.6', port=3066, db=db)
#         # Connection.__init__(self)
#         # self.connection = pymysql.connect(host='10.26.235.6',
#         #                                   port=3066,
#         #                                   user='dba',
#         #                                   passwd='123456',
#         #                                   db=db,
#         #                                   cursorclass=pymysql.cursors.DictCursor,
#         #                                   charset='utf8mb4')
#
#
# class RouteRepository(Repository):
#     def __init__(self):
#         Repository.__init__(self, host='10.26.235.6', port=3066, db="fashion_product")
#         # Repository.__init__(self, host='172.16.8.147', port=3306, db="fashion_product")


class MonitorRepository(Repository):
    def __init__(self):
        Repository.__init__(self)

    def set_platform_product_status(self, product_id, product_status):
        print "set product(%s) status=%s" % (product_id, product_status)
        sql = """
        UPDATE t_product SET product_status=%s,modify_time=unix_timestamp(),editor_name='monitor' WHERE product_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (product_status, product_id))
            self.connection.commit()
            cursor.close()

    def get_last_crawl_time(self, product_id):
        sql = "SELECT * FROM monitor.t_product_monitor WHERE product_id=%s"
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product_id)
            return cursor.fetchone()

    def update_crawl_time(self, monitor_task, status):
        sql = """
        REPLACE INTO `monitor`.`t_product_monitor` 
        (`product_id`, `source_type`, `source_id`, `status`, `date_modified`) 
        VALUES 
        (%s, %s, %s, %s, now());
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (
                monitor_task["product_id"],
                monitor_task["source_type"],
                monitor_task["resource_code"],
                status))
            self.connection.commit()

    def get_monitor_products(self):
        sql = """
        SELECT
          a.product_id,
          b.spider_product_id,
          b.source_url,
          b.resource_code,
          b.flag
        FROM
            fashion_product.t_product a,
            fashion_product.t_spider_product b
        WHERE
            a.spider_product_id IS NOT NULL
        AND a.spider_product_id = b.spider_product_id
        AND a.product_status = 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()


class CommonRepository(Repository):
    def __init__(self):
        Repository.__init__(self, db="farfetch")

    def get_appoint_products(self):
        sql = """SELECT * FROM spider2.t_spider_product_appoint"""
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def update_catalog_task(self, task):
        sql = """
        UPDATE farfetch.t_task SET `status` = 1,`end_time`=now() WHERE task_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, task["task_id"])
        self.connection.commit()

    def get_catalog_tasks(self):
        sql = """
        SELECT task_id,url,`gender`,start_time,name FROM farfetch.t_task WHERE `status` <> 1 OR `status` IS NULL
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()


class ProductRepository(Repository):
    def __init__(self):
        Repository.__init__(self, db="farfetch")

    def check_product(self, product):
        with self.connection.cursor() as cursor:
            sql = """
            SELECT * FROM t_product WHERE product_id=%s
            """
            cursor.execute(sql, product["product_id"])
            return cursor.fetchone()

    def create_product(self, product):
        print "create product:", product["product_id"]
        sql = """
        INSERT INTO `farfetch`.`t_product` 
        (`product_id`, 
        `cover`, 
        `status`, 
        `manufacturer_id`, 
        `category_id`, 
        `sub_category_id`, 
        `designer_style_code`, 
        `date_added`) 
        VALUES 
        (%(product_id)s,
        %(cover)s,
        %(product_status)s,
        %(manufacturer_id)s,
        %(category_id)s,
        %(sub_category_id)s,
        %(designer_style_code)s,
        now());
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product)
            self.connection.commit()
            cursor.close()

    def update_product(self, product):
        print "update product:", product["product_id"]
        sql = """
        UPDATE `farfetch`.`t_product` SET 
        `status`=%(product_status)s, 
        `manufacturer_id`=%(manufacturer_id)s, 
        `category_id`=%(category_id)s, 
        `sub_category_id`=%(sub_category_id)s, 
        `designer_style_code`=%(designer_style_code)s, 
        `color`=%(color)s,
        `department`=%(department)s, 
        `date_modified`=now() 
        WHERE `product_id`=%(product_id)s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product)
            self.connection.commit()
            cursor.close()

    def save_product(self, product):
        if self.check_product(product):
            self.update_product(product)
        else:
            self.create_product(product)

    def save_description(self, description):
        sql = """
        REPLACE INTO `farfetch`.`t_product_description` 
        (`product_id`, 
        `name`, 
        `description`, 
        `constitute`, 
        `location`, 
        `size_description`, 
        `language_id`, 
        `editor_name`, 
        `date_added`) 
        VALUES 
        (%(product_id)s,
        %(product_name)s,
        %(description)s,
        %(constitute)s,
        %(location)s,
        %(size_description)s,
        %(language_id)s,
        %(editor_name)s,
        now());
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, description)
            self.connection.commit()
            cursor.close()

    def save_manufacturer(self, manufacturer):
        sql = """
        REPLACE INTO `farfetch`.`t_manufacturer` 
        (`manufacturer_id`, `description`, `date_added`) 
        VALUES 
        (%(manufacturer_id)s, %(manufacturer)s, now());
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, manufacturer)
            self.connection.commit()
            cursor.close()

    @staticmethod
    def save_size(size, cursor):
        sql = """
        REPLACE INTO `farfetch`.`t_size` (`size_id`, `description`, `date_added`) VALUES (%(size_id)s, %(size)s, now())
        """
        cursor.execute(sql, size)

    @staticmethod
    def save_scale(scale, cursor):
        sql = """
        REPLACE INTO `farfetch`.`t_scale` (`scale_id`, `description`, `date_added`) VALUES (%(scale_id)s, %(scale)s, now())
        """
        cursor.execute(sql, scale)

    def save_product_sizes(self, sizes, product_id):
        sql = """
        REPLACE INTO `farfetch`.`t_product_sku` 
        (`product_id`, `store_id`, `size_id`, `scale_id`, `price`, `sale_price`, `quantity`, `currency`, `date_added`) 
        VALUES 
        (%(product_id)s,%(store_id)s,%(size_id)s,%(scale_id)s,%(price)s,%(sale_price)s,%(quantity)s,%(currency)s,now());
        """
        with self.connection.cursor() as cursor:
            for size in sizes:
                size["product_id"] = product_id
                cursor.execute(sql, size)
                # 保存尺码
                self.save_size(size, cursor)
                self.save_scale(size, cursor)
                self.connection.commit()
            cursor.close()

    def save_product_price(self, price):
        sql = """
        REPLACE INTO `farfetch`.`t_product_price` (`product_id`, `currency`, `price`, `sale_price`, `date_added`) 
        VALUES 
        (%(product_id)s,%(currency)s,%(price)s,%(sale_price)s,now());
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, price)
            self.connection.commit()
            cursor.close()

    def save_image_urls(self, image):
        sql = """
        INSERT INTO t_product_image(product_id, image_urls) VALUES(%s, %s) ON DUPLICATE KEY UPDATE date_modified=now()
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (image["product_id"], json.dumps(image["image_urls"])))
            self.connection.commit()

    def save(self, data, language_id):
        data["editor_name"] = "spider"
        data["language_id"] = language_id

        product = {
            "product_status": "CREATED",
            "designer_style_code": data.get("designerStyleId"),
            "sub_category_id": data.get("subCategoryId"),
            "manufacturer_id": data.get("manufacturerId"),
            "manufacturer": data.get("manufacturer"),
            "product_id": data["product_id"],
            "category_id": data["categoryId"],
            "department": data["department"],
            "price": data.get("unitPrice"),
            "sale_price": data.get("unitSalePrice"),
            "currency": data["currencyCode"],
            "color": data["color"],
            "cover": data["cover"],
            "image_urls": data["image_urls"]
        }

        # 如果没有尺码信息，说明没有库存了
        if not data["sizes"]:
            product["product_status"] = "OVERSOLD"

        # 保存商品信息
        self.save_product(product)

        # 保存图片信息
        self.save_image_urls(product)

        # 保存商品价格
        if product["price"] or product["sale_price"]:
            self.save_product_price(product)

        # 保存商品描述
        description = {}
        for name in ['product_id',
                     'description',
                     'constitute',
                     'location',
                     'size_description',
                     'language_id',
                     'editor_name']:
            description[name] = data[name]
        description["product_name"] = data["name"]
        self.save_description(description)

        # 保存尺码信息
        self.save_product_sizes(data["sizes"], product["product_id"])

        # 保存厂商信息
        self.save_manufacturer(product)

    def get_product_descriptions(self, language_id=1):
        sql = """
        SELECT a.resource_code,a.flag,a.source_url,b.* FROM spider2.t_spider_product a, spider2.t_spider_product_description b 
        WHERE a.spider_product_id=b.spider_product_id AND b.language_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, language_id)
            return cursor.fetchall()

    def get_product_descriptions_zh_need_translate(self):
        descriptions_zh_need_translate = []
        for description in self.get_product_descriptions():
            if not contain_zh(description["description"]):
                descriptions_zh_need_translate.append(description)
        return descriptions_zh_need_translate

    def create_appoint_products(self):
        sql = """
        REPLACE INTO farfetch.t_product_appoint (`product_id`, `status`)VALUES(%s, 0)
        """
        for product in self.get_product_descriptions_zh_need_translate():
            with self.connection.cursor() as cursor:
                if product["resource_code"]:
                    cursor.execute(sql, product["resource_code"])
        self.connection.commit()

    def get_products_from_spider(self):
        sql = """
        SELECT
          a.product_id,
          b.spider_product_id,
          b.source_url,
          b.resource_code,
          b.flag
        FROM
            fashion_product.t_product a,
            fashion_product.t_spider_product b
        WHERE
            a.spider_product_id IS NOT NULL
        AND a.spider_product_id = b.spider_product_id
        AND a.product_status = 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()


class ProductDescription:
    def __init__(self, connection):
        self.connection = connection

    def save(self, spider_product_id, product):
        sql = """
        REPLACE INTO `fashion_product`.`t_spider_product_description` 
        (`spider_product_id`,`name`,`description`,`constitute`,`location`,`size_description`,`language_id`,`editor_name`,`date_added`) 
        VALUES 
        (%(spider_product_id)s, %(product_name)s, %(description)s, %(constitute)s,
        %(location)s,%(size_description)s,%(language_id)s,"spider",now())
        """
        data = {
            "product_name": product['name'],
            "spider_product_id": spider_product_id
        }
        for name in ["description", "constitute", "location", "size_description", "language_id"]:
            data[name] = product[name]

        with self.connection.cursor() as cursor:
            cursor.execute(sql, data)
            self.connection.commit()


class ProductSku:
    def __init__(self, connection):
        self.connection = connection

    def save(self, spider_product_id, sku):
        sku["spider_product_id"] = spider_product_id
        sql = """
        REPLACE INTO t_spider_product_sku(`spider_product_id`,`size`,`price`,`currency`,`discount_price`,`editor_name`)
        VALUES 
        (%(spider_product_id)s,%(size)s,%(price)s,%(currency)s,%(discount_price)s,"spider")
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, sku)
            self.connection.commit()


class SpiderProductRepository(Repository):
    def __init__(self):
        Repository.__init__(db="fashion_product")
        self.description = ProductDescription(self.connection)
        self.sku = ProductSku(self.connection)
        self.created_counter = 0
        self.updated_counter = 0

    def save_product(self, product, language_id=1):
        product["language_id"] = language_id
        print json.dumps(product)
        if self.check_product(product):
            print "update product:", self.updated_counter
            self.updated_counter = self.updated_counter + 1
        else:
            # 创建商品信息
            spider_product_id = self.create_product(product)

            # 保存商品描述
            self.description.save(spider_product_id, product)
            # 只保存欧元价的sku信息
            if "EURO" == product["currency"]:
                for sku in product["sizes"]:
                    sku["currency"] = product["currency"]
                    sku["discount_price"] = product["unitSalePrice"]
                    self.sku.save(spider_product_id, sku)
            self.created_counter = self.created_counter + 1
            print "create product[%d]:" % spider_product_id, self.created_counter
            return spider_product_id

    def create_product(self, product):
        data = {}
        for name in ["designerName", "gender", "designer_code", "resource_code", "source_url"]:
            data[name] = product[name]

        # 商品是否下架
        if product["is_sold_out"]:
            data["selling_status"] = 2
        else:
            data["selling_status"] = 1

        data["category"] = product["category"] + "/" + product["subcategory"]
        data["color_code"] = product["color"]

        sql = """
        INSERT INTO fashion_product.t_spider_product
        (`designer`,`gender`,`category`,`status`,`color_code`,`designer_code`,`resource_code`, `selling_status`,`flag`,`source_url`, `editor_name`)
        VALUES
        (%(designerName)s, %(gender)s, %(category)s, 0, %(color_code)s, %(designer_code)s, %(resource_code)s,%(selling_status)s, '001', %(source_url)s, 'spider')
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, data)
            spider_product_id = cursor.lastrowid
            self.connection.commit()
            cursor.close()
            return spider_product_id

    @staticmethod
    def update_product(product):
        print product

    def check_product(self, product):
        sql = """
        SELECT * FROM t_spider_product WHERE resource_code=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product["product_id"])
            return cursor.fetchone()


class FilterRepository(Repository):
    def __init__(self):
        Repository.__init__(self, db="robin")

    def find_18ss_products(self):
        sql = """
           SELECT * FROM robin.farfetch_18ss a WHERE a.spider_product_id IS NOT NULL
           """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def find_17fw_products(self):
        sql = """
           SELECT * FROM robin.farfetch_17fw a WHERE a.spider_product_id IS NOT NULL
           """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()


class CatalogRepository(Repository):
    def __init__(self):
        Repository.__init__(self, db="farfetch")

    def create_appoint_product_tasks(self):
        sql = """
        SELECT * FROM t_product_appoint a, t_product_catalog b WHERE a.product_id = b.product_id GROUP BY a.product_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            for task in cursor.fetchall():
                print "create product task:", task["product_id"]
                task["url"] = "/cn" + task["url"][3:]
                task["language_id"] = 1
                RedisTaskScheduler().push(KEY_PRODUCT_TASK, json.dumps(task, cls=DatetimeEncoder))

    def create_appoint_product_tasks_from_spider2(self):
        sql = """
        SELECT
            a.product_id,
            b.source_url AS url
        FROM
            t_product_appoint a,
            spider2.t_spider_product b
        WHERE
            a.product_id = b.resource_code
        AND b.flag IN (
            SELECT
                `code`
            FROM
                t_shop_source
        )
        GROUP BY
            a.product_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            for task in cursor.fetchall():
                print "create product task:", task["product_id"]
                task["url"] = "/cn" + task["url"][len("https://www.farfetch.cn/cn"):]
                task["language_id"] = 1
                RedisTaskScheduler().push(KEY_PRODUCT_TASK, json.dumps(task, cls=DatetimeEncoder))

    def check_catalog(self, catalog):
        sql = "SELECT * FROM t_catalog WHERE url=%s"
        with self.connection.cursor() as cursor:
            cursor.execute(sql, catalog["url"])
            return cursor.fetchone()

    def update_catalog(self, catalog):
        # print "update catalog:", catalog
        sql = """
        UPDATE `farfetch`.`t_catalog` SET 
            `url`=%(url)s, 
            `product_id`=%(product_id)s, 
            `name`=%(product_name)s, 
            `price`=%(price)s, 
            `gender`=%(gender)s, 
            `store_id`=%(store_id)s, 
            `language_id`=%(language_id)s, 
            `cover`=%(cover)s, 
            `task_id`=%(task_id)s, 
            `context`=%(catalog_context)s, 
            `date_modified`=now()
        WHERE 
            `catalog_id`=%(catalog_id)s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, catalog)
        self.connection.commit()

    def create_catalog(self, catalog):
        # print "create catalog:", catalog
        sql = """
        INSERT INTO `farfetch`.`t_catalog` 
            (`url`, 
            `product_id`, 
            `name`, 
            `price`, 
            `gender`, 
            `store_id`, 
            `language_id`, 
            `cover`, 
            `task_id`, 
            `context`, 
            `date_added`) 
        VALUES 
            (%(url)s,
            %(product_id)s, 
            %(product_name)s, 
            %(price)s, 
            %(gender)s, 
            %(store_id)s, 
            %(language_id)s, 
            %(cover)s, 
            %(task_id)s, 
            %(catalog_context)s, 
            now());
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, catalog)
        self.connection.commit()

    def save_catalog(self, catalog):
        old_catalog = self.check_catalog(catalog)
        if old_catalog:
            catalog["catalog_id"] = old_catalog["catalog_id"]
            self.update_catalog(catalog)
        else:
            self.create_catalog(catalog)

    def get_men_product_covers(self):
        sql = """
        SELECT
            a.*, b.oss_url
        FROM
            farfetch_men_cover_1000 a
        LEFT JOIN t_download_image b ON a.cover = b.image_url;
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def get_product_tasks(self):
        sql = """
        SELECT * FROM t_catalog WHERE status IS NULL LIMIT 100
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def set_catalog_status(self, catalog, status):
        sql = """
        UPDATE t_catalog SET status=%s WHERE url=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (status, catalog["url"]))
        self.connection.commit()

    def get_product_source_urls(self, product_id):
        sql = """
        SELECT * FROM farfetch.t_catalog WHERE product_id = %s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product_id)
            return cursor.fetchall()


class Dao:
    def __init__(self):
        self.product = None
        self.catalog = None
        self.common = None
        self.monitor = None
        self.filter = None
        self.create_repositories()

    def create_repositories(self):
        self.filter = FilterRepository()
        self.product = ProductRepository()
        self.catalog = CatalogRepository()
        self.common = CommonRepository()
        self.monitor = MonitorRepository()

    def reset(self):
        self.create_repositories()


dao = Dao()
