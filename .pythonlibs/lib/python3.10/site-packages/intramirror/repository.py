# -*- coding: UTF-8 -*-
import pymysql
import json
from modules.repository import Repository


# def create_connection():
#     return pymysql.connect(host="10.26.235.6", port=3066, user='dba', passwd='123456', db='intramirror',
#                            charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)


class MonitorRepository(Repository):
    def __init__(self):
        Repository.__init__(self)

    def get_monitor_products(self):
        sql = """
        SELECT
            a.product_sn2,
            b.sn,
            a.product_id,
            b.shop_product_id
        FROM
            t_product a,
            t_shop_product b
        WHERE
            a.shop_product_id IS NOT NULL
        AND a.product_sn2 LIKE "intramirror:%"
        AND a.shop_product_id = b.shop_product_id;
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def get_platform_product(self, product_id):
        sql = """
        SELECT * FROM fashion_product.t_product WHERE product_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product_id)
            product = cursor.fetchone()

        if not product:
            return product

        sql = """
        SELECT * FROM t_product_sku WHERE product_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product_id)
            product["skus"] = cursor.fetchall()

        return product

    def set_platform_product_status(self, product_id, product_status):
        print "set product(%s) status=%s" % (product_id, product_status)
        sql = """
        UPDATE t_product SET product_status=%s,modify_time=unix_timestamp(),editor_name='crawler-for-im' WHERE product_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (product_status, product_id))
            self.connection.commit()
            cursor.close()

    def set_platform_product_sizes_status(self, product_id, size, sku_status):
        sql = """
        UPDATE t_product_sku SET sku_status=%s,modify_time=unix_timestamp(),editor_name='crawler-for-im' WHERE product_id=%s AND size=%s
        """
        print "set product(%s) sku(%s) status=%s" % (product_id, size, sku_status)
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (sku_status, product_id, size))
            self.connection.commit()
            cursor.close()

    def set_platform_product_size_quantity(self, product_id, size, quantity):
        sql = """
        UPDATE t_product_sku SET quantity=%s,modify_time=unix_timestamp(),editor_name='crawler-for-im' WHERE product_id=%s AND size=%s
        """
        print "set product(%s) sku(%s) quantity=%s" % (product_id, size, quantity)
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (quantity, product_id, size))
            self.connection.commit()
            cursor.close()


class ProductRepository(Repository):
    def __init__(self):
        Repository.__init__(self, db="intramirror")

    def save_product(self, product):
        print "[%d]save product:" % product["product_id"], product["name"], product["category"]
        sql = """
        REPLACE INTO `t_product` 
        (`product_id`, `category_id`, `designer_id`, `price`, `sale_price`, `color_code`, `status`, 
        `designer_code`, `image_urls`,  `thumbnails`, `context`, `date_added`)
        VALUES 
        (%(product_id)s, %(category_id)s, %(designer_id)s, %(price)s, %(sale_price)s, %(color_code)s, %(product_status)s, %(designer_code)s, 
        %(image_urls)s, %(thumbnails)s, %(context_string)s, now());
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product)
            self.connection.commit()

    def check_description(self, description):
        sql = """
        SELECT * FROM t_product_description WHERE product_id=%(product_id)s AND language_id=%(language_id)s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, description)
            return cursor.fetchone()

    def save_description(self, description):
        # 默认设置为2
        if not description.get("language_id"):
            description["language_id"] = 2

        found_description = self.check_description(description)
        if found_description:
            description["product_description_id"] = found_description["product_description_id"]
            sql = """
            UPDATE `t_product_description` 
            SET 
            `product_id`=%(product_id)s, 
            `name`=%(product_name)s, 
            `description`=%(description)s, 
            `composition`=%(composition)s, 
            `location`=%(location)s, 
            `language_id`=%(language_id)s, 
            `edd_title`=%(edd_title)s, 
            `edd_description`=%(edd_description)s,
            `date_modified` = now()
             WHERE (`product_description_id`=%(product_description_id)s)        
            """
        else:
            sql = """
            INSERT INTO `t_product_description` 
            (`product_id`, `name`, `description`, `composition`, `location`, `language_id`, `edd_title`, 
            `edd_description`, `date_added`) 
            VALUES 
            (%(product_id)s, %(product_name)s, %(description)s, %(composition)s, %(location)s, %(language_id)s, 
            %(edd_title)s, %(edd_description)s, now());
            """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, description)
            self.connection.commit()

    def save_designer(self, designer):
        sql = """
        REPLACE INTO `t_designer` (`designer_id`, `name`,`date_added`)
         VALUES 
        (%(designer_id)s, %(designer_name)s, now() );
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, designer)
            self.connection.commit()

    def find_descriptions_zh(self):
        sql = """
        SELECT
            *
        FROM
            t_product_description
        WHERE
            language_id = 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def find_descriptions(self):
        sql = """
        SELECT
            *
        FROM
            t_product_description
        WHERE
            language_id = 2
        AND composition IS NOT NULL
        AND TRIM(composition) <> ""
        AND product_id NOT IN (
            SELECT
                product_id
            FROM
                t_product_description
            WHERE
                language_id = 1
        )
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()


class CategoryRepository(Repository):
    def __init__(self):
        Repository.__init__(self, db="intramirror")

    def save_categories(self, categories):
        for category in categories:
            category["name_zh"] = category["chinese_name"]
            category["category_code"] = category["show_code_int"]
            category["category_name"] = category["name"]
            category["category_level"] = category["level"]
            self.save_category(category)

    def save_category(self, category):
        print "save category:", category
        sql = """
        REPLACE INTO `t_category` 
        (`category_id`, `name`, `name_zh`, `level`, `sort_order`, `code`, `enabled`, `parent_id`, `remark`, `date_added`) 
        VALUES 
        (%(category_id)s,%(category_name)s,%(name_zh)s,%(category_level)s,%(sort_order)s,%(category_code)s,%(enabled)s,%(parent_id)s,%(remark)s,now())
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, category)
            self.connection.commit()


class CatalogRepository(Repository):
    def __init__(self):
        Repository.__init__(self, db="intramirror")
        self.catalog_creates = 0
        self.catalog_updates = 0
        self.catalog_sku_creates = 0
        self.catalog_sku_updates = 0

    def reset(self):
        self.connection.close()
        self.__init__()

    def find_catalogs_for_task(self):
        sql = """
        SELECT a.* FROM t_catalog a LEFT JOIN t_product b ON a.product_id=b.product_id 
        WHERE b.product_id IS NULL AND (a.status <> 0 OR a.status IS NULL) LIMIT 10
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def save_error(self, name, message, context):
        sql = """
        INSERT INTO `t_error` (`key`, `error`, `referer`, `date_added`, `date_modified`) VALUES 
        (%s, %s, %s, now(), now());
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (name, str(message), str(context)))

    def check_catalog(self, product_id):
        sql = """
        SELECT product_id FROM t_catalog WHERE product_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product_id)
            return cursor.fetchone()

    def check_sku(self, product_sku_id):
        sql = """
        SELECT product_sku_id FROM t_product_sku WHERE product_sku_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product_sku_id)
            return cursor.fetchone()

    def save_catalog(self, catalog):
        print "save catalog", catalog["product_id"]
        # 检查商品是否已存在
        if self.check_catalog(catalog["product_id"]):
            sql = """
            UPDATE t_catalog SET  
            `cover`=%(cover)s, 
            `name`=%(product_name)s,
            `designer`=%(designer)s, 
            `season`=%(season)s, 
            `min_price`=%(min_price)s, 
            `image_urls`=%(image_urls)s, 
            `shop_product_id`=%(shop_product_id)s, 
            `context`=%(context_string)s, 
            `date_modified`=now() WHERE product_id=%(product_id)s
            """
            self.catalog_updates += 1
        else:
            sql = """
            INSERT INTO t_catalog 
            (`product_id`, `cover`, `name`, `designer`, `season`, `min_price`, `image_urls`, `shop_product_id`, `context`, 
            `date_added`) 
            VALUES (%(product_id)s, %(cover)s, %(product_name)s, %(designer)s, %(season)s, %(min_price)s, %(image_urls)s, 
            %(shop_product_id)s, %(context_string)s,now());
            """
            self.catalog_creates += 1

        with self.connection.cursor() as cursor:
            cursor.execute(sql, catalog)
            self.connection.commit()

    def get_catalog_by_product_id(self, product_id):
        sql = """
        SELECT * FROM t_catalog WHERE product_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product_id)
            return cursor.fetchone()

    def save_catalogs(self, catalogs):
        keys = ["product_id", "cover", "product_name", "designer", "season", "min_price", "image_urls",
                "shop_product_id", "context_string"]
        for product in catalogs:
            image_urls = json.loads(product[u'cover_img'])
            product["context_string"] = json.dumps(product)
            product["cover"] = image_urls[0]
            product["min_price"] = product[u'minprice']
            product["designer"] = product[u'brand_englishName']
            skus = product[u'skuList']
            product["product_name"] = skus[0][u'name'] or None
            product["image_urls"] = json.dumps(image_urls)

            #  复制到 catalog 对象
            catalog = {}
            for key in keys:
                catalog[key] = product[key]

            self.save_catalog(catalog)
            self.save_skus(skus)
            print "catalogs created:", self.catalog_creates, "updated:", self.catalog_updates, \
                "sku created:", self.catalog_sku_creates, "updated:", self.catalog_sku_updates

    def save_skus(self, skus):
        sql_for_update = """
        UPDATE t_product_sku SET  
        `product_id`=%(product_id)s, 
        `name`=%(sku_name)s, 
        `size`=%(size)s, 
        `price`=%(price)s, 
        `sale_price`=%(sale_price)s, 
        `quantity`=%(quantity)s,
        `code`=%(sku_code)s, 
        `shop_product_sku_id`=%(shop_product_sku_id)s, 
        `context`=%(context_string)s,
        `date_modified`=now() WHERE (`product_sku_id`=%(product_sku_id)s)
        """
        sql_for_insert = """
        INSERT INTO t_product_sku
        (`product_sku_id`, `product_id`, `name`, `size`, `price`, `sale_price`, `quantity`, `code`,
         `shop_product_sku_id`, `context`, `date_added`)
        VALUES
        (%(product_sku_id)s, %(product_id)s, %(sku_name)s, %(size)s, %(price)s, %(sale_price)s, %(quantity)s, 
        %(sku_code)s, %(shop_product_sku_id)s, %(context_string)s, now())
        """
        with self.connection.cursor() as cursor:
            for index, sku in enumerate(skus):
                sku["context_string"] = json.dumps(sku)
                sku["product_sku_id"] = sku[u'sku_id']
                sku["sku_name"] = sku[u'name']
                sku["quantity"] = sku[u'store'] or None
                sku["size"] = sku[u'productValue']
                if self.check_sku(sku["product_sku_id"]):
                    cursor.execute(sql_for_update, sku)
                    self.catalog_sku_updates += 1
                else:
                    cursor.execute(sql_for_insert, sku)
                    self.catalog_sku_creates += 1
            self.connection.commit()

    def save_catalog_images(self, local_path, oss_urls, product_id):
        print "save catalog images:", product_id
        sql = """
        REPLACE INTO t_product_images
        (`product_id`, `local_path`, oss_urls, `date_added`) 
        VALUES 
        (%s, %s, %s, now())
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (product_id, local_path, json.dumps(oss_urls)))
            self.connection.commit()

    def find_image_urls_for_task(self):
        sql = """
        SELECT a.product_id, a.image_urls FROM t_catalog a LEFT JOIN t_product_images b ON a.product_id = b.product_id 
        WHERE b.local_path IS NULL LIMIT 10
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def set_catalog_status(self, product_id, status):
        sql = """
        UPDATE t_catalog SET status=%s WHERE product_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (status, product_id))
            self.connection.commit()


class Dao:
    def __init__(self):
        self.catalog = CatalogRepository()
        self.category = CategoryRepository()
        self.product = ProductRepository()
        self.monitor = MonitorRepository()


dao = Dao()
