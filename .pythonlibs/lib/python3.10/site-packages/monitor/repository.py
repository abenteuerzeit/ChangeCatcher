# -*- coding: UTF-8 -*-
from modules.repository import Repository
import logging
import os

logger = logging.getLogger(os.path.basename(__file__))


class MonitorRepository(Repository):
    def __init__(self):
        Repository.__init__(self)

    def set_platform_product_status(self, product_id, product_status):
        print("[%s]set product status=%s" % (product_id, product_status))
        sql = """
        UPDATE fashion_product.t_product SET product_status=%s,modify_time=unix_timestamp(),editor_name='monitor' WHERE product_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (product_status, product_id))
            self.connection.commit()
            cursor.close()

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
           SELECT * FROM fashion_product.t_product_sku WHERE product_id=%s AND sku_status='ON'
           """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, product_id)
            product["skus"] = cursor.fetchall()

        return product

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

    def set_platform_product_sizes_status(self, product_id, size, sku_status):
        sql = """
        UPDATE fashion_product.t_product_sku SET 
            sku_status=%s,
            modify_time=unix_timestamp(),
            editor_name='monitor' 
        WHERE product_id=%s AND size=%s
        """
        print("[%s]set product size:%s status=%s" % (product_id, size, sku_status))
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (sku_status, product_id, size))
            self.connection.commit()
            cursor.close()

        sql = """
        REPLACE INTO `monitor`.`t_product_sku_monitor` 
            (`product_id`, `size`, `status`, `date_modified`) 
        VALUES 
            (%s, %s, %s, now());
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (product_id, size, 0 if "OFF" == sku_status else 0))
            self.connection.commit()
            cursor.close()

    def set_platform_product_size_quantity(self, product_id, size, quantity):
        sql = """
        UPDATE fashion_product.t_product_sku SET quantity=%s,modify_time=unix_timestamp(),editor_name='monitor' WHERE product_id=%s AND size=%s
        """
        print("[%s]set product sku:%s quantity=%s" % (product_id, size, quantity))
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (quantity, product_id, size))
            self.connection.commit()
            cursor.close()

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

    def get_monitor_products_from_im(self):
        sql = """
        SELECT
            c.url,
            b.*
        FROM
            fashion_product.t_product a,
            spider.t_product_source b,
            spider.t_catalog c
        WHERE
            a.product_id = b.product_id
        AND b.source_type = 3
        AND b.source_id = c.source_id
        AND b.source_type = c.source_type
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()


class Dao:
    def __init__(self):
        self.monitor = None
        self.create_repositories()

    def create_repositories(self):
        self.monitor = MonitorRepository()

    def reset(self):
        self.create_repositories()


dao = Dao()
