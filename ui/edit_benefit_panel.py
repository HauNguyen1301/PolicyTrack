from ttkbootstrap import Frame
from ttkbootstrap import ttk

class EditBenefitPanel(Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        label = ttk.Label(
            self,
            text="CHỈNH SỬA QUYỀN LỢI (đang phát triển)",
            style="Title.TLabel",
            font=("Arial", 14, "bold")
        )
        label.pack(padx=10, pady=40, anchor="center")
