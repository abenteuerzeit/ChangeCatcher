import pymysql
import time
import json


class ProductMonitor:
    def __init__(self):
        self.connection = pymysql.connect(host='10.26.235.6',
                                          port=3066,
                                          user='dba',
                                          passwd='123456',
                                          db='monitor',
                                          cursorclass=pymysql.cursors.DictCursor,
                                          charset='utf8mb4')
        timestamp = int(time.time())
        self.file_no_sku = open("data/no_sku_product_%d.txt" % timestamp, "w")

    def __del__(self):
        self.file_no_sku.close()

    def create_sku_size(self):
        sql = "call create_sku_size()"
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
        self.connection.commit()

    def set_no_sku_product_off(self):
        sql = "SELECT * FROM v_no_sku_product"
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            no_sku_products = cursor.fetchall()
            self.file_no_sku.write(json.dumps(no_sku_products))

        sql = """
          UPDATE fashion_product.t_product a, v_no_sku_product b 
          SET a.product_status=0,modify_time = unix_timestamp()
          WHERE a.product_id=b.product_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
        self.connection.commit()

    def start(self):
        self.create_sku_size()
        self.set_no_sku_product_off()


if __name__ == "__main__":
    ProductMonitor().start()
