import sys
import asyncio

# Ensure compatible event loop on Windows when running frozen without start.py
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



import tkinter as tk
from tkinter import ttk, messagebox
from ui.login_frame import LoginFrame
from ui.main_app_frame import MainApplicationFrame
import database

# ====== Update checking imports ======
import threading
import requests
from packaging.version import parse as _vparse
from policytrack_version import __version__

# URL tới file JSON chứa thông tin phiên bản mới nhất
UPDATE_URL = (
    "https://raw.githubusercontent.com/"
    "HauNguyen1301/PolicyTrack/main/updates/latest.json"
)

def _check_for_update(parent):
    """Chạy ở luồng nền; nếu có version mới thì thông báo."""
    try:
        resp = requests.get(UPDATE_URL, timeout=3)
        if __debug__:
            print("[UpdateCheck] HTTP status:", resp.status_code)
        data = resp.json()
        remote_ver = data.get("version", "")
        if __debug__:
            print(f"[UpdateCheck] Local {__version__} / Remote {remote_ver}")
        if remote_ver and _vparse(remote_ver) > _vparse(__version__):
            raw_notes = data.get("notes", "")
            if isinstance(raw_notes, list):
                notes = "\n".join(f"- {line}" for line in raw_notes)
            else:
                notes = str(raw_notes)
            parent.after(0, lambda: messagebox.showinfo(
                "Có phiên bản mới",
                f"Version {remote_ver} đã sẵn sàng!\n\n{notes}",
                parent=parent
            ))
    except Exception as e:
        if __debug__:
            print('[UpdateCheck] Error:', e)

        # Im lặng nếu không thể kiểm tra (offline, lỗi JSON, v.v.)
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"PolicyTrack {__version__}")
        self.geometry("1000x800")

        # Để sau khi đăng nhập mới kiểm tra phiên bản → tránh hộp thoại che màn hình login
        self._update_thread_started = False
        
        # DB schema được quản lý sẵn trên Turso, không cần khởi tạo tại client
        # database.init_db()


        self.current_user = None
        
        # Cấu hình grid của cửa sổ chính
        self.grid_rowconfigure(0, weight=1) # Hàng cho container chính
        self.grid_rowconfigure(1, weight=0) # Hàng cho status bar
        self.grid_columnconfigure(0, weight=1)

        # Container chính, sẽ chứa các frame khác nhau (login, main_app)
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")

        # Cấu hình grid của container để các frame con có thể co giãn
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # --- Status Bar ---
        status_bar = ttk.Frame(self) # Bỏ viền
        status_bar.grid(row=1, column=0, sticky='ew')
        
        copyright_label = ttk.Label(
            status_bar, 
            text="\u00a9 Copyright by HauNguyen", # Thêm biểu tượng ©
            font=("Segoe UI", 8), 
            foreground="gray"
        )
        copyright_label.pack(side='right', padx=10)

        self.frames = {}
        for F in (LoginFrame, MainApplicationFrame):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginFrame")

    def show_frame(self, page_name):
        """Hiển thị một frame dựa trên tên của nó."""
        frame = self.frames[page_name]
        frame.tkraise()

    def login_success(self, user):
        """Xử lý sau khi đăng nhập thành công."""
        self.current_user = user
        main_frame = self.frames["MainApplicationFrame"]
        
        # Cập nhật lời chào và trạng thái các nút dựa trên vai trò
        main_frame.update_welcome_message(user['full_name'])
        main_frame.update_button_states_by_role(user['role'])
        
        self.show_frame("MainApplicationFrame")

        # Chỉ khởi chạy kiểm tra phiên bản một lần sau khi đăng nhập đầu tiên
        if not getattr(self, "_update_thread_started", False):
            threading.Thread(target=_check_for_update, args=(self,), daemon=True).start()
            self._update_thread_started = True
        

    def logout(self):
        """Xử lý đăng xuất, quay về màn hình Login."""
        if messagebox.askyesno("Xác nhận Đăng xuất", "Bạn có chắc chắn muốn đăng xuất không?", parent=self):
            # Reset lại trạng thái của MainApplicationFrame
            main_frame = self.frames["MainApplicationFrame"]
            main_frame.reset_to_default_state()

            # Xóa thông tin người dùng hiện tại
            self.current_user = None

            # Hiển thị lại màn hình đăng nhập và xóa các ô nhập liệu
            login_frame = self.frames["LoginFrame"]
            login_frame.clear_entries()
            self.show_frame("LoginFrame")

if __name__ == "__main__":
    app = App()
    app.mainloop()