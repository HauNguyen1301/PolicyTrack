import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
import database as db
import datetime  # TODO: Remove if no longer used elsewhere
from utils.date_utils import format_date, format_date_range




class EditContractPanel(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_contract = None
        self.contracts_data = {}
        self.waiting_time_rows = []
        self.special_card_rows = []

        self._fetch_data()
        
        # Configure compact button style
        style = ttk.Style()
        style.configure('TButton', padding=2)  # Reduce padding for all buttons
        style.configure('Accent.TButton', padding=2)  # Also adjust the accent style if used
        
        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            self, 
            text="CHỈNH SỬA HỢP ĐỒNG CHÍNH", 
            style="Title.TLabel",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 20), sticky="n")
        
        # Main container with 3 panels on top and 1 panel at bottom
        self.main_container = ttk.Frame(self, padding=5)
        self.main_container.grid(row=1, column=0, sticky="nsew")
        
        # Configure grid weights for main container
        # Cả 3 cột đều có weight=1 để chia đều không gian
        self.main_container.columnconfigure(0, weight=1, uniform='panels')  # Cột tìm kiếm
        self.main_container.columnconfigure(1, weight=1, uniform='panels')  # Cột kết quả
        self.main_container.columnconfigure(2, weight=1, uniform='panels')  # Cột thông tin
        
        # Cấu hình dòng (Top panels: 1/3, Bottom panel: 2/3)
        self.main_container.rowconfigure(0, weight=1)      # Dòng trên (tìm kiếm, kết quả, thông tin)
        self.main_container.rowconfigure(1, weight=2)      # Dòng dưới (form chỉnh sửa)
        
        # Đặt kích thước tối thiểu cho các panel (nhỏ gọn hơn)
        self.main_container.columnconfigure(0, minsize=200)  # Panel tìm kiếm
        self.main_container.columnconfigure(1, minsize=500)  # Panel kết quả
        self.main_container.columnconfigure(2, minsize=200)  # Panel thông tin
        
        # ========== Panel 1: Search Panel ==========
        search_frame = ttk.LabelFrame(self.main_container, text="Tìm kiếm hợp đồng", padding=5, bootstyle="info")
        search_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))
        search_frame.columnconfigure(0, weight=1)
        search_frame.rowconfigure(1, weight=1)
        search_frame.columnconfigure(1, weight=1)
        
        # Search entry on its own row
        ttk.Label(search_frame, text="Số HĐ/Tên công ty:").grid(row=0, column=0, columnspan=3, padx=2, pady=2, sticky="w")
        
        # Create a container frame for the search row
        search_row = ttk.Frame(search_frame)
        search_row.grid(row=1, column=0, columnspan=3, sticky="ew")
        search_row.columnconfigure(0, weight=1)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=25)  # Reduced from 30 to 25
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 2))
        self.search_entry.bind('<Return>', lambda e: self.search_contract())
        
        # Search button
        search_btn = ttk.Button(
            search_row, 
            text=" Tìm ",  # Added spaces for better width
            command=self.search_contract,
            bootstyle="light"
        )
        search_btn.pack(side="right", padx=(0, 0))
        
        # Configure row weights for search frame
        search_frame.rowconfigure(0, weight=0)
        search_frame.rowconfigure(1, weight=0)
        
        # ========== Panel 2: Search Results Panel ==========
        self.results_frame = ttk.LabelFrame(
            self.main_container, 
            text="Kết quả tìm kiếm", 
            padding=5,
            bootstyle="info"
        )
        self.results_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=(0, 5))
        self.results_frame.columnconfigure(0, weight=1)
        self.results_frame.rowconfigure(0, weight=1)
        
        # Tạo container cho Treeview và thanh cuộn
        tree_container = ttk.Frame(self.results_frame)
        tree_container.grid(row=0, column=0, sticky="nsew")
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        
        # Tạo thanh cuộn dọc
        y_scrollbar = ttk.Scrollbar(tree_container)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tạo thanh cuộn ngang
        x_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Tạo Treeview
        columns = ("Số HĐ", "Công ty", "Từ ngày", "Đến ngày")
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            selectmode="browse",
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        # Kết nối thanh cuộn
        y_scrollbar.config(command=self.tree.yview)
        x_scrollbar.config(command=self.tree.xview)
        
        # Đặt kích thước cột (nhỏ gọn hơn)
        self.tree.column("#0", width=0, stretch=tk.NO)  # Ẩn cột đầu tiên
        self.tree.column("Số HĐ", width=100, anchor="w", minwidth=80, stretch=tk.NO)
        self.tree.column("Công ty", width=200, anchor="w", minwidth=150, stretch=tk.NO)
        self.tree.column("Từ ngày", width=80, anchor="center", minwidth=70, stretch=tk.NO)
        self.tree.column("Đến ngày", width=80, anchor="center", minwidth=70, stretch=tk.NO)
        
        # Đặt tiêu đề cột
        for col in columns:
            self.tree.heading(col, text=col)
        
        # Đặt Treeview vào container với thanh cuộn
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind events
        self.tree.bind("<Double-1>", self.on_contract_select)
        # Tooltip for row hover
        self._tooltip_window = None
        self._current_hover_row = None
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", lambda e: self._hide_tooltip())
        
        # ========== Panel 3: Contract Info Panel ==========
        self.contract_info_frame = ttk.LabelFrame(
            self.main_container, 
            text="Thông tin hợp đồng", 
            padding=5,
            bootstyle="info"
        )
        self.contract_info_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=(0, 5))
        self.contract_info_frame.columnconfigure(1, weight=1)
        self.contract_info_frame.columnconfigure(0, weight=1)
        
        # Add a label that will be shown when no contract is selected
        self.no_contract_label = ttk.Label(
            self.contract_info_frame,
            text="Chọn hợp đồng từ kết quả tìm kiếm",
            style="Info.TLabel"
        )
        self.no_contract_label.pack(expand=True)
        
        # ========== Panel 4: Edit Contract Form (Notebook) ==========
        self._create_notebook_panels()

        # Status bar (use grid instead of pack)
        self.rowconfigure(2, weight=0)
        self.status_frame = ttk.Frame(self, height=22)
        self.status_frame.grid(row=2, column=0, sticky="ew")
        self.status_label = ttk.Label(
            self.status_frame,
            text="Sẵn sàng. Vui lòng tìm kiếm và chọn một hợp đồng.",
            style="Info.TLabel",
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=5, pady=1)

        # Initialize form state
        self.toggle_forms(False)
        

    
    def search_contract(self):
        """Searches for contracts using the new database function."""
        search_term = self.search_var.get().strip()
        if not search_term:
            Messagebox.show_warning("Vui lòng nhập số hợp đồng hoặc tên công ty để tìm kiếm", "Cảnh báo")
            return

        try:
            # Tìm theo tên công ty trước
            results = db.search_contracts(company_name=search_term, contract_number='')
            # Nếu không thấy, thử tìm theo số hợp đồng
            if not results:
                results = db.search_contracts(company_name='', contract_number=search_term)
            
            # Clear previous results from tree and data store
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.contracts_data.clear()

            if not results:
                Messagebox.show_info("Không tìm thấy hợp đồng nào phù hợp", "Thông báo")
                self.status_label.config(text="Không tìm thấy hợp đồng nào phù hợp", style="Error.TLabel")
                return

            # Populate treeview and store full data for later use
            for contract in results:
                details = contract['details']
                hd_id = details['id']
                self.contracts_data[str(hd_id)] = contract  # Store by ID as string
                
                self.tree.insert(
                    "", 
                    "end", 
                    text=str(hd_id),  # Store the contract ID in the hidden text field
                    values=(
                        details.get('soHopDong', ''),
                        details.get('tenCongTy', ''),
                        format_date(details.get('HLBH_tu', '')),
                        format_date(details.get('HLBH_den', ''))
                    )
                )
            
            self.status_label.config(text=f"Tìm thấy {len(results)} hợp đồng phù hợp", style="Success.TLabel")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Lỗi khi tìm kiếm hợp đồng: {error_details}")
            Messagebox.show_error(f"Lỗi khi thực hiện tìm kiếm: {e}", "Lỗi")
            self.status_label.config(text="Đã xảy ra lỗi khi tìm kiếm", style="Error.TLabel")
    
    # ---------------- Tooltip helpers -----------------
    def _on_tree_motion(self, event):
        """Show/update tooltip when hovering over a Treeview row."""
        row_id = self.tree.identify_row(event.y)
        if row_id != self._current_hover_row:
            self._current_hover_row = row_id
            if not row_id:
                self._hide_tooltip()
                return
            # Get data for tooltip
            values = self.tree.item(row_id, "values")
            if not values:
                self._hide_tooltip()
                return
            card_no = values[0]  # "Số HĐ" column value
            company = values[1]  # "Công ty" column value
            text = f"Số thẻ: {card_no}\nCông ty: {company}"
            self._show_tooltip(event.x_root + 20, event.y_root + 10, text)
        else:
            # Reposition existing tooltip
            if self._tooltip_window and self._tooltip_window.winfo_exists():
                self._tooltip_window.geometry(f"+{event.x_root + 20}+{event.y_root + 10}")

    def _show_tooltip(self, x, y, text):
        self._hide_tooltip()
        self._tooltip_window = tw = tk.Toplevel(self.tree)
        tw.wm_overrideredirect(True)
        tw.attributes("-topmost", True)
        label = ttk.Label(tw, text=text, padding=5, bootstyle="light")
        label.pack()
        tw.geometry(f"+{x}+{y}")

    def _hide_tooltip(self):
        if self._tooltip_window and self._tooltip_window.winfo_exists():
            self._tooltip_window.destroy()
        self._tooltip_window = None
        self._current_hover_row = None

    # ---------------- Existing methods -----------------
    def on_contract_select(self, event):
        """Handle contract selection from search results."""
        try:
            tree = event.widget
            selected_items = tree.selection()
            
            if not selected_items:
                return
                
            selected_item = selected_items[0]
            contract_id = tree.item(selected_item, "text") # Get ID from hidden text
            
            if not contract_id or contract_id not in self.contracts_data:
                print(f"Error: Contract ID '{contract_id}' not found in stored data.")
                return
                
            # Retrieve the full contract data from our stored dictionary
            self.current_contract = self.contracts_data[contract_id]
            
            # Update contract info frame with detailed data
            self.update_contract_info()

            # Populate and enable the edit form
            self._populate_forms()
            self.toggle_forms(True)
            
            # Update status bar
            self.status_label.config(
                text=f"Đã chọn hợp đồng: {self.current_contract['details']['soHopDong']}",
                style="Success.TLabel"
            )
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            Messagebox.show_error(f"Không thể chọn hợp đồng: {e}", "Lỗi")
            self.status_label.config(text="Đã xảy ra lỗi khi chọn hợp đồng", style="Error.TLabel")
    
    def update_contract_info(self):
        """Update the contract information display"""
        if not self.current_contract:
            return
            
        try:
            # Clear previous widgets
            for widget in self.contract_info_frame.winfo_children():
                widget.destroy()
            
            # Configure grid for contract info
            self.contract_info_frame.columnconfigure(1, weight=1)
            
            # Add contract details with better formatting
            row = 0
            
            # Header
            header = ttk.Label(
                self.contract_info_frame,
                text="THÔNG TIN HỢP ĐỒNG",
                font=("Arial", 10, "bold"),
                foreground="#d32f2f"
            )
            header.grid(row=row, column=0, columnspan=2, pady=(0, 10), sticky="n")
            row += 1
            
            # Separator
            ttk.Separator(self.contract_info_frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 5))
            row += 1
            
            details = self.current_contract['details']
            
            # Display fields
            tinh_trang_text = "Hoạt động" if details.get('isActive') else "Không hoạt động"
            fields = {
                "Số HĐ:": details.get('soHopDong', 'N/A'),
                "Công ty:": details.get('tenCongTy', 'N/A'),
                "Hiệu lực:": format_date_range(details.get('HLBH_tu'), details.get('HLBH_den')),
                "Tình trạng:": tinh_trang_text
            }
            
            for label_text, value_text in fields.items():
                label = ttk.Label(self.contract_info_frame, text=label_text, font=("Arial", 9, "bold"))
                label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
                
                value = ttk.Label(self.contract_info_frame, text=value_text, wraplength=180) # Wraplength for long company names
                value.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                row += 1
                
        except Exception as e:
            import traceback
            print(f"Error updating contract info: {traceback.format_exc()}")
            Messagebox.show_error(f"Lỗi hiển thị thông tin hợp đồng: {e}", "Lỗi")

    def _create_notebook_panels(self):
        """Creates the notebook with tabs for editing different contract aspects."""
        self.notebook = ttk.Notebook(self.main_container, bootstyle="info")
        self.notebook.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(10, 0))

        # Create frames for each tab
        self.tab_general = ttk.Frame(self.notebook, padding=10)
        self.tab_waiting = ttk.Frame(self.notebook, padding=10)
        self.tab_special = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_general, text="  Thông tin chung  ")
        self.notebook.add(self.tab_waiting, text="  Thời gian chờ  ")
        self.notebook.add(self.tab_special, text="  Thẻ đặc biệt  ")

        # Populate each tab with widgets
        self._create_general_info_tab()
        self._create_waiting_periods_tab()
        self._create_special_cards_tab()

    def _create_general_info_tab(self):
        """Creates the widgets for the 'General Info' editing tab."""
        frame = self.tab_general
        frame.columnconfigure(1, weight=1)

        # Create StringVars for fields
        self.soHopDong_var = tk.StringVar()
        self.tenCongTy_var = tk.StringVar()
        self.HLBH_tu_var = tk.StringVar()
        self.HLBH_den_var = tk.StringVar()
        self.coPay_var = tk.StringVar()

        # Create widgets
        self.edit_fields = {
            "Số Hợp Đồng:": ttk.Entry(frame, textvariable=self.soHopDong_var),
            "Tên Công Ty:": ttk.Entry(frame, textvariable=self.tenCongTy_var),
            "Hiệu lực từ (DD/MM/YYYY):": ttk.Entry(frame, textvariable=self.HLBH_tu_var),
            "Hiệu lực đến (DD/MM/YYYY):": ttk.Entry(frame, textvariable=self.HLBH_den_var),
            "Đồng chi trả (%):": ttk.Entry(frame, textvariable=self.coPay_var),
        }

        for i, (label_text, widget) in enumerate(self.edit_fields.items()):
            ttk.Label(frame, text=label_text).grid(row=i, column=0, sticky="w", pady=3, padx=5)
            widget.grid(row=i, column=1, sticky="ew", pady=3, padx=5)

        # Save button for this tab
        self.save_general_info_button = ttk.Button(
            frame,
            text="Lưu thay đổi thông tin chung",
            command=self._save_general_info_changes,
            bootstyle="success-outline"
        )
        self.save_general_info_button.grid(row=len(self.edit_fields), column=0, columnspan=2, pady=(15, 5))

    def _create_waiting_periods_tab(self):
        """Creates the dynamic row UI for the 'Waiting Periods' editing tab."""
        # Container for dynamic rows
        self.dynamic_rows_frame = ttk.Frame(self.tab_waiting)
        self.dynamic_rows_frame.pack(fill="x", expand=True, pady=5, padx=5)
        self.dynamic_rows_frame.columnconfigure(0, weight=1)

        # Save button for this tab
        self.save_waiting_periods_button = ttk.Button(
            self.tab_waiting,
            text="Lưu thay đổi Thời gian chờ",
            command=self._save_waiting_periods_changes,
            bootstyle="success-outline"
        )
        self.save_waiting_periods_button.pack(pady=(10, 5))

    def _create_special_cards_tab(self):
        """Creates the dynamic row UI for the 'Special Cards' editing tab."""
        # Container for header and dynamic rows
        container = ttk.Frame(self.tab_special)
        container.pack(fill="both", expand=True, pady=5, padx=5)
        container.columnconfigure(0, weight=1) # Name
        container.columnconfigure(1, weight=1) # Card Number
        container.columnconfigure(2, weight=2) # Notes

        # Header
        header_frame = ttk.Frame(container)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=1)
        header_frame.columnconfigure(2, weight=2)
        ttk.Label(header_frame, text="Tên NĐBH", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky='w')
        ttk.Label(header_frame, text="Số thẻ", font=("Arial", 9, "bold")).grid(row=0, column=1, sticky='w')
        ttk.Label(header_frame, text="Ghi chú", font=("Arial", 9, "bold")).grid(row=0, column=2, sticky='w')

        # Container for dynamic rows
        self.special_cards_container = ttk.Frame(container)
        self.special_cards_container.grid(row=1, column=0, sticky="nsew", columnspan=3)
        self.special_cards_container.columnconfigure(0, weight=1)

        # Save button for this tab
        self.save_special_cards_button = ttk.Button(
            self.tab_special,
            text="Lưu thay đổi Thẻ đặc biệt",
            command=self._save_special_cards_changes,
            bootstyle="success-outline"
        )
        self.save_special_cards_button.pack(pady=(10, 5))

    def _save_special_cards_changes(self):
        """Handles the save button click for the Special Cards tab."""
        self._save_special_cards()

    def _populate_forms(self):
        """Populates all forms in the notebook with data from the selected contract."""
        if not self.current_contract:
            return
        
        # 1. Populate General Info Tab
        details = self.current_contract['details']
        self.soHopDong_var.set(details.get('soHopDong', ''))
        self.tenCongTy_var.set(details.get('tenCongTy', ''))
        self.HLBH_tu_var.set(format_date(details.get('HLBH_tu', '')))
        self.HLBH_den_var.set(format_date(details.get('HLBH_den', '')))
        self.coPay_var.set(details.get('coPay', ''))
        
        # 2. Populate Waiting Periods Tab
        self._populate_waiting_periods_tab()
        
        # 3. Populate Special Cards Tab
        self._populate_special_cards_tab()

    def _populate_waiting_periods_tab(self):
        """Clears and populates the waiting periods tab with contract data."""
        # Clear existing rows
        for row_frame in self.waiting_time_rows:
            row_frame.destroy()
        self.waiting_time_rows.clear()

        waiting_periods = self.current_contract.get('waiting_periods', [])

        if not waiting_periods:
            # Add a single blank row if there are no existing periods
            self._add_waiting_time_row()
        else:
            # Create a row for each existing period
            for period in waiting_periods:
                self._add_waiting_time_row(cho_id=period.get('cho_id'), value=period.get('value'))

        self._update_plus_minus_buttons()

    def _save_general_info_changes(self):
        """Saves the changes made in the general info tab."""
        # TODO: Implement validation and database update logic
        Messagebox.show_info("Chức năng đang được phát triển.", "Thông báo")
        print("Saving general info changes (not yet implemented)...")

    def _save_waiting_periods_changes(self):
        """Saves the changes made in the waiting periods tab."""
        if not self.current_contract:
            Messagebox.show_warning("Vui lòng chọn một hợp đồng trước khi lưu.", "Chưa chọn hợp đồng")
            return

        hopdong_id = self.current_contract['details']['id']
        
        new_waiting_periods = []
        try:
            for row_frame in self.waiting_time_rows:
                widgets = row_frame.winfo_children()
                if len(widgets) < 2: continue # Skip if row is malformed
                
                combo = widgets[0]
                value_entry = widgets[1]

                loai_cho_text = combo.get()
                value = value_entry.get().strip()

                if not loai_cho_text:
                    # Skip empty rows that haven't been filled out
                    continue
                
                if not value:
                    Messagebox.show_warning(f"Vui lòng nhập giá trị cho '{loai_cho_text}'.", "Thiếu thông tin")
                    return # Stop to let the user fix it

                cho_id = self.waiting_time_text_to_id_map.get(loai_cho_text)
                if cho_id is None:
                    Messagebox.show_error(f"Loại thời gian chờ không hợp lệ: '{loai_cho_text}'.", "Lỗi dữ liệu")
                    return

                new_waiting_periods.append({
                    'cho_id': cho_id,
                    'gia_tri': value
                })
            
            # Call the database function to update
            db.update_contract_waiting_periods(hopdong_id, new_waiting_periods)
            
            # Update the local data store to reflect the change
            self.current_contract['waiting_periods'] = new_waiting_periods
            
            Messagebox.show_info("Cập nhật thời gian chờ thành công!", "Thành công")
            self.status_label.config(text=f"Đã cập nhật thời gian chờ cho hợp đồng ID: {hopdong_id}", style="Success.TLabel")

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            Messagebox.show_error(f"Lỗi khi lưu thời gian chờ: {e}", "Lỗi")
            self.status_label.config(text="Lỗi khi lưu thời gian chờ.", style="Error.TLabel")

    def toggle_forms(self, enabled):
        """Enables or disables all input widgets in the notebook."""
        state = "normal" if enabled else "disabled"
        
        try:
            for i in range(self.notebook.index("end")):
                self.notebook.tab(i, state=state)
        except tk.TclError:
            pass

        # Toggle general info tab widgets
        for widget in self.edit_fields.values():
            widget.config(state=state)
        self.save_general_info_button.config(state=state)

        # Toggle waiting periods tab widgets
        for row_frame in self.waiting_time_rows:
            for widget in row_frame.winfo_children():
                try:
                    widget.config(state=state if not isinstance(widget, ttk.Button) else "normal" if enabled else "disabled")
                except tk.TclError:
                    pass
        self.save_waiting_periods_button.config(state=state)

        # Toggle special cards tab widgets
        for row_frame in self.special_card_rows:
            for widget in row_frame.winfo_children():
                try:
                    widget.config(state=state if not isinstance(widget, ttk.Button) else "normal" if enabled else "disabled")
                except tk.TclError:
                    pass
        self.save_special_cards_button.config(state=state)

    def _fetch_data(self):
        """Lấy dữ liệu cần thiết từ database."""
        try:
            waiting_times_data = db.get_all_waiting_times()
            self.waiting_time_id_to_text_map = {
                item['id']: f"{item['loai_cho']} - {item['mo_ta']}" for item in waiting_times_data
            }
            self.waiting_time_text_to_id_map = {
                v: k for k, v in self.waiting_time_id_to_text_map.items()
            }
            self.waiting_time_options = list(self.waiting_time_text_to_id_map.keys())
        except Exception as e:
            Messagebox.show_error(f"Không thể tải dữ liệu thời gian chờ: {e}", "Lỗi Database")
            self.waiting_time_id_to_text_map = {}
            self.waiting_time_text_to_id_map = {}
            self.waiting_time_options = []

    def _populate_waiting_periods_tab(self):
        """Clears and populates the waiting periods tab with contract data."""
        for row_frame in self.waiting_time_rows:
            row_frame.destroy()
        self.waiting_time_rows.clear()

        waiting_periods = self.current_contract.get('waiting_periods', [])
        if not waiting_periods:
            self._add_waiting_time_row()
        else:
            for period in waiting_periods:
                self._add_waiting_time_row(cho_id=period.get('cho_id'), value=period.get('gia_tri'))
        self._update_plus_minus_buttons()

    def _add_waiting_time_row(self, cho_id=None, value=""):
        """Thêm một hàng mới cho việc nhập thời gian chờ."""
        row_frame = ttk.Frame(self.dynamic_rows_frame)
        row_frame.grid(row=len(self.waiting_time_rows), column=0, sticky="ew", pady=2)
        row_frame.columnconfigure(0, weight=1)

        combo = ttk.Combobox(row_frame, values=self.waiting_time_options, state="readonly")
        combo.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        if cho_id:
            combo.set(self.waiting_time_id_to_text_map.get(cho_id, ''))

        value_entry = ttk.Entry(row_frame, width=15)
        value_entry.grid(row=0, column=1, sticky="w", padx=(0, 5))
        value_entry.insert(0, str(value))

        add_button = ttk.Button(row_frame, text="+", width=3, command=self._add_waiting_time_row)
        add_button.grid(row=0, column=2, padx=(0, 2))

        remove_button = ttk.Button(row_frame, text="-", width=3, command=lambda rf=row_frame: self._remove_waiting_time_row(rf))
        remove_button.grid(row=0, column=3)

        self.waiting_time_rows.append(row_frame)
        self._update_plus_minus_buttons()

    def _remove_waiting_time_row(self, row_frame):
        """Xóa một hàng thời gian chờ."""
        row_frame.destroy()
        self.waiting_time_rows = [r for r in self.waiting_time_rows if r.winfo_exists()]
        self._update_plus_minus_buttons()

    def _update_plus_minus_buttons(self):
        """Cập nhật trạng thái của các nút +/- cho tab Thời gian chờ."""
        num_rows = len(self.waiting_time_rows)
        if num_rows == 0:
            self._add_waiting_time_row()
            return

        for i, frame in enumerate(self.waiting_time_rows):
            widgets = frame.winfo_children()
            if len(widgets) < 4: continue
            add_button, remove_button = widgets[2], widgets[3]
            add_button.grid_remove()
            remove_button.grid()

        last_row_widgets = self.waiting_time_rows[-1].winfo_children()
        if last_row_widgets:
            last_row_widgets[2].grid()

        if num_rows == 1:
            first_row_widgets = self.waiting_time_rows[0].winfo_children()
            if first_row_widgets:
                first_row_widgets[3].grid_remove()

    def _populate_special_cards_tab(self):
        """Clears and populates the special cards tab with contract data."""
        for row_frame in self.special_card_rows:
            row_frame.destroy()
        self.special_card_rows.clear()

        special_cards = self.current_contract.get('special_cards', [])
        if not special_cards:
            self._add_special_card_row()
        else:
            for card in special_cards:
                self._add_special_card_row(card)
        self._update_special_card_buttons()

    def _add_special_card_row(self, card_data=None):
        """Adds a new row for a special card entry."""
        if card_data is None:
            card_data = {}

        row_frame = ttk.Frame(self.special_cards_container)
        row_frame.pack(fill="x", pady=2)

        holder_name_entry = ttk.Entry(row_frame, width=30)
        holder_name_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
        holder_name_entry.insert(0, str(card_data.get('ten_NDBH', '')))

        card_number_entry = ttk.Entry(row_frame, width=30)
        card_number_entry.pack(side="left", padx=5, fill="x", expand=True)
        card_number_entry.insert(0, str(card_data.get('so_the', '')))

        notes_entry = ttk.Entry(row_frame, width=40)
        notes_entry.pack(side="left", padx=5, fill="x", expand=True)
        notes_entry.insert(0, str(card_data.get('ghi_chu', '')))

        add_button = ttk.Button(row_frame, text="+", width=3, command=self._add_special_card_row)
        add_button.pack(side="left", padx=(5, 2))

        remove_button = ttk.Button(row_frame, text="-", width=3, command=lambda rf=row_frame: self._remove_special_card_row(rf))
        remove_button.pack(side="left")

        self.special_card_rows.append(row_frame)
        self._update_special_card_buttons()

    def _remove_special_card_row(self, row_frame):
        """Removes a special card row."""
        row_frame.destroy()
        self.special_card_rows = [r for r in self.special_card_rows if r.winfo_exists()]
        self._update_special_card_buttons()

    def _update_special_card_buttons(self):
        """Updates the +/- buttons for the special cards tab."""
        num_rows = len(self.special_card_rows)
        if num_rows == 0:
            self._add_special_card_row()
            return

        for i, frame in enumerate(self.special_card_rows):
            widgets = frame.winfo_children()
            if len(widgets) < 5: continue
            add_button, remove_button = widgets[3], widgets[4]
            add_button.pack_forget()
            remove_button.pack()

        last_row_widgets = self.special_card_rows[-1].winfo_children()
        if last_row_widgets:
            last_row_widgets[3].pack(side="left", padx=(5, 2))

        if num_rows == 1:
            first_row_widgets = self.special_card_rows[0].winfo_children()
            if first_row_widgets:
                first_row_widgets[4].pack_forget()

    def _save_special_cards(self):
        """Saves the special cards data for the current contract."""
        if not self.current_contract:
            return

        hopdong_id = self.current_contract['details']['id']
        new_special_cards = []
        try:
            for row_frame in self.special_card_rows:
                widgets = row_frame.winfo_children()
                if len(widgets) < 3: continue

                name = widgets[0].get().strip()
                number = widgets[1].get().strip()
                notes = widgets[2].get().strip()

                if not name and not number and not notes:
                    continue  # Skip completely empty rows

                if not name or not number:
                    Messagebox.show_warning("Vui lòng nhập đầy đủ Tên NĐBH và Số thẻ.", "Thiếu thông tin")
                    return

                new_special_cards.append({
                    'ten_NDBH': name,
                    'so_the': number,
                    'ghi_chu': notes
                })

            db.update_contract_special_cards(hopdong_id, new_special_cards)
            self.current_contract['special_cards'] = new_special_cards
            Messagebox.show_info("Cập nhật thẻ đặc biệt thành công!", "Thành công")
            self.status_label.config(text=f"Đã cập nhật thẻ đặc biệt cho hợp đồng ID: {hopdong_id}", style="Success.TLabel")

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            Messagebox.show_error(f"Lỗi khi lưu thẻ đặc biệt: {e}", "Lỗi")
            self.status_label.config(text="Lỗi khi lưu thẻ đặc biệt.", style="Error.TLabel")
