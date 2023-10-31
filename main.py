import asyncio
import re

from datetime import datetime
from config import Config
from logger import Logger
from web_monitor import PageMonitor

from email_notifier import send_notification_email
from jinja2 import Environment, FileSystemLoader

logger = Logger.setup_logger()

env = Environment(loader=FileSystemLoader('.'))

template = env.get_template('email_template.html')


def load_email_style():
  with open('email_style.css', 'r') as file:
    return file.read()


def generate_email_body(current_date, old_content, url):
  style = load_email_style()
  return template.render(style=style,
                         current_date=current_date,
                         old_content=old_content,
                         url=url)


async def fetch_old_content(monitor: PageMonitor, url: str):
  spinner_task = asyncio.create_task(Logger.async_spinner(30, "Fetching old content"))
  content = await monitor.fetch_content_from_url(url)
  spinner_task.cancel()
  return content


def extract_date_from_url(url: str):
  date_match = re.search(r'/(\d{14})/', url)
  return datetime.strptime(date_match.group(1), '%Y%m%d%H%M%S').strftime(
      '%Y-%m-%d %H:%M:%S') if date_match else "Unknown date"


async def main():
  config = Config()

  logger.info('Starting the page monitor...')

  monitor = PageMonitor(config)
  old_content = await fetch_old_content(monitor, config.OLD_URL)
  old_date = extract_date_from_url(config.OLD_URL)

  logger.info(f'Fetched old content from {config.OLD_URL} (Date: {old_date}).')

  current_date = datetime.now().strftime('%B %d, %Y %H:%M:%S')
  email_body = generate_email_body(current_date, old_content, config.URL)

  send_notification_email('Monitoring Started', email_body, config)
  logger.info(f'Test email sent for {config.URL}. Beginning monitoring...')
  await monitor.monitor()


if __name__ == '__main__':
  asyncio.run(main())
