# -*- coding: UTF-8 -*-
import re
from modules.scheduler import task_scheduler
from modules.repository import repositories
from mozia.crawler.repository import dao
from mozia.crawler.proxy import crawl_product


class ProductMonitor:
    def __init__(self, source_type=1):
        self.name = ''
        if not dao.task.get_monitor_task_length() > 0:
            dao.task.create_monitor_tasks(source_type)

    def start(self):
        task = dao.task.get_monitor_task()
        while task:
            # try:
            task['is_monitor'] = True
            task['language_id'] = 1
            url = task['url']
            if url.startswith('/cn'):
                task['url'] = '/it/%s' % url[4:]
            source, from_cache = crawl_product(task)
            if not from_cache:
                self.check_product(task, source)
            task = dao.task.get_monitor_task()
            # except Exception as e:
            #     print("monitor error:", repr(e))

    @staticmethod
    def check_product_sold_out(task, source_product):
        if not source_product:
            return False

        status = source_product.get('status')
        # 商品已售罄
        if 100 == status or 101 == status:
            dao.monitor.set_platform_product_status(task['product_id'], 0)
            return False

        sizes = source_product.get('sizes')
        if not sizes or len(sizes) == 0:
            dao.monitor.set_platform_product_status(task['product_id'], 0)
            return False

        return True

    def check_product(self, task, source_product):
        # print(task, source)
        if not self.check_product_sold_out(task, source_product):
            print('product sold out,', task)
            dao.monitor.update_monitored_time(task, 0)
            return
        status = 1 if self.check_product_sizes(task, source_product) else 0
        # 下架商品
        if 0 == status:
            dao.monitor.set_platform_product_status(task['product_id'], 0)

        # 更新监控时间
        dao.monitor.update_monitored_time(task, status)

    @staticmethod
    def get_sizes_mapped(source):
        sizes_mapped = {}
        for size in source['sizes']:
            sizes_mapped[size['size']] = size
            if '均码' == size['size']:
                sizes_mapped['OS'] = size
        return sizes_mapped

    @staticmethod
    def get_size_key(size):
        pattern = re.compile('^(\w+|\d+)\[.*\]$')
        match = pattern.match(size)
        if match:
            return match.group(1)

        if size.upper() == 'ONE SIZE':
            return '均码'

        if size.upper() == 'ONESIZE':
            return '均码'

        return size

    def check_product_sizes(self, task, source):
        platform_product = dao.monitor.get_platform_product(task['product_id'])
        if not platform_product:
            print("product no found:", task)
            return True

        sizes_mapped = self.get_sizes_mapped(source)
        product_id = task['product_id']
        source_type = task['source_type']

        sizes_no_found = 0
        is_need_update = False
        for sku in platform_product['skus']:
            # 只更新欧元价的sku
            if 'EURO' != sku['currency']:
                print('Only update euro sku>>>>>>>>>')
                continue
            size_key = self.get_size_key(sku['size'])
            print('[%s:%s]check product size:%s => %s' % (product_id, source_type, size_key, sku['size']))
            sku_matched = sizes_mapped.get(size_key)
            if not sku_matched:
                dao.monitor.set_platform_product_sizes_status(product_id, sku['size'], 'OFF')
                sizes_no_found += 1
                is_need_update = True
            else:
                # 如果源网站的价格变化了，则平台商品的价格也跟着变化
                f_supply_price = sku_matched.get('supply_price')
                if f_supply_price:
                    f_supply_price = round(float(f_supply_price), 2)

                f_original_price = sku_matched.get('original_price')
                if f_original_price:
                    f_original_price = round(float(f_original_price), 2)

                f_old_supply_price = sku.get('supply_price')
                if f_old_supply_price:
                    f_old_supply_price = float(f_old_supply_price)

                f_old_original_price = sku.get('original_price')
                if f_old_original_price:
                    f_old_original_price = float(f_old_original_price)
                item = {
                    'size': sku_matched.get('size'),
                    'product_sku_id': sku.get('product_sku_id'),
                    'original_price': f_original_price,
                    'supply_price': f_supply_price,
                    'old_supply_price': f_old_supply_price,
                    'old_original_price': f_old_original_price,
                    'quantity': sku_matched['quantity'] if sku_matched.get('quantity') else 0
                }
                if f_supply_price != f_old_supply_price or f_original_price != f_old_original_price:
                    if source_type == 1:
                        # farfetch 商品只有当源商品价格变高了,平台才跟着变
                        if f_original_price and f_old_original_price and f_original_price > f_old_original_price:
                            dao.monitor.update_platform_product_sku(product_id, item)
                        else:
                            print('farfetch price cutted:', item)
                            dao.monitor.update_platform_product_sku(product_id, item)
                    else:
                        dao.monitor.update_platform_product_sku(product_id, item)
                    is_need_update = True
                else:
                    print('price no change:', item)
        # 如果sku更新了，则需要更新商品修改时间，否则 es扫描不到
        if is_need_update:
            dao.monitor.update_platform_product_time(product_id)

        return len(platform_product['skus']) > sizes_no_found


if __name__ == "__main__":
    task_scheduler.connect()
    repositories.connect(host='rm-bp1ri4cfj25gqey09no.mysql.rds.aliyuncs.com', passwd='dba@123456')
    monitor = ProductMonitor(1)
    monitor.start()
    assert ('40' == monitor.get_size_key('40[IT]'))
    assert ('40' == monitor.get_size_key('40'))
    assert ('均码' == monitor.get_size_key('One Size'))
    assert ('均码' == monitor.get_size_key('OneSize'))
    assert ('均码' == monitor.get_size_key('One size'))
    assert ('44' == monitor.get_size_key('44[IT/FR]'))
    assert ('XL' == monitor.get_size_key('XL[IT]'))
