# -*- coding: UTF-8 -*-
import json
import time
from datetime import date, datetime
import decimal
from repository import dao
from modules.repository import repositories
import pymysql


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        # if isinstance(obj, datetime.datetime):
        #     return int(mktime(obj.timetuple()))
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            return json.JSONEncoder.default(self, obj)


class SpiderProductTransmitter:
    def __init__(self):
        self.filter_repository = dao.filter
        self.source_connection = pymysql.connect(host='172.16.8.147',
                                                 port=3306,
                                                 user='dba',
                                                 passwd='123456',
                                                 db="spider2",
                                                 cursorclass=pymysql.cursors.DictCursor,
                                                 charset='utf8mb4')

        self.target_connection = pymysql.connect(host='10.26.235.6',
                                                 port=3066,
                                                 user='dba',
                                                 passwd='123456',
                                                 db="fashion_product",
                                                 cursorclass=pymysql.cursors.DictCursor,
                                                 charset='utf8mb4')
        # ProductionConnection("fashion_product").connection
        time_string = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        self.file_error = open("data/product_%s_error.txt" % time_string, "w")
        self.file_copied = open("data/product_%s_copy.txt" % time_string, "w")
        self.file_exists = open("data/product_%s_exists.txt" % time_string, "w")
        self.create_product_number = 0
        self.create_product_images_number = 0
        self.create_product_sku_number = 0
        self.create_product_description_number = 0

    def __del__(self):
        self.file_error.close()
        self.file_copied.close()
        self.file_exists.close()
        self.source_connection.close()
        self.target_connection.close()

    def check_target_product(self, spider_product_id):
        sql = """
        SELECT * FROM t_spider_product WHERE spider_product_id=%s
        """
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql, spider_product_id)
            return cursor.fetchone()

    def get_source_product(self, spider_product_id):
        sql = """
        SELECT * FROM spider2.t_spider_product WHERE spider_product_id=%s
        """
        with self.source_connection.cursor() as cursor:
            cursor.execute(sql, spider_product_id)
            return cursor.fetchone()

    def get_source_product_description(self, spider_product_id):
        sql = """
        SELECT * FROM spider2.t_spider_product_description WHERE spider_product_id=%s
        """
        with self.source_connection.cursor() as cursor:
            cursor.execute(sql, spider_product_id)
            return cursor.fetchall()

    def get_source_product_images(self, spider_product_id):
        sql = """
        SELECT * FROM spider2.t_spider_product_images WHERE spider_product_id=%s
        """
        with self.source_connection.cursor() as cursor:
            cursor.execute(sql, spider_product_id)
            return cursor.fetchone()

    def get_source_product_skus(self, spider_product_id):
        sql = """
        SELECT   * FROM  spider2.t_spider_product_sku  WHERE  spider_product_id=%s
        """
        with self.source_connection.cursor() as cursor:
            cursor.execute(sql, spider_product_id)
            return cursor.fetchall()

    def commit_target_product(self, source_product, descriptions, product_images,
                              product_skus):
        self.create_target_product(source_product)
        self.create_product_descriptions(descriptions)
        self.create_product_images(product_images)
        self.create_product_skus(product_skus)

        self.target_connection.commit()

        self.create_product_number = self.create_product_number + 1
        self.create_product_images_number = self.create_product_images_number + 1
        self.create_product_sku_number = self.create_product_sku_number + len(product_skus)
        self.create_product_description_number = self.create_product_description_number + len(descriptions)

    def create_target_product(self, source_product):
        sql = """
        INSERT INTO `fashion_product`.`t_spider_product` 
        (`spider_product_id`, `designer`, `gender`, `category`, `cover`, `status`, `flag`, `color_code`, 
        `designer_code`, `resource_code`, `season`, `source_url`, `editor_name`, `date_added`, `selling_status`) 
        VALUES 
        (%(spider_product_id)s, %(designer)s, %(gender)s, %(category)s, %(cover)s, 1, %(flag)s, %(color_code)s, 
        %(designer_code)s, %(resource_code)s, %(season)s, %(source_url)s, "yuanjie", now(), %(selling_status)s);
        """
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql, source_product)
            # self.target_connection.commit()

    def create_product_descriptions(self, source_descriptions):
        sql = """
        INSERT INTO `fashion_product`.`t_spider_product_description` 
        (`spider_product_id`, `name`, `description`, `constitute`, `location`, `size_description`, 
        `category_description`, `language_id`, `editor_name`, `date_added`) VALUES 
        (%(spider_product_id)s, %(meta_name)s, %(description)s, %(constitute)s, %(location)s, %(size_description)s,
        %(category_description)s, %(language_id)s, "yuanjie", now());
        """
        with self.target_connection.cursor() as cursor:
            for description in source_descriptions:
                description["meta_name"] = description["name"]
                cursor.execute(sql, description)
                print "save product description:", description
                # self.target_connection.commit()

    def create_product_images(self, product_images):
        sql = """
        INSERT INTO `fashion_product`.`t_spider_product_images` 
        (`spider_product_id`, `images`, `farfetch_images`, `date_added`) VALUES 
        (%(spider_product_id)s, %(images)s, %(farfetch_images)s, now());
        """
        with self.target_connection.cursor() as cursor:
            cursor.execute(sql, product_images)
            # self.target_connection.commit()

    def create_product_skus(self, products_skus):
        sql = """
        INSERT INTO `fashion_product`.`t_spider_product_sku` 
        (`spider_product_sku_id`, `spider_product_id`, `size`, `price`, `discount_price`, `currency`, `editor_name`, 
        `date_added`, `stock_status`) 
        VALUES 
        (%(spider_product_sku_id)s, %(spider_product_id)s, %(size)s, %(price)s, %(discount_price)s, %(currency)s, "yuanjie", 
        now(), %(stock_status)s);
        """
        with self.target_connection.cursor() as cursor:
            for sku in products_skus:
                cursor.execute(sql, sku)
                print "save product sku:", sku
                # self.target_connection.commit()

    def copy_product_from_source_17fw(self):
        for source in self.filter_repository.find_17fw_products():
            target_product = self.check_target_product(source["spider_product_id"])
            if target_product:
                print "target product exists:", source
                self.file_exists.write(json.dumps(source))
                continue
            print "start create product:", source
            source_product = self.get_source_product(source["spider_product_id"])
            source_product_descriptions = self.get_source_product_description(source["spider_product_id"])
            source_product_images = self.get_source_product_images(source["spider_product_id"])
            source_product_skus = self.get_source_product_skus(source["spider_product_id"])

            # 设置季节
            source_product["season"] = "17FW"

            if source_product and source_product_descriptions and source_product_images and source_product_skus:
                self.commit_target_product(source_product, source_product_descriptions, source_product_images,
                                           source_product_skus)
                source_product["descriptions"] = source_product_descriptions
                source_product["images"] = source_product_images
                source_product["skus"] = source_product_skus
                self.file_copied.write(json.dumps(source_product, cls=DatetimeEncoder))
            else:
                print "product invalid:", source
                self.file_error.write(json.dumps(source, cls=DatetimeEncoder))

        print "copy products finish:", self.create_product_number, self.create_product_images_number, \
            self.create_product_description_number, self.create_product_sku_number

    def copy_product_from_source_18ss(self):
        for source in self.filter_repository.find_18ss_products():
            target_product = self.check_target_product(source["spider_product_id"])
            if target_product:
                print "target product exists:", source
                self.file_exists.write(json.dumps(source))
                continue
            print "start create product:", source
            source_product = self.get_source_product(source["spider_product_id"])
            source_product_descriptions = self.get_source_product_description(source["spider_product_id"])
            source_product_images = self.get_source_product_images(source["spider_product_id"])
            source_product_skus = self.get_source_product_skus(source["spider_product_id"])

            # 设置季节
            source_product["season"] = "18SS"

            if source_product and source_product_descriptions and source_product_images and source_product_skus:
                self.commit_target_product(source_product, source_product_descriptions, source_product_images,
                                           source_product_skus)
                source_product["descriptions"] = source_product_descriptions
                source_product["images"] = source_product_images
                source_product["skus"] = source_product_skus
                self.file_copied.write(json.dumps(source_product, cls=DatetimeEncoder))
            else:
                print "product invalid:", source
                self.file_error.write(json.dumps(source, cls=DatetimeEncoder))

        print "copy products finish:", self.create_product_number, self.create_product_images_number, \
            self.create_product_description_number, self.create_product_sku_number


if __name__ == '__main__':
    repositories.connect()
    SpiderProductTransmitter().copy_product_from_source_17fw()
    SpiderProductTransmitter().copy_product_from_source_18ss()
