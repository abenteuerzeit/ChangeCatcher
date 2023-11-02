"""
email_notifier.py
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_notification_email(subject, email_body, config):
    """Send email notification with the provided body."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = config.sender
    msg['To'] = config.recipient

    html_content = MIMEText(email_body, 'html')
    msg.attach(html_content)
    with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(config.username, config.password)
        server.sendmail(config.sender, [config.recipient], msg.as_string())
