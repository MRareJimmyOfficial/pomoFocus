# settings_window.py

import tkinter as tk
from tkinter import ttk, messagebox
from ..constants.styling import COLORS, FONTS
from ..core import logger
from .components import RoundedButton

def show_timer_settings(root, pomodoro_time, break_time, update_timer_settings):
    """
    Display a settings dialog for configuring Pomodoro and break times.
    
    Args:
        root: The parent window
        pomodoro_time: Current pomodoro time in seconds
        break_time: Current break time in seconds
        update_timer_settings: Callback function to apply new settings
    """
    logger.info("Opening timer settings dialog")
    
    settings_window = tk.Toplevel(root)
    settings_window.title("Timer Settings")
    settings_window.geometry("300x250")
    settings_window.resizable(False, False)
    settings_window.config(bg=COLORS["bg"])
    settings_window.transient(root)
    settings_window.grab_set()
    
    # Center window relative to parent
    settings_window.geometry(f"+{root.winfo_rootx() + root.winfo_width()//2 - 150}+{root.winfo_rooty() + root.winfo_height()//2 - 125}")
    
    # Settings title
    tk.Label(settings_window, text="Timer Settings", font=FONTS["medium"], 
           bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=(20, 30))
    
    # Pomodoro duration
    pomodoro_frame = tk.Frame(settings_window, bg=COLORS["bg"])
    pomodoro_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
    
    tk.Label(pomodoro_frame, text="Pomodoro length (minutes):", 
           bg=COLORS["bg"], fg=COLORS["text"]).pack(side=tk.LEFT)
    
    pomodoro_minutes = tk.StringVar(value=str(pomodoro_time // 60))
    pomodoro_spinbox = ttk.Spinbox(pomodoro_frame, from_=1, to=60, 
                                 textvariable=pomodoro_minutes, width=5)
    pomodoro_spinbox.pack(side=tk.RIGHT)
    
    # Break duration
    break_frame = tk.Frame(settings_window, bg=COLORS["bg"])
    break_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
    
    tk.Label(break_frame, text="Break length (minutes):", 
           bg=COLORS["bg"], fg=COLORS["text"]).pack(side=tk.LEFT)
    
    break_minutes = tk.StringVar(value=str(break_time // 60))
    break_spinbox = ttk.Spinbox(break_frame, from_=1, to=30, 
                              textvariable=break_minutes, width=5)
    break_spinbox.pack(side=tk.RIGHT)
    
    # Action buttons
    button_frame = tk.Frame(settings_window, bg=COLORS["bg"])
    button_frame.pack(fill=tk.X, padx=20, pady=(20, 0))
    
    def save_settings():
        try:
            logger.debug(f"Saving settings: pomodoro={pomodoro_minutes.get()}, break={break_minutes.get()}")
            new_pomodoro = int(pomodoro_minutes.get()) * 60
            new_break = int(break_minutes.get()) * 60
            
            if new_pomodoro < 60 or new_pomodoro > 3600:
                logger.warning(f"Invalid pomodoro time: {new_pomodoro}")
                raise ValueError("Pomodoro time must be between 1-60 minutes")
                
            if new_break < 60 or new_break > 1800:
                logger.warning(f"Invalid break time: {new_break}")
                raise ValueError("Break time must be between 1-30 minutes")
            
            update_timer_settings(new_pomodoro, new_break)
            settings_window.destroy()
            logger.info("Timer settings saved successfully")
            messagebox.showinfo("Settings Saved", "Timer settings have been updated!")
            
        except ValueError as e:
            logger.error(f"Invalid input: {str(e)}")
            messagebox.showerror("Invalid Input", str(e))
    
    RoundedButton(button_frame, "Save", save_settings, COLORS["primary"], width=120, height=35).pack(side=tk.LEFT, padx=(0, 10))
    RoundedButton(button_frame, "Cancel", settings_window.destroy, COLORS["gray"], width=120, height=35).pack(side=tk.RIGHT)
