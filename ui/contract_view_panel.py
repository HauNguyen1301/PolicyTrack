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
        self.displayed_contracts = {} # Dictionary để lưu {contract_id: contract_data}

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
        
        # Add instruction label
        instruction_label = ttk.Label(search_button_frame, 
            text="Double click vào hợp đồng để xác thực thông tin lần 2",
            font=("Arial", 10, "italic"),
            foreground="gray"
        )
        instruction_label.pack(side='left', padx=(0, 10))
        
        search_button = ttk.Button(search_button_frame, text="Tìm kiếm",bootstyle="outline-info", command=self.perform_search)
        search_button.pack(side='right')
        
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

        # Gán sự kiện click
        self.result_text.bind("<Button-1>", self._on_result_click)

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
        self.result_text.config(state='normal')
        self.result_text.delete('1.0', tk.END)
        self.displayed_contracts.clear() # Xóa dữ liệu hợp đồng cũ

        company_name = self.company_entry.get().strip()
        contract_number = self.contract_entry.get().strip()
        selected_group_ids = [group_id for group_id, var in self.benefit_vars.items() if var.get()]

        # Kiểm tra xem có nhập ít nhất một trong hai entry không
        if not company_name and not contract_number:
            Messagebox.show_warning("Vui lòng nhập ít nhất một trong hai tiêu chí: Tên công ty hoặc Số HĐ.", "Cảnh báo", parent=self)
            return

        try:
            # Lấy tất cả kết quả không phân biệt nhóm quyền lợi
            results = database.search_contracts(company_name, contract_number, [])
            
            # Nếu có nhóm quyền lợi được chọn, lọc lại kết quả
            if selected_group_ids:
                filtered_results = []
                for result in results:
                    # Kiểm tra xem hợp đồng có quyền lợi thuộc các nhóm được chọn không
                    has_selected_benefit = any(
                        benefit.get('nhom_id') in selected_group_ids 
                        for benefit in result.get('benefits', [])
                    )
                    if has_selected_benefit:
                        filtered_results.append(result)
                results = filtered_results

            if not results:
                Messagebox.show_info("Không tìm thấy hợp đồng nào phù hợp.", "Thông báo", parent=self)
            else:
                for i, contract_data in enumerate(results):
                    contract_id = contract_data.get('details', {}).get('id')
                    if contract_id:
                        self.displayed_contracts[contract_id] = contract_data
                    self._display_single_contract(contract_data, selected_group_ids)
                    if i < len(results) - 1:
                        self.result_text.insert(tk.END, "-" * 80 + "\n", "separator")
        except Exception as e:
            Messagebox.show_error(f"Đã xảy ra lỗi khi tìm kiếm: {e}", "Lỗi", parent=self)
            print(f"Search error: {e}")
        finally:
            self.result_text.config(state='disabled')

    def _display_single_contract(self, contract_data, selected_group_ids=None):
        """Hiển thị thông tin chi tiết cho một hợp đồng."""
        details = contract_data.get('details', {})
        self._display_header(details)
        self._display_special_cards(contract_data.get('special_cards', []))
        self._display_meta_info(details)
        self._display_waiting_periods(contract_data.get('waiting_periods', []))
        self._display_mr_app(details)
        self._display_benefits(contract_data.get('benefits', []), selected_group_ids)

    def _display_header(self, details):
        """Hiển thị tiêu đề chính của hợp đồng, thêm dấu check nếu đã xác thực."""
        contract_id = details.get('id')
        is_verified = details.get('verify_by') is not None

        check_mark = "✓ " if is_verified else ""

        hlbh_tu = format_date(details.get('HLBH_tu'))
        hlbh_den = format_date(details.get('HLBH_den'))
        header = f"{check_mark}{details.get('tenCongTy', 'N/A')} - {details.get('soHopDong', 'N/A')} (HL: {hlbh_tu} -> {hlbh_den})\n"
        
        # Thêm tag chung và tag riêng cho từng hợp đồng
        header_tags = ("header", f"contract_{contract_id}")
        self.result_text.insert(tk.END, header, header_tags)

    def _display_special_cards(self, special_cards):
        """Hiển thị danh sách thẻ đặc biệt."""
        if not special_cards:
            return
        self.result_text.insert(tk.END, "- Thẻ đặc biệt:\n", "subheader")
        for card in special_cards:
            card_info = f"  + {card.get('ten_NDBH', 'N/A')} (Số thẻ: {card.get('so_the', 'N/A')})"
            if card.get('ghi_chu'):
                card_info += f" - Ghi chú: {card['ghi_chu']}"
            self.result_text.insert(tk.END, card_info + "\n", "special_card")

    def _display_meta_info(self, details):
        """Hiển thị thông tin Co-pay và SignCF."""
        copay_value = details.get('coPay')
        copay_display = "N/A"
        if copay_value:
            try:
                copay_display = f"{int(float(copay_value))}%"
            except (ValueError, TypeError):
                copay_display = str(copay_value)
        
        self.result_text.insert(tk.END, "- Co-pay: ", "benefit")
        self.result_text.insert(tk.END, copay_display, "db_bold")

        signcf_val = details.get('signCF', "N/A")
        value_tag = "db_value" if "&" not in signcf_val or "ký" not in signcf_val.lower() else "benefit"
        self.result_text.insert(tk.END, " | XN GYCTT: ", "benefit")
        self.result_text.insert(tk.END, signcf_val, value_tag)
        self.result_text.insert(tk.END, "\n", "benefit")

    def _display_waiting_periods(self, waiting_periods):
        """Hiển thị các quy định về thơi gian chờ."""
        if not waiting_periods:
            return
        self.result_text.insert(tk.END, "- Thời gian chờ:\n", "subheader")
        for period in waiting_periods:
            mo_ta_display = f"- {period.get('mo_ta', '')}" if period.get('mo_ta') else ""
            line = f"  + {period.get('loai_cho', 'N/A')} {mo_ta_display}: {period.get('gia_tri', 'N/A')}\n"
            self.result_text.insert(tk.END, line, "benefit")

    def _display_mr_app(self, details):
        """Hiển thị thông tin về MR App."""
        mr_app_info = details.get('mr_app', '').strip()
        if mr_app_info and mr_app_info.lower() != 'không':
            self.result_text.insert(tk.END, "- MR App BVDirect: ", "subheader")
            self.result_text.insert(tk.END, f"{mr_app_info}\n", "db_value")

    def _display_benefits(self, benefits, selected_group_ids=None):
        """Hiển thị danh sách quyền lợi chi tiết."""
        if not benefits:
            return
            
        # Nếu có nhóm quyền lợi được chọn, lọc quyền lợi
        if selected_group_ids:
            benefits = [benefit for benefit in benefits 
                       if benefit.get('nhom_id') in selected_group_ids]
            
        if not benefits:
            self.result_text.insert(tk.END, "- Không có quyền lợi phù hợp\n", "subheader")
            return
            
        self.result_text.insert(tk.END, "- Quyền lợi:\n", "subheader")
        for benefit_row in sorted(benefits, key=lambda x: x.get('ten_quyenloi', '')):
            ten_ql = benefit_row.get('ten_quyenloi', 'N/A')
            han_muc_val = benefit_row.get('han_muc')
            mo_ta_val = benefit_row.get('mo_ta', '')
            nhom_id = benefit_row.get('nhom_id')  # Lấy nhom_id

            han_muc = f"{han_muc_val:,.0f}" if isinstance(han_muc_val, (int, float)) else str(han_muc_val)
            mo_ta = f"({mo_ta_val})" if mo_ta_val else ""
            
            # Tạo tag riêng cho từng quyền lợi dựa trên nhom_id
            benefit_tag = f"benefit_{nhom_id}" if nhom_id else "benefit"
            
            self.result_text.insert(tk.END, f"  + {ten_ql}: ", benefit_tag)
            self.result_text.insert(tk.END, f"{han_muc} ", "db_bold")
            self.result_text.insert(tk.END, f"{mo_ta}\n", "db_value")

    def _on_result_click(self, event):
        """Xử lý sự kiện khi người dùng click vào kết quả tìm kiếm."""
        try:
            index = self.result_text.index(f"@{event.x},{event.y}")
            tags = self.result_text.tag_names(index)

            contract_id = None
            for tag in tags:
                if tag.startswith("contract_"):
                    contract_id = int(tag.split('_')[1])
                    break
            
            if contract_id and contract_id in self.displayed_contracts:
                self._show_verification_popup(contract_id)

        except (tk.TclError, ValueError, IndexError):
            # Bỏ qua lỗi khi click vào vùng trống hoặc tag không hợp lệ
            pass

    def _show_verification_popup(self, contract_id):
        """Hiển thị popup xác thực hoặc thông báo nếu đã được xác thực."""
        contract_data = self.displayed_contracts[contract_id]
        details = contract_data.get('details', {})

        # 1. Kiểm tra nếu đã được xác thực
        if details.get('verify_by') is not None:
            Messagebox.show_info(
                title="Đã xác thực",
                message="Hợp đồng này đã được xác thực trước đó.",
                parent=self
            )
            return # Dừng lại, không hiển thị popup

        # 2. Kiểm tra xem người tạo hợp đồng có phải là người đang đăng nhập không
        created_by = details.get('created_by')
        current_user_id = self.controller.current_user.get('id')
        
        if created_by == current_user_id:
            Messagebox.show_error(
                title="Không được phép",
                message="Bạn không thể xác thực hợp đồng do chính bạn tạo.",
                parent=self
            )
            return

        # 3. Nếu chưa, hiển thị popup như bình thường
        company_name = details.get('tenCongTy', 'N/A')
        contract_number = details.get('soHopDong', 'N/A')

        # Tạo cửa sổ Toplevel
        popup = ttk.Toplevel(master=self, title="Xác thực hợp đồng")
        popup.transient(self) # Giữ popup luôn ở trên cửa sổ chính
        popup.grab_set() # Chặn tương tác với cửa sổ chính
        popup.geometry("400x150")

        main_frame = ttk.Frame(popup, padding=15)
        main_frame.pack(expand=True, fill='both')

        info_text = f"Công ty: {company_name}\nSố HĐ: {contract_number}"
        ttk.Label(main_frame, text=info_text, justify='left').pack(pady=10, anchor='w')

        def on_verify():
            answer = Messagebox.yesno(
                title="Xác nhận",
                message=f"Bạn có chắc chắn muốn xác thực hợp đồng này cho công ty {company_name}?",
                parent=popup
            )
            if answer == "Yes":
                user_id = self.controller.current_user.get('id')
                if not user_id:
                    Messagebox.show_error("Không tìm thấy thông tin người dùng.", parent=popup)
                    return

                success, message = database.update_contract_verification(contract_id, user_id)
                if success:
                    Messagebox.show_info(message, parent=popup)
                    popup.destroy()
                else:
                    Messagebox.show_error(message, parent=popup)
            else:
                popup.destroy()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side='bottom', fill='x', pady=10)

        verify_button = ttk.Button(button_frame, text="VERIFY", command=on_verify, bootstyle="success")
        verify_button.pack(side='right', padx=5)

        cancel_button = ttk.Button(button_frame, text="Hủy", command=popup.destroy, bootstyle="secondary")
        cancel_button.pack(side='right')
