# logger.py

import logging
import os
from datetime import datetime
from pathlib import Path

class Logger:
    def __init__(self, log_level=logging.INFO):
        self.logger = logging.getLogger('pomodoro')
        self.logger.setLevel(log_level)
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        log_file = logs_dir / f"pomodoro_{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.info('Logger initialized')
    def get_logger(self):
        return self.logger

_logger_instance = None

def get_logger():
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance.get_logger()

def debug(msg): get_logger().debug(msg)
def info(msg): get_logger().info(msg)
def warning(msg): get_logger().warning(msg)
def error(msg): get_logger().error(msg)
def critical(msg): get_logger().critical(msg)
def exception(msg): get_logger().exception(msg)
