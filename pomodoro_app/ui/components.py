# components.py

import tkinter as tk
from ..constants.styling import COLORS, FONTS
from ..core import logger

def round_rect_points(x1, y1, x2, y2, r):
    logger.debug(f"Creating rounded rectangle points: ({x1}, {y1}), ({x2}, {y2}), r={r}")
    return [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]

class RoundedFrame(tk.Canvas):
    def __init__(self, parent, w, h, r, bg=None, **kwargs):
        logger.debug(f"Creating RoundedFrame: w={w}, h={h}, r={r}, bg={bg}")
        super().__init__(parent, width=w, height=h, bg=bg, highlightthickness=0, **kwargs)
        self.create_polygon(round_rect_points(0, 0, w, h, r), fill=bg, smooth=True)

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, cmd, bg, fg="white", width=100, height=40, radius=10, **kwargs):
        logger.debug(f"Creating RoundedButton: text='{text}', bg={bg}, fg={fg}")
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.cmd = cmd
        self.create_polygon(round_rect_points(0, 0, width, height, radius), fill=bg, smooth=True)
        self.create_text(width//2, height//2, text=text, fill=fg, font=FONTS["small"])
        self.bind("<Button-1>", lambda e: self.cmd())
        self.bind("<Enter>", lambda e: self.config(cursor="hand2"))
