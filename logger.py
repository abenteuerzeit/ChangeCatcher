import logging
import os
import asyncio
import sys


class Logger:

  class LogColors:
    HEADER = '\033[95m'
    INFO = '\033[94m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DELIMITER = '\033[96m'

  LEVEL_COLORS = {
      logging.WARNING: LogColors.WARNING,
      logging.ERROR: LogColors.FAIL,
      logging.INFO: LogColors.INFO
  }

  @classmethod
  def setup_logger(cls):
    """Set up the logger with custom formatting and colors."""
    terminal_width = os.get_terminal_size().columns

    delimiter_start = f"{cls.LogColors.DELIMITER}"
    delimiter_end = f"{cls.LogColors.ENDC}"
    delimiter_dash = '-' * terminal_width
    delimiter_equal = '=' * terminal_width

    bold_underline = f"{cls.LogColors.BOLD}{cls.LogColors.UNDERLINE}"
    date_info = f"{cls.LogColors.INFO}%(asctime)s{cls.LogColors.ENDC}"
    module_info = f"{cls.LogColors.HEADER}%(module)s -> %(funcName)s{cls.LogColors.ENDC}"

    delimiter_line = f"{delimiter_start}{delimiter_dash}{delimiter_end}"
    level_info = (f"{bold_underline}%(levelname)s{cls.LogColors.ENDC} "
                  f"[{date_info} | {module_info}]")
    end_delimiter = f"{delimiter_start}{delimiter_equal}{delimiter_end}"

    log_format = (f"{delimiter_line}\n"
                  f"{level_info}\n"
                  f"%(message)s\n"
                  f"{end_delimiter}\n")

    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt='%Y-%m-%d %H:%M:%S')

    for level, color in cls.LEVEL_COLORS.items():
      logging.addLevelName(
          level, f"{color}{logging.getLevelName(level)}{cls.LogColors.ENDC}")

    return logging.getLogger()

  @classmethod
  async def async_spinner(self, duration: int, message: str = "Processing"):
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
