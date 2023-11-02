"""Configuration module."""
import os
from dotenv import load_dotenv


class Config:
    """Configuration class."""
    def __init__(
        self,
        smtp_server=None,
        smtp_port=None,
        username=None,
        password=None,
        sender=None,
        recipient=None,
        url=None,
        keywords=None,
        interval=None,
        timeout=None
    ):
        load_dotenv()
        self.smtp_server = self._get_config(
            "SMTP_SERVER", smtp_server, "Enter SMTP server: "
        )
        self.smtp_port = smtp_port or os.getenv("SMTP_PORT") or 587
        self.username = self._get_config("USERNAME", username, "Enter email username: ")
        self.password = self._get_config("PASSWORD", password, "Enter email password: ")
        self.sender = self._get_config("SENDER", sender, "Enter sender email address: ")
        self.recipient = self._get_config(
            "RECIPIENT", recipient, "Enter recipient email address: "
        )
        self.url = url or "https://www.castleparty.com/bilety.html"
        self.keywords = keywords if keywords is not None else ["ticket", "bird"]
        self.interval = interval or 1800
        self.timeout = timeout or 5

    def _get_config(self, env_var, default, prompt):
        """Helper method to get a value from an environment variable or user input."""
        return default or os.getenv(env_var) or input(prompt)
