import logging
import os


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
{LogColors.BOLD}%(levelname)s{LogColors.ENDC}: {LogColors.INFO}%(asctime)s{LogColors.ENDC} 

%(message)s

{'-'*terminal_width}
"""


def setup_logger():
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

  return logging.getLogger()
