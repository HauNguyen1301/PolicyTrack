import tkinter as tk
from tkinter import ttk, messagebox
import database

class AddContractFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.create_widgets()

    def create_widgets(self):
        """Tạo các widget cho giao diện thêm hợp đồng."""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")

        title_label = ttk.Label(main_frame, text="Thêm Hợp Đồng Bảo Hiểm Mới", style="Title.TLabel")
        title_label.pack(pady=(0, 20))

        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill="x", expand=True)
        form_frame.columnconfigure(1, weight=1)

        # Các trường nhập liệu
        self.fields = {
            "soHopDong": ("Số Hợp Đồng:", ttk.Entry(form_frame)),
            "tenCongTy": ("Tên Công Ty:", ttk.Entry(form_frame)),
            "HLBH_tu": ("Hiệu lực từ (YYYY-MM-DD):", ttk.Entry(form_frame)),
            "HLBH_den": ("Hiệu lực đến (YYYY-MM-DD):", ttk.Entry(form_frame)),
            "coPay": ("Đồng chi trả (%):", ttk.Entry(form_frame)),
            "sign_CF": ("Sign CF:", ttk.Combobox(form_frame, state="readonly"))
        }

        # Lấy dữ liệu cho Sign CF Combobox
        try:
            sign_cf_data = database.get_all_sign_cf()
            self.sign_cf_map = {item['mo_ta']: item['id'] for item in sign_cf_data}
            self.fields["sign_CF"][1]['values'] = list(self.sign_cf_map.keys())
        except Exception as e:
            messagebox.showerror("Lỗi Database", f"Không thể tải dữ liệu Sign CF: {e}")
            self.sign_cf_map = {}

        # Hiển thị các trường
        for i, (key, (label_text, widget)) in enumerate(self.fields.items()):
            ttk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky="w", pady=5, padx=5)
            widget.grid(row=i, column=1, sticky="ew", pady=5, padx=5)

        # Các nút bấm
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Lưu Hợp Đồng", command=self.submit, style="Accent.TButton").pack(side="left", padx=10)
        ttk.Button(button_frame, text="Xóa Form", command=self.clear_form).pack(side="left")

    def submit(self):
        """Thu thập, kiểm tra và lưu dữ liệu hợp đồng mới."""
        contract_data = {}
        for key, (label_text, widget) in self.fields.items():
            value = widget.get()
            if not value:
                messagebox.showerror("Lỗi", f"Trường '{label_text}' không được để trống.")
                return
            contract_data[key] = value

        try:
            contract_data['coPay'] = float(contract_data['coPay'])
        except ValueError:
            messagebox.showerror("Lỗi", "'Đồng chi trả' phải là một con số.")
            return

        selected_sign_cf_text = contract_data.pop('sign_CF')
        contract_data['sign_CF_id'] = self.sign_cf_map.get(selected_sign_cf_text)

        if not self.controller.current_user:
            messagebox.showerror("Lỗi", "Không xác định được người dùng. Vui lòng đăng nhập lại.")
            return
        contract_data['user_id'] = self.controller.current_user['id']

        success, message = database.add_contract(contract_data)

        if success:
            messagebox.showinfo("Thành công", message)
            self.clear_form()
        else:
            messagebox.showerror("Lỗi", message)

    def clear_form(self):
        """Xóa toàn bộ dữ liệu trên form."""
        for key, (_, widget) in self.fields.items():
            if isinstance(widget, ttk.Combobox):
                widget.set('')
            else:
                widget.delete(0, tk.END)
