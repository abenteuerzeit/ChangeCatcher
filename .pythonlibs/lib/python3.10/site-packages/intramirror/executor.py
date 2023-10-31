import time

from modules.scheduler.scheudler import RedisTaskScheduler
from modules.tools import translator, contain_zh
from repository import dao
from task import get_translate_task, create_translate_tasks

task_scheduler = RedisTaskScheduler()


def start_translate():
    task = get_translate_task()
    while task:
        composition = task["composition"]
        if not composition:
            continue

        composition_zh = translator.en_to_zh(composition)
        print "translate composition ok:", composition_zh, task["product_id"]
        task["composition"] = composition_zh
        task["language_id"] = 1

        # if task["name"] and not contain_zh(task["name"]):
        #     task["product_name"] = translator.en_to_zh(task["name"])
        #     print "translate name ok:", task["product_name"], task["name"]
        # else:
        task["product_name"] = task["name"]

        description = task["description"]
        if description and not contain_zh(description):
            task["description"] = translator.en_to_zh(description)
            print "translate description ok:", task["description"]

        location = task["location"]
        if location and not contain_zh(location):
            task["location"] = translator.en_to_zh(location)
            print "translate location ok:", task["location"]

        dao.product.save_description(task)
        task = get_translate_task()


if __name__ == '__main__':
    while True:
        timestamp = int(time.time())
        print ">>>>>>begin translate", time.time()
        try:
            start_translate()
            create_translate_tasks()
        except Exception as e:
            print "translate error:", e
        print ">>>>>>end translate, cost:", int(time.time()) - timestamp
        time.sleep(30)
