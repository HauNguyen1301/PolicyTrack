# PolicyTrack

## Overview
PolicyTrack is a desktop application designed to manage insurance contracts, user authentication, and related details such as benefits, waiting periods, and special cards. It provides a user-friendly interface built with `tkinter` and `ttkbootstrap` and connects to a Turso (libsql) database for data storage.

## Features
- User authentication with different roles (admin, user).
- Management of insurance contracts: add, view, update, delete.
- Detailed contract information including company, policy dates, co-pay, and sign-off details.
- Management of waiting periods associated with contracts.
- Management of detailed benefits for each contract, categorized by groups.
- Management of special cards linked to contracts.
- Search functionality for contracts based on various criteria.
- Automatic update checking for new application versions.

## Technologies Used
- Python 3
- `tkinter` and `ttkbootstrap` for the graphical user interface.
- `libsql-client` for connecting to the Turso database.
- `bcrypt` for secure password hashing.
- `requests` for HTTP requests (e.g., update checking).
- `python-dotenv` for environment variable management.
- Turso (libsql) as the primary database.

## Installation

### Prerequisites
- Python 3.8+
- A Turso database instance. You will need its URL and an authentication token.

### Steps
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/HauNguyen1301/PolicyTrack.git
    cd PolicyTrack
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (Note: A `requirements.txt` file is assumed. If not present, you might need to install `ttkbootstrap`, `libsql-client`, `bcrypt`, `requests`, `python-dotenv`, `packaging`, `certifi` manually.)

4.  **Configure Database Connection:**
    Create a `.env` file in the root directory of the project and add your Turso database credentials:
    ```
    TURSO_DATABASE_URL="libsql://your-database-name-your-org.turso.io"
    TURSO_AUTH_TOKEN="your_auth_token"
    ```
    Replace `your-database-name-your-org.turso.io` and `your_auth_token` with your actual Turso database URL and authentication token.

5.  **Initialize the Database (Optional, if not already initialized on Turso):**
    The application expects the database schema to be pre-initialized on the Turso server. The `database.py` script contains an `init_db()` function that can create tables and default users if the database is empty. However, in `main.py`, this call is commented out, implying the schema is managed directly on Turso.
    If you need to initialize your Turso database with the schema, you can manually run the `schema.sql` content against your Turso database using the Turso CLI or a database management tool.

    Default users created by `init_db()`:
    - **Admin User:**
        - Username: `admin`
        - Password: 
        - Role: 
    - **Normal User:**
        - Username: `user`
        - Password: 
        - Role: 

## Usage

### Running the Application
After installation and database configuration, run the application using:
```bash
python main.py
```

## User Guide (Hướng dẫn sử dụng)

### 1. Màn hình Đăng nhập (`LoginFrame`)
-   **Chức năng:** Cho phép người dùng đăng nhập vào hệ thống.
-   **Cách sử dụng:**
    1.  Nhập `Tên đăng nhập` và `Mật khẩu` vào các ô tương ứng.
    2.  Nhấn nút `Đăng nhập` hoặc nhấn `Enter` để xác thực.
-   **Tài khoản mặc định:**
    -   **Admin:** Tên đăng nhập: `admin`, Mật khẩu: `admin`
    -   **Người dùng thường:** Tên đăng nhập: `user`, Mật khẩu: `user`
-   **Lưu ý:** Nếu thông tin đăng nhập không chính xác, một thông báo lỗi sẽ hiển thị.

### 2. Màn hình Ứng dụng chính (`MainApplicationFrame`)
-   **Chức năng:** Là giao diện chính sau khi đăng nhập, chứa các nút điều hướng đến các chức năng quản lý hợp đồng và người dùng.
-   **Các nút chức năng chính:**
    -   **Kiểm tra Hợp đồng:** Mở panel tìm kiếm và xem chi tiết hợp đồng.
    -   **Thêm Hợp đồng mới:** Mở panel để nhập thông tin hợp đồng bảo hiểm mới.
    -   **Thêm Quyền Lợi:** Mở panel để thêm quyền lợi chi tiết cho một hợp đồng đã có.
    -   **Chỉnh sửa Hợp đồng:** Mở một panel lựa chọn để chỉnh sửa hợp đồng chính hoặc quyền lợi.
-   **Các nút quản lý người dùng (chỉ Admin):**
    -   **Quản lý User:** Mở popup để xem, tìm kiếm, đặt lại mật khẩu và thay đổi vai trò của các người dùng hiện có.
    -   **Tạo User Mới:** Mở popup để tạo tài khoản người dùng mới.
-   **Đổi Mật Khẩu:** Mở popup cho phép người dùng hiện tại thay đổi mật khẩu của mình.
-   **Đăng xuất:** Đăng xuất khỏi ứng dụng và quay về màn hình đăng nhập.

### 3. Thêm Hợp đồng mới (`AddContractFrame`)
-   **Chức năng:** Cho phép nhập và lưu thông tin chi tiết của một hợp đồng bảo hiểm mới.
-   **Cách sử dụng:**
    1.  **Thông tin Hợp đồng:**
        -   Điền các trường: `Số Hợp Đồng`, `Tên Công Ty`, `Hiệu lực từ`, `Hiệu lực đến`, `Đồng chi trả (%)`.
        -   Chọn `Đóng dấu trên CF` từ danh sách thả xuống.
    2.  **Quy Định Thời Gian Chờ:**
        -   Sử dụng nút `+` để thêm dòng nhập thời gian chờ.
        -   Chọn loại thời gian chờ từ danh sách và nhập giá trị (ví dụ: "365 ngày").
        -   Nút `New data` cho phép thêm loại thời gian chờ mới vào danh mục.
    3.  **Mở Rộng Bồi Thường Qua App:**
        -   Sử dụng công tắc để bật/tắt tính năng này.
        -   Nếu bật, có thể nhập thêm thông tin chi tiết vào ô `Thông tin chi tiết`.
    4.  **Thẻ Đặc Biệt:**
        -   Sử dụng nút `+` để thêm dòng nhập thông tin thẻ đặc biệt.
        -   Điền `Số thẻ`, `Tên Người Được Bảo Hiểm`, và `Ghi chú` (tùy chọn).
    5.  Sau khi điền đầy đủ thông tin, nhấn `Lưu Hợp Đồng` để lưu vào cơ sở dữ liệu.
    6.  Nhấn `Xóa Form` để xóa tất cả dữ liệu đã nhập trên form.

### 4. Kiểm tra Hợp đồng (`CheckContractPanel`)
-   **Chức năng:** Tìm kiếm và hiển thị thông tin chi tiết của các hợp đồng bảo hiểm.
-   **Cách sử dụng:**
    1.  **Tiêu chí tìm kiếm:**
        -   Nhập `Tên công ty` hoặc `Số HĐ` (hoặc cả hai).
        -   Chọn các `Nhóm quyền lợi` để lọc kết quả theo quyền lợi.
    2.  Nhấn nút `Tìm kiếm` hoặc nhấn `Enter` trong các ô nhập liệu để thực hiện tìm kiếm.
    3.  **Kết quả tìm kiếm:** Các hợp đồng phù hợp sẽ hiển thị trong khung kết quả.
    4.  **Xác thực hợp đồng:** Double click vào một hợp đồng trong danh sách kết quả để mở popup xác thực.
        -   Bạn không thể xác thực hợp đồng do chính mình tạo.
        -   Nếu hợp đồng đã được xác thực, hệ thống sẽ thông báo.
        -   Nếu chưa, bạn có thể nhấn `VERIFY` để xác thực hợp đồng.

### 5. Tính năng Admin (`AdminFeaturesFrame`)
-   **Chức năng:** Cung cấp các công cụ quản lý người dùng cho tài khoản có vai trò `Admin`.
-   **Quản lý User:**
    1.  Mở popup `Quản lý User` từ màn hình chính.
    2.  Sử dụng ô `Tìm kiếm` để lọc danh sách người dùng theo tên đăng nhập hoặc họ và tên.
    3.  Chọn một người dùng từ danh sách.
    4.  **Đặt lại mật khẩu:** Nhấn `Đặt lại mật khẩu`, nhập mật khẩu mới và xác nhận.
    5.  **Đổi vai trò:** Nhấn `Đổi vai trò`, chọn vai trò mới (`Admin`, `Creator`, `Viewer`) và xác nhận.
-   **Tạo User Mới:**
    1.  Mở popup `Tạo User Mới` từ màn hình chính.
    2.  Điền `Tên đăng nhập`, `Họ và tên`, `Mật khẩu` và chọn `Vai trò` cho người dùng mới.
    3.  Nhấn `Tạo User` để hoàn tất.

## Database Schema

The application uses a SQLite-compatible database (Turso). Here's a summary of the main tables:

-   **`users`**: Stores user authentication details, including hashed passwords and roles.
    -   `id`: Primary Key
    -   `username`: Unique username
    -   `full_name`: User's full name
    -   `password`: Hashed password (using bcrypt)
    -   `role`: User role (`admin`, `user`)
    -   `isActive`: Account status (1 for active, 0 for inactive)
    -   `created_at`: Timestamp of creation

-   **`sign_CF`**: Lookup table for "Sign CF" (Confirmation Form) descriptions.
    -   `id`: Primary Key
    -   `mo_ta`: Description of the sign-off type

-   **`thoi_gian_cho`**: Lookup table for different types of waiting periods.
    -   `id`: Primary Key
    -   `loai_cho`: Type of waiting period (e.g., "Bệnh thông thường")
    -   `mo_ta`: Description

-   **`nhom_quyenloi`**: Lookup table for benefit groups.
    -   `id`: Primary Key
    -   `ten_nhom`: Name of the benefit group
    -   `mo_ta`: Description

-   **`hopdong_baohiem`**: Main table for insurance contracts.
    -   `id`: Primary Key
    -   `soHopDong`: Unique contract number
    -   `tenCongTy`: Company name
    -   `HLBH_tu`: Policy start date
    -   `HLBH_den`: Policy end date
    -   `coPay`: Co-payment details
    -   `sign_CF_id`: Foreign key to `sign_CF`
    -   `isActive`: Contract status (1 for active, 0 for inactive)
    -   `created_by`: Foreign key to `users` (who created the contract)
    -   `mr_app`: MR Approval status/notes
    -   `created_at`: Timestamp of creation
    -   `updated_at`: Timestamp of last update

-   **`hopdong_quydinh_cho`**: Junction table linking contracts to waiting periods.
    -   `hopdong_id`: Foreign key to `hopdong_baohiem`
    -   `cho_id`: Foreign key to `thoi_gian_cho`
    -   `gia_tri`: Value/duration of the waiting period
    -   `ghi_chu`: Notes

-   **`quyenloi_chitiet`**: Detailed benefits for each contract.
    -   `id`: Primary Key
    -   `hopdong_id`: Foreign key to `hopdong_baohiem`
    -   `nhom_id`: Foreign key to `nhom_quyenloi`
    -   `ten_quyenloi`: Name of the benefit
    -   `han_muc`: Benefit limit
    -   `mo_ta`: Description
    -   `isActive`: Benefit status
    -   `created_at`: Timestamp of creation

-   **`sothe_dacbiet`**: Special cards associated with contracts.
    -   `id`: Primary Key
    -   `hopdong_id`: Foreign key to `hopdong_baohiem`
    -   `so_the`: Card number
    -   `ten_NDBH`: Name of the insured person
    -   `ghi_chu`: Notes
    -   `created_at`: Timestamp of creation

-   **History Tables (`_history` suffix)**:
    -   `hopdong_baohiem_history`: Logs changes to `hopdong_baohiem`.
    -   `quyenloi_chitiet_history`: Logs changes to `quyenloi_chitiet`.
    These tables store `old_data` and `new_data` as JSON strings for auditing purposes.

## Contributing
(Add instructions for contributing if this is an open-source project)

## License
(Add license information)

## Contact
For questions or support, please contact HauNguyen.

