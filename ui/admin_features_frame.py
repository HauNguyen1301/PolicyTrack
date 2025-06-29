import tkinter as tk
from tkinter import ttk, messagebox
import database

class AdminFeaturesFrame:
    """Lớp này không phải là một widget, mà là một nơi tập trung logic cho các tính năng của admin."""
    def __init__(self, controller):
        self.controller = controller

    def show_manage_users_popup(self):
        """Mở cửa sổ popup để quản lý tất cả người dùng."""
        popup = tk.Toplevel(self.controller)
        popup.title("Quản lý User")
        popup.geometry("700x500")
        popup.transient(self.controller)
        popup.grab_set()

        frame = ttk.Frame(popup, padding="10")
        frame.pack(expand=True, fill="both")

        # --- Khung tìm kiếm ---
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(search_frame, text="Tìm kiếm:").pack(side='left', padx=(0, 5))
        search_entry = ttk.Entry(search_frame)
        search_entry.pack(side='left', expand=True, fill='x', padx=5)

        # --- Cây hiển thị danh sách user ---
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(expand=True, fill='both')
        columns = ('username', 'full_name', 'role')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        tree.heading('username', text='Tên đăng nhập')
        tree.heading('full_name', text='Họ và tên')
        tree.heading('role', text='Vai trò')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side='left', expand=True, fill='both')
        scrollbar.pack(side='right', fill='y')

        def populate_tree(users):
            for i in tree.get_children():
                tree.delete(i)
            for user in users:
                tree.insert('', 'end', values=(user['username'], user['full_name'], user['role']))

        def refresh_user_list():
            search_entry.delete(0, 'end')
            users = database.get_all_users()
            populate_tree(users)

        def perform_search(event=None):
            search_term = search_entry.get()
            if not search_term:
                users = database.get_all_users()
            else:
                users = database.search_users(search_term)
            populate_tree(users)
        
        search_entry.bind('<Return>', perform_search)
        ttk.Button(search_frame, text="Tìm kiếm", command=perform_search).pack(side='left', padx=5)
        ttk.Button(search_frame, text="Làm mới", command=refresh_user_list).pack(side='left')

        refresh_user_list() # Tải danh sách ban đầu

        # --- Các nút chức năng ---
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=10)

        def get_selected_username():
            selected_item = tree.focus()
            if not selected_item:
                messagebox.showwarning("Chưa chọn User", "Vui lòng chọn một user để thực hiện thao tác.", parent=popup)
                return None
            return tree.item(selected_item)['values'][0]

        def open_reset_password_popup():
            username = get_selected_username()
            if username:
                self._show_reset_password_popup(popup, username, refresh_user_list)

        def open_change_role_popup():
            username = get_selected_username()
            if username:
                self._show_change_role_popup(popup, username, refresh_user_list)

        ttk.Button(button_frame, text="Đặt lại mật khẩu", command=open_reset_password_popup).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Đổi vai trò", command=open_change_role_popup).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Đóng", command=popup.destroy).pack(side='right', padx=5)

    def show_create_user_popup(self):
        """Mở cửa sổ popup để tạo người dùng mới."""
        popup = tk.Toplevel(self.controller)
        popup.title("Tạo User Mới")
        popup.geometry("400x300")
        popup.transient(self.controller)
        popup.grab_set()

        frame = ttk.Frame(popup, padding="15")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="Tên đăng nhập:").grid(row=0, column=0, sticky="w", pady=5)
        username_entry = ttk.Entry(frame)
        username_entry.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Họ và tên:").grid(row=1, column=0, sticky="w", pady=5)
        fullname_entry = ttk.Entry(frame)
        fullname_entry.grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Mật khẩu:").grid(row=2, column=0, sticky="w", pady=5)
        password_entry = ttk.Entry(frame, show="*")
        password_entry.grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Vai trò:").grid(row=3, column=0, sticky="w", pady=5)
        role_combobox = ttk.Combobox(frame, values=['Admin', 'Creator', 'Viewer'], state="readonly")
        role_combobox.grid(row=3, column=1, sticky="ew", pady=5)
        role_combobox.set('Viewer')

        def submit():
            username = username_entry.get()
            fullname = fullname_entry.get()
            password = password_entry.get()
            role = role_combobox.get()

            if not all([username, fullname, password, role]):
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin.", parent=popup)
                return

            success, message = database.create_user(username, password, fullname, role)
            if success:
                messagebox.showinfo("Thành công", message, parent=popup)
                popup.destroy()
            else:
                messagebox.showerror("Lỗi", message, parent=popup)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Tạo User", command=submit).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Hủy", command=popup.destroy).pack(side="left")

        frame.columnconfigure(1, weight=1)

    def _show_reset_password_popup(self, parent, username, callback):
        """Popup riêng cho việc reset mật khẩu."""
        popup = tk.Toplevel(parent)
        popup.title(f"Đặt lại mật khẩu cho {username}")
        popup.geometry("350x150")
        popup.transient(parent)
        popup.grab_set()

        frame = ttk.Frame(popup, padding="15")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="Mật khẩu mới:").grid(row=0, column=0, sticky="w", pady=5)
        new_password_entry = ttk.Entry(frame, show="*")
        new_password_entry.grid(row=0, column=1, sticky="ew", pady=5)

        def submit():
            new_password = new_password_entry.get()
            if not new_password:
                messagebox.showerror("Lỗi", "Mật khẩu không được để trống.", parent=popup)
                return
            database.update_password(username, new_password)
            messagebox.showinfo("Thành công", f"Đã đặt lại mật khẩu cho {username}.", parent=popup)
            callback()
            popup.destroy()

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Xác nhận", command=submit).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Hủy", command=popup.destroy).pack(side="left")

        frame.columnconfigure(1, weight=1)

    def _show_change_role_popup(self, parent, username, callback):
        """Popup riêng cho việc thay đổi vai trò."""
        popup = tk.Toplevel(parent)
        popup.title(f"Đổi vai trò cho {username}")
        popup.geometry("350x150")
        popup.transient(parent)
        popup.grab_set()

        frame = ttk.Frame(popup, padding="15")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="Vai trò mới:").grid(row=0, column=0, sticky="w", pady=5)
        role_combobox = ttk.Combobox(frame, values=['Admin', 'Creator', 'Viewer'], state="readonly")
        role_combobox.grid(row=0, column=1, sticky="ew", pady=5)

        def submit():
            new_role = role_combobox.get()
            if not new_role:
                messagebox.showerror("Lỗi", "Vui lòng chọn một vai trò.", parent=popup)
                return
            database.update_user_role(username, new_role)
            messagebox.showinfo("Thành công", f"Đã cập nhật vai trò cho {username} thành {new_role}.", parent=popup)
            callback()
            popup.destroy()

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Xác nhận", command=submit).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Hủy", command=popup.destroy).pack(side="left")

        frame.columnconfigure(1, weight=1)
