# pomodoro_app/main.py
import tkinter as tk
import sys
import argparse
import atexit
from pomodoro_app.core.logger import get_logger, logging
from pomodoro_app.core.timer import PomodoroTimerCore
from pomodoro_app.data.task_manager import TaskManager
from pomodoro_app.data.storage_manager import StorageManager
from pomodoro_app.utils.tray_icon import SystemTrayIcon
from pomodoro_app.ui.main_window import MainWindow

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Pomodoro Timer Application")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--pomodoro', type=int, help='Set pomodoro time in minutes', default=25)
    parser.add_argument('--break', type=int, help='Set break time in minutes', default=5)
    return parser.parse_args()

def main():
    """Main application entry point"""
    # Parse command line arguments
    args = parse_args()
    
    # Configure logging level based on arguments
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = get_logger()
    logger.setLevel(log_level)
    
    logger.info("Starting Pomodoro Timer Application")
    
    try:
        # Create the storage manager
        storage_manager = StorageManager()
        
        # Create the root Tkinter window
        root = tk.Tk()
        root.title("Pomodoro Timer")
        root.geometry("400x900")
        root.resizable(False, True)
        
        # Initialize core components with storage manager
        timer_core = PomodoroTimerCore(storage_manager)
        task_manager = TaskManager(storage_manager)
        
        # Create a placeholder for SystemTrayIcon
        tray_icon = SystemTrayIcon(None)
        
        # Create the main window
        app = MainWindow(root, timer_core, task_manager, tray_icon)
        
        # Update the tray icon with the real app
        tray_icon.app = app
        
        # Register app.save_state with atexit to ensure state is saved when app exits
        atexit.register(app.save_state)
        
        # Handle window close event
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        
        # Start the Tkinter event loop
        logger.info("Entering main event loop")
        root.mainloop()
        
        logger.info("Application terminated normally")
    
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        logger.exception("Exception details:")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
