"""
website_monitor.py
"""
import hashlib
import requests

from bs4 import BeautifulSoup
from email_notifier import send_notification_email
from logger import Logger

logger = Logger.setup_logger()


class WebsiteMonitor:
    """
    WebsiteMonitor class for monitoring a website for updates.
    """

    def __init__(self, config):
        """Initialize the PageMonitor with the given configuration."""
        self.config = config
        content = self._fetch_from_url(self.config.url)
        if content:
            self.hash = hashlib.md5(content.encode()).hexdigest()
            logger.info(
                "Monitoring initialized for %s. Initial content: %s",
                self.config.url,
                content,
            )
        else:
            self.hash = ""
            logger.info(
                "Monitoring initialized for %s. No initial content fetched.",
                self.config.url,
            )

    def _fetch_from_url(self, url: str, element_id: str = "welcome"):
        """Fetch content from the given url and extract the specified element."""
        try:
            response = requests.get(url, timeout=self.config.timeout)
        except requests.RequestException as e:
            logger.error("Fetch Failed: %s. Error: %s", url, str(e))
            return None

        if response.status_code != 200:
            logger.error("Fetch Failed: %s. HTTP status: %d", url, response.status_code)
            return None

        content = response.text
        soup = BeautifulSoup(content, "html.parser")
        section = soup.find("section", {"id": element_id})
        if section:
            logger.debug("Content fetched from %s", url)
            return str(section)
        else:
            logger.warning(
                "Element with id: %s not found in the content from url: %s.",
                element_id,
                url,
            )
            return "Element not found"

    def _has_keywords(self, content: str) -> bool:
        """Check if the content has any of the predefined keywords."""
        return any(keyword in content.lower() for keyword in self.config.keywords)

    def _handle_missing_content(self, send_email):
        """Handle scenarios where the expected content is missing."""
        send_email("Element Missing", "Element not found", self.config)
        logger.warning("Element not found. Email sent.")

    def _get_updated_page_hash(self, content, send_email):
        """Check for updates in the content by comparing MD5 hashes."""
        new_hash = hashlib.md5(content.encode()).hexdigest()
        if self.hash != new_hash:
            self.hash = new_hash
            logger.info("Content update detected.")
            send_email(
                "Content Updated",
                f"New content available at {self.config.url}. Content: {content}",
                self.config,
            )
        return new_hash

    def _read_page(self, send_email):
        """Read the content of the page and perform necessary checks."""
        logger.info("Checking %s for updates...", self.config.url)

        content = self._fetch_from_url(self.config.url)

        if not content or content == "Element not found":
            self._handle_missing_content(send_email)
            return None

        if self._has_keywords(content):
            send_email("Keyword Detected", "Keyword found in the content", self.config)
            logger.info("Keyword detected in the content.")

        hash_update = self._get_updated_page_hash(content, send_email)
        if hash_update == self.hash:
            logger.info("No updates detected on %s.", self.config.url)
        return hash_update

    def run(self, send_email=send_notification_email):
        """Main loop for periodically checking the page for updates."""
        while True:
            try:
                self._read_page(send_email)
                Logger.display_timer(self.config.interval)

            except requests.ConnectionError as error:
                logger.error("Connection error while accessing %s: %s", self.config.url, error)

            except requests.Timeout as error:
                logger.error("Timeout occurred while accessing %s: %s", self.config.url, error)

            except requests.HTTPError as error:
                logger.error("HTTP error while accessing %s: %s", self.config.url, error)

            except requests.RequestException as error:
                logger.error("Error while making a request to %s: %s", self.config.url, error)

            except KeyboardInterrupt:
                logger.info("Monitoring interrupted by user")
                break

            # except Exception as e:
            #     logger.error(
            #         "An unexpected error occurred while monitoring %s: %s",
            #         self.config.url, e
            #     )
