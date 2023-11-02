"""
main.py
"""
import asyncio
from config import Config
from logger import Logger
from website_monitor import WebsiteMonitor

logger = Logger.setup_logger()


async def main():
    """Entry point for the application."""
    logger.info("Starting the page monitor...")
    page_monitor = WebsiteMonitor(Config(interval=180))
    page_monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
