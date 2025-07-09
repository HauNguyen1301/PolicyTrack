import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
import database
from PIL import Image, ImageTk

class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.image_path = "image/backgroud.jpeg"
        self.bg_image = None

        # Cấu hình grid của LoginFrame để đẩy canvas ra giữa
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Canvas cho hình nền ---
        self.canvas = ttk.Canvas(self, width=960, height=498, bd=0, highlightthickness=0)
        self.canvas.grid(row=0, column=0)

        # Tải và hiển thị hình nền
        self.load_and_display_background()

        # --- Form đăng nhập ---
        self.create_login_widgets()

    def load_and_display_background(self):
        try:
            # Mở ảnh gốc và resize
            self.original_image = Image.open(self.image_path)
            resized_image = self.original_image.resize((960, 498), Image.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(resized_image)

            # Vẽ hình mới
            self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        except FileNotFoundError:
            self.canvas.create_text(
                480, 249, # Giữa canvas 960x498
                text="Không tìm thấy ảnh nền", font=("Arial", 16), fill="red"
            )
        except Exception as e:
            print(f"Lỗi khi tải ảnh: {e}")

    def create_login_widgets(self):
        # Frame chứa các widget đăng nhập, đặt trên canvas
        # Để làm cho frame và label trong suốt, chúng ta không set background
        login_frame = ttk.Frame(self.canvas, style='TFrame')

        # --- Các widget ---
        # Bỏ background để chữ hiển thị trực tiếp trên ảnh
        ttk.Label(login_frame, text="Đăng Nhập", font=("Arial", 24, "bold"), foreground="white").grid(row=0, column=0, columnspan=2, pady=20)

        ttk.Label(login_frame, text="Tên đăng nhập:", font=("Arial", 12), foreground="white").grid(row=1, column=0, pady=10, padx=10, sticky='w')
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.grid(row=1, column=1, pady=10, padx=10)
        self.username_entry.focus()

        ttk.Label(login_frame, text="Mật khẩu:", font=("Arial", 12), foreground="white").grid(row=2, column=0, pady=10, padx=10, sticky='w')
        self.password_entry = ttk.Entry(login_frame, show="*", width=30)
        self.password_entry.grid(row=2, column=1, pady=10, padx=10)

        self.username_entry.bind('<Return>', self.login)
        self.password_entry.bind('<Return>', self.login)

        ttk.Button(login_frame, text="Đăng nhập", command=self.login, bootstyle="success").grid(row=3, column=0, columnspan=2, pady=20)

        # Đặt frame widget vào giữa-trái canvas
        self.canvas.create_window(330, 249, window=login_frame, anchor="center")

    def clear_entries(self):
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.username_entry.focus()

    def login(self, event=None):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user = database.verify_user(username, password)
        if user:
            self.controller.login_success(user)
        else:
            Messagebox.show_error("Tên đăng nhập hoặc mật khẩu không đúng.", "Lỗi")
