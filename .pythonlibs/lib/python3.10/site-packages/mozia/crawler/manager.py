from mozia.crawler.monitor import start_product_monitor

from modules.repository import repositories
from modules.scheduler import task_scheduler

if __name__ == '__main__':
    repositories.connect(host='10.26.235.6', port=3066)
    task_scheduler.connect()
    start_product_monitor()
    # app.run(debug=True, port=9604, host="0.0.0.0")
