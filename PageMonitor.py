import hashlib
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from logger import Logger
from email_notifier import send_notification_email

logger = Logger.setup_logger()


class PageMonitor:

  def __init__(self, config):
    self.config = config
    self.hash = ''
    self.keywords = ["ticket", "bird"]

  async def fetch_from_url(self, url: str, element_id: str = "welcome"):
    async with Logger.pause_spinner():
      logger.info(f'Fetching element_id: {element_id} from URL: {url}')
    async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
        if response.status != 200:
          async with Logger.pause_spinner():
            logger.error(
                f'Fetch Failed: {url}. HTTP status: {response.status}')
          return None
        content = await response.text()
        soup = BeautifulSoup(content, 'html.parser')
        section = soup.find('section', {'id': element_id})
    if section:
      async with Logger.pause_spinner():
        logger.info(f'Found {element_id}: {str(section)}')
      return str(section)
    else:
      async with Logger.pause_spinner():
        logger.warning(
            f'Element with id: {element_id} not found in the content from URL: {url}.'
        )
      return "Element not found"

  def has_keywords(self, content: str) -> bool:
    return any(keyword in content.lower() for keyword in self.keywords)

  async def handle_missing_content(self, send_email):
    await send_email('Element Missing', 'Element not found', self.config)
    logger.warning('Element not found. Email sent.')

  async def has_tickets(self, content, send_email) -> bool:
    has_keywords = self.has_keywords(content)
    if has_keywords:
      await send_email('Tickets Available',
                       'Tickets might be available. Check the website.',
                       self.config)
      logger.info('Tickets might be available. Email sent.')
    return has_keywords

  async def get_updated_page_hash(self, content, send_email):
    new_hash = hashlib.md5(content.encode()).hexdigest()
    if not self.hash or self.hash == new_hash:
      return new_hash
    await send_email('Page Updated', content, self.config)
    logger.info('Update detected. Email sent.')
    return new_hash

  async def handle_error(self, error, send_email):
    await send_email('Error in Page Monitor', str(error), self.config)
    logger.error(f'Error while monitoring {self.config.URL}: {str(error)}')
    await asyncio.sleep(10)

  async def read_page(self, send_email):
    content = await Logger.with_spinner("Fetching content...",
                                        self.fetch_from_url, self.config.URL)
    if content == "Element not found":
      await self.handle_missing_content(send_email)
      return None
    return await self.get_updated_page_hash(content, send_email)

  async def run(self, send_email=send_notification_email):
    while True:
      try:
        logger.info(f'Checking {self.config.URL} for updates...')
        await Logger.with_spinner("Fetching content...", self.read_page,
                                  send_email)
        logger.info(f'No updates detected on {self.config.URL}.')
        Logger.start_spinner("Waiting for the next check...")
        await asyncio.sleep(self.config.INTERVAL)
        Logger.stop_spinner()
      except Exception as e:
        await self.handle_error(e, send_email)
