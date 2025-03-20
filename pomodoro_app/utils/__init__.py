# utils/__init__.py

from .notifications import send_notification
from .tray_icon import SystemTrayIcon

# Configure what gets imported with "from utils import *"
__all__ = [
    'send_notification',
    'SystemTrayIcon'
]

# Package-level constants
PACKAGE_VERSION = '1.0.0'

# Import logging module
from ..core import logger

# Package initialization log
logger.info("Utils package initialized")
