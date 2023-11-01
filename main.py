import asyncio

from config import Config
from logger import Logger
from PageMonitor import PageMonitor

from jinja2 import Environment, FileSystemLoader


logger = Logger.setup_logger()


def load_email_style():
  with open('email_style.css', 'r') as file:
    return file.read()

def generate_email_body(current_date, content, url):
  env = Environment(loader=FileSystemLoader('.'))
  template = env.get_template('email_template.html')
  style = load_email_style()
  return template.render(style=style,
                         current_date=current_date,
                         content=content,
                         url=url)
async def main():
  config = Config()
  logger.info('Starting the page monitor...')
  page_monitor = PageMonitor(config)
  logger.info(f'Page monitor started. Watching {config.URL}')
  await page_monitor.run()


if __name__ == '__main__':
  asyncio.run(main())
