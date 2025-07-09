import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
import database
from utils.date_utils import _to_date
class AddContractFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.waiting_time_rows = []
        self.special_card_rows = []
        self._fetch_data()
        self.create_widgets()

    def create_widgets(self):
        """Tạo các widget cho giao diện thêm hợp đồng."""
        # --- Tiêu đề ---
        title_label = ttk.Label(
            self, 
            text="\nTHÊM HỢP ĐỒNG BẢO HIỂM MỚI", 
            style="Title.TLabel",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Container chính, sử dụng grid để chia thành 2 cột bằng nhau
        container = ttk.Frame(self, padding="10")  # Giảm padding tổng
        container.pack(expand=True, fill="both")
        # Cả 2 cột có weight bằng nhau để chia đều không gian
        container.grid_columnconfigure(0, weight=1, minsize=400)  # Thêm minsize
        container.grid_columnconfigure(1, weight=1, minsize=400)  # Thêm minsize
        container.grid_rowconfigure(1, weight=1)  # Hàng chứa 2 panel

        # --- Panel bên trái ---
        left_panel = ttk.Frame(container)
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(0, weight=0)  # Panel thông tin
        left_panel.rowconfigure(1, weight=0)  # Panel thẻ đặc biệt

        # --- Panel thông tin chung (trên) ---
        top_left_panel = ttk.LabelFrame(left_panel, text="Thông tin Hợp đồng", bootstyle="info", padding=(10, 10, 10, 5))  # Giảm padding dưới
        top_left_panel.grid(row=0, column=0, sticky="nsew")
        top_left_panel.columnconfigure(1, weight=1, minsize=200)  # Thêm minsize cho cột nhập liệu

        # Các trường nhập liệu
        self.fields = {
            "soHopDong": ("Số Hợp Đồng:", ttk.Entry(top_left_panel)),
            "tenCongTy": ("Tên Công Ty:", ttk.Entry(top_left_panel)),
            "HLBH_tu": ("Hiệu lực từ (DD/MM/YYYY):", ttk.Entry(top_left_panel)),
            "HLBH_den": ("Hiệu lực đến (DD/MM/YYYY):", ttk.Entry(top_left_panel)),
            "coPay": ("Đồng chi trả (%):", ttk.Entry(top_left_panel)),
            "sign_CF": ("Đóng dấu trên CF:", ttk.Combobox(top_left_panel, state="readonly"))
        }

        # Lấy dữ liệu cho Sign CF Combobox
        self.fields["sign_CF"][1]['values'] = list(self.sign_cf_map.keys())

        # Hiển thị các trường trong panel trên bên trái
        for i, (key, (label_text, widget)) in enumerate(self.fields.items()):
            ttk.Label(top_left_panel, text=label_text).grid(row=i, column=0, sticky="w", pady=2, padx=2)
            widget.grid(row=i, column=1, sticky="ew", pady=2, padx=2)

        # --- Panel Thẻ Đặc Biệt (dưới) ---
        bottom_left_panel = ttk.LabelFrame(left_panel, text="Thẻ Đặc Biệt",bootstyle="info", padding=10)
        bottom_left_panel.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        bottom_left_panel.columnconfigure(0, weight=1)
        bottom_left_panel.rowconfigure(0, weight=1)

        self.special_cards_dynamic_frame = ttk.Frame(bottom_left_panel)
        self.special_cards_dynamic_frame.grid(row=0, column=0, sticky="nsew")
        self.special_cards_dynamic_frame.columnconfigure(0, weight=1)

        self._add_special_card_row()

        # --- Panel bên phải ---
        right_panel = ttk.Frame(container)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=0)  # Phần thời gian chờ
        right_panel.rowconfigure(1, weight=0)  # Phần MR App

        # --- Panel Thời gian chờ (trên) ---
        waiting_time_panel = ttk.LabelFrame(right_panel, text="Quy Định Thời Gian Chờ", bootstyle="info",padding=(10, 10, 10, 5))
        waiting_time_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        waiting_time_panel.columnconfigure(0, weight=1)
        waiting_time_panel.rowconfigure(1, weight=1)  # Dynamic rows frame

        # Nút 'New data' cho thời gian chờ
        ttk.Button(waiting_time_panel, text="New data", command=self._show_add_waiting_time_popup).grid(row=0, column=0, sticky='e', pady=(0, 5))

        # Khung chứa các dòng thời gian chờ động
        self.dynamic_rows_frame = ttk.Frame(waiting_time_panel)
        self.dynamic_rows_frame.grid(row=1, column=0, sticky="nsew")
        self.dynamic_rows_frame.columnconfigure(0, weight=1)

        # --- Panel MR App (dưới) ---
        mr_app_panel = ttk.LabelFrame(right_panel, text="Mở Rộng Bồi Thường Qua App", bootstyle="info", padding=(10, 10, 10, 5))
        mr_app_panel.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        mr_app_panel.columnconfigure(1, weight=1)

        # Tạo biến và switch cho MR App
        self.mr_app_var = tk.BooleanVar(value=False)

        self.mr_app_label = ttk.Label(mr_app_panel, text="Mở rộng bồi thường qua app Bvdirect:")
        self.mr_app_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        mr_app_switch = ttk.Checkbutton(
            mr_app_panel,
            bootstyle="round-toggle",
            variable=self.mr_app_var,
            command=self._toggle_mr_app_details
        )
        mr_app_switch.grid(row=0, column=1, sticky="w", pady=(0, 5), padx=5)

        # Ô nhập thông tin chi tiết (ban đầu bị ẩn)
        self.mr_app_details_label = ttk.Label(mr_app_panel, text="Thông tin chi tiết:")
        self.mr_app_details_label.grid(row=1, column=0, sticky="w", pady=(10, 5))

        self.mr_app_details = ttk.Entry(mr_app_panel)
        self.mr_app_details.grid(row=1, column=1, sticky="ew", padx=5, pady=(10, 5))

        # Khởi tạo trạng thái ban đầu
        self._toggle_mr_app_details()

        self._add_waiting_time_row() # Add the first row initially


        # --- Các nút bấm ---
        button_frame = ttk.Frame(container)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Lưu Hợp Đồng", bootstyle="success-outline", command=self.submit).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Xóa Form", bootstyle="danger-outline", command=self.clear_form).pack(side="left")

    def submit(self):
        """Thu thập, kiểm tra và lưu dữ liệu hợp đồng mới."""
        # --- Thu thập dữ liệu từ panel trái ---
        contract_data = {}
        for key, (label_text, widget) in self.fields.items():
            value = widget.get()
            if not value:
                Messagebox.show_error(f"Trường '{label_text}' không được để trống.", "Lỗi")
                return
            # Chuẩn hóa ngày cho hai trường HLBH_tu, HLBH_den
            if key in ("HLBH_tu", "HLBH_den"):
                parsed_date = _to_date(value)
                if not parsed_date:
                    Messagebox.show_error(f"{label_text} không đúng định dạng dd/mm/yyyy.", "Lỗi")
                    return
                contract_data[key] = parsed_date.strftime("%Y-%m-%d")
            else:
                contract_data[key] = value

        contract_data['coPay'] = contract_data['coPay'].strip()

        selected_sign_cf_text = contract_data.pop('sign_CF')
        contract_data['sign_CF_id'] = self.sign_cf_map.get(selected_sign_cf_text)
        
        # Thêm thông tin MR App vào dữ liệu hợp đồng
        if self.mr_app_var.get():  # Nếu switch đang BẬT
            mr_app_status = "Có"
            mr_app_details = self.mr_app_details.get().strip()
            # Nếu bật mà không nhập chi tiết, vẫn lưu là "Có"
            contract_data['mr_app'] = f"{mr_app_status} - {mr_app_details}" if mr_app_details else mr_app_status
        else:
            contract_data['mr_app'] = "Không"

        if not self.controller.current_user or 'id' not in self.controller.current_user:
            Messagebox.show_error("Không xác định được người dùng. Vui lòng đăng nhập lại.", "Lỗi")
            return
        contract_data['created_by'] = self.controller.current_user['id']
        contract_data['isActive'] = 1  # Mặc định hợp đồng mới là active

        # --- Thu thập dữ liệu thời gian chờ từ panel phải ---
        waiting_times = []
        for row_frame in self.waiting_time_rows:
            widgets = row_frame.winfo_children()
            combo = widgets[0]
            value_entry = widgets[1]
            selected_text = combo.get()
            value = value_entry.get().strip()

            if selected_text:
                cho_id = self.waiting_time_map.get(selected_text)
                if cho_id:
                    waiting_times.append((cho_id, value))
        unique_waiting_times = dict(waiting_times)
        # Convert waiting times to the format expected by the database layer
        contract_data['waiting_periods'] = [
            {"id": cho_id, "value": val}
            for cho_id, val in unique_waiting_times.items()
        ]

        # --- Thu thập dữ liệu thẻ đặc biệt ---
        special_cards = []
        for row_frame in self.special_card_rows:
            widgets = row_frame.winfo_children()
            so_the_entry, ten_ndbh_entry, ghi_chu_entry = widgets[0], widgets[1], widgets[2]
            so_the = so_the_entry.get().strip()
            ten_ndbh = ten_ndbh_entry.get().strip()
            ghi_chu = ghi_chu_entry.get().strip()

            # Bỏ qua nếu người dùng không nhập (vẫn giữ placeholder hoặc rỗng)
            placeholders = {"Số thẻ", "Tên Người Được Bảo Hiểm", "Ghi chú"}
            if so_the in placeholders:
                so_the = ""
            if ten_ndbh in placeholders:
                ten_ndbh = ""
            if ghi_chu in placeholders:
                ghi_chu = ""

            if so_the and ten_ndbh:  # Chỉ thêm nếu người dùng nhập ít nhất 2 trường chính
                special_cards.append({
                    "number": so_the,
                    "holder_name": ten_ndbh,
                    "notes": ghi_chu
                })
        contract_data['special_cards'] = special_cards

        # --- Gửi dữ liệu tới database ---
        success, message = database.add_contract(contract_data)

        if success:
            Messagebox.show_info(message, "Thành công")
            self.clear_form()
        else:
            Messagebox.show_error(message, "Lỗi")

    def _fetch_data(self):
        """Lấy dữ liệu cần thiết từ database."""
        try:
            # Dữ liệu cho Sign CF
            sign_cf_data = database.get_all_sign_cf()
            self.sign_cf_map = {item['mo_ta']: item['id'] for item in sign_cf_data}
            
            # Dữ liệu cho Thời gian chờ
            waiting_times_data = database.get_all_waiting_times()
            # Format text for display and store map of display_text -> id
            self.waiting_time_map = {f"{item['loai_cho']} - {item['mo_ta']}": item['id'] for item in waiting_times_data}
            self.waiting_time_options = list(self.waiting_time_map.keys())

        except Exception as e:
            Messagebox.show_error(f"Không thể tải dữ liệu: {e}", "Lỗi Database")
            self.sign_cf_map = {}
            self.waiting_time_map = {}
            self.waiting_time_options = []

    def _refresh_waiting_time_data(self):
        """Làm mới dữ liệu thời gian chờ từ DB và cập nhật các combobox."""
        try:
            # 1. Lấy dữ liệu đã cập nhật
            waiting_times_data = database.get_all_waiting_times()
            self.waiting_time_map = {f"{item['loai_cho']} - {item['mo_ta']}": item['id'] for item in waiting_times_data}
            self.waiting_time_options = list(self.waiting_time_map.keys())

            # 2. Cập nhật tất cả các combobox hiện có
            for row_frame in self.waiting_time_rows:
                combo = row_frame.winfo_children()[0]
                current_value = combo.get()
                combo['values'] = self.waiting_time_options
                # Cố gắng khôi phục lựa chọn trước đó nếu nó vẫn tồn tại
                if current_value in self.waiting_time_options:
                    combo.set(current_value)
                else:
                    combo.set('') # Xóa nếu giá trị cũ không còn
                    
        except Exception as e:
            Messagebox.show_error(f"Không thể làm mới danh sách thời gian chờ: {e}", "Lỗi Database")

    def _add_waiting_time_row(self):
        """Thêm một hàng mới cho việc nhập thời gian chờ."""
        row_index = len(self.waiting_time_rows)
        row_frame = ttk.Frame(self.dynamic_rows_frame)
        row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
        row_frame.columnconfigure(0, weight=1)

        combo = ttk.Combobox(row_frame, values=self.waiting_time_options, state="readonly")
        combo['postcommand'] = lambda: self._adjust_dropdown_width(combo)
        combo.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        value_entry = ttk.Entry(row_frame, width=10)
        value_entry.grid(row=0, column=1, sticky="w", padx=(0, 5))
        value_entry.insert(0, "365 ngày") # Giá trị mặc định mới

        add_button = ttk.Button(row_frame, text="+", width=3, command=self._add_waiting_time_row)
        add_button.grid(row=0, column=2, padx=(0, 2))

        remove_button = ttk.Button(row_frame, text="-", width=3, command=lambda rf=row_frame: self._remove_waiting_time_row(rf))
        remove_button.grid(row=0, column=3)

        self.waiting_time_rows.append(row_frame)
        self._update_plus_minus_buttons()

    def _adjust_dropdown_width(self, combo):
        """Điều chỉnh độ rộng của danh sách dropdown để vừa với nội dung dài nhất."""
        if not self.waiting_time_options:
            return
        # Tìm độ dài của mục dài nhất trong danh sách
        max_len = max(len(s) for s in self.waiting_time_options)
        # Đặt độ rộng (tính bằng số ký tự) cho Listbox của Combobox.
        combo.option_add('*TCombobox*Listbox.width', max_len)

    def _remove_waiting_time_row(self, row_frame):
        """Xóa một hàng thời gian chờ."""
        row_frame.destroy()
        # This is a bit inefficient, but safest way to rebuild list
        self.waiting_time_rows = [child for child in self.dynamic_rows_frame.winfo_children() if isinstance(child, ttk.Frame)]
        self._update_plus_minus_buttons()

    def _clear_waiting_time_rows(self):
        """Xóa và khởi tạo lại các dòng thời gian chờ."""
        for row_frame in self.waiting_time_rows:
            row_frame.destroy()
        self.waiting_time_rows.clear()
        self._add_waiting_time_row()

    def _update_plus_minus_buttons(self):
        """Cập nhật trạng thái của các nút +/-."""
        for i, frame in enumerate(self.waiting_time_rows):
            # frame.winfo_children() -> [combo, entry, add_btn, remove_btn]
            widgets = frame.winfo_children()
            add_button = widgets[2]
            remove_button = widgets[3]

            # Only the last row has a visible '+' button
            if i == len(self.waiting_time_rows) - 1:
                add_button.grid()
            else:
                add_button.grid_remove()

            # The '-' button is hidden if there's only one row
            if len(self.waiting_time_rows) > 1:
                remove_button.grid()
            else:
                remove_button.grid_remove()

    def _toggle_mr_app_details(self):
        """Xử lý việc hiển thị/ẩn các chi tiết của MR App dựa trên trạng thái của switch."""
        if self.mr_app_var.get():  # Nếu switch đang BẬT
            self.mr_app_label.config(text="CÓ MỞ RỘNG:")
            self.mr_app_details_label.grid()
            self.mr_app_details.grid()
            self.mr_app_details.delete(0, tk.END)  # Xóa văn bản mặc định
            self.mr_app_details.focus() # Tự động focus vào ô nhập liệu
        else:  # Nếu switch đang TẮT
            self.mr_app_label.config(text="Mở rộng bồi thường qua app Bvdirect:")
            self.mr_app_details_label.grid_remove()
            self.mr_app_details.grid_remove()
            self.mr_app_details.delete(0, tk.END)
            self.mr_app_details.insert(0, "Không")

    def clear_form(self):
        """Hiển thị hộp thoại xác nhận trước khi xóa toàn bộ dữ liệu trên form."""
        result = Messagebox.yesno(
            title="Xác nhận Xóa Form",
            message="Bạn có chắc chắn muốn xóa toàn bộ thông tin đã nhập không?",
            alert=True  # Hiển thị cửa sổ như một cảnh báo
        )
        
        if result == "Yes":
            # Clear left panel fields
            for key, (_, widget) in self.fields.items():
                if isinstance(widget, ttk.Combobox):
                    widget.set('')
                else:
                    widget.delete(0, tk.END)

            # Reset right panel (waiting times)
            self._clear_waiting_time_rows()
            
            # Reset MR App section
            self.mr_app_var.set(False)
            self._toggle_mr_app_details()

            # Reset bottom left panel (special cards)
            self._clear_special_card_rows()

    def _show_add_waiting_time_popup(self):
        """Hiển thị popup để thêm thời gian chờ mới."""
        popup = tk.Toplevel(self)
        popup.title("Thêm Quy Định Chờ Mới")
        popup.geometry("350x200")
        popup.transient(self)
        popup.grab_set()

        frame = ttk.Frame(popup, padding="15")
        frame.pack(expand=True, fill="both")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Loại chờ:").grid(row=0, column=0, sticky="w", pady=5)
        loai_cho_entry = ttk.Entry(frame)
        loai_cho_entry.grid(row=0, column=1, sticky="ew")

        ttk.Label(frame, text="Mô tả:").grid(row=1, column=0, sticky="w", pady=5)
        mo_ta_entry = ttk.Entry(frame)
        mo_ta_entry.grid(row=1, column=1, sticky="ew")

        def submit():
            loai_cho = loai_cho_entry.get().strip()
            mo_ta = mo_ta_entry.get().strip()

            if not loai_cho or not mo_ta:
                Messagebox.show_error("Vui lòng điền đầy đủ thông tin.", "Lỗi", parent=popup)
                return

            success, message = database.add_waiting_time(loai_cho, mo_ta)
            if success:
                Messagebox.show_info(message, "Thành công", parent=popup)
                popup.destroy()
                self._refresh_waiting_time_data() # Refresh data and UI
            else:
                Messagebox.show_error(message, "Lỗi", parent=popup)

        def show_guide():
            Messagebox.show_info(
                "Lưu ý: Chỉ nhập thông tin chưa có trong danh mục thời gian chờ.\n\n1. Chỉ nhập quy định chờ, không cần nhập số ngày chờ.",
                "Hướng dẫn",
                parent=popup
            )

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Lưu", command=submit, style="Accent.TButton").pack(side="left", padx=10)
        ttk.Button(button_frame, text="Hủy", command=popup.destroy).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Guide", command=show_guide).pack(side="left")

    def _refresh_waiting_time_data(self):
        """Làm mới dữ liệu thời gian chờ và cập nhật các combobox."""
        # Refetch data from the database
        try:
            waiting_times_data = database.get_all_waiting_times()
            self.waiting_time_map = {f"{item['loai_cho']} - {item['mo_ta']}": item['id'] for item in waiting_times_data}
            self.waiting_time_options = list(self.waiting_time_map.keys())
        except Exception as e:
            Messagebox.show_error(f"Không thể tải lại dữ liệu thời gian chờ: {e}", "Lỗi Database")
            return

        # Update all existing comboboxes
        for row_frame in self.waiting_time_rows:
            combo = row_frame.winfo_children()[0] # Assuming combobox is the first widget
            current_value = combo.get()
            combo['values'] = self.waiting_time_options
            # Try to keep the current selection if it still exists
            if current_value in self.waiting_time_options:
                combo.set(current_value)
            else:
                combo.set('')

    # --- Quản lý các dòng Thẻ Đặc Biệt ---
    def _add_special_card_row(self):
        row_index = len(self.special_card_rows)
        row_frame = ttk.Frame(self.special_cards_dynamic_frame)
        row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
        row_frame.columnconfigure(1, weight=1) # Cột Tên NĐBH co giãn

        so_the_entry = ttk.Entry(row_frame, width=20)
        so_the_entry.grid(row=0, column=0, padx=(0, 5))
        so_the_entry.insert(0, "Số thẻ")

        ten_ndbh_entry = ttk.Entry(row_frame)
        ten_ndbh_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        ten_ndbh_entry.insert(0, "Tên Người Được Bảo Hiểm")

        ghi_chu_entry = ttk.Entry(row_frame, width=25)
        ghi_chu_entry.grid(row=0, column=2, padx=(0, 5))
        ghi_chu_entry.insert(0, "Ghi chú")

        add_button = ttk.Button(row_frame, text="+", width=3, command=self._add_special_card_row)
        add_button.grid(row=0, column=3, padx=(0, 2))

        remove_button = ttk.Button(row_frame, text="-", width=3, command=lambda rf=row_frame: self._remove_special_card_row(rf))
        remove_button.grid(row=0, column=4)

        self.special_card_rows.append(row_frame)
        self._update_special_card_buttons()

    def _remove_special_card_row(self, row_frame):
        row_frame.destroy()
        self.special_card_rows.remove(row_frame)
        self._update_special_card_buttons()

    def _update_special_card_buttons(self):
        for i, frame in enumerate(self.special_card_rows):
            widgets = frame.winfo_children()
            add_button = widgets[3]
            remove_button = widgets[4]

            add_button.grid_remove() if i < len(self.special_card_rows) - 1 else add_button.grid()
            remove_button.grid() if len(self.special_card_rows) > 1 else remove_button.grid_remove()

    def _clear_special_card_rows(self):
        for row_frame in self.special_card_rows:
            row_frame.destroy()
        self.special_card_rows.clear()
        self._add_special_card_row()
