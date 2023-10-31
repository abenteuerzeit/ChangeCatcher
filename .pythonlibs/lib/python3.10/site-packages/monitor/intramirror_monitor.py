# -*- coding: UTF-8 -*-
# import json
import time
import logging
from repository import dao
# from modules.scheduler import task_scheduler
from modules.repository import repositories
from intramirror.product import crawl_product_from_monitor

KEY_INTRAMIRROR_MONITOR_TASKS = "intramirror.monitor.tasks"

monitor_task_list = []


def get_monitor_task_length():
    # return task_scheduler.length(KEY_INTRAMIRROR_MONITOR_TASKS)
    return len(monitor_task_list)


def create_monitor_tasks():
    if get_monitor_task_length() > 0:
        return

    for item in dao.monitor.get_monitor_products_from_im():
        # task_scheduler.push(KEY_INTRAMIRROR_MONITOR_TASKS, json.dumps(item))
        monitor_task_list.append(item)


def get_monitor_task():
    # task_string = task_scheduler.pop(KEY_INTRAMIRROR_MONITOR_TASKS)
    # return json.loads(task_string) if task_string else None
    return monitor_task_list.pop(0) if len(monitor_task_list) > 0 else None


def process_result(task):
    if task["event"] == "SKU_NO_FOUND" or task["event"] == "SKU_ZERO_QUANTITY_ALL":
        # 没有SKU，则下架商品
        dao.monitor.set_platform_product_status(task["product_id"], 0)
        return

    for sku in task["skus"]:
        if sku["quantity"] > 0:
            dao.monitor.set_platform_product_size_quantity(task["product_id"], sku["size"], sku["quantity"])
        else:
            dao.monitor.set_platform_product_size_status(task["product_id"], sku["size"], "OFF")


def compare_product(task, crawl_product):
    # 商品已下架， 需要处理
    if not crawl_product:
        print("product no found:", task)

    platform_product = dao.monitor.get_platform_product(task["product_id"])

    sizes_mapped = {}
    if crawl_product.get("skus"):
        for sku in crawl_product.get("skus"):
            sizes_mapped[sku["size"]] = sku

    zero_quantity_sizes = []
    platform_skus = platform_product.get("skus")
    if platform_skus:
        for sku in platform_skus:
            size_name = sku["size"]
            if not sizes_mapped.get(size_name):
                sku["quantity"] = 0
                zero_quantity_sizes.append(size_name)
                continue

            crawl_size = sizes_mapped[size_name]
            sku["quantity"] = crawl_size["count"]
            if not sku["quantity"]:
                zero_quantity_sizes.append(size_name)

    task["event"] = "UPDATE"
    # 没有SKU, 商品要下架
    if not platform_skus:
        task["event"] = "SKU_NO_FOUND"

    # 所有 SKU 库存为零
    if len(zero_quantity_sizes) == len(platform_skus):
        task["event"] = "SKU_ZERO_QUANTITY_ALL"

    # 需要列新平台商品SKU
    task["skus"] = platform_skus
    task["zero_quantity_sizes"] = zero_quantity_sizes

    return task


def exec_monitor_task(task):
    print("begin task", task)
    product_id = task["product_id"]
    crawl_product = crawl_product_from_monitor(product_id, task["url"])
    process_result(compare_product(task, crawl_product))
    print("end task", task["event"], task["product_id"])


def start_monitor_task():
    task = get_monitor_task()
    while task:
        try:
            exec_monitor_task(task)
        except Exception as e:
            print(repr(e))
        task = get_monitor_task()


def start_intramirror_monitor():
    create_monitor_tasks()
    start_monitor_task()


if __name__ == "__main__":
    repositories.connect()
    while True:
        start_intramirror_monitor()
        time.sleep(10)
