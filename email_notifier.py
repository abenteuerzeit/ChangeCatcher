import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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
