# tray_icon.py

import threading
import pystray
from PIL import Image, ImageDraw, ImageFont
from ..constants.styling import COLORS
from ..core import logger

class SystemTrayIcon:
    def __init__(self, app):
        logger.info("Initializing SystemTrayIcon")
        self.app = app
        self.icon = None
        self.running = False
        self.current_time = "25:00"
        self.current_mode = "pomodoro"
    def create_image(self):
        logger.debug(f"Creating tray icon image: time={self.current_time}, mode={self.current_mode}")
        w, h = 64, 64
        color = COLORS["primary"] if self.current_mode == "pomodoro" else COLORS["secondary"]
        img = Image.new('RGBA', (w, h), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([(0, 0), (w, h)], fill=color)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
            logger.debug("Using arial.ttf font for tray icon")
        except:
            font = ImageFont.load_default()
            logger.warning("Could not load arial.ttf, using default font for tray icon")
        bbox = draw.textbbox((0, 0), self.current_time, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pos = ((w - text_w) / 2, (h - text_h) / 2)
        draw.text(pos, self.current_time, font=font, fill="white")
        return img
    def update_icon(self, time_str, mode):
        logger.debug(f"Updating tray icon: time={time_str}, mode={mode}")
        self.current_time, self.current_mode = time_str, mode
        if self.icon and self.running:
            try:
                self.icon.icon = self.create_image()
                logger.debug("Tray icon updated successfully")
            except Exception as e:
                logger.error(f"Error updating tray icon: {str(e)}")
    def setup(self):
        try:
            logger.info("Setting up system tray icon")
            menu = pystray.Menu(
                pystray.MenuItem("Open Timer", self.app.open_main_window),
                pystray.MenuItem("Exit", self.app.quit_app)
            )
            self.icon = pystray.Icon("pomodoro", self.create_image(), "Pomodoro Timer", menu)
            self.running = True
            threading.Thread(target=lambda: self.icon.run(), daemon=True).start()
            logger.info("System tray icon set up successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to setup system tray icon: {str(e)}")
            return False
    def stop(self):
        if self.icon and self.running:
            try:
                logger.info("Stopping system tray icon")
                self.running = False
                self.icon.stop()
                logger.debug("System tray icon stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping system tray icon: {str(e)}")
