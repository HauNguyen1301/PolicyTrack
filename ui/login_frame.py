import tkinter as tk
from tkinter import ttk, messagebox
import database

class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Cấu hình grid của LoginFrame để đẩy form con ra giữa
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        frame = ttk.Frame(self, padding="20")
        frame.grid(row=0, column=0) # Đặt form con vào giữa grid

        # Sử dụng grid layout để căn chỉnh tốt hơn
        ttk.Label(frame, text="Đăng Nhập", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(frame, text="Tên đăng nhập:").grid(row=1, column=0, pady=5, padx=5, sticky='w')
        self.username_entry = ttk.Entry(frame, width=30)
        self.username_entry.grid(row=1, column=1, pady=5, padx=5)
        self.username_entry.focus()

        ttk.Label(frame, text="Mật khẩu:").grid(row=2, column=0, pady=5, padx=5, sticky='w')
        self.password_entry = ttk.Entry(frame, show="*", width=30)
        self.password_entry.grid(row=2, column=1, pady=5, padx=5)

        # Cho phép nhấn Enter để đăng nhập từ một trong hai ô
        self.username_entry.bind('<Return>', self.login)
        self.password_entry.bind('<Return>', self.login)

        ttk.Button(frame, text="Đăng nhập", command=self.login).grid(row=3, column=0, columnspan=2, pady=20)

    def clear_entries(self):
        """Xóa nội dung trong các ô nhập liệu."""
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.username_entry.focus()

    def login(self, event=None):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user = database.verify_user(username, password)
        if user:
            self.controller.login_success(user)
        else:
            messagebox.showerror("Lỗi", "Tên đăng nhập hoặc mật khẩu không đúng.")
