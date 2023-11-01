import os


class Config:

  def __init__(self,
               smtp_server=None,
               smtp_port=None,
               username=None,
               password=None,
               sender=None,
               recipient=None,
               url=None,
               keywords=None,
               interval=None):

    self.SMTP_SERVER = self._get_config('SMTP_SERVER', smtp_server,
                                        'Enter SMTP server: ')
    self.SMTP_PORT = smtp_port or os.getenv('SMTP_PORT') or 587
    self.USERNAME = self._get_config('USERNAME', username,
                                     'Enter email username: ')
    self.PASSWORD = self._get_config('PASSWORD', password,
                                     'Enter email password: ')
    self.SENDER = self._get_config('SENDER', sender,
                                   'Enter sender email address: ')
    self.RECIPIENT = self._get_config('RECIPIENT', recipient,
                                      'Enter recipient email address: ')
    self.URL = url or 'https://www.castleparty.com/bilety.html'
    self.KEYWORDS = keywords if keywords is not None else ["ticket", "bird"]
    self.INTERVAL = interval or 1800

  def _get_config(self, env_var, default, prompt):
    """Helper method to get a value from an environment variable or user input."""
    return default or os.getenv(env_var) or input(prompt)
