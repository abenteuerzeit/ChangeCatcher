import os
from modules.repository import Repository, repositories


class RepairRepository(Repository):
    def __init__(self):
        Repository.__init__(self)

    def get_task_products(self):
        sql = """
        SELECT
        a.cover,
        a.product_id,
        b.status,
        c.sku_images,
        c.product_id AS id2
        FROM
        fashion_product.t_product a,
        spider.t_product_task b,
        fashion_product.t_product_sku c
        WHERE
        a.product_id = b.product_id
        AND b.`status` IN (1)
        AND c.product_id = a.product_id
        GROUP BY
        a.product_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def set_product_task_url(self, product_id, url):
        sql = """
        UPDATE spider.t_product_task SET cover_url=%s WHERE product_id=%s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (url, product_id))
        self.connection.commit()


repair = RepairRepository()

repositories.connect(host="10.26.235.6", port=3066)

for product in repair.get_task_products():
    cover_url = "%s/00.jpg" % os.path.dirname(product['cover'])
    print(cover_url, product["status"])
    repair.set_product_task_url(product["product_id"], cover_url)
