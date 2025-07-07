import sys
import os
import certifi
# Ensure bundled certs are used before any network library imports
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
import asyncio

# Import embedded environment variables (generated at build time)
try:
    import internal_env  # noqa: F401  # sets os.environ via side-effects
except ModuleNotFoundError:
    # Running from source without generated module – fall back to .env if exists
    from pathlib import Path
    env_path = Path(__file__).with_suffix('.env')
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

# Ensure compatible event loop on Windows when running frozen without start.py
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# link check version : https://raw.githubusercontent.com/HauNguyen1301/PolicyTrack/refs/heads/main/updates/latest.json


import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ui.login_frame import LoginFrame
from ui.main_app_frame import MainApplicationFrame
import database

# ====== Update checking imports ======
import threading
import requests
from packaging.version import parse as _vparse
import webbrowser
from policytrack_version import __version__

# URL tới file JSON chứa thông tin phiên bản mới nhất
UPDATE_URL = os.environ.get('POLICYTRACK_UPDATE_URL', (
    "https://raw.githubusercontent.com/"
    "HauNguyen1301/PolicyTrack/main/updates/latest.json"
))

def _check_for_update(parent):
    """Chạy ở luồng nền; nếu có version mới thì thông báo."""
    try:
        resp = requests.get(UPDATE_URL, 
                          timeout=3,
                          verify=True,  # Enable SSL verification
                          headers={'User-Agent': 'PolicyTrack/1.0'})
        
        if resp.status_code != 200:
            raise Exception(f"HTTP Error {resp.status_code}")
            
        if __debug__:
            print("[UpdateCheck] HTTP status:", resp.status_code)
        
        data = resp.json()
        remote_ver = data.get("version", "")
        
        if __debug__:
            print(f"[UpdateCheck] Local {__version__} / Remote {remote_ver}")
        
        if remote_ver and _vparse(remote_ver) > _vparse(__version__):
            # Sanitize notes to prevent XSS
            raw_notes = data.get("notes", "")
            if isinstance(raw_notes, list):
                notes = "\n".join(f"- {line}" for line in raw_notes)
            else:
                notes = str(raw_notes)
                
            # Escape HTML entities
            notes = notes.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
            parent.after(0, lambda: _show_update_dialog(parent, remote_ver, notes))
    except requests.exceptions.RequestException as e:
        if __debug__:
            print('[UpdateCheck] Network Error:', e)
        pass
    except ValueError as e:
        if __debug__:
            print('[UpdateCheck] JSON Error:', e)
        pass
    except Exception as e:
        if __debug__:
            print('[UpdateCheck] Error:', e)
        pass

# ---- Custom update dialog ----
DOWNLOAD_URL = "https://1drv.ms/f/c/5f21643f394cb276/EmPmLLE1dYtNrzdyMwIzwQgB-662e46VFM1G0CWAz74x5w"

def _show_update_dialog(parent: tk.Tk, remote_ver: str, notes: str):
    """Hiển thị hộp thoại cập nhật với nút Download."""
    dlg = ttk.Toplevel(parent)
    dlg.title("Có phiên bản mới")
    dlg.transient(parent)
    dlg.grab_set()
    dlg.resizable(False, False)

    ttk.Label(dlg, text=f"Version {remote_ver} đã sẵn sàng!", font=("Segoe UI", 10, "bold"), justify="left").pack(padx=20, pady=(15, 5))
    ttk.Label(dlg, text=notes, justify="left").pack(padx=20, pady=(0, 10))

    btn_frame = ttk.Frame(dlg)
    btn_frame.pack(pady=(0, 15))

    def _open_download():
        webbrowser.open_new(DOWNLOAD_URL)
        dlg.destroy()

    ttk.Button(btn_frame, text="Download", command=_open_download).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Đóng", command=dlg.destroy).pack(side="left", padx=5)

    # Canh giữa dialog so với parent
    parent.update_idletasks()
    w, h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
    x = parent.winfo_x() + (parent.winfo_width() - w) // 2
    y = parent.winfo_y() + (parent.winfo_height() - h) // 2
    dlg.geometry(f"{w}x{h}+{x}+{y}")


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        self.title(f"PolicyTrack {__version__}")
        self.geometry("1000x800")

        # Xử lý sự kiện đóng cửa sổ để thoát ứng dụng một cách an toàn
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

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

    def on_closing(self):
        """Xử lý khi người dùng đóng cửa sổ chính."""
        self.destroy()

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
        if Messagebox.yesno("Xác nhận Đăng xuất", "Bạn có chắc chắn muốn đăng xuất không?") == "Yes":
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
