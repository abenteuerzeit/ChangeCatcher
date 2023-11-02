"""
main.py
"""

import asyncio
from config import Config
from logger import Logger
from website_monitor import WebsiteMonitor

logger = Logger.setup_logger()


def parse_interval_input(interval_str):
    """Parse the interval input and return the duration in seconds."""
    interval_mapping = {
        "1m": 60,
        "30m": 1800,
        "1h": 3600,
        "4h": 14400,
        "12h": 43200,
        "24h": 86400,
        "48h": 172800,
        "72h": 259200,
        "1w": 604800,
    }

    if interval_str == "":
        return 300  # Default interval of 5 minutes

    if interval_str in interval_mapping:
        return interval_mapping[interval_str]

    try:
        custom_interval = int(interval_str)
        if custom_interval <= 0:
            raise ValueError("Interval must be a positive number of seconds.")
        return custom_interval
    except ValueError as e:
        logger.error(str(e))
        return None


def get_interval_legend():
    """Return a string with helpful information about the interval input."""
    return (
        "Enter an interval for monitoring updates:\n"
        "Type '1m' for 1 minute, '30m' for 30 minutes, '1h' for 1 hour, \n"
        "'4h' for 4 hours, '12h' for 12 hours, '24h' for 24 hours,\n"
        "'48h' for 48 hours, '72h' for 72 hours, '1w' for one week,\n"
        "or enter a custom interval in seconds (e.g., '30' for 30 seconds).\n"
        "Press Enter to use the default interval of 5 minutes, or type 'quit' to exit."
    )


async def get_interval():
    """Prompt the user for the interval duration and return it."""
    while True:
        logger.info(get_interval_legend())
        interval_str = (input(
            "Enter a time key or custom interval in seconds (default 5m): ").
                        strip().lower())

        if interval_str == "quit":
            logger.info("Operation aborted by the user.")
            raise SystemExit

        interval = parse_interval_input(interval_str)
        if interval is not None:
            return interval
        else:
            logger.error(
                "Invalid input. Please use one of the predefined keys,"
                "enter a positive number of seconds,"
                "or type 'quit' to exit.")


async def main():
    """Entry point for the application."""
    logger.info("Starting the website monitor...")
    try:
        interval = await get_interval()
        website_monitor = WebsiteMonitor(Config(interval=interval))
        website_monitor.run()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error("The website monitor could not be started.")


if __name__ == "__main__":
    asyncio.run(main())
