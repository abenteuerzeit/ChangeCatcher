import json

from modules.scheduler.scheudler import RedisTaskScheduler
from modules.tools import DatetimeEncoder
from modules.tools import contain_zh
from repository import dao

task_scheduler = RedisTaskScheduler()

KEY_INTRAMIRROR_TRANSLATE_TASKS = "intramirror.translate.tasks"
KEY_INTRAMIRROR_DOWNLOAD_IMAGES_TASKS = "intramirror.download_images.tasks"


def clear_translate_tasks():
    task = task_scheduler.pop(KEY_INTRAMIRROR_TRANSLATE_TASKS)
    while task:
        task = task_scheduler.pop(KEY_INTRAMIRROR_TRANSLATE_TASKS)


def get_translate_task():
    task = task_scheduler.pop(KEY_INTRAMIRROR_TRANSLATE_TASKS)
    return json.loads(task) if task else None


def get_download_images_task():
    task = task_scheduler.pop(KEY_INTRAMIRROR_DOWNLOAD_IMAGES_TASKS)
    return json.loads(task) if task else None


def create_download_images_tasks():
    for image in dao.catalog.find_image_urls_for_task():
        print "create download images task:", image
        task_scheduler.push(KEY_INTRAMIRROR_DOWNLOAD_IMAGES_TASKS, json.dumps(image, cls=DatetimeEncoder))


def create_translate_tasks():
    for description in dao.product.find_descriptions():
        composition = description["composition"]
        if not composition:
            continue

        if contain_zh(composition):
            print "No need translate:", description["product_id"]
            continue

        task_scheduler.push(KEY_INTRAMIRROR_TRANSLATE_TASKS, json.dumps(description, cls=DatetimeEncoder))


if __name__ == '__main__':
    clear_translate_tasks()
    create_translate_tasks()
