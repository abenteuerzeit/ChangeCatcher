import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader

def load_email_style() -> str:
    with open('email_style.css', 'r') as file:
        return file.read()

def generate_email_body(current_date, content, url) -> str:
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('email_template.html')
    style = load_email_style()
    return template.render(style=style,
                           current_date=current_date,
                           content=content,
                           url=url)

def send_notification_email(subject, email_body, config):
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
