# pomodoro_app/core/timer.py
import time
import threading
from . import logger
from ..utils.notifications import send_notification

class PomodoroTimerCore:
    """Core timer functionality separate from UI"""
    
    def __init__(self, storage_manager=None):
        logger.info("Initializing PomodoroTimerCore")
        self.storage_manager = storage_manager
        
        # Timer default values
        self.default_pomodoro = 25 * 60  # 25 minutes
        self.default_break = 5 * 60      # 5 minutes
        
        # Current settings
        self.pomodoro_time = self.default_pomodoro
        self.break_time = self.default_break
        
        # State variables
        self.timer_running = False
        self.current_time_left = self.pomodoro_time
        self.current_mode = "pomodoro"
        self.pomodoro_count = 0
        
        # Callback functions to be set by UI
        self.on_tick = None
        self.on_pomodoro_complete = None
        self.on_break_complete = None
        
        # Timer thread
        self.timer_thread = None
        
        # Load saved state if storage manager is provided
        if self.storage_manager:
            self._load_state()
    
    def start(self):
        """Start or resume the timer"""
        if self.timer_running:
            logger.warning("Attempted to start timer that is already running")
            return False
            
        logger.info(f"Starting timer in {self.current_mode} mode")
        self.timer_running = True
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()
        self._save_state()
        return True
    
    def pause(self):
        """Pause the timer"""
        if not self.timer_running:
            logger.warning("Attempted to pause timer that is not running")
            return False
            
        logger.info(f"Pausing timer with {self.current_time_left} seconds left")
        self.timer_running = False
        self._save_state()
        return True
    
    def reset(self):
        """Reset the timer"""
        was_running = self.timer_running
        self.timer_running = False
        
        # Wait for timer thread to stop if it was running
        if was_running and self.timer_thread and self.timer_thread.is_alive():
            logger.debug("Waiting for timer thread to stop")
            self.timer_thread.join(timeout=1.0)
        
        # Reset timer state
        if self.current_mode == "pomodoro":
            logger.info(f"Resetting pomodoro timer to {self.pomodoro_time} seconds")
            self.current_time_left = self.pomodoro_time
        else:
            logger.info(f"Resetting break timer to {self.break_time} seconds")
            self.current_time_left = self.break_time
        
        # Notify UI
        if self.on_tick:
            self.on_tick(self.current_time_left, self.current_mode)
        
        self._save_state()
        return True
    
    def _run_timer(self):
        """The main timer loop (runs in a separate thread)"""
        logger.debug(f"Timer thread started in {self.current_mode} mode")
        
        while self.current_time_left > 0 and self.timer_running:
            # Notify UI of current time
            if self.on_tick:
                self.on_tick(self.current_time_left, self.current_mode)
            
            # Wait one second
            time.sleep(1)
            
            # Decrement time if still running
            if self.timer_running:
                self.current_time_left -= 1
                # Save state periodically (every 10 seconds to reduce disk writes)
                if self.current_time_left % 10 == 0:
                    self._save_state()
        
        # Check if timer completed (not just paused or reset)
        if self.timer_running:
            if self.current_mode == "pomodoro":
                logger.info("Pomodoro completed")
                self.pomodoro_count += 1
                
                # Notify UI
                if self.on_pomodoro_complete:
                    self.on_pomodoro_complete(self.pomodoro_count)
                
                # Switch to break mode
                self.current_mode = "break"
                self.current_time_left = self.break_time
                self.timer_running = False
                
                # Send notification
                send_notification(
                    "Pomodoro Completed! 🎉",
                    "Time for a break!"
                )
            else:
                logger.info("Break completed")
                
                # Notify UI
                if self.on_break_complete:
                    self.on_break_complete()
                
                # Switch to pomodoro mode
                self.current_mode = "pomodoro"
                self.current_time_left = self.pomodoro_time
                self.timer_running = False
                
                # Send notification
                send_notification(
                    "Break Finished!",
                    "Ready to focus again?"
                )
            
            # Save state after completing a timer session
            self._save_state()
        
        logger.debug("Timer thread ending")
    
    def set_timer_duration(self, pomodoro_time, break_time):
        """Update timer durations"""
        self.pomodoro_time = pomodoro_time
        self.break_time = break_time
        
        # If timer is not running, update current_time_left
        if not self.timer_running:
            if self.current_mode == "pomodoro":
                self.current_time_left = pomodoro_time
            else:
                self.current_time_left = break_time
        
        self._save_state()
    
    def _save_state(self):
        """Save timer state using storage manager"""
        if self.storage_manager:
            state = {
                "pomodoro_time": self.pomodoro_time,
                "break_time": self.break_time,
                "current_time_left": self.current_time_left,
                "current_mode": self.current_mode,
                "pomodoro_count": self.pomodoro_count
            }
            self.storage_manager.save_state(state)
    
    def _load_state(self):
        """Load timer state using storage manager"""
        if self.storage_manager:
            default_state = {
                "pomodoro_time": self.pomodoro_time,
                "break_time": self.break_time,
                "current_time_left": self.current_time_left,
                "current_mode": self.current_mode,
                "pomodoro_count": self.pomodoro_count
            }
            state = self.storage_manager.load_state(default_state)
            
            self.pomodoro_time = state.get("pomodoro_time", self.default_pomodoro)
            self.break_time = state.get("break_time", self.default_break)
            self.current_time_left = state.get("current_time_left", self.pomodoro_time)
            self.current_mode = state.get("current_mode", "pomodoro")
            self.pomodoro_count = state.get("pomodoro_count", 0)
            logger.info(f"Loaded timer state: mode={self.current_mode}, time_left={self.current_time_left}")
