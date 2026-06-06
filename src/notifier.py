import smtplib
import requests
import logging
from email.mime.text import MIMEText
from src.config import config

logger = logging.getLogger("AutomationAgent.Notifier")

class Notifier:
    def __init__(self):
        self.gmail_enabled = config.get("notifications.gmail.enabled", False)
        self.smtp_server = config.get("notifications.gmail.smtp_server", "smtp.gmail.com")
        self.smtp_port = config.get("notifications.gmail.smtp_port", 587)
        self.sender_email = config.get("notifications.gmail.sender_email")
        self.sender_password = config.get("notifications.gmail.sender_password")
        self.recipient_email = config.get("notifications.gmail.recipient_email")

        self.whatsapp_enabled = config.get("notifications.whatsapp.enabled", False)
        self.whatsapp_phone = config.get("notifications.whatsapp.phone_number")
        self.whatsapp_apikey = config.get("notifications.whatsapp.apikey")

    def send_gmail(self, subject, body):
        """Sends an email notification via SMTP."""
        if not self.gmail_enabled:
            logger.info(f"[Gmail Disabled] Would send subject: '{subject}'")
            return True
            
        if not self.sender_email or self.sender_email == "your-email@gmail.com":
            logger.warning("Gmail notifications enabled but credentials not configured in settings.yaml. Skipping.")
            return False

        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls() # Enable security
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
                
            logger.info(f"Gmail alert sent to {self.recipient_email} - Subject: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Gmail alert: {e}")
            return False

    def send_whatsapp(self, message):
        """Sends a WhatsApp message using the free CallMeBot gateway."""
        if not self.whatsapp_enabled:
            logger.info(f"[WhatsApp Disabled] Would send message: '{message}'")
            return True

        if not self.whatsapp_phone or self.whatsapp_phone == "+91XXXXXXXXXX":
            logger.warning("WhatsApp notifications enabled but phone/apikey not configured in settings.yaml. Skipping.")
            return False

        try:
            # CallMeBot URL formatting requires URL encoding the text
            url = "https://api.callmebot.com/whatsapp.php"
            params = {
                "phone": self.whatsapp_phone,
                "text": message,
                "apikey": self.whatsapp_apikey
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                logger.info("WhatsApp alert sent successfully via CallMeBot.")
                return True
            else:
                logger.error(f"CallMeBot WhatsApp gateway error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send WhatsApp alert: {e}")
            return False

    def notify_script_ready(self, topic_title):
        """Sends a notification that a script is drafted and awaiting approval."""
        subject = f"🚨 Action Required: New Shorts Script Generated!"
        body = (
            f"Hi Creator,\n\n"
            f"A new YouTube Shorts script has been generated on the topic: '{topic_title}'.\n"
            f"It is saved as a 'DRAFT' in your Google Sheet (or local database).\n\n"
            f"Please review it, make any manual edits you want, and change the 'Approval Status' "
            f"to 'APPROVED' to trigger the video rendering pipeline.\n\n"
            f"Best,\nAI Automation Agent"
        )
        self.send_gmail(subject, body)
        self.send_whatsapp(f"🤖 AI Shorts Alert: Script for '{topic_title}' is ready for review in Google Sheets. Change status to 'APPROVED' to render.")

    def notify_video_ready(self, topic_title):
        """Sends a notification that a video has been compiled and is awaiting publish approval."""
        subject = f"🎬 Action Required: Shorts Video Rendered & Ready to Publish!"
        body = (
            f"Hi Creator,\n\n"
            f"The video for '{topic_title}' has been successfully compiled and rendered with subtitles.\n\n"
            f"Please watch the video to check quality. If you are satisfied, change the "
            f"'Approval Status' in your database to 'PUBLISH'. This will trigger the Playwright "
            f"automated uploader to publish it to YouTube Shorts.\n\n"
            f"Best,\nAI Automation Agent"
        )
        self.send_gmail(subject, body)
        self.send_whatsapp(f"🤖 AI Shorts Alert: Video for '{topic_title}' has finished rendering. Check the file and set status to 'PUBLISH' to upload!")

    def notify_upload_success(self, topic_title):
        """Sends a confirmation that a video has been published to YouTube Shorts."""
        subject = f"🚀 Success: Shorts Video Published to YouTube!"
        body = (
            f"Hi Creator,\n\n"
            f"Congratulations! The video for '{topic_title}' has been successfully uploaded "
            f"and published to your YouTube channel as a Short.\n\n"
            f"Check your YouTube Studio dashboard for analytics.\n\n"
            f"Best,\nAI Automation Agent"
        )
        self.send_gmail(subject, body)
        self.send_whatsapp(f"🎉 AI Shorts Success: Video '{topic_title}' has been uploaded and published on YouTube! Check your channel.")
base_notifier = Notifier()
