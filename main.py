import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import time, threading
from datetime import datetime
from plyer import notification
import pystray
from PIL import Image, ImageDraw, ImageFont

# Color and font definitions
COLORS = {
    "bg": "#FFF5F5", "primary": "#FF6B6B", "secondary": "#4ECDC4", 
    "text": "#1C1C1E", "accent": "#FFD166", "white": "white", "gray": "#6C757D",
    "success": "#28a745", "warning": "#ffc107", "danger": "#dc3545"
}

FONTS = {
    "title": ("Segoe UI", 24, "bold"), "large": ("Segoe UI", 56, "bold"),
    "medium": ("Segoe UI", 16), "small": ("Segoe UI", 14, "bold"),
    "tiny": ("Segoe UI", 12), "list": ("Segoe UI", 10)
}

def round_rect_points(x1, y1, x2, y2, r):
    return [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]

class RoundedFrame(tk.Canvas):
    def __init__(self, parent, w, h, r, bg=None, **kwargs):
        super().__init__(parent, width=w, height=h, bg=bg, highlightthickness=0, **kwargs)
        self.create_polygon(round_rect_points(0, 0, w, h, r), fill=bg, smooth=True)

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, cmd, bg, fg="white", width=100, height=40, radius=10, **kwargs):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.cmd = cmd
        self.create_polygon(round_rect_points(0, 0, width, height, radius), fill=bg, smooth=True)
        self.create_text(width//2, height//2, text=text, fill=fg, font=FONTS["small"])
        self.bind("<Button-1>", lambda e: self.cmd())
        self.bind("<Enter>", lambda e: self.config(cursor="hand2"))

class SystemTrayIcon:
    def __init__(self, app):
        self.app, self.icon, self.running = app, None, False
        self.current_time, self.current_mode = "25:00", "pomodoro"
        
    def create_image(self):
        w, h = 64, 64
        color = COLORS["primary"] if self.current_mode == "pomodoro" else COLORS["secondary"]
        img = Image.new('RGBA', (w, h), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([(0, 0), (w, h)], fill=color)
        
        try: font = ImageFont.truetype("arial.ttf", 20)
        except: font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), self.current_time, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pos = ((w - text_w) / 2, (h - text_h) / 2)
        draw.text(pos, self.current_time, font=font, fill="white")
        return img
    
    def update_icon(self, time_str, mode):
        self.current_time, self.current_mode = time_str, mode
        if self.icon and self.running:
            try: self.icon.icon = self.create_image()
            except: pass
    
    def setup(self):
        try:
            menu = pystray.Menu(
                pystray.MenuItem("Open Timer", self.app.open_main_window),
                pystray.MenuItem("Exit", self.app.quit_app)
            )
            self.icon = pystray.Icon("pomodoro", self.create_image(), "Pomodoro Timer", menu)
            self.running = True
            threading.Thread(target=lambda: self.icon.run(), daemon=True).start()
            return True
        except: return False
    
    def stop(self):
        if self.icon and self.running:
            try: self.running = False; self.icon.stop()
            except: pass

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro Timer")
        self.root.geometry("400x900")
        self.root.resizable(False, True)
        self.root.config(bg=COLORS["bg"])
        
        # Timer variables
        self.default_pomodoro, self.default_break = 25 * 60, 5 * 60
        self.pomodoro_time, self.break_time = self.default_pomodoro, self.default_break
        self.timer_running = False
        self.current_time_left = self.pomodoro_time
        self.pomodoro_count = 0
        self.current_task = "No task set"
        self.current_mode = "pomodoro"
        self.task_history = []
        
        # System tray
        self.tray_icon = SystemTrayIcon(self)
        
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
    
    def setup_ui(self):
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
        self.counter_label = tk.Label(main, text="🍅 × 0", font=FONTS["medium"], 
                                    bg=COLORS["bg"], fg=COLORS["primary"])
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
    
    def create_timer_display(self, parent):
        timer_frame = RoundedFrame(parent, 360, 180, 15, bg=COLORS["primary"])
        timer_frame.pack(pady=(0, 20))
        
        mins, secs = divmod(self.pomodoro_time, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        self.time_display = tk.Label(timer_frame, text=time_str, font=FONTS["large"], 
                                   bg=COLORS["primary"], fg=COLORS["white"])
        timer_frame.create_window(180, 70, window=self.time_display)
        
        self.status_label = tk.Label(timer_frame, text="Ready to start", font=FONTS["medium"], 
                                   bg=COLORS["primary"], fg=COLORS["white"])
        timer_frame.create_window(180, 130, window=self.status_label)
    
    def create_task_section(self, parent):
        task_frame = RoundedFrame(parent, 360, 90, 15, bg=COLORS["white"])
        task_frame.pack(pady=(0, 20))
        
        task_frame.create_window(180, 25, window=tk.Label(task_frame, text="Current Task", 
                                                      font=FONTS["small"], bg=COLORS["white"], 
                                                      fg=COLORS["text"]))
        self.task_label = tk.Label(task_frame, text=self.current_task, font=FONTS["tiny"], 
                                 bg=COLORS["white"], fg=COLORS["primary"], wraplength=320)
        task_frame.create_window(180, 55, window=self.task_label)
    
    def create_buttons(self, parent):
        btn_frame = tk.Frame(parent, bg=COLORS["bg"])
        btn_frame.pack(pady=(0, 20))
        
        self.start_button = RoundedButton(btn_frame, "Start", self.start_timer, COLORS["primary"], width=110)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        RoundedButton(btn_frame, "Reset", self.reset_timer, COLORS["gray"], width=110).pack(side=tk.LEFT, padx=(0, 10))
        RoundedButton(btn_frame, "Set Task", self.set_task, COLORS["accent"], width=110).pack(side=tk.LEFT)
    
    def create_history_section(self, parent):
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
        self.history_listbox.delete(0, tk.END)
        
        filter_status = self.status_filter.get()
        filtered_tasks = [task for task in self.task_history 
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
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Timer Settings")
        settings_window.geometry("300x250")
        settings_window.resizable(False, False)
        settings_window.config(bg=COLORS["bg"])
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Center window
        settings_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + self.root.winfo_width()//2 - 150,
            self.root.winfo_rooty() + self.root.winfo_height()//2 - 125
        ))
        
        # Settings content
        tk.Label(settings_window, text="Timer Settings", font=FONTS["medium"], 
               bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=(20, 30))
        
        # Pomodoro duration
        pomodoro_frame = tk.Frame(settings_window, bg=COLORS["bg"])
        pomodoro_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        tk.Label(pomodoro_frame, text="Pomodoro length (minutes):", 
               bg=COLORS["bg"], fg=COLORS["text"]).pack(side=tk.LEFT)
        
        pomodoro_minutes = tk.StringVar(value=str(self.pomodoro_time // 60))
        pomodoro_spinbox = ttk.Spinbox(pomodoro_frame, from_=1, to=60, 
                                     textvariable=pomodoro_minutes, width=5)
        pomodoro_spinbox.pack(side=tk.RIGHT)
        
        # Break duration
        break_frame = tk.Frame(settings_window, bg=COLORS["bg"])
        break_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        tk.Label(break_frame, text="Break length (minutes):", 
               bg=COLORS["bg"], fg=COLORS["text"]).pack(side=tk.LEFT)
        
        break_minutes = tk.StringVar(value=str(self.break_time // 60))
        break_spinbox = ttk.Spinbox(break_frame, from_=1, to=30, 
                                  textvariable=break_minutes, width=5)
        break_spinbox.pack(side=tk.RIGHT)
        
        # Action buttons
        button_frame = tk.Frame(settings_window, bg=COLORS["bg"])
        button_frame.pack(fill=tk.X, padx=20, pady=(20, 0))
        
        def save_settings():
            try:
                new_pomodoro = int(pomodoro_minutes.get()) * 60
                new_break = int(break_minutes.get()) * 60
                
                if new_pomodoro < 60 or new_pomodoro > 3600:
                    raise ValueError("Pomodoro time must be between 1-60 minutes")
                if new_break < 60 or new_break > 1800:
                    raise ValueError("Break time must be between 1-30 minutes")
                
                self.pomodoro_time = new_pomodoro
                self.break_time = new_break
                
                if not self.timer_running and self.current_mode == "pomodoro":
                    self.current_time_left = self.pomodoro_time
                    mins, secs = divmod(self.pomodoro_time, 60)
                    self.time_display.config(text=f"{mins:02d}:{secs:02d}")
                elif not self.timer_running and self.current_mode == "break":
                    self.current_time_left = self.break_time
                    mins, secs = divmod(self.break_time, 60)
                    self.time_display.config(text=f"{mins:02d}:{secs:02d}")
                
                settings_window.destroy()
                messagebox.showinfo("Settings Saved", "Timer settings have been updated!")
            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e))
        
        RoundedButton(button_frame, "Save", save_settings, COLORS["primary"], width=120, height=35).pack(side=tk.LEFT, padx=(0, 10))
        RoundedButton(button_frame, "Cancel", settings_window.destroy, COLORS["gray"], width=120, height=35).pack(side=tk.RIGHT)
    
    def set_task(self):
        task = simpledialog.askstring("Set Task", "What are you working on?", parent=self.root)
        if task:
            self.current_task = task
            self.task_label.config(text=self.current_task)
            
            # Add to history immediately
            timestamp = datetime.now().strftime("%H:%M")
            self.task_history.insert(0, {"time": timestamp, "task": self.current_task, "status": "ongoing"})
            self.update_history_display()
    
    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            is_pomodoro = self.current_mode == "pomodoro"
            
            # Update button
            self.start_button.delete("all")
            self.start_button.create_polygon(round_rect_points(0, 0, 110, 40, 10), 
                                          fill=COLORS["primary"], smooth=True)
            self.start_button.create_text(55, 20, text="Pause", fill="white", font=FONTS["small"])
            
            # Ask for task if not set
            if self.current_task == "No task set":
                self.set_task()
            
            # Start timer thread
            threading.Thread(target=self.run_timer, daemon=True).start()
        else:
            self.timer_running = False
            
            # Update button
            self.start_button.delete("all")
            self.start_button.create_polygon(round_rect_points(0, 0, 110, 40, 10), 
                                          fill=COLORS["primary"], smooth=True)
            self.start_button.create_text(55, 20, text="Resume", fill="white", font=FONTS["small"])
            
            # Mark as interrupted if pomodoro
            if self.current_mode == "pomodoro" and self.current_time_left < self.pomodoro_time:
                self.update_last_task_status("interrupted")
    
    def run_timer(self):
        is_pomodoro = self.current_mode == "pomodoro"
        self.status_label.config(text="Focus Time!" if is_pomodoro else "Break Time!")
        
        while self.current_time_left > 0 and self.timer_running:
            mins, secs = divmod(self.current_time_left, 60)
            time_str = f"{mins:02d}:{secs:02d}"
            self.time_display.config(text=time_str)
            self.tray_icon.update_icon(time_str, self.current_mode)
            self.root.update_idletasks()
            
            self.current_time_left -= 1
            
            if self.timer_running and self.current_time_left > 0:
                time.sleep(1)
        
        if self.timer_running:
            self.complete_pomodoro() if is_pomodoro else self.complete_break()
    
    def update_last_task_status(self, status):
        if self.task_history and self.task_history[0]["task"] == self.current_task:
            self.task_history[0]["status"] = status
            self.update_history_display()
    
    def complete_pomodoro(self):
        # Update counter and status
        self.pomodoro_count += 1
        self.counter_label.config(text=f"🍅 × {self.pomodoro_count}")
        self.update_last_task_status("completed")
        
        # Notify user
        notification.notify(
            title="Pomodoro Completed! 🎉",
            message=f"Great job focusing on: {self.current_task}",
            timeout=10
        )
        
        # Switch to break mode
        self.current_mode = "break"
        self.current_time_left = self.break_time
        self.timer_running = False
        
        # Update UI
        mins, secs = divmod(self.break_time, 60)
        self.time_display.config(text=f"{mins:02d}:{secs:02d}")
        self.status_label.config(text="Take a break!")
        
        # Update button
        self.start_button.delete("all")
        self.start_button.create_polygon(round_rect_points(0, 0, 110, 40, 10), 
                                      fill=COLORS["secondary"], smooth=True)
        self.start_button.create_text(55, 20, text="Start Break", fill="white", font=FONTS["small"])
        
        # Show break message
        messagebox.showinfo("Break Time!", "Time for a break!")
    
    def complete_break(self):
        notification.notify(
            title="Break Finished!",
            message="Ready to focus again?",
            timeout=10
        )
        
        # Reset for next pomodoro
        self.current_mode = "pomodoro"
        self.current_time_left = self.pomodoro_time
        self.timer_running = False
        
        # Update UI
        mins, secs = divmod(self.pomodoro_time, 60)
        self.time_display.config(text=f"{mins:02d}:{secs:02d}")
        self.status_label.config(text="Ready to start")
        
        # Update button
        self.start_button.delete("all")
        self.start_button.create_polygon(round_rect_points(0, 0, 110, 40, 10), 
                                      fill=COLORS["primary"], smooth=True)
        self.start_button.create_text(55, 20, text="Start", fill="white", font=FONTS["small"])
        
        # Ask for next task
        if messagebox.askyesno("Continue?", "Would you like to start another Pomodoro?"):
            self.set_task()
            self.start_timer()
    
    def reset_timer(self):
        self.timer_running = False
        is_pomodoro = self.current_mode == "pomodoro"
        
        # Mark as interrupted if active pomodoro
        if is_pomodoro and self.current_time_left < self.pomodoro_time and self.current_time_left > 0:
            self.update_last_task_status("interrupted")
        
        # Reset timer state
        if is_pomodoro:
            self.current_time_left = self.pomodoro_time
            mins, secs = divmod(self.pomodoro_time, 60)
            self.time_display.config(text=f"{mins:02d}:{secs:02d}")
        else:
            self.current_time_left = self.break_time
            mins, secs = divmod(self.break_time, 60)
            self.time_display.config(text=f"{mins:02d}:{secs:02d}")
        
        # Update UI
        self.status_label.config(text="Ready to start")
        
        # Update button
        self.start_button.delete("all")
        button_color = COLORS["primary"] if is_pomodoro else COLORS["secondary"]
        self.start_button.create_polygon(round_rect_points(0, 0, 110, 40, 10), 
                                      fill=button_color, smooth=True)
        self.start_button.create_text(55, 20, text="Start", fill="white", font=FONTS["small"])
    
    def minimize_to_tray(self):
        if not self.tray_icon.running:
            success = self.tray_icon.setup()
            if not success:
                messagebox.showwarning("System Tray Error", 
                                     "Could not create system tray icon. The application will be minimized instead.")
                self.root.iconify()
                return
        
        mins, secs = divmod(self.current_time_left, 60)
        self.tray_icon.update_icon(f"{mins:02d}:{secs:02d}", self.current_mode)
        self.root.withdraw()
    
    def open_main_window(self):
        self.root.deiconify()
        self.root.lift()
    
    def quit_app(self):
        self.tray_icon.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()
