import asyncio

from config import Config
from logger import Logger
from PageMonitor import PageMonitor

from jinja2 import Environment, FileSystemLoader

logger = Logger.setup_logger()


async def main():
  logger.info('Starting the page monitor...')
  page_monitor = PageMonitor(Config(interval=30))
  page_monitor.run()


if __name__ == '__main__':
  asyncio.run(main())
