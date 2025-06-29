import tkinter as tk
from tkinter import ttk, messagebox, font
import database as db
import datetime  # TODO: Remove if no longer used elsewhere
from utils.date_utils import format_date, format_date_range

class AddBenefitFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_contract = None
        
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
        search_frame = ttk.LabelFrame(self.main_container, text="Tìm kiếm hợp đồng", padding=5)
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
            command=self.search_contract
        )
        search_btn.pack(side="right", padx=(0, 0))
        
        # Configure row weights for search frame
        search_frame.rowconfigure(0, weight=0)
        search_frame.rowconfigure(1, weight=0)
        
        # ========== Panel 2: Search Results Panel ==========
        self.results_frame = ttk.LabelFrame(
            self.main_container, 
            text="Kết quả tìm kiếm", 
            padding=5
        )
        self.results_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=(0, 5))
        self.results_frame.columnconfigure(0, weight=1)
        self.results_frame.rowconfigure(0, weight=1)
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
        
        # Đặt kích thước tối thiểu cho khung kết quả tìm kiếm (nhỏ gọn hơn)
        self.results_frame.columnconfigure(0, weight=1, minsize=500)
        
        # Cho phép Treeview mở rộng tối đa
        self.tree.pack_configure(expand=True, fill=tk.BOTH)
        
        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_contract_select)
        
        # ========== Panel 3: Contract Info Panel ==========
        self.contract_info_frame = ttk.LabelFrame(
            self.main_container, 
            text="Thông tin hợp đồng", 
            padding=5
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
            padding=40
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
        
        # Load benefit types from database
        self.load_benefit_types()
        
        # Configure benefit details form
        self.setup_benefit_details_form()
        
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
            contract_number = self.current_contract.get('soHopDong', 'N/A')
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
        """Tìm kiếm hợp đồng theo số hợp đồng hoặc tên công ty"""
        search_term = self.search_var.get().strip()
        
        if not search_term:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập số hợp đồng hoặc tên công ty để tìm kiếm")
            return
            
        conn = None
        try:

            # Tìm kiếm hợp đồng phù hợp với từ khóa tìm kiếm
            query = """
                SELECT id, soHopDong, tenCongTy, HLBH_tu, HLBH_den 
                FROM hopdong_baohiem 
                WHERE (soHopDong LIKE ? OR tenCongTy LIKE ?) 
                AND isActive = 1
                ORDER BY HLBH_den DESC
                LIMIT 100
            """
            search_pattern = f"%{search_term}%"
            
            # In thông tin debug
            print(f"Đang tìm kiếm với từ khóa: {search_pattern}")
            
            try:
                conn = db.get_db_connection()
                print("Đã kết nối đến cơ sở dữ liệu")
                
                cursor = conn.cursor()
                cursor.execute(query, (search_pattern, search_pattern))
                results = cursor.fetchall()
                
                print(f"Tìm thấy {len(results)} kết quả")
                
                if not results:
                    messagebox.showinfo("Thông báo", "Không tìm thấy hợp đồng nào phù hợp")
                    self.status_label.config(
                        text="Không tìm thấy hợp đồng nào phù hợp", 
                        style="Error.TLabel"
                    )
                    return

                # Có kết quả mới → xoá danh sách cũ rồi hiển thị
                for item in self.tree.get_children():
                    self.tree.delete(item)

                # Thêm kết quả vào treeview với định dạng ngày dd/mm/yyyy
                for row in results:
                    self.tree.insert(
                        "", 
                        "end", 
                        text=str(row[0]),  # Lưu ID hợp đồng
                        values=(
                            row[1],                 # soHopDong
                            row[2],                 # tenCongTy
                            format_date(row[3]),    # HLBH_tu
                            format_date(row[4])     # HLBH_den
                        )
                    )
                
                self.status_label.config(
                    text=f"Tìm thấy {len(results)} hợp đồng phù hợp", 
                    style="Success.TLabel"
                )
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Lỗi khi thực hiện truy vấn: {error_details}")
                messagebox.showerror("Lỗi", f"Lỗi khi thực hiện tìm kiếm: {str(e)}\n\nChi tiết lỗi đã được ghi vào console.")
                self.status_label.config(
                    text="Đã xảy ra lỗi khi tìm kiếm", 
                    style="Error.TLabel"
                )
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Lỗi không xác định: {error_details}")
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi không xác định: {str(e)}")
            self.status_label.config(
                text="Đã xảy ra lỗi không xác định", 
                style="Error.TLabel"
            )
            
        finally:
            if conn:
                try:
                    conn.close()
                    print("Đã đóng kết nối cơ sở dữ liệu")
                except Exception as e:
                    print(f"Lỗi khi đóng kết nối: {str(e)}")
    
    def on_contract_select(self, event):
        """Handle contract selection from search results"""
        try:
            tree = event.widget
            selected_items = tree.selection()
            
            if not selected_items:
                return
                
            selected_item = selected_items[0]
            item_values = tree.item(selected_item, "values")
            
            if not item_values:
                return
                
            # Store selected contract info
            self.current_contract = {
                "id": tree.item(selected_item, "text"),  # Store the contract ID
                "soHopDong": item_values[0],
                "tenCongTy": item_values[1],
                "HLBH_tu": item_values[2],
                "HLBH_den": item_values[3]
            }
            
            # Highlight the selected row
            for item in tree.selection():
                tree.selection_remove(item)
            tree.selection_add(selected_item)
            tree.focus(selected_item)
            
            # Update contract info frame
            self.update_contract_info()
            
            # Enable the form
            self.toggle_benefit_form(True)
            
            # Update status
            self.status_label.config(
                text=f"Đã chọn hợp đồng: {self.current_contract['soHopDong']}",
                style="Success.TLabel"
            )
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể chọn hợp đồng: {str(e)}")
            self.status_label.config(
                text="Đã xảy ra lỗi khi chọn hợp đồng",
                style="Error.TLabel"
            )
    
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
            ttk.Label(
                self.contract_info_frame,
                text="Số HD:",
                font=("Arial", 9, "bold")
            ).grid(row=row, column=0, sticky="e", padx=5, pady=2)
            ttk.Label(
                self.contract_info_frame,
                text=self.current_contract["soHopDong"],
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
                text=self.current_contract["tenCongTy"],
                font=("Arial", 9),
                wraplength=250
            ).grid(row=row, column=1, sticky="w", padx=5, pady=2)
            row += 1
            
            # Định dạng ngày hiệu lực hợp đồng
            from_date = self.current_contract.get('HLBH_tu')
            to_date = self.current_contract.get('HLBH_den')
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
            messagebox.showerror("Lỗi", f"Không thể cập nhật thông tin hợp đồng: {str(e)}")
            self.status_label.config(
                text="Đã xảy ra lỗi khi cập nhật thông tin hợp đồng",
                style="Error.TLabel"
            )
    
    def load_benefit_types(self):
        """Tải danh sách các nhóm quyền lợi từ cơ sở dữ liệu"""
        try:
            conn = db.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ten_nhom, mo_ta FROM nhom_quyenloi ORDER BY id")
            benefit_types = cursor.fetchall()
            
            # Tạo các nút radio cho từng nhóm quyền lợi
            self.benefit_type_var = tk.StringVar()
            
            for i, (type_id, ten_nhom, mo_ta) in enumerate(benefit_types):
                btn = ttk.Radiobutton(
                    self.benefit_type_frame,
                    text=ten_nhom,
                    variable=self.benefit_type_var,
                    value=type_id,
                    command=self.on_benefit_type_select
                )
                btn.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
                
                # Tooltip cho mô tả chi tiết
                tooltip = f"{ten_nhom}"
                if mo_ta:
                    tooltip += f"\n{mo_ta}"
                self.create_tooltip(btn, tooltip)
                
                # Chọn nhóm đầu tiên mặc định
                if i == 0:
                    self.benefit_type_var.set(type_id)
                    
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách quyền lợi: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def setup_benefit_details_form(self):
        """Tạo form nhập thông tin chi tiết quyền lợi"""
        # Tạo các label
        ttk.Label(self.benefit_details_frame, text="Tên quyền lợi:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        ttk.Label(self.benefit_details_frame, text="Hạn mức:").grid(row=1, column=0, padx=5, pady=2, sticky="e")
        ttk.Label(self.benefit_details_frame, text="Nội dung:").grid(row=2, column=0, padx=5, pady=2, sticky="ne")
        
        # Tạo các ô nhập liệu
        self.benefit_name_entry = ttk.Entry(self.benefit_details_frame)
        self.benefit_limit_entry = ttk.Entry(self.benefit_details_frame)
        self.benefit_desc_text = tk.Text(
            self.benefit_details_frame,
            height=4,
            wrap=tk.WORD,
            font=("Segoe UI", 10)
        )
        
        # Đặt vị trí các ô nhập liệu
        self.benefit_name_entry.grid(row=0, column=1, columnspan=4, padx=5, pady=2, sticky="ew")
        self.benefit_limit_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.benefit_desc_text.grid(row=2, column=1, columnspan=4, padx=5, pady=2, sticky="nsew")
        
        # Nút lưu
        save_btn = ttk.Button(
            self.benefit_details_frame,
            text="Lưu quyền lợi",
            command=self.save_benefit,
            style="Accent.TButton"
        )
        save_btn.grid(row=3, column=4, padx=5, pady=10, sticky="e")
        
        # Cấu hình grid
        self.benefit_details_frame.columnconfigure(1, weight=1)
        self.benefit_details_frame.rowconfigure(2, weight=1)
    
    def on_benefit_type_select(self):
        """Xử lý khi chọn loại quyền lợi"""
        # Có thể thêm xử lý khi chọn loại quyền lợi khác
        pass
    
    def save_benefit(self):
        """Lưu thông tin quyền lợi vào cơ sở dữ liệu"""
        if not self.current_contract:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn hợp đồng trước khi thêm quyền lợi")
            return
            
        ten_quyenloi = self.benefit_name_entry.get().strip()
        han_muc = self.benefit_limit_entry.get().strip()
        mo_ta = self.benefit_desc_text.get("1.0", tk.END).strip()
        nhom_id = self.benefit_type_var.get()
        
        if not ten_quyenloi:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên quyền lợi")
            return
            
        try:
            conn = db.get_db_connection()
            cursor = conn.cursor()
            
            # Thêm quyền lợi vào bảng quyenloi_chitiet
            cursor.execute("""
                INSERT INTO quyenloi_chitiet 
                (hopdong_id, nhom_id, ten_quyenloi, han_muc, mo_ta, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (self.current_contract['id'], nhom_id, ten_quyenloi, han_muc, mo_ta))
            
            conn.commit()
            messagebox.showinfo("Thành công", "Đã thêm quyền lợi mới thành công!")
            
            # Xóa nội dung form
            self.clear_benefit_form()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu quyền lợi: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def create_tooltip(self, widget, text):
        """Tạo tooltip cho widget"""
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry("+0+0")
        tooltip.withdraw()
        
        label = ttk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1, padding=5)
        label.pack()
        
        def enter(event):
            x = widget.winfo_rootx() + widget.winfo_width() // 2
            y = widget.winfo_rooty() + widget.winfo_height()
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.deiconify()
        
        def leave(event):
            tooltip.withdraw()
            
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
    
    def clear_benefit_form(self):
        """Xóa nội dung các trường nhập liệu trong form thêm quyền lợi"""
        if hasattr(self, 'benefit_name_entry'):
            self.benefit_name_entry.delete(0, tk.END)
        if hasattr(self, 'benefit_limit_entry'):
            self.benefit_limit_entry.delete(0, tk.END)
        if hasattr(self, 'benefit_desc_text'):
            self.benefit_desc_text.delete("1.0", tk.END)
    
    def add_new_benefit(self):
        """Xử lý thêm quyền lợi mới"""
        if not self.current_contract:
            return
            
        self.load_benefit_types()
        self.setup_benefit_details_form()
        self.clear_benefit_form()  # Đảm bảo form trống khi thêm mới
