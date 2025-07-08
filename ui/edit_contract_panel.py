import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
import database as db
from utils.date_utils import format_date, format_date_range, _to_date

class EditContractPanel(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_contract = None
        self.contracts_data = {}
        self.waiting_time_rows = []
        self.special_card_rows = []
        self.sc_scrollable_frame = None
        self.save_special_cards_button = None

        self._fetch_data()
        
        style = ttk.Style()
        style.configure('TButton', padding=2)
        style.configure('Accent.TButton', padding=2)
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        title_label = ttk.Label(
            self, 
            text="CHỈNH SỬA HỢP ĐỒNG CHÍNH", 
            style="Title.TLabel",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 20), sticky="n")
        
        self.main_container = ttk.Frame(self, padding=5)
        self.main_container.grid(row=1, column=0, sticky="nsew")
        
        self.main_container.columnconfigure(0, weight=1, uniform='panels')
        self.main_container.columnconfigure(1, weight=2, uniform='panels')
        self.main_container.columnconfigure(2, weight=1, uniform='panels')
        
        self.main_container.rowconfigure(0, weight=1)
        self.main_container.rowconfigure(1, weight=2)
        
        self._create_search_panel()
        self._create_results_panel()
        self._create_info_panel()
        self._create_notebook_panels()
        self._create_status_bar()

        self.toggle_forms(False)

    def _create_search_panel(self):
        search_frame = ttk.LabelFrame(self.main_container, text="Tìm kiếm hợp đồng", padding=10, bootstyle="info")
        search_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Số HĐ/Tên công ty:").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        self.search_entry.bind('<Return>', lambda e: self.search_contract())
        
        search_btn = ttk.Button(search_frame, text="Tìm", command=self.search_contract, bootstyle="light")
        search_btn.grid(row=0, column=2, padx=(0, 2))

    def _create_results_panel(self):
        results_frame = ttk.LabelFrame(self.main_container, text="Kết quả tìm kiếm", padding=10, bootstyle="info")
        results_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=(0, 5))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        tree_container = ttk.Frame(results_frame)
        tree_container.grid(row=0, column=0, sticky="nsew")
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        
        y_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        columns = ("Số HĐ", "Công ty", "Từ ngày", "Đến ngày")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", selectmode="browse", yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        y_scrollbar.config(command=self.tree.yview)
        x_scrollbar.config(command=self.tree.xview)
        
        self.tree.column("Số HĐ", width=120, anchor="w")
        self.tree.column("Công ty", width=250, anchor="w")
        self.tree.column("Từ ngày", width=100, anchor="center")
        self.tree.column("Đến ngày", width=100, anchor="center")
        
        for col in columns:
            self.tree.heading(col, text=col)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_contract_select)

    def _create_info_panel(self):
        self.contract_info_frame = ttk.LabelFrame(self.main_container, text="Thông tin hợp đồng", padding=10, bootstyle="info")
        self.contract_info_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=(0, 5))
        self.contract_info_frame.columnconfigure(1, weight=1)
        self.no_contract_label = ttk.Label(self.contract_info_frame, text="Chọn hợp đồng để xem chi tiết", style="secondary")
        self.no_contract_label.pack(expand=True)

    def _create_notebook_panels(self):
        self.notebook = ttk.Notebook(self.main_container, bootstyle="info")
        self.notebook.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(10, 0))

        self.tab_general = ttk.Frame(self.notebook, padding=10)
        self.tab_waiting = ttk.Frame(self.notebook, padding=10)
        self.tab_special = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_general, text="Thông tin chung")
        self.notebook.add(self.tab_waiting, text="Thời gian chờ")
        self.notebook.add(self.tab_special, text="Thẻ đặc biệt")

        self._create_general_info_tab()
        self._create_waiting_periods_tab()
        self._create_special_cards_tab()

    def _create_special_cards_tab(self):
        frame = self.tab_special
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1) # Row for the canvas

        # Header
        header_frame = ttk.Frame(frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5)
        ttk.Label(header_frame, text="Số thẻ", width=25).pack(side="left", padx=(0, 5))
        ttk.Label(header_frame, text="Tên Người Được Bảo Hiểm", width=40).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Label(header_frame, text="Ghi chú").pack(side="left", expand=True, fill="x", padx=(0, 5))

        # Scrollable area
        canvas = tk.Canvas(frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        self.sc_scrollable_frame = ttk.Frame(canvas)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.sc_canvas_window = canvas.create_window((0, 0), window=self.sc_scrollable_frame, anchor="nw")
        self.sc_scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind('<Configure>', self._on_sc_canvas_configure)

        # Save button
        self.save_special_cards_button = ttk.Button(frame, text="Lưu thay đổi Thẻ đặc biệt", command=self.on_save_special_cards)
        self.save_special_cards_button.grid(row=2, column=0, columnspan=2, pady=10)

    def _on_sc_canvas_configure(self, event):
        canvas = event.widget
        canvas.itemconfig(self.sc_canvas_window, width=event.width)

    def _create_status_bar(self):
        self.status_frame = ttk.Frame(self, height=22)
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
        self.status_label = ttk.Label(self.status_frame, text="Sẵn sàng.", style="secondary")
        self.status_label.pack(side="left")

    def search_contract(self):
        search_term = self.search_var.get().strip()
        if not search_term:
            Messagebox.show_warning("Vui lòng nhập tiêu chí tìm kiếm.", "Thiếu thông tin")
            return
        try:
            results = db.search_contracts(company_name=search_term, contract_number=search_term)
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.contracts_data.clear()

            if not results:
                Messagebox.show_info("Không tìm thấy hợp đồng phù hợp.", "Thông báo")
                return

            for contract in results:
                details = contract['details']
                hd_id = details['id']
                self.contracts_data[str(hd_id)] = contract
                self.tree.insert("", "end", text=str(hd_id), values=(
                    details.get('soHopDong', ''),
                    details.get('tenCongTy', ''),
                    format_date(details.get('HLBH_tu', '')),
                    format_date(details.get('HLBH_den', ''))
                ))
            self.status_label.config(text=f"Tìm thấy {len(results)} hợp đồng.", style="info")
        except Exception as e:
            Messagebox.show_error(f"Lỗi khi tìm kiếm: {e}", "Lỗi")

    def on_contract_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        contract_id = self.tree.item(selected_items[0], "text")
        self.current_contract = self.contracts_data.get(contract_id)
        if self.current_contract:
            self.update_contract_info()
            self._populate_forms()
            self.toggle_forms(True)
            self.status_label.config(text=f"Đã chọn HĐ: {self.current_contract['details']['soHopDong']}", style="info")

    def update_contract_info(self):
        for widget in self.contract_info_frame.winfo_children():
            widget.destroy()
        details = self.current_contract['details']
        fields = {
            "Số HĐ:": details.get('soHopDong', 'N/A'),
            "Công ty:": details.get('tenCongTy', 'N/A'),
            "Hiệu lực:": format_date_range(details.get('HLBH_tu'), details.get('HLBH_den')),
            "Tình trạng:": "Hoạt động" if details.get('isActive') else "Không hoạt động"
        }
        for i, (label, value) in enumerate(fields.items()):
            ttk.Label(self.contract_info_frame, text=label, font=("Arial", 9, "bold")).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(self.contract_info_frame, text=value, wraplength=180).grid(row=i, column=1, sticky="w", padx=5, pady=2)

    def _create_general_info_tab(self):
        frame = self.tab_general
        frame.columnconfigure(1, weight=1)
        self.edit_fields = {
            "Số hợp đồng:": tk.StringVar(), "Tên công ty:": tk.StringVar(),
            "Hiệu lực từ:": tk.StringVar(), "Hiệu lực đến:": tk.StringVar(),
            "Co-pay:": tk.StringVar()
        }
        for i, (label, var) in enumerate(self.edit_fields.items()):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            ttk.Entry(frame, textvariable=var).grid(row=i, column=1, sticky="ew", padx=5, pady=5)
        self.save_general_info_button = ttk.Button(frame, text="Lưu thay đổi chung", command=self._save_general_info_changes)
        self.save_general_info_button.grid(row=len(self.edit_fields), column=0, columnspan=2, pady=10)

    def _create_waiting_periods_tab(self):
        frame = self.tab_waiting
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        canvas = tk.Canvas(frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind('<Configure>', self._on_canvas_configure)
        self.save_waiting_periods_button = ttk.Button(frame, text="Lưu thay đổi Thời gian chờ", command=self.on_save_waiting_periods)
        self.save_waiting_periods_button.grid(row=1, column=0, columnspan=2, pady=10)

    def _create_special_cards_tab(self):
        ttk.Label(self.tab_special, text="Chức năng đang được phát triển.").pack(pady=20)

    def _fetch_data(self):
        try:
            waiting_times_data = db.get_all_waiting_times()
            self.waiting_time_id_to_text_map = {item['id']: item['loai_cho'] for item in waiting_times_data}
            self.waiting_time_text_to_id_map = {v: k for k, v in self.waiting_time_id_to_text_map.items()}
            self.waiting_time_options = sorted(list(self.waiting_time_text_to_id_map.keys()))
        except Exception as e:
            Messagebox.show_error(f"Không thể tải dữ liệu: {e}", "Lỗi Database")
            self.waiting_time_id_to_text_map, self.waiting_time_text_to_id_map, self.waiting_time_options = {}, {}, []

    def _populate_special_cards_tab(self):
        for widget in self.special_card_rows:
            widget.destroy()
        self.special_card_rows.clear()
        special_cards = self.current_contract.get('special_cards', [])
        if not special_cards:
            self._add_special_card_row()
        else:
            for card in special_cards:
                self._add_special_card_row(number=card.get('so_the', ''), holder=card.get('ten_NDBH', ''), notes=card.get('ghi_chu', ''))
        self._update_sc_plus_minus_buttons()
        self.sc_scrollable_frame.update_idletasks()
        canvas = self.sc_scrollable_frame.master
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _add_special_card_row(self, number="", holder="", notes=""):
        row_frame = ttk.Frame(self.sc_scrollable_frame)
        row_frame.pack(fill="x", expand=True, pady=2, padx=5)

        entry_number = ttk.Entry(row_frame, width=25)
        entry_number.pack(side="left", padx=(0, 5))
        entry_number.insert(0, number)

        entry_holder = ttk.Entry(row_frame, width=40)
        entry_holder.pack(side="left", expand=True, fill="x", padx=(0, 5))
        entry_holder.insert(0, holder)

        entry_notes = ttk.Entry(row_frame)
        entry_notes.pack(side="left", expand=True, fill="x", padx=(0, 5))
        entry_notes.insert(0, notes)

        button_frame = ttk.Frame(row_frame)
        button_frame.pack(side="left")
        add_button = ttk.Button(button_frame, text="+", width=2, command=self._add_special_card_row, bootstyle="success-outline")
        add_button.pack(side="left")
        remove_button = ttk.Button(button_frame, text="-", width=2, command=lambda rf=row_frame: self._remove_special_card_row(rf), bootstyle="danger-outline")
        remove_button.pack(side="left", padx=(2, 0))

        self.special_card_rows.append(row_frame)
        self._update_sc_plus_minus_buttons()

    def _remove_special_card_row(self, row_frame):
        row_frame.destroy()
        self.special_card_rows = [r for r in self.special_card_rows if r.winfo_exists()]
        self._update_sc_plus_minus_buttons()

    def _update_sc_plus_minus_buttons(self):
        num_rows = len(self.special_card_rows)
        if not self.special_card_rows and self.current_contract:
            self._add_special_card_row()
            return
        for i, row_frame in enumerate(self.special_card_rows):
            button_frame = row_frame.winfo_children()[3]
            add_btn, remove_btn = button_frame.winfo_children()
            add_btn.pack_forget()
            remove_btn.pack(side="left", padx=(2, 0))
            if i == num_rows - 1:
                add_btn.pack(side="left")
            if num_rows == 1:
                remove_btn.pack_forget()

    def on_save_special_cards(self):
        if not self.current_contract:
            return
        cards_to_save = []
        seen_cards = set()
        try:
            for row_frame in self.special_card_rows:
                number_entry, holder_entry, notes_entry = row_frame.winfo_children()[:3]
                card_number = number_entry.get().strip()
                holder_name = holder_entry.get().strip()
                notes = notes_entry.get().strip()

                if not card_number and not holder_name: # Bỏ qua các hàng trống
                    continue
                
                if not card_number or not holder_name:
                    Messagebox.show_warning("Số thẻ và Tên người được bảo hiểm là bắt buộc cho mỗi thẻ.", "Thiếu thông tin")
                    return

                if card_number in seen_cards:
                    Messagebox.show_warning(f"Số thẻ '{card_number}' bị trùng lặp.", "Dữ liệu không hợp lệ")
                    return
                seen_cards.add(card_number)

                cards_to_save.append({"number": card_number, "holder_name": holder_name, "notes": notes})
            
            db.update_contract_special_cards(self.current_contract['details']['id'], cards_to_save)
            Messagebox.show_info("Đã lưu thành công thẻ đặc biệt!", "Thành công")
            self.refresh_current_contract_data()
        except Exception as e:
            Messagebox.show_error(f"Lỗi khi lưu thẻ đặc biệt: {e}", "Lỗi Database")

    def toggle_forms(self, enabled):
        state = "normal" if enabled else "disabled"
        for i in range(self.notebook.index("end")):
            self.notebook.tab(i, state=state)
        for widget in self.tab_general.winfo_children():
            if isinstance(widget, (ttk.Entry, ttk.Button)):
                widget.config(state=state)
        for row_frame in self.waiting_time_rows:
            for widget in row_frame.winfo_children():
                if isinstance(widget, (ttk.Combobox, ttk.Entry, ttk.Button)):
                    widget.config(state=state)
                elif isinstance(widget, ttk.Frame): # Nút +/- 
                    for btn in widget.winfo_children():
                        btn.config(state=state)
        for row_frame in self.special_card_rows:
            for widget in row_frame.winfo_children():
                if isinstance(widget, (ttk.Entry, ttk.Button)):
                    widget.config(state=state)
                elif isinstance(widget, ttk.Frame): # Nút +/- 
                    for btn in widget.winfo_children():
                        btn.config(state=state)

        if self.save_waiting_periods_button:
            self.save_waiting_periods_button.config(state=state)
        if self.save_special_cards_button:
            self.save_special_cards_button.config(state=state)
        for row_frame in self.waiting_time_rows:
            for widget in row_frame.winfo_children():
                if isinstance(widget, (ttk.Combobox, ttk.Entry)):
                    widget.config(state=state)
                elif isinstance(widget, ttk.Frame):
                    for btn in widget.winfo_children():
                        btn.config(state="normal" if enabled else "disabled")
        self.save_waiting_periods_button.config(state=state)

    def _populate_forms(self):
        self._populate_general_info_tab()
        self._populate_waiting_periods_tab()
        self._populate_special_cards_tab()

    def _populate_general_info_tab(self):
        details = self.current_contract['details']
        for key, var in self.edit_fields.items():
            db_key = {"Số hợp đồng:": "soHopDong", "Tên công ty:": "tenCongTy", "Hiệu lực từ:": "HLBH_tu", "Hiệu lực đến:": "HLBH_den", "Co-pay:": "coPay"}[key]
            value = details.get(db_key, '')
            if "Hiệu lực" in key:
                var.set(format_date(value))
            else:
                var.set(value)

    def _populate_waiting_periods_tab(self):
        for widget in self.waiting_time_rows:
            widget.destroy()
        self.waiting_time_rows.clear()
        waiting_periods = self.current_contract.get('waiting_periods', [])
        if not waiting_periods:
            self._add_waiting_time_row()
        else:
            for period in waiting_periods:
                cho_id = self.waiting_time_text_to_id_map.get(period.get('loai_cho'))
                if cho_id is not None:
                    self._add_waiting_time_row(cho_id=cho_id, value=period.get('gia_tri'))
        self._update_plus_minus_buttons()
        self.scrollable_frame.update_idletasks()
        canvas = self.scrollable_frame.master
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        canvas = event.widget
        canvas.itemconfig(self.canvas_window, width=event.width)

    def _add_waiting_time_row(self, cho_id=None, value=""):
        row_frame = ttk.Frame(self.scrollable_frame)
        row_frame.pack(fill="x", expand=True, pady=2, padx=5)
        combo = ttk.Combobox(row_frame, values=self.waiting_time_options, state="readonly", width=40)
        combo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        if cho_id:
            combo.set(self.waiting_time_id_to_text_map.get(cho_id, ''))
        entry = ttk.Entry(row_frame, width=25)
        entry.pack(side="left", padx=(0, 5))
        entry.insert(0, str(value) if value is not None else "")
        button_frame = ttk.Frame(row_frame)
        button_frame.pack(side="left")
        add_button = ttk.Button(button_frame, text="+", width=2, command=self._add_waiting_time_row, bootstyle="success-outline")
        add_button.pack(side="left")
        remove_button = ttk.Button(button_frame, text="-", width=2, command=lambda rf=row_frame: self._remove_waiting_time_row(rf), bootstyle="danger-outline")
        remove_button.pack(side="left", padx=(2, 0))
        self.waiting_time_rows.append(row_frame)
        self._update_plus_minus_buttons()

    def _remove_waiting_time_row(self, row_frame):
        row_frame.destroy()
        self.waiting_time_rows = [r for r in self.waiting_time_rows if r.winfo_exists()]
        self._update_plus_minus_buttons()

    def _update_plus_minus_buttons(self):
        num_rows = len(self.waiting_time_rows)
        if not self.waiting_time_rows and self.current_contract:
            self._add_waiting_time_row()
            return
        for i, row_frame in enumerate(self.waiting_time_rows):
            button_frame = row_frame.winfo_children()[2]
            add_btn, remove_btn = button_frame.winfo_children()
            add_btn.pack_forget()
            remove_btn.pack(side="left", padx=(2, 0))
            if i == num_rows - 1:
                add_btn.pack(side="left")
            if num_rows == 1:
                remove_btn.pack_forget()

    def _save_general_info_changes(self):
        if not self.current_contract:
            Messagebox.show_warning("Vui lòng chọn một hợp đồng để chỉnh sửa.", "Chưa chọn hợp đồng")
            return

        try:
            data_to_update = {}
            raw_data = {label: var.get() for label, var in self.edit_fields.items()}

            # --- VALIDATION --- #
            # 1. Kiểm tra các trường bắt buộc
            if not raw_data.get("Số hợp đồng:") or not raw_data.get("Tên công ty:"):
                Messagebox.show_warning("Số hợp đồng và Tên công ty không được để trống.", "Thiếu thông tin")
                return

            # 2. Kiểm tra và xử lý ngày tháng
            date_from_str = raw_data.get("Hiệu lực từ:")
            date_to_str = raw_data.get("Hiệu lực đến:")

            date_from_obj = _to_date(date_from_str)
            date_to_obj = _to_date(date_to_str)

            if not date_from_obj or not date_to_obj:
                Messagebox.show_warning(f"Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng DD/MM/YYYY.", "Lỗi định dạng")
                return

            if date_to_obj < date_from_obj:
                Messagebox.show_warning("Ngày 'Hiệu lực đến' phải sau hoặc bằng ngày 'Hiệu lực từ'.", "Lỗi logic ngày")
                return

            # --- CHUẨN BỊ DỮ LIỆU ĐỂ LƯU ---
            data_to_update = {
                'soHopDong': raw_data.get("Số hợp đồng:"),
                'tenCongTy': raw_data.get("Tên công ty:"),
                'coPay': raw_data.get("Co-pay:"),
                'HLBH_tu': date_from_obj.strftime('%Y-%m-%d'),
                'HLBH_den': date_to_obj.strftime('%Y-%m-%d')
            }

            # Gọi hàm cập nhật từ database
            hopdong_id = self.current_contract['details']['id']
            success, message = db.update_contract_general_info(hopdong_id, data_to_update)

            if success:
                Messagebox.show_info(message, "Thành công")
                # Làm mới dữ liệu sau khi cập nhật
                self.refresh_current_contract_data()
                self.update_contract_info() # Cập nhật lại panel thông tin
                self._populate_general_info_tab() # Cập nhật lại tab thông tin chung
            else:
                Messagebox.show_error(message, "Lỗi")

        except Exception as e:
            Messagebox.show_error(f"Đã xảy ra lỗi không mong muốn: {e}", "Lỗi hệ thống")

    def on_save_waiting_periods(self):
        if not self.current_contract:
            return
        periods_to_save = []
        seen_types = set()
        try:
            for row_frame in self.waiting_time_rows:
                combo, entry = row_frame.winfo_children()[:2]
                loai_cho_text, gia_tri_str = combo.get().strip(), entry.get().strip()

                if not loai_cho_text: # Bỏ qua hàng trống
                    continue

                # 1. Kiểm tra giá trị nhập liệu
                if not gia_tri_str:
                    Messagebox.show_warning(f"Vui lòng nhập giá trị cho '{loai_cho_text}'.", "Thiếu thông tin")
                    return
                try:
                    gia_tri_val = int(gia_tri_str)
                except ValueError:
                    Messagebox.show_warning(f"Giá trị cho '{loai_cho_text}' phải là một con số.", "Dữ liệu không hợp lệ")
                    return

                # 2. Kiểm tra loại thời gian chờ hợp lệ và trùng lặp
                cho_id = self.waiting_time_text_to_id_map.get(loai_cho_text)
                if not cho_id:
                    Messagebox.show_error(f"Loại thời gian chờ không hợp lệ: '{loai_cho_text}'.", "Dữ liệu không hợp lệ")
                    return
                if cho_id in seen_types:
                    Messagebox.show_warning(f"Loại thời gian chờ '{loai_cho_text}' bị trùng lặp.", "Dữ liệu không hợp lệ")
                    return
                seen_types.add(cho_id)

                periods_to_save.append({"cho_id": cho_id, "gia_tri": gia_tri_val})
            
            db.update_contract_waiting_periods(self.current_contract['details']['id'], periods_to_save)
            Messagebox.show_info("Đã lưu thành công!", "Thành công")
            self.refresh_current_contract_data()
        except Exception as e:
            Messagebox.show_error(f"Lỗi khi lưu: {e}", "Lỗi Database")

    def refresh_current_contract_data(self):
        if not self.current_contract:
            return
        try:
            contract_id = self.current_contract['details']['id']
            updated_contracts = db.search_contracts(contract_id=contract_id)
            if updated_contracts:
                self.contracts_data[str(contract_id)] = updated_contracts[0]
                self.current_contract = updated_contracts[0]
        except Exception as e:
            print(f"Error refreshing contract data: {e}")
