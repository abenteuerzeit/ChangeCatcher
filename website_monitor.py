import hashlib
import requests

from bs4 import BeautifulSoup
from email_notifier import send_notification_email
from logger import Logger

logger = Logger.setup_logger()


class WebsiteMonitor:

  def __init__(self, config):
    """Initialize the PageMonitor with the given configuration."""
    self.config = config
    content = self._fetch_from_url(self.config.URL)
    if content:
      self.hash = hashlib.md5(content.encode()).hexdigest()
      logger.info(
          f"Monitoring initialized for {self.config.URL}. Initial content: {content}"
      )
    else:
      self.hash = ''
      logger.info(
          f"Monitoring initialized for {self.config.URL}. No initial content fetched."
      )

  def _fetch_from_url(self, url: str, element_id: str = "welcome"):
    """Fetch content from the given URL and extract the specified element."""
    response = requests.get(url)
    if response.status_code != 200:
      logger.error(f'Fetch Failed: {url}. HTTP status: {response.status_code}')
      return None
    content = response.text
    soup = BeautifulSoup(content, 'html.parser')
    section = soup.find('section', {'id': element_id})
    if section:
      logger.debug(f'Content fetched from {url}')
      return str(section)
    else:
      logger.warning(
          f'Element with id: {element_id} not found in the content from URL: {url}.'
      )
      return "Element not found"

  def _has_keywords(self, content: str) -> bool:
    """Check if the content has any of the predefined keywords."""
    return any(keyword in content.lower() for keyword in self.config.KEYWORDS)

  def _handle_missing_content(self, send_email):
    """Handle scenarios where the expected content is missing."""
    send_email('Element Missing', 'Element not found', self.config)
    logger.warning('Element not found. Email sent.')

  def _get_updated_page_hash(self, content, send_email):
    """Check for updates in the content by comparing MD5 hashes."""
    new_hash = hashlib.md5(content.encode()).hexdigest()
    if self.hash != new_hash:
      self.hash = new_hash
      logger.info('Content update detected.')
      send_email(
          'Content Updated',
          f'New content available at {self.config.URL}. Content: {content}',
          self.config)
    return new_hash

  def _read_page(self, send_email):
    """Read the content of the page and perform necessary checks."""
    logger.info(f'Checking {self.config.URL} for updates...')

    content = self._fetch_from_url(self.config.URL)

    if not content or content == "Element not found":
      self._handle_missing_content(send_email)
      return None

    if self._has_keywords(content):
      send_email('Keyword Detected', 'Keyword found in the content',
                 self.config)
      logger.info('Keyword detected in the content.')

    hash_update = self._get_updated_page_hash(content, send_email)
    if hash_update == self.hash:
      logger.info(f'No updates detected on {self.config.URL}.')
    return hash_update

  def run(self, send_email=send_notification_email):
    """Main loop for periodically checking the page for updates."""
    while True:
      try:
        Logger.display_timer(self.config.INTERVAL)
        self._read_page(send_email)

      except Exception as e:
        logger.error(f'Error while monitoring {self.config.URL}: {str(e)}')
