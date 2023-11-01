import logging
import os
import asyncio
import sys
from contextlib import asynccontextmanager


class Logger:
  _spinner_task = None
  _stop_spinner = asyncio.Event()

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
  @asynccontextmanager
  async def spinner_context(cls, message: str):
    cls.start_spinner(message)
    try:
      yield
    finally:
      cls.stop_spinner()

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
  def start_spinner(cls, message: str = "Processing"):
    if cls._spinner_task is not None:
      cls.stop_spinner()
    cls._stop_spinner.clear()
    cls._spinner_task = asyncio.create_task(cls._async_spinner(message))

  @classmethod
  @asynccontextmanager
  async def pause_spinner(cls):
    cls.stop_spinner(clear_line=True)
    yield
    cls.start_spinner()

  @classmethod
  def stop_spinner(cls, clear_line=False):
    if cls._spinner_task is not None:
      cls._stop_spinner.set()
      cls._spinner_task.cancel()
      cls._spinner_task = None
    if clear_line:
      sys.stdout.write('\r' + ' ' * 80 + '\r')

  @classmethod
  async def _async_spinner(cls, message: str = "Processing"):
    """Display an asynchronous spinner for a given duration."""
    symbols = ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']
    sys.stdout.write('\033[?25l')
    while not cls._stop_spinner.is_set():
      for symbol in symbols:
        sys.stdout.write(f'\r{message}... {symbol}')
        sys.stdout.flush()
        await asyncio.sleep(0.125)
        if cls._stop_spinner.is_set():
          break
    sys.stdout.write('\r' + ' ' *
                     (len(message) + len(max(symbols, key=len)) + 5) + '\r')
    cls._stop_spinner.clear()
    sys.stdout.write('\033[?25h')

  @classmethod
  async def with_spinner(cls, message, coroutine, *args, **kwargs):
    """Execute a coroutine with a spinner."""
    cls.start_spinner(message)
    try:
      result = await coroutine(*args, **kwargs)
      cls.stop_spinner()
      return result
    except Exception as e:
      cls.stop_spinner()
      raise e
