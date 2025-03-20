# pomodoro_app/data/task_manager.py
from datetime import datetime
from ..core import logger

class TaskManager:
    """Manages task history and status updates"""
    
    def __init__(self, storage_manager=None):
        logger.info("Initializing TaskManager")
        self.storage_manager = storage_manager
        self.task_history = []
        self.current_task = "No task set"
        
        # Load saved state if storage manager is provided
        if self.storage_manager:
            self._load_state()
    
    def get_current_task(self):
        """Get the current task"""
        return self.current_task
    
    def set_task(self, task):
        """Set a new current task"""
        if not task:
            logger.warning("Attempted to set empty task")
            return False
            
        logger.info(f"Setting new task: '{task}'")
        self.current_task = task
        
        # Add to history immediately
        timestamp = datetime.now().strftime("%H:%M")
        self.task_history.insert(0, {
            "time": timestamp, 
            "task": self.current_task, 
            "status": "ongoing"
        })
        logger.debug(f"Added task to history: '{task}' at {timestamp}")
        
        # Save state if storage manager is available
        self._save_state()
        return True
    
    def update_task_status(self, status):
        """Update the status of the current task in history"""
        if not self.task_history:
            logger.warning(f"Attempted to update task status to '{status}' but history is empty")
            return False
            
        if self.task_history[0]["task"] == self.current_task:
            logger.info(f"Updating task '{self.current_task}' status to '{status}'")
            self.task_history[0]["status"] = status
            
            # Save state if storage manager is available
            self._save_state()
            return True
        else:
            logger.warning(f"Task '{self.current_task}' not found at top of history")
            return False
    
    def _save_state(self):
        """Save task state using storage manager"""
        if self.storage_manager:
            state = {
                "task_history": self.task_history,
                "current_task": self.current_task
            }
            self.storage_manager.save_state(state)
    
    def _load_state(self):
        """Load task state using storage manager"""
        if self.storage_manager:
            default_state = {
                "task_history": self.task_history,
                "current_task": self.current_task
            }
            state = self.storage_manager.load_state(default_state)
            
            self.task_history = state.get("task_history", [])
            self.current_task = state.get("current_task", "No task set")
            logger.info(f"Loaded {len(self.task_history)} tasks from storage")
