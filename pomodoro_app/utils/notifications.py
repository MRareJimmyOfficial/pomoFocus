# notifications.py

from plyer import notification
from ..core import logger

def send_notification(title, message, timeout=10):
    try:
        logger.info(f"Sending notification: {title}")
        notification.notify(
            title=title,
            message=message,
            timeout=timeout
        )
        logger.debug("Notification sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        return False
