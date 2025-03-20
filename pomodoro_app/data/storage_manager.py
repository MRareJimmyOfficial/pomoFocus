# pomodoro_app/data/storage_manager.py
import os
import shelve
from ..core import logger

class StorageManager:
    """Manages persistent storage of application state using shelve"""
    
    def __init__(self, storage_file="pomodoro_data"):
        """Initialize the storage manager with a default storage file"""
        logger.info(f"Initializing StorageManager with file: {storage_file}")
        self.storage_file = storage_file
        self.storage_path = os.path.join(os.path.expanduser("~"), ".pomodoro_app")
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
            logger.info(f"Created storage directory at {self.storage_path}")
    
    def save_state(self, state_dict):
        """Save application state to persistent storage"""
        logger.info("Saving application state")
        try:
            full_path = os.path.join(self.storage_path, self.storage_file)
            with shelve.open(full_path) as storage:
                for key, value in state_dict.items():
                    storage[key] = value
                    logger.debug(f"Saved state item: {key}")
            logger.info("Application state saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save application state: {str(e)}")
            return False
    
    def load_state(self, default_state=None):
        """Load application state from persistent storage"""
        logger.info("Loading application state")
        state = {} if default_state is None else default_state.copy()
        
        try:
            full_path = os.path.join(self.storage_path, self.storage_file)
            with shelve.open(full_path) as storage:
                # Update state with stored values
                for key in state.keys():
                    if key in storage:
                        state[key] = storage[key]
                        logger.debug(f"Loaded state item: {key}")
            logger.info("Application state loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load application state: {str(e)}")
        
        return state
