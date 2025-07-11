import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
import database as db
import datetime  # TODO: Remove if no longer used elsewhere
from utils.date_utils import format_date, format_date_range
from utils.text_utils import remove_accents_and_lowercase




class AddBenefitFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_contract = None
        self.contracts_data = {}
        
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
            text="THÊM QUYỀN LỢI HỢP ĐỒNG", 
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
        
        # Cấu hình dòng
        self.main_container.rowconfigure(0, weight=1)      # Dòng trên (tìm kiếm, kết quả, thông tin)
        self.main_container.rowconfigure(1, weight=0)      # Dòng dưới (form thêm quyền lợi)
        
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
        
        # ========== Panel 4: Add Benefit Form ==========
        self.add_benefit_frame = ttk.LabelFrame(
            self.main_container,
            text="Thêm quyền lợi mới",
            padding=40,
            bootstyle="info"
        )
        # Make it span all 3 columns
        self.add_benefit_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        
        # Configure the form frame with 6 equal columns
        for i in range(6):
            self.add_benefit_frame.columnconfigure(i, weight=1, uniform='benefit_cols')
        
        # Create a frame for the benefit type selection (6 columns)
        self.benefit_type_frame = ttk.Frame(self.add_benefit_frame)
        self.benefit_type_frame.grid(row=0, column=0, columnspan=6, sticky="nsew", pady=(0, 10))
        
        # Create a frame for the benefit details (spans all columns)
        self.benefit_details_frame = ttk.Frame(self.add_benefit_frame)
        self.benefit_details_frame.grid(row=1, column=0, columnspan=6, sticky="nsew")
        
        # Benefit Type selection using Radiobuttons
        ttk.Label(self.benefit_type_frame, text="Nhóm quyền lợi:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky='w')
        self.benefit_group_var = tk.StringVar()

        # Container frame for radiobuttons
        self.benefit_groups_frame = ttk.Frame(self.benefit_type_frame)
        self.benefit_groups_frame.grid(row=0, column=1, columnspan=5, sticky='w')

        # Load radiobuttons from DB
        self.load_benefit_groups()
        
        # Configure benefit details form
        self.setup_benefit_details_form()

        # Submit Button
        submit_button = ttk.Button(self.add_benefit_frame, text="Lưu quyền lợi", bootstyle="success-outline", command=self.submit_benefit)
        submit_button.grid(row=2, column=0, columnspan=6, pady=(15, 5))
        
        # Status bar (use grid instead of pack)
        self.rowconfigure(2, weight=0)
        self.status_frame = ttk.Frame(self, height=22)
        self.status_frame.grid(row=2, column=0, sticky="ew")
        self.status_label = ttk.Label(
            self.status_frame, 
            text="Vui lòng tìm kiếm hợp đồng để thêm quyền lợi", 
            style="Info.TLabel",
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=5, pady=1)
        
        # Initialize form state
        self.toggle_benefit_form(False)
        
    def toggle_benefit_form(self, enabled):
        """Enable or disable the benefit form based on whether a contract is selected"""
        state = "normal" if enabled and self.current_contract else "disabled"
        
        # Toggle form fields
        self.benefit_name_entry.config(state=state)
        self.benefit_limit_entry.config(state=state)
        self.benefit_desc_text.config(state=state)
        
        # Update status message
        if enabled and self.current_contract:
            contract_number = self.current_contract['details'].get('soHopDong', 'N/A')
            self.status_label.config(
                text=f"Đang thêm quyền lợi cho hợp đồng: {contract_number}",
                style="Success.TLabel"
            )
        else:
            self.status_label.config(
                text="Vui lòng tìm kiếm và chọn hợp đồng để thêm quyền lợi",
                style="Info.TLabel"
            )
            
        # Clear form when disabled
        if not enabled:
            self.benefit_name_entry.delete(0, tk.END)
            self.benefit_limit_entry.delete(0, tk.END)
            self.benefit_desc_text.delete("1.0", tk.END)
    
    def search_contract(self):
        """Searches for contracts using the new database function."""
        search_term = self.search_var.get().strip()
        if not search_term:
            Messagebox.show_warning("Vui lòng nhập số hợp đồng hoặc tên công ty để tìm kiếm", "Cảnh báo")
            return

        try:
            # Clear previous results from tree and data store
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.contracts_data.clear()

            # Xử lý chuỗi tìm kiếm để tìm không dấu
            search_term_no_accent = remove_accents_and_lowercase(search_term)

            # Tìm kiếm dựa trên cả tên công ty (có dấu và không dấu) và số hợp đồng
            results = db.search_contracts(
                company_name=search_term,
                contract_number=search_term,
                status='all',
                company_name_no_accent=search_term_no_accent
            )
                
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
            
            # Enable the benefit submission form
            self.toggle_benefit_form(True)
            
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
            header.grid(row=row, column=0, columnspan=2, pady=(0, 10), sticky="w")
            row += 1
            
            # Contract details
            contract_details = self.current_contract['details']
            ttk.Label(
                self.contract_info_frame,
                text="Số HD:",
                font=("Arial", 9, "bold")
            ).grid(row=row, column=0, sticky="e", padx=5, pady=2)
            ttk.Label(
                self.contract_info_frame,
                text=contract_details["soHopDong"],
                font=("Arial", 9)
            ).grid(row=row, column=1, sticky="w", padx=5, pady=2)
            row += 1
            
            ttk.Label(
                self.contract_info_frame,
                text="Tên cty:",
                font=("Arial", 9, "bold")
            ).grid(row=row, column=0, sticky="e", padx=5, pady=2)
            ttk.Label(
                self.contract_info_frame,
                text=contract_details["tenCongTy"],
                font=("Arial", 9),
                wraplength=250
            ).grid(row=row, column=1, sticky="w", padx=5, pady=2)
            row += 1
            
            # Định dạng ngày hiệu lực hợp đồng
            from_date = contract_details.get('HLBH_tu')
            to_date = contract_details.get('HLBH_den')
            date_range = format_date_range(from_date, to_date)

                
            ttk.Label(
                self.contract_info_frame,
                text="Hiệu lực:",
                style="Bold.TLabel"
            ).grid(row=row, column=0, sticky="e", padx=5, pady=2)
            ttk.Label(
                self.contract_info_frame,
                text=date_range,
                style="Normal.TLabel"
            ).grid(row=row, column=1, sticky="w", padx=5, pady=2)
            row += 1
            
            # Thêm dấu phân cách
            ttk.Separator(
                self.contract_info_frame,
                orient="horizontal"
            ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
            
        except Exception as e:
            Messagebox.show_error(f"Không thể cập nhật thông tin hợp đồng: {str(e)}", "Lỗi")
    

    
    def load_benefit_groups(self):
        """Loads benefit groups from the database into the combobox."""
        try:
            groups = db.get_all_benefit_groups()
            self.benefit_groups_map = {g['ten_nhom']: g['id'] for g in groups}

            # Clear any existing radiobuttons
            for child in self.benefit_groups_frame.winfo_children():
                child.destroy()

            # Create radiobutton for each group
            for idx, name in enumerate(self.benefit_groups_map.keys()):
                rb = ttk.Radiobutton(
                    self.benefit_groups_frame,
                    text=name,
                    variable=self.benefit_group_var,
                    value=name
                )
                rb.grid(row=0, column=idx, padx=2, pady=2, sticky='w')
        except Exception as e:
            Messagebox.show_error(f"Không thể tải danh sách nhóm quyền lợi: {e}", "Lỗi")

    def setup_benefit_details_form(self):
        """Creates the form for benefit details."""
        # Configure grid
        self.benefit_details_frame.columnconfigure(1, weight=1)

        # Labels
        ttk.Label(self.benefit_details_frame, text="Tên quyền lợi:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(self.benefit_details_frame, text="Hạn mức:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(self.benefit_details_frame, text="Mô tả chi tiết:").grid(row=2, column=0, padx=5, pady=5, sticky="ne")
        
        # Entry fields
        self.benefit_name_entry = ttk.Entry(self.benefit_details_frame, width=40)
        self.benefit_limit_entry = ttk.Entry(self.benefit_details_frame, width=40)
        self.benefit_desc_text = ttk.Text(self.benefit_details_frame, height=4, wrap=tk.WORD, font=("Segoe UI", 10))
        
        # Layout
        self.benefit_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.benefit_limit_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.benefit_desc_text.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
        
        self.benefit_details_frame.rowconfigure(2, weight=1)

    def submit_benefit(self):
        """Validates form data and submits the new benefit to the database."""
        if not self.current_contract:
            Messagebox.show_warning("Vui lòng chọn một hợp đồng trước khi thêm quyền lợi.", "Cảnh báo")
            return

        # --- Get and validate data ---
        group_name = self.benefit_group_var.get()
        benefit_name = self.benefit_name_entry.get().strip()
        benefit_limit = self.benefit_limit_entry.get().strip()
        benefit_desc = self.benefit_desc_text.get("1.0", tk.END).strip()

        if not all([group_name, benefit_name, benefit_limit]):
            Messagebox.show_warning("Vui lòng điền đầy đủ các trường bắt buộc: Nhóm, Tên, và Giới hạn quyền lợi.", "Thiếu thông tin")
            return

        try:
            group_id = self.benefit_groups_map[group_name]
            contract_id = self.current_contract['details']['id']

            # --- Add to DB ---
            success = db.add_benefit(contract_id, group_id, benefit_name, benefit_limit, benefit_desc)

            if success:
                Messagebox.show_info(f"Đã thêm quyền lợi '{benefit_name}' vào hợp đồng.", "Thành công")
                # Clear form for next entry
                self.benefit_name_entry.delete(0, tk.END)
                self.benefit_limit_entry.delete(0, tk.END)
                self.benefit_desc_text.delete("1.0", tk.END)
                self.benefit_group_var.set('')
                self.benefit_name_entry.focus()
            else:
                Messagebox.show_error("Không thể lưu quyền lợi vào cơ sở dữ liệu.", "Lỗi")

        except KeyError:
            Messagebox.show_error("Nhóm quyền lợi không hợp lệ.", "Lỗi")
        except Exception as e:
            Messagebox.show_error(f"Đã xảy ra lỗi khi lưu quyền lợi: {e}", "Lỗi")
