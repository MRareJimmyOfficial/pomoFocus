# main_window.py

import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from ..constants.styling import COLORS, FONTS
from ..core import logger
from .settings_window import show_timer_settings
from .components import RoundedButton, RoundedFrame, round_rect_points

class FloatingBubble(tk.Toplevel):
    """Creates a floating transparent bubble with live timer"""
    
    def __init__(self, parent, timer_core):
        logger.info("Creating floating timer bubble")
        super().__init__(parent)
        
        # Configure window properties
        self.overrideredirect(True)  # Remove window decorations
        self.wm_attributes('-topmost', True)  # Stay on top
        self.wm_attributes('-alpha', 0.75)  # Set transparency
        
        # Try to make it a tool window on Windows
        try:
            self.wm_attributes("-toolwindow", True)
        except:
            logger.debug("Tool window attribute not supported on this platform")
        
        # Set bubble position (bottom right corner)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        bubble_size = 120
        self.geometry(f"{bubble_size}x{bubble_size}+{screen_width-bubble_size-20}+{screen_height-bubble_size-50}")
        
        # Configure bubble appearance
        self.bubble_color = COLORS["primary"] if timer_core.current_mode == "pomodoro" else COLORS["secondary"]
        self.configure(bg=self.bubble_color)
        
        # Make it round (as much as possible cross-platform)
        canvas = tk.Canvas(self, width=bubble_size, height=bubble_size, 
                         bg=self.bubble_color, highlightthickness=0)
        canvas.pack()
        canvas.create_oval(10, 10, bubble_size-10, bubble_size-10, 
                        fill=self.bubble_color, outline=self.bubble_color)
        
        # Add timer label
        self.time_label = tk.Label(
            self, 
            font=FONTS["medium"],
            bg=self.bubble_color,
            fg=COLORS["white"],
            text="--:--"
        )
        self.time_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Add mode indicator
        mode_text = "POMODORO" if timer_core.current_mode == "pomodoro" else "BREAK"
        self.mode_label = tk.Label(
            self,
            font=FONTS["tiny"],
            bg=self.bubble_color,
            fg=COLORS["white"],
            text=mode_text
        )
        self.mode_label.place(relx=0.5, rely=0.75, anchor=tk.CENTER)
        
        # Store reference to timer core
        self.timer_core = timer_core
        
        # Add click event to restore main window
        self.bind("<Button-1>", self._on_click)
        
        # Make window draggable
        self.bind("<ButtonPress-1>", self._start_drag)
        self.bind("<B1-Motion>", self._on_drag)
        
        # Update timer display
        self.update_time()
        
        logger.debug("Floating bubble created successfully")
    
    def _start_drag(self, event):
        """Save initial position for dragging"""
        self._drag_x = event.x
        self._drag_y = event.y
    
    def _on_drag(self, event):
        """Handle mouse dragging to move the bubble"""
        x = self.winfo_x() - self._drag_x + event.x
        y = self.winfo_y() - self._drag_y + event.y
        self.geometry(f"+{x}+{y}")
    
    def _on_click(self, event):
        """Handle click on the bubble"""
        self.master.open_main_window()
    
    def update_time(self):
        """Update the time display in the bubble"""
        if not self.winfo_exists():
            return
            
        # Calculate minutes and seconds
        mins, secs = divmod(self.timer_core.current_time_left, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        # Update label
        self.time_label.config(text=time_str)
        
        # Update bubble color based on mode
        current_color = COLORS["primary"] if self.timer_core.current_mode == "pomodoro" else COLORS["secondary"]
        if current_color != self.bubble_color:
            self.bubble_color = current_color
            self.configure(bg=self.bubble_color)
            self.time_label.config(bg=self.bubble_color)
            self.mode_label.config(bg=self.bubble_color)
            mode_text = "POMODORO" if self.timer_core.current_mode == "pomodoro" else "BREAK"
            self.mode_label.config(text=mode_text)
        
        # Add pulsing effect if timer is running
        if self.timer_core.timer_running and secs % 2 == 0:
            self.time_label.config(fg=COLORS["white"])
        else:
            self.time_label.config(fg=COLORS["white"])
        
        # Schedule next update
        self.after(1000, self.update_time)

class MainWindow:
    def __init__(self, root, timer_core, task_manager, tray_icon):
        logger.info("Initializing MainWindow")
        self.root = root
        self.root.title("Pomodoro Timer")
        self.root.geometry("400x900")
        self.root.resizable(False, True)
        self.root.config(bg=COLORS["bg"])
        
        self.timer_core = timer_core
        self.task_manager = task_manager
        self.tray_icon = tray_icon
        
        # Set callbacks for timer core
        self.timer_core.on_tick = self.update_timer_display
        self.timer_core.on_pomodoro_complete = self.on_pomodoro_complete
        self.timer_core.on_break_complete = self.on_break_complete
        
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        logger.info("MainWindow initialized successfully")
    
    def setup_ui(self):
        logger.debug("Setting up UI components")
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main, text="Pomodoro Timer", font=FONTS["title"], 
               bg=COLORS["bg"], fg=COLORS["primary"]).pack(pady=(0, 20))
        
        # Timer display with rounded corners
        self.create_timer_display(main)
        
        # Task section with rounded corners
        self.create_task_section(main)
        
        # Pomodoro counter
        self.counter_label = tk.Label(main, text=f"🍅 × {self.timer_core.pomodoro_count}", 
                                    font=FONTS["medium"], bg=COLORS["bg"], fg=COLORS["primary"])
        self.counter_label.pack(pady=(0, 20))
        
        # Control buttons
        self.create_buttons(main)
        
        # Timer settings button
        RoundedButton(main, "⚙️ Timer Settings", self.show_timer_settings, 
                    COLORS["gray"], width=360, height=40, radius=10).pack(pady=(5, 15))
        
        # Task history section
        self.create_history_section(main)
        
        # Minimize button
        tk.Button(main, text="Minimize to Tray", font=FONTS["list"], 
               bg=COLORS["bg"], fg=COLORS["text"], relief=tk.FLAT,
               command=self.minimize_to_tray, borderwidth=0).pack(pady=(10, 0))
        
        logger.debug("UI setup completed")
    
    def create_timer_display(self, parent):
        logger.debug("Creating timer display")
        timer_frame = RoundedFrame(parent, 360, 180, 15, bg=COLORS["primary"])
        timer_frame.pack(pady=(0, 20))
        
        mins, secs = divmod(self.timer_core.current_time_left, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        self.time_display = tk.Label(timer_frame, text=time_str, font=FONTS["large"], 
                                   bg=COLORS["primary"], fg=COLORS["white"])
        timer_frame.create_window(180, 70, window=self.time_display)
        
        self.status_label = tk.Label(timer_frame, text="Ready to start", font=FONTS["medium"], 
                                   bg=COLORS["primary"], fg=COLORS["white"])
        timer_frame.create_window(180, 130, window=self.status_label)
    
    def create_task_section(self, parent):
        logger.debug("Creating task section")
        task_frame = RoundedFrame(parent, 360, 90, 15, bg=COLORS["white"])
        task_frame.pack(pady=(0, 20))
        
        task_frame.create_window(180, 25, window=tk.Label(task_frame, text="Current Task", 
                                                      font=FONTS["small"], bg=COLORS["white"], 
                                                      fg=COLORS["text"]))
        self.task_label = tk.Label(task_frame, text=self.task_manager.current_task, 
                                 font=FONTS["tiny"], bg=COLORS["white"], fg=COLORS["primary"], 
                                 wraplength=320)
        task_frame.create_window(180, 55, window=self.task_label)
    
    # In the create_buttons method, add a switch mode button:
    def create_buttons(self, parent):
        logger.debug("Creating control buttons")
        btn_frame = tk.Frame(parent, bg=COLORS["bg"])
        btn_frame.pack(pady=(0, 20))
        
        self.start_button = RoundedButton(btn_frame, "Start", self.start_timer, 
                                    COLORS["primary"], width=110)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        RoundedButton(btn_frame, "Reset", self.reset_timer, 
                COLORS["gray"], width=110).pack(side=tk.LEFT, padx=(0, 10))
        
        # Add the switch mode button
        switch_color = COLORS["secondary"] if self.timer_core.current_mode == "pomodoro" else COLORS["primary"]
        switch_text = "→ Break" if self.timer_core.current_mode == "pomodoro" else "→ Pomodoro"
        self.switch_button = RoundedButton(btn_frame, switch_text, self.switch_mode, 
                                        switch_color, width=110)
        self.switch_button.pack(side=tk.LEFT, padx=(0, 10))
        
        RoundedButton(btn_frame, "Set Task", self.set_task, 
                COLORS["accent"], width=110).pack(side=tk.LEFT)

    # Then add the switch_mode method:
    def switch_mode(self):
        """Switch between Pomodoro and break modes"""
        logger.info(f"Switching from {self.timer_core.current_mode} mode")
        
        was_running = self.timer_core.timer_running
        if was_running:
            self.timer_core.pause()
        
        # If in pomodoro mode, mark task as interrupted if running
        if self.timer_core.current_mode == "pomodoro" and was_running:
            if self.timer_core.current_time_left < self.timer_core.pomodoro_time:
                self.task_manager.update_task_status("interrupted")
                self.update_history_display()
        
        # Toggle mode
        new_mode = "break" if self.timer_core.current_mode == "pomodoro" else "pomodoro"
        self.timer_core.current_mode = new_mode
        
        # Reset timer to the appropriate time for the new mode
        if new_mode == "pomodoro":
            self.timer_core.current_time_left = self.timer_core.pomodoro_time
            self.status_label.config(text="Ready to start")
        else:
            self.timer_core.current_time_left = self.timer_core.break_time
            self.status_label.config(text="Break time")
        
        # Update the UI
        self.update_timer_display(self.timer_core.current_time_left, self.timer_core.current_mode)
        
        # Update the button colors
        button_color = COLORS["primary"] if new_mode == "pomodoro" else COLORS["secondary"]
        button_text = "Start"
        
        self.start_button.delete("all")
        self.start_button.create_polygon(round_rect_points(0, 0, 110, 40, 10), 
                                    fill=button_color, smooth=True)
        self.start_button.create_text(55, 20, text=button_text, fill="white", font=FONTS["small"])
        
        # Update switch button
        switch_color = COLORS["secondary"] if new_mode == "pomodoro" else COLORS["primary"]
        switch_text = "→ Break" if new_mode == "pomodoro" else "→ Pomodoro"
        
        self.switch_button.delete("all")
        self.switch_button.create_polygon(round_rect_points(0, 0, 110, 40, 10), 
                                    fill=switch_color, smooth=True)
        self.switch_button.create_text(55, 20, text=switch_text, fill="white", font=FONTS["small"])
        
        logger.info(f"Switched to {new_mode} mode")

    
    def create_history_section(self, parent):
        logger.debug("Creating history section")
        # History header
        tk.Label(parent, text="Task History", font=FONTS["medium"], 
               bg=COLORS["bg"], fg=COLORS["primary"]).pack(anchor=tk.W, pady=(0, 5))
        
        # History frame
        history_frame = tk.LabelFrame(parent, text="", bg=COLORS["white"], bd=2, relief=tk.GROOVE)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(1, weight=1)
        
        # Filter buttons
        filter_frame = tk.Frame(history_frame, bg=COLORS["white"])
        filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.status_filter = tk.StringVar(value="all")
        
        for status, label, color in [
            ("all", "All", COLORS["text"]),
            ("completed", "Completed", COLORS["success"]),
            ("ongoing", "Ongoing", COLORS["warning"]),
            ("interrupted", "Interrupted", COLORS["danger"])
        ]:
            rb = tk.Radiobutton(filter_frame, text=label, variable=self.status_filter, 
                             value=status, command=self.update_history_display,
                             bg=COLORS["white"], fg=color, selectcolor=COLORS["bg"], 
                             borderwidth=0, font=FONTS["list"], indicatoron=0)
            rb.pack(side=tk.LEFT, padx=5)
        
        # Listbox container
        list_container = tk.Frame(history_frame, bg=COLORS["white"], height=150)
        list_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        list_container.grid_propagate(False)
        
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Listbox
        self.history_listbox = tk.Listbox(
            list_container, font=FONTS["list"], bg=COLORS["white"], 
            fg=COLORS["text"], borderwidth=0, highlightthickness=1,
            selectbackground=COLORS["primary"], yscrollcommand=scrollbar.set
        )
        self.history_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.history_listbox.yview)
        
        # Style scrollbar
        style = ttk.Style()
        style.configure("TScrollbar", background=COLORS["primary"], troughcolor=COLORS["white"])
        
        self.root.after(100, self.update_history_display)
    
    def update_history_display(self):
        logger.debug("Updating history display")
        self.history_listbox.delete(0, tk.END)
        
        filter_status = self.status_filter.get()
        filtered_tasks = [task for task in self.task_manager.task_history 
                        if filter_status == "all" or task["status"] == filter_status]
        
        status_colors = {
            "completed": COLORS["success"],
            "interrupted": COLORS["danger"],
            "ongoing": COLORS["warning"]
        }
        
        if not filtered_tasks:
            self.history_listbox.insert(tk.END, "No tasks to display")
            return
        
        for task in filtered_tasks:
            text = f"{task['time']} - {task['task']} ({task['status']})"
            self.history_listbox.insert(tk.END, text)
            idx = self.history_listbox.size() - 1
            self.history_listbox.itemconfig(idx, fg=status_colors.get(task["status"], COLORS["text"]))
        
        self.history_listbox.see(0)
        self.root.update_idletasks()
    
    def show_timer_settings(self):
        logger.info("Opening timer settings dialog")
        def update_timer_settings(new_pomodoro, new_break):
            logger.info(f"Updating timer settings: pomodoro={new_pomodoro}, break={new_break}")
            self.timer_core.pomodoro_time = new_pomodoro
            self.timer_core.break_time = new_break
            
            if not self.timer_core.timer_running:
                if self.timer_core.current_mode == "pomodoro":
                    self.timer_core.current_time_left = self.timer_core.pomodoro_time
                else:
                    self.timer_core.current_time_left = self.timer_core.break_time
                self.update_timer_display(self.timer_core.current_time_left, self.timer_core.current_mode)
        
        show_timer_settings(
            self.root,
            self.timer_core.pomodoro_time,
            self.timer_core.break_time,
            update_timer_settings
        )
    
    def set_task(self):
        logger.info("Opening set task dialog")
        task = simpledialog.askstring("Set Task", "What are you working on?", parent=self.root)
        if task:
            self.task_manager.set_task(task)
            self.task_label.config(text=self.task_manager.current_task)
            self.update_history_display()
            logger.info(f"Task set: '{task}'")
    
    def start_timer(self):
        logger.debug("Start timer button clicked")
        if not self.timer_core.timer_running:
            # If no task is set, prompt user
            if self.task_manager.current_task == "No task set":
                logger.info("No task set, prompting user")
                self.set_task()
            
            success = self.timer_core.start()
            if success:
                button_text = "Pause"
                logger.info("Timer started successfully")
            else:
                return
        else:
            success = self.timer_core.pause()
            if success:
                button_text = "Resume"
                logger.info("Timer paused successfully")
                
                # Mark as interrupted if pomodoro
                if self.timer_core.current_mode == "pomodoro" and self.timer_core.current_time_left < self.timer_core.pomodoro_time:
                    self.task_manager.update_task_status("interrupted")
                    self.update_history_display()
            else:
                return
        
        # Update button appearance
        self.start_button.delete("all")
        self.start_button.create_polygon(round_rect_points(0, 0, 110, 40, 10), 
                                      fill=COLORS["primary"], smooth=True)
        self.start_button.create_text(55, 20, text=button_text, fill="white", font=FONTS["small"])
    
    def reset_timer(self):
        logger.info("Reset timer button clicked")
        was_running = self.timer_core.timer_running
        
        # Mark task as interrupted if active pomodoro
        if self.timer_core.current_mode == "pomodoro" and was_running:
            logger.debug("Marking current task as interrupted")
            self.task_manager.update_task_status("interrupted")
            self.update_history_display()
        
        # Reset the timer
        self.timer_core.reset()
        
        # Update UI button
        button_text = "Start"
        self.start_button.delete("all")
        button_color = COLORS["primary"] if self.timer_core.current_mode == "pomodoro" else COLORS["secondary"]
        self.start_button.create_polygon(round_rect_points(0, 0, 110, 40, 10), 
                                      fill=button_color, smooth=True)
        self.start_button.create_text(55, 20, text=button_text, fill="white", font=FONTS["small"])
        
        # Update status
        self.status_label.config(text="Ready to start")
    
    def update_timer_display(self, time_left, mode):
        mins, secs = divmod(time_left, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        logger.debug(f"Updating timer display: {time_str} ({mode})")
        
        self.time_display.config(text=time_str)
        
        # Update tray icon if it exists
        if self.tray_icon.running:
            self.tray_icon.update_icon(time_str, mode)
            
        # Update bubble if it exists
        if hasattr(self, 'bubble') and self.bubble.winfo_exists():
            # The bubble handles its own update through its update_time method
            pass

    def on_close(self):
        """Handle window close event"""
        logger.info("Application window closing")
        
        # First save application state
        self.save_state()
        
        # Then handle window closing behavior
        if self.tray_icon and self.tray_icon.running:
            self.minimize_to_tray()
        else:
            self.quit_app()

    def save_state(self):
        """Save application state before exit"""
        logger.info("Saving application state before exit")
        
        # Save timer state if it has a storage manager
        if hasattr(self.timer_core, 'storage_manager') and self.timer_core.storage_manager:
            # Timer will handle its own state saving
            logger.debug("Saving timer state")
            if hasattr(self.timer_core, '_save_state'):
                self.timer_core._save_state()
        
        # Save task state if it has a storage manager
        if hasattr(self.task_manager, 'storage_manager') and self.task_manager.storage_manager:
            # Task manager will handle its own state saving
            logger.debug("Saving task manager state")
            if hasattr(self.task_manager, '_save_state'):
                self.task_manager._save_state()
        
        logger.info("Application state saved successfully")
    
    def on_pomodoro_complete(self, pomodoro_count):
        logger.info(f"Pomodoro #{pomodoro_count} completed")
        self.counter_label.config(text=f"🍅 × {pomodoro_count}")
        self.task_manager.update_task_status("completed")
        self.update_history_display()
        
        # Update UI for break mode
        self.status_label.config(text="Take a break!")
        
        # Update button
        self.start_button.delete("all")
        self.start_button.create_polygon(round_rect_points(0, 0, 110, 40, 10), 
                                      fill=COLORS["secondary"], smooth=True)
        self.start_button.create_text(55, 20, text="Start Break", fill="white", font=FONTS["small"])
        
        # Show break message
        messagebox.showinfo("Break Time!", "Time for a break!")
    
    def on_break_complete(self):
        logger.info("Break completed")
        
        # Update UI for next pomodoro
        self.status_label.config(text="Ready to start")
        
        # Update button
        self.start_button.delete("all")
        self.start_button.create_polygon(round_rect_points(0, 0, 110, 40, 10), 
                                      fill=COLORS["primary"], smooth=True)
        self.start_button.create_text(55, 20, text="Start", fill="white", font=FONTS["small"])
        
        # Ask for next task
        if messagebox.askyesno("Continue?", "Would you like to start another Pomodoro?"):
            logger.info("User chose to start another pomodoro")
            self.set_task()
            self.start_timer()
    
    def minimize_to_tray(self):
        logger.info("Minimizing to system tray")
        if not self.tray_icon.running:
            success = self.tray_icon.setup()
            if not success:
                logger.error("Failed to create system tray icon")
                messagebox.showwarning("System Tray Error", 
                                     "Could not create system tray icon. The application will be minimized instead.")
                self.root.iconify()
                return
        
        mins, secs = divmod(self.timer_core.current_time_left, 60)
        self.tray_icon.update_icon(f"{mins:02d}:{secs:02d}", self.timer_core.current_mode)
        
        # Create floating bubble
        self.bubble = FloatingBubble(self.root, self.timer_core)
        
        # Hide main window
        self.root.withdraw()
    
    def open_main_window(self):
        logger.info("Opening main window from tray")
        
        # Destroy floating bubble if it exists
        if hasattr(self, 'bubble') and self.bubble.winfo_exists():
            logger.debug("Destroying floating bubble")
            self.bubble.destroy()
        
        self.root.deiconify()
        self.root.lift()
    
    def quit_app(self):
        logger.info("Quitting application")
        
        # Destroy floating bubble if it exists
        if hasattr(self, 'bubble') and self.bubble.winfo_exists():
            logger.debug("Destroying floating bubble")
            self.bubble.destroy()
            
        self.tray_icon.stop()
        self.root.destroy()
