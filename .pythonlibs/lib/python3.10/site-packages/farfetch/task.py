# -*- coding: UTF-8 -*-
import json

from keys import KEY_CATALOG_TASK, KEY_PRODUCT_TASK, KEY_HAOZHUO_PRODUCT_TASKS
from modules.scheduler import task_scheduler
from modules.tools import DatetimeEncoder
from repository import dao


def create_product_tasks():
    if task_scheduler.redis.llen(KEY_PRODUCT_TASK) > 0:
        return

    dao.reset()
    for task in dao.catalog.get_product_tasks():
        print "create product tasks:", task["url"]
        task_scheduler.push(KEY_PRODUCT_TASK, json.dumps(task, cls=DatetimeEncoder))


def create_catalog_tasks():
    if task_scheduler.redis.llen(KEY_CATALOG_TASK) > 0:
        return

    dao.reset()
    for catalog_task in dao.common.get_catalog_tasks():
        print "[%s][%s]create catalog task:" % (catalog_task["task_id"], catalog_task["gender"]), catalog_task["url"]
        task_scheduler.push(KEY_CATALOG_TASK, json.dumps(catalog_task, cls=DatetimeEncoder))


def create_description_zh_tasks():
    for task in dao.product.get_product_descriptions_zh_need_translate():
        url = task["source_url"]
        if url.startswith("https://www.farfetch.cn/cn"):
            url = url.replace("https://www.farfetch.cn/cn", "https://www.farfetch.cn/it")
            zh_task = {
                "url": url,
                "flag": task["flag"],
                "url_id": 0,
                "spider_product_id": task["spider_product_id"]
            }
            print "create description zh task:", zh_task
            task_scheduler.push(KEY_HAOZHUO_PRODUCT_TASKS, json.dumps(zh_task))


def create_haozhuo_spider_task(url, flag, url_id, spider_product_id):
    zh_task = {
        "url": url,
        "flag": flag,
        "url_id": url_id,
        "spider_product_id": spider_product_id
    }
    print "create haozhuo description task:", zh_task
    task_scheduler.push(KEY_HAOZHUO_PRODUCT_TASKS, json.dumps(zh_task))


if __name__ == "__main__":
    create_product_tasks()
    create_catalog_tasks()
