# Page Monitor by Adrian Mróz

import asyncio
import hashlib
import logging
import os
import shutil
import smtplib
import sys
import re

import aiohttp
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


class Config:
  SMTP_SERVER = os.environ['SMTP_SERVER']
  SMTP_PORT = 587
  USERNAME = os.environ['USERNAME']
  PASSWORD = os.environ['PASSWORD']
  SENDER = os.environ['SENDER']
  RECIPIENT = os.environ['RECIPIENT']

  URL = 'https://www.castleparty.com/bilety.html'
  OLD_URL = 'https://web.archive.org/web/20221127061715/https://castleparty.com/bilety.html'
  INTERVAL = 180


class LogColors:
  HEADER = '\033[95m'
  INFO = '\033[94m'
  SUCCESS = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'


terminal_width = os.get_terminal_size().columns

log_format = f"""
{'-'*terminal_width}
{LogColors.INFO}%(asctime)s{LogColors.ENDC} - 
{LogColors.BOLD}%(levelname)s{LogColors.ENDC}: 
%(message)s
"""

logging.basicConfig(level=logging.INFO,
                    format=log_format,
                    datefmt='%Y-%m-%d %H:%M:%S')

logging.addLevelName(
    logging.WARNING,
    f"{LogColors.WARNING}{logging.getLevelName(logging.WARNING)}{LogColors.ENDC}"
)
logging.addLevelName(
    logging.ERROR,
    f"{LogColors.FAIL}{logging.getLevelName(logging.ERROR)}{LogColors.ENDC}")
logging.addLevelName(
    logging.INFO,
    f"{LogColors.INFO}{logging.getLevelName(logging.INFO)}{LogColors.ENDC}")


def send_notification_email(subject, email_body, config: Config):
  """Send email notification with the provided body."""
  msg = MIMEMultipart('alternative')
  msg['Subject'] = subject
  msg['From'] = config.SENDER
  msg['To'] = config.RECIPIENT

  html_content = MIMEText(email_body, 'html')
  msg.attach(html_content)
  with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
    server.ehlo()
    server.starttls()
    server.login(config.USERNAME, config.PASSWORD)
    server.sendmail(config.SENDER, [config.RECIPIENT], msg.as_string())


async def fetch_content_from_url(url: str, element_id: str = "welcome"):
  """Fetch content for a specific element ID from the provided URL."""
  async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
      content = await response.text()
      soup = BeautifulSoup(content, 'html.parser')
      section = soup.find('section', {'id': element_id})
      return str(section) if section else "Element not found"


async def async_spinner(duration: int, message: str = "Processing"):
  """Display an asynchronous spinner for a given duration."""
  symbols = ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']
  end_time = asyncio.get_event_loop().time() + duration
  while asyncio.get_event_loop().time() < end_time:
    for symbol in symbols:
      sys.stdout.write(f'\r{message}... {symbol}')
      sys.stdout.flush()
      await asyncio.sleep(0.125)
  sys.stdout.write(
      f'\r{message}... Done!{" " * (len(max(symbols, key=len)) + 3)}\n')


def keywords_present(content: str, keywords: list) -> bool:
  """
  Check if any of the keywords are present in the content.
  """
  return any(keyword in content.lower() for keyword in keywords)


async def monitor_page_changes(url: str, interval: int, config: Config):
  """Monitor changes on the provided URL at specified intervals."""
  last_content = ''
  last_hash = ''
  keywords = ["ticket", "bird"]

  while True:
    try:
      logging.info(f'Checking {url} for updates...')
      current_content = await fetch_content_from_url(url)

      if current_content == "Element not found":
        send_notification_email('Element Missing', current_content, config)
        logging.warning(f'Element not found on {url}. Email sent.')
      else:
        current_hash = hashlib.md5(current_content.encode()).hexdigest()

        if last_hash and last_hash != current_hash:
          send_notification_email('Page Updated', current_content, config)
          logging.info(f'Update detected on {url}. Email sent.')

          if keywords_present(current_content, keywords):
            send_notification_email(
                'Tickets Available',
                'Tickets might be available. Check the website.', config)
            logging.info(f'Tickets might be available on {url}. Email sent.')

        else:
          logging.info(f'No updates detected on {url}.')

        last_hash = current_hash

      await async_spinner(interval, "Waiting for the next check")

    except Exception as e:
      send_notification_email('Error in Page Monitor', str(e), config)
      logging.error(f'Error while monitoring {url}: {str(e)}')
      logging.info('Retrying in a moment...')
      await asyncio.sleep(10)


async def main():
  logging.info('Starting the page monitor...')

  config = Config()

  spinner_task = asyncio.create_task(async_spinner(30, "Fetching old content"))
  old_content = await fetch_content_from_url(config.OLD_URL)
  spinner_task.cancel()

  date_match = re.search(r'/(\d{14})/', config.OLD_URL)
  if date_match:
    old_date = datetime.strptime(date_match.group(1),
                                 '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
  else:
    old_date = "Unknown date"

  logging.info(
      f'Fetched old content from {config.OLD_URL} (Date: {old_date}).')

  current_date = datetime.now().strftime('%B %d, %Y %H:%M:%S')
  email_body = f"""
  <style>
      .flex-container {{
          display: flex;
          flex-direction: row-reverse;
          justify-content: space-between;
      }}
      .box {{
          flex: 1;
          padding: 10px;
          border: 1px solid #ddd;
          margin: 5px;
          border-radius: 5px;
      }}
      .updated-content {{
          border-color: #4CAF50;
          background-color: #e8f5e9;
      }}
      h3 {{
          text-align: center;
          background-color: #f5f5f5;
          padding: 5px;
          border-radius: 5px;
          margin-bottom: 10px;
      }}
  </style>
  <em>{current_date}</em>
  <div class="flex-container">
      <div class="box">
          <h3>Previous Content</h3>
          {old_content}
      </div>
      <div class="box updated-content">
          <h3>Updated Content</h3>
          Monitoring has started for the page {config.URL}.
      </div>
  </div>
  """

  send_notification_email('Monitoring Started', email_body, config)
  logging.info(f'Test email sent for {config.URL}. Beginning monitoring...')
  await monitor_page_changes(config.URL, config.INTERVAL, config)


if __name__ == '__main__':
  asyncio.run(main())
