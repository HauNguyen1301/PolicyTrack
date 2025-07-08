import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import database
from .admin_features_frame import AdminFeaturesFrame
from .add_contract_frame import AddContractFrame
from .contract_view_panel import CheckContractPanel
from .add_benefit_frame import AddBenefitFrame
from .edit_contract_panel import EditContractPanel
from .edit_benefit_panel import EditBenefitPanel

class EditPanelSelector(ttk.Frame):
    def __init__(self, master, show_edit_contract, show_edit_benefit):
        super().__init__(master)
        label = ttk.Label(
            self,
            text="Chọn hành động chỉnh sửa:",
            style="Title.TLabel",
            font=("Arial", 14, "bold")
        )
        label.pack(pady=(20, 15))
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        btn_edit_contract = ttk.Button(btn_frame, text="Chỉnh sửa hợp đồng chính", bootstyle="warning-outline", command=show_edit_contract, width=25)
        btn_edit_contract.pack(side='left', padx=10)
        btn_edit_benefit = ttk.Button(btn_frame, text="Chỉnh sửa quyền lợi", bootstyle="warning-outline", command=show_edit_benefit, width=25)
        btn_edit_benefit.pack(side='left', padx=10)


class MainApplicationFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.admin_features = AdminFeaturesFrame(self.controller)
        self.frames = {}

        self._create_widgets()
        self._initialize_content_frames()
        self.update_button_states_by_role(None) # Đặt trạng thái ban đầu

    def _create_widgets(self):
        # --- Thanh công cụ trên cùng ---
        top_bar = ttk.Frame(self, padding=(10, 5))
        top_bar.pack(side='top', fill='x')

        self.welcome_label = ttk.Label(top_bar, text="Chào mừng!", font=("Segoe UI", 12, "bold"))
        self.welcome_label.pack(side='left', padx=10)

        buttons_right_frame = ttk.Frame(top_bar)
        buttons_right_frame.pack(side='right', padx=5)

        self.manage_users_button = ttk.Button(buttons_right_frame, text="Quản lý User", command=self.admin_features.show_manage_users_popup, bootstyle="secondary-outline")
        self.create_user_button = ttk.Button(buttons_right_frame, text="Tạo User Mới", command=self.admin_features.show_create_user_popup, bootstyle="secondary-outline")
        self.change_password_button = ttk.Button(buttons_right_frame, text="Đổi Mật Khẩu", command=self.change_password_popup, bootstyle="secondary-outline")
        self.change_password_button.pack(side='left', padx=5)
        ttk.Button(buttons_right_frame, text="Đăng xuất", command=lambda: self.controller.logout(), bootstyle="danger").pack(side='left', padx=5)

        # --- Khu vực nội dung chính ---
        main_content_area = ttk.Frame(self, padding="10")
        main_content_area.pack(expand=True, fill="both")

        # --- Các nút chức năng chính ---
        button_panel = ttk.Frame(main_content_area)
        button_panel.pack(fill='x', side='top', pady=(0, 10))

        self.check_contract_button = ttk.Button(button_panel, text="Kiểm tra Hợp đồng", bootstyle="primary-outline", command=lambda: self.show_content_panel('CheckContractPanel'))
        self.add_contract_button = ttk.Button(button_panel, text="Thêm Hợp đồng mới", bootstyle="success-outline", command=lambda: self.show_content_panel('AddContractFrame'))
        self.add_benefit_button = ttk.Button(button_panel, text="Thêm Quyền Lợi", bootstyle="info-outline", command=lambda: self.show_content_panel('AddBenefitFrame'), state="disabled")
        self.edit_contract_button = ttk.Button(button_panel, text="Chỉnh sửa Hợp đồng", bootstyle="warning-outline", command=lambda: self.show_content_panel("EditPanelSelector"))

        self.check_contract_button.pack(side='left', expand=True, fill='x', padx=5)
        self.add_contract_button.pack(side='left', expand=True, fill='x', padx=5)
        self.add_benefit_button.pack(side='left', expand=True, fill='x', padx=5)
        self.edit_contract_button.pack(side='left', expand=True, fill='x', padx=5)

        # --- Panel chứa nội dung động ---
        self.content_panel = ttk.Frame(main_content_area)
        self.content_panel.pack(fill='both', expand=True)
        self.content_panel.grid_rowconfigure(0, weight=1)
        self.content_panel.grid_columnconfigure(0, weight=1)

    def _initialize_content_frames(self):
        self.frames = {}
        for F in (AddContractFrame, CheckContractPanel, AddBenefitFrame):
            page_name = F.__name__
            frame = F(self.content_panel, self.controller)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        # Thêm panel selector trung gian
        self.frames['EditPanelSelector'] = EditPanelSelector(self.content_panel, lambda: self.show_content_panel('EditContractPanel'), lambda: self.show_content_panel('EditBenefitPanel'))
        self.frames['EditContractPanel'] = EditContractPanel(self.content_panel, self.controller)
        self.frames['EditBenefitPanel'] = EditBenefitPanel(self.content_panel)
        self.frames['EditPanelSelector'].grid(row=0, column=0, sticky="nsew")
        self.frames['EditContractPanel'].grid(row=0, column=0, sticky="nsew")
        self.frames['EditBenefitPanel'].grid(row=0, column=0, sticky="nsew")
        self.show_content_panel(None) # Ẩn tất cả khi bắt đầu

    def show_content_panel(self, page_name):
        for frame in self.frames.values():
            frame.grid_remove()
        
        if page_name in self.frames:
            frame = self.frames[page_name]
            frame.grid()

    def update_welcome_message(self, full_name):
        self.welcome_label.config(text=f"Chào mừng, {full_name}!")

    def show_admin_features(self):
        # Pack theo thứ tự ngược lại để chúng xuất hiện đúng: Quản lý -> Tạo mới
        self.create_user_button.pack(side='left', padx=5, before=self.change_password_button)
        self.manage_users_button.pack(side='left', padx=5, before=self.create_user_button)

    def hide_admin_features(self):
        self.manage_users_button.pack_forget()
        self.create_user_button.pack_forget()

    def change_password_popup(self):
        popup = ttk.Toplevel(self.controller)
        popup.title("Đổi Mật Khẩu")
        popup.geometry("400x250")
        popup.transient(self.controller)
        popup.grab_set()

        frame = ttk.Frame(popup, padding="15")
        frame.pack(expand=True, fill="both")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Mật khẩu cũ:").grid(row=0, column=0, sticky="w", pady=5)
        old_password_entry = ttk.Entry(frame, show="*")
        old_password_entry.grid(row=0, column=1, sticky="ew")

        ttk.Label(frame, text="Mật khẩu mới:").grid(row=1, column=0, sticky="w", pady=5)
        new_password_entry = ttk.Entry(frame, show="*")
        new_password_entry.grid(row=1, column=1, sticky="ew")

        ttk.Label(frame, text="Xác nhận mật khẩu mới:").grid(row=2, column=0, sticky="w", pady=5)
        confirm_password_entry = ttk.Entry(frame, show="*")
        confirm_password_entry.grid(row=2, column=1, sticky="ew")

        def submit():
            old_password = old_password_entry.get()
            new_password = new_password_entry.get()
            confirm_password = confirm_password_entry.get()

            if not all([old_password, new_password, confirm_password]):
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin.", parent=popup)
                return

            username = self.controller.current_user['username']
            user = database.verify_user(username, old_password)
            if not user:
                messagebox.showerror("Lỗi", "Mật khẩu cũ không chính xác.", parent=popup)
                return

            if new_password != confirm_password:
                messagebox.showerror("Lỗi", "Mật khẩu mới không khớp.", parent=popup)
                return
            
            database.update_password(username, new_password)
            messagebox.showinfo("Thành công", "Đổi mật khẩu thành công!", parent=popup)
            popup.destroy()

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Xác nhận", command=submit, bootstyle="success").pack(side="left", padx=10)
        ttk.Button(button_frame, text="Hủy", command=popup.destroy, bootstyle="secondary").pack(side="left")

    def update_button_states_by_role(self, role):
        role_lower = role.lower() if role else None
        if role_lower == 'admin':
            for btn in (self.check_contract_button,
                         self.add_contract_button,
                         self.add_benefit_button,
                         self.edit_contract_button):
                btn.config(state='normal')
            self.show_admin_features()
        elif role_lower == 'creator':
            for btn in (self.check_contract_button,
                         self.add_contract_button,
                         self.add_benefit_button,
                         self.edit_contract_button):
                btn.config(state='normal')
            self.hide_admin_features()
        elif role_lower == 'viewer':
            self.check_contract_button.config(state='normal')
            self.add_contract_button.config(state='disabled')
            self.add_benefit_button.config(state='disabled')
            self.edit_contract_button.config(state='disabled')
            self.hide_admin_features()
        else:
            for btn in (self.check_contract_button,
                         self.add_contract_button,
                         self.add_benefit_button,
                         self.edit_contract_button):
                btn.config(state='disabled')
            self.hide_admin_features()

    def reset_to_default_state(self):
        """Resets the frame to its initial state upon logout."""
        self.show_content_panel(None) # Ẩn tất cả các panel
        self.welcome_label.config(text="Chào mừng!")
        self.update_button_states_by_role(None)
