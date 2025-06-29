import tkinter as tk
from tkinter import ttk

class AddBenefitFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        label = ttk.Label(self, text="Chức năng Thêm Quyền Lợi - Đang phát triển", style="Title.TLabel")
        label.pack(pady=50, padx=50)
