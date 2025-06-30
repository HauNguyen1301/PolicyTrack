import sqlite3
import json
import os
from database import get_db_connection

# Thư mục để lưu các tệp JSON
EXPORT_DIR = "data_export"
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)

# Danh sách các bảng cần export
TABLES_TO_EXPORT = [
    'users',
    'config_sign_cf',
    'hopdong_baohiem',
    'nhom_quyenloi',
    'quyenloi_chitiet',
    'sothe_dacbiet',
    'thoi_gian_cho',
    'hopdong_baohiem_history',
    'quyenloi_chitiet_history'
]

def export_data():
    """
    Trích xuất dữ liệu từ tất cả các bảng trong database
    và lưu chúng vào các tệp JSON riêng biệt.
    """
    print("Starting data export process...")
    conn = get_db_connection()
    
    for table_name in TABLES_TO_EXPORT:
        print(f"  - Exporting table: {table_name}...")
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Chuyển đổi sqlite3.Row thành list of dicts, xử lý giá trị bytes
            data = []
            for row in rows:
                row_dict = dict(row)
                for key, value in row_dict.items():
                    if isinstance(value, bytes):
                        # Chuyển đổi bytes thành string để có thể ghi vào JSON
                        row_dict[key] = value.decode('utf-8')
                data.append(row_dict)
            
            if not data:
                print(f"    -> Table '{table_name}' is empty, skipping.")
                continue

            # Ghi dữ liệu vào tệp JSON
            file_path = os.path.join(EXPORT_DIR, f"{table_name}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            print(f"    -> Saved {len(data)} records to '{file_path}'")

        except sqlite3.Error as e:
            # Bỏ qua nếu bảng không tồn tại
            if "no such table" in str(e):
                print(f"    -> Table '{table_name}' does not exist, skipping.")
            else:
                print(f"    -> Error exporting table '{table_name}': {e}")
        except Exception as e:
            print(f"    -> Unknown error processing table '{table_name}': {e}")

    conn.close()
    print("\nData export process finished!")
    print(f"Data has been saved in directory: '{EXPORT_DIR}'")

if __name__ == '__main__':
    export_data()
