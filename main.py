import tkinter as tk
from tkinter import ttk, messagebox
import database
from ui.login_frame import LoginFrame
from ui.main_app_frame import MainApplicationFrame

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PolicyTrack v0.1")
        self.geometry("1000x800")
        
        # Khởi tạo DB nếu chưa có
        database.init_db()

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