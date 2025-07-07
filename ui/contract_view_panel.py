import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from datetime import datetime   
import database
from utils.date_utils import format_date


class CheckContractPanel(ttk.Frame):
    """Panel chứa chức năng tìm kiếm và hiển thị hợp đồng."""
    def __init__(self, parent, controller):
        super().__init__(parent, padding="10")
        self.controller = controller # Lưu lại controller

        # Title
        title_label = ttk.Label(
            self, 
            text="TÌM KIẾM THÔNG TIN HỢP ĐỒNG", 
            style="Title.TLabel",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(10, 20))

        self.benefit_vars = {} # Dictionary để lưu {group_id: BooleanVar}

        # --- Khung tìm kiếm ---
        search_frame = ttk.LabelFrame(self, text="Tiêu chí tìm kiếm", padding="10", bootstyle="info")
        search_frame.pack(fill='x', pady=5, padx=5)

        # Dòng 1: Tên công ty và Số HĐ
        ttk.Label(search_frame, text="Tên công ty:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.company_entry = ttk.Entry(search_frame, width=40)
        self.company_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        ttk.Label(search_frame, text="Số HĐ:").grid(row=0, column=2, padx=(20, 5), pady=5, sticky='w')
        self.contract_entry = ttk.Entry(search_frame, width=40)
        self.contract_entry.grid(row=0, column=3, padx=5, pady=5, sticky='ew')

        # Dòng 2: Nhóm quyền lợi với Checkboxes
        ttk.Label(search_frame, text="Nhóm quyền lợi:").grid(row=1, column=0, padx=5, pady=5, sticky='nw')
        
        checkbox_frame = ttk.Frame(search_frame)
        checkbox_frame.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky='ewns')
        
        all_benefit_groups = database.get_all_benefit_groups()
        num_columns = 4 # Số cột cho checkbox
        for i, group in enumerate(all_benefit_groups):
            group_id = group['id']
            group_name = group['ten_nhom']
            var = tk.BooleanVar()
            self.benefit_vars[group_id] = var
            
            cb = ttk.Checkbutton(checkbox_frame, text=group_name, variable=var, bootstyle="info")
            row_num = i // num_columns
            col_num = i % num_columns
            cb.grid(row=row_num, column=col_num, padx=5, pady=2, sticky='w')

        # Nút tìm kiếm
        search_button_frame = ttk.Frame(search_frame)
        search_button_frame.grid(row=2, column=0, columnspan=4, pady=10, sticky='e')
        search_button = ttk.Button(search_button_frame, text="Tìm kiếm",bootstyle="outline-info", command=self.perform_search)
        search_button.pack()
        
        # Bind Enter key to perform search
        search_button.bind('<Return>', lambda e: self.perform_search())
        
        # Also bind Enter key to the entry fields
        self.company_entry.bind('<Return>', lambda e: self.perform_search())
        self.contract_entry.bind('<Return>', lambda e: self.perform_search())

        search_frame.columnconfigure(1, weight=1)
        search_frame.columnconfigure(3, weight=1)

        # --- Khung kết quả (Text Area) ---
        result_frame = ttk.LabelFrame(self, text="Kết quả tìm kiếm", padding="10", bootstyle="info")
        result_frame.pack(expand=True, fill='both', pady=(10, 5), padx=5)

        self.result_text = tk.Text(result_frame, wrap='word', height=15, font=("Segoe UI", 10))
        text_scrollbar_y = ttk.Scrollbar(result_frame, orient='vertical', command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=text_scrollbar_y.set)

        self.result_text.pack(side='left', fill='both', expand=True)
        text_scrollbar_y.pack(side='right', fill='y')

        # Thiết lập tag cho việc định dạng
        self.result_text.tag_configure("header", font=("Segoe UI", 11, "bold"))
        self.result_text.tag_configure("subheader", font=("Segoe UI", 10, "italic"))
        self.result_text.tag_configure("benefit", font=("Segoe UI", 10))
        self.result_text.tag_configure("special_card", font=("Segoe UI", 10), lmargin1=20, lmargin2=20)
        self.result_text.tag_configure("separator", font=("Segoe UI", 10), spacing3=10)
        # Giá trị lấy từ database sẽ in nghiêng để dễ nhận diện
        self.result_text.tag_configure("db_value", font=("Segoe UI", 10, "italic"))
        # Giá trị Co-pay cần in đậm để nổi bật
        self.result_text.tag_configure("db_bold", font=("Segoe UI", 10, "bold"))

    def format_date(self, date_str):
        """Chuyển đổi ngày tháng về định dạng DD/MM/YYYY."""
        return format_date(date_str)


    def perform_search(self):
        """Thực hiện tìm kiếm và hiển thị kết quả."""
        # Xóa kết quả cũ và chuyển sang chế độ chỉnh sửa
        self.result_text.config(state='normal')
        self.result_text.delete('1.0', tk.END)

        # Lấy các tiêu chí tìm kiếm
        company_name = self.company_entry.get().strip()
        contract_number = self.contract_entry.get().strip()
        selected_group_ids = [group_id for group_id, var in self.benefit_vars.items() if var.get()]

        # Kiểm tra điều kiện tìm kiếm
        if not company_name and not contract_number and not selected_group_ids:
            Messagebox.show_warning("Vui lòng nhập ít nhất một tiêu chí tìm kiếm.", "Cảnh báo",parent=self)
            return

        results = database.search_contracts(company_name, contract_number, selected_group_ids)

        if not results:
            Messagebox.show_info( "Không tìm thấy hợp đồng nào phù hợp.","Thông báo", parent=self)
        else:
            for i, contract_data in enumerate(results):
                details = contract_data['details']
                waiting_periods = contract_data['waiting_periods']
                benefits = contract_data.get('benefits', [])  # Sử dụng get với giá trị mặc định là list rỗng
                special_cards = contract_data.get('special_cards', [])  # Lấy dữ liệu thẻ đặc biệt

                # Định dạng ngày tháng
                hlbh_tu = format_date(details['HLBH_tu'])
                hlbh_den = format_date(details['HLBH_den'])

                # Dòng tiêu đề hợp đồng
                header = f"{details['tenCongTy']} - {details['soHopDong']} (HL: {hlbh_tu} -> {hlbh_den})\n"
                self.result_text.insert(tk.END, header, "header")

                # Thẻ đặc biệt
                if special_cards:
                    self.result_text.insert(tk.END, "- Thẻ đặc biệt:\n", "subheader")
                    for card in special_cards:
                        card_info = f"  + {card['ten_NDBH']} (Số thẻ: {card['so_the']})"
                        if card['ghi_chu']:
                            card_info += f" - Ghi chú: {card['ghi_chu']}"
                        self.result_text.insert(tk.END, card_info + "\n", "special_card")
                
                # 2. Định dạng Co-pay và SignCF (italic chỉ giá trị phù hợp)
                copay_value = details['coPay']
                # Nhãn Co-pay
                self.result_text.insert(tk.END, "- Co-pay: ", "benefit")
                # Giá trị Co-pay in nghiêng (luôn luôn)
                self.result_text.insert(
                    tk.END,
                    (f"{int(float(copay_value))}%" if str(copay_value).replace('.', '', 1).isdigit() else str(copay_value)) if copay_value else "N/A",
                    "db_bold"
                )

                # Nhãn XN GYCTT
                self.result_text.insert(tk.END, " | XN GYCTT: ", "benefit")
                signcf_val = details['signCF'] if details['signCF'] else "N/A"
                # Điều kiện: nếu value chứa cả '&' và 'ký' thì KHÔNG in nghiêng
                if "&" in signcf_val and "ký" in signcf_val.lower():
                    value_tag = "benefit"
                else:
                    value_tag = "db_value"
                self.result_text.insert(tk.END, signcf_val, value_tag)
                # Xuống dòng
                self.result_text.insert(tk.END, "\n", "benefit")
                
                # Thời gian chờ
                if waiting_periods:
                    self.result_text.insert(tk.END, "- Thời gian chờ:\n", "subheader")
                    for period in waiting_periods:
                        self.result_text.insert(tk.END, f"  + {period[0]}: {period[1]}\n", "benefit")


                # Hiển thị thông tin MR App nếu có
                mr_app_info = details.get('mr_app', '')
                if mr_app_info and mr_app_info != 'Không':
                    self.result_text.insert(tk.END, "- MR App BVDirect: ", "subheader")
                    self.result_text.insert(tk.END, f"{mr_app_info}\n", "benefit")

                # Danh sách quyền lợi
                if benefits:
                    self.result_text.insert(tk.END, "- Quyền lợi:\n", "subheader")
                    for benefit in sorted(benefits):
                        han_muc = f"{benefit[1]:,.0f}" if isinstance(benefit[1], (int, float)) else benefit[1]
                        mo_ta = f"({benefit[2]})" if benefit[2] else ""
                        self.result_text.insert(tk.END, f"  + {benefit[0]}: {han_muc} {mo_ta}\n", "benefit")
                

                
                # Thêm dòng phân cách giữa các hợp đồng
                if i < len(results) - 1:
                    self.result_text.insert(tk.END, "-" * 80 + "\n", "separator")

        # Chuyển về chế độ chỉ đọc
        self.result_text.config(state='disabled')
