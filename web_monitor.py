import hashlib
import asyncio

import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime

from logger import Logger
from email_notifier import send_notification_email

logger = Logger.setup_logger()


class PageMonitor:
  def __init__(self, config):
    self.config = config
    self.last_hash = ''
    self.keywords = ["ticket", "bird"]

  async def fetch_content_from_url(self,
                                   url: str,
                                   element_id: str = "welcome"):
    async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
        content = await response.text()
        soup = BeautifulSoup(content, 'html.parser')
        section = soup.find('section', {'id': element_id})
        return str(section) if section else "Element not found"

  def keywords_present(self, content: str) -> bool:
    return any(keyword in content.lower() for keyword in self.keywords)

  async def handle_missing_content(self, send_email):
    send_email('Element Missing', 'Element not found', self.config)
    logger.warning('Element not found. Email sent.')

  async def check_content_changes(self, current_content, send_email):
    current_hash = hashlib.md5(current_content.encode()).hexdigest()

    if not self.last_hash or self.last_hash == current_hash:
      return current_hash

    send_email('Page Updated', current_content, self.config)
    logger.info('Update detected. Email sent.')

    if self.keywords_present(current_content):
      send_email('Tickets Available',
                 'Tickets might be available. Check the website.', self.config)
      logger.info('Tickets might be available. Email sent.')

    return current_hash

  async def handle_error(self, e, send_email):
    send_email('Error in Page Monitor', str(e), self.config)
    logger.error(f'Error while monitoring {self.config.URL}: {str(e)}')
    await asyncio.sleep(10)

  async def monitor_content(self, send_email):
    current_content = await self.fetch_content_from_url(self.config.URL)
    if current_content == "Element not found":
      await self.handle_missing_content(send_email)
      return None

    self.last_hash = await self.check_content_changes(current_content, send_email)
    return self.last_hash

  async def monitor(self, send_email=send_notification_email):
    while True:
      try:
        logger.info(f'Checking {self.config.URL} for updates...')
        last_hash = await self.monitor_content(send_email)
        if not last_hash:
          logger.info(f'No updates detected on {self.config.URL}.')
        await Logger.async_spinner(self.config.INTERVAL, "Waiting for the next check")

      except Exception as e:
        await self.handle_error(e, send_email)


