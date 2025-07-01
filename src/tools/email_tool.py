import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

class EmailTool:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("SENDER_EMAIL")

        if not all([self.smtp_server, self.smtp_port, self.smtp_username, self.smtp_password, self.sender_email]):
            raise ValueError("One or more SMTP environment variables are not set.")

    def send_email(self, to: str, subject: str, body: str):
        """
        Sends an email using smtplib.
        """
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            return f"Email sent successfully to {to}"
        except Exception as e:
            return f"An error occurred while sending the email: {e}" 