import os

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
